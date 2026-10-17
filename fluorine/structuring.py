"""Fluorine HTML element tree, with optional live DOM synchronization."""
from html import escape
import json
import re
from .styling import Style
from .scripting import _ScriptEvent

HTML_TAGS = '''a abbr address area article aside audio b base bdi bdo blockquote body br button canvas caption cite code col colgroup data datalist dd del details dfn dialog div dl dt em embed fieldset figcaption figure footer form h1 h2 h3 h4 h5 h6 head header hgroup hr html i iframe img input_ ins kbd label legend li link main map_ mark menu meta meter nav noscript object_ ol optgroup option output p picture pre progress q rp rt ruby s samp script search section select slot small source span strong style sub summary sup table tbody td template textarea tfoot th thead time title tr track u ul var video wbr'''.split()
VOID_TAGS = set('area base br col embed hr img input link meta source track wbr'.split())
ALIASES = {'input_': 'input', 'map_': 'map', 'object_': 'object'}


def _attr_name(name):
    if name.startswith(('aria_', 'data_')):
        return name.replace('_', '-')
    return {'class_': 'class', 'for_': 'for', 'http_equiv': 'http-equiv'}.get(name, name.rstrip('_') if name.endswith('_') else name)


class _ElementStyle:
    def __init__(self, element): self.element = element
    def __setattr__(self, name, value):
        if name == 'element': object.__setattr__(self, name, value); return
        self.element._styles[name.replace('_', '-')] = value
        self.element._sync('style', name.replace('_', '-'), value)
    def __getattr__(self, name): return self.element._styles.get(name.replace('_', '-'))
    def __call__(self, **styles):
        for k, v in styles.items(): setattr(self, k, v)
        return self.element


class Element:
    def __init__(self, tag, *contents, **args):
        object.__setattr__(self, 'tag', ALIASES.get(tag, tag))
        object.__setattr__(self, 'contents', list(contents))
        object.__setattr__(self, 'args', {_attr_name(k): v for k, v in args.items()})
        object.__setattr__(self, '_styles', {})
        object.__setattr__(self, '_page', None)
        object.__setattr__(self, '_uid', None)
        object.__setattr__(self, '_events', {})
        object.__setattr__(self, 'style', _ElementStyle(self))

    def __setattr__(self, name, value):
        if name in ('tag', 'contents', 'args', 'style', 'text', 'html') or name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            # Attribute assignments update the HTML tree and the live DOM.
            self.set(**{name: value})

    def clone(self):
        copy = Element(self.tag, *(c.clone() if isinstance(c, Element) else c for c in self.contents), **self.args)
        copy._styles.update(self._styles)
        copy._events.update(self._events)
        return copy

    def __getattr__(self, name):
        # Preserve Fluorine's .classname shorthand on template elements.
        if name.startswith('_'): raise AttributeError(name)
        copy = self.clone()
        copy.args['class'] = (str(copy.args.get('class', '')) + ' ' + name).strip()
        return copy

    def __call__(self, *contents, **args):
        copy = self.clone()
        copy.contents.extend(contents)
        copy.args.update({_attr_name(k): v for k, v in args.items()})
        return copy

    @property
    def text(self): return ''.join(str(c) for c in self.contents if not isinstance(c, Element))
    @text.setter
    def text(self, value):
        self.contents = [str(value)]
        self._sync('text', None, str(value))

    @property
    def html(self): return ''.join(c.__build__() if isinstance(c, Element) else str(c) for c in self.contents)
    @html.setter
    def html(self, value):
        self.contents = [RawHTML(str(value))]
        self._sync('html', None, str(value))

    def append(self, *children):
        self.contents.extend(children)
        if self._page and self._uid is not None:
            self._sync('html', None, self._inner_html(self._page))
        return self

    def replace(self, *children):
        """Replace children with one DOM update, preserving element objects."""
        self.contents = list(children)
        if self._page and self._uid is not None:
            self._sync('html', None, self._inner_html(self._page))
        return self

    def clear(self):
        self.contents.clear()
        self._sync('html', None, '')
        return self

    def set(self, **attrs):
        for name, value in attrs.items():
            key = _attr_name(name)
            self.args[key] = value
            self._sync('attr', key, value)
        return self

    def bind(self, event_name, handler):
        event_name = event_name.lower()
        if not event_name.startswith('on'):
            event_name = 'on' + event_name
        self._events[event_name] = handler
        self.args[event_name] = handler
        self._sync('attr', event_name, handler)
        return self

    def __matmul__(self, modifiers):
        copy = self.clone()
        if isinstance(modifiers, (Style, _ScriptEvent)): modifiers = (modifiers,)
        for mod in modifiers:
            if isinstance(mod, Style): copy._styles.update({k.replace('_', '-'): v for k, v in mod.styles.items()})
            elif isinstance(mod, _ScriptEvent): copy.bind(mod.name, mod.handler)
            else: raise TypeError(f'Unsupported @ modifier: {mod!r}')
        return copy

    def _sync(self, action, key, value):
        page = self._page
        if page is None or self._uid is None: return
        js = ('(function(){const e=document.querySelector(' + json.dumps('[data-fluorine-id="' + self._uid + '"]') + ');if(!e)return;')
        if action == 'text': js += 'e.textContent=' + json.dumps(value) + ';'
        elif action == 'html': js += 'e.innerHTML=' + json.dumps(value) + ';'
        elif action == 'style': js += 'e.style.setProperty(' + json.dumps(key) + ',' + json.dumps(str(value)) + ');'
        elif action == 'attr':
            if callable(value):
                value = value.as_handler() if hasattr(value, 'as_handler') else page.register_python_handler(value)
            if value is None or value is False:
                js += 'e.removeAttribute(' + json.dumps(key) + ');'
            else:
                js += 'e.setAttribute(' + json.dumps(key) + ',' + json.dumps('' if value is True else str(value)) + ');'
        page._run(js + '})();')

    def _inner_html(self, page=None):
        return ''.join(c.__build__(page) if isinstance(c, Element) else str(c) if isinstance(c, RawHTML) else escape(str(c)) for c in self.contents)

    def __build__(self, page=None):
        if page is not None:
            self._page = page
            if self._uid is None: self._uid = page._next_uid()
        attrs = dict(self.args)
        if self._styles:
            existing = attrs.get('style', '')
            attrs['style'] = (str(existing).rstrip(';') + '; ' if existing else '') + str(Style(**{k.replace('-', '_'): v for k, v in self._styles.items()}))
        if self._uid is not None: attrs['data-fluorine-id'] = self._uid
        rendered = []
        for key, value in attrs.items():
            if value is None or value is False: continue
            if callable(value):
                if hasattr(value, 'as_handler'): value = value.as_handler()
                elif page is not None: value = page.register_python_handler(value)
                else: value = f'window.pywebview.api.{getattr(value, "__name__", "handler")}()'
            if value is True: rendered.append(key); continue
            rendered.append(f'{key}="{escape(str(value), quote=True)}"')
        start = '<' + self.tag + (' ' + ' '.join(rendered) if rendered else '') + '>'
        if self.tag in VOID_TAGS: return start
        return start + self._inner_html(page) + '</' + self.tag + '>'


class RawHTML:
    def __init__(self, html): self.html = html
    def __str__(self): return self.html


def component(fn):
    """Mark a factory that returns a Fluorine Element."""
    from functools import wraps
    @wraps(fn)
    def factory(*args, **kwargs):
        result = fn(*args, **kwargs)
        if not isinstance(result, Element): raise TypeError('Components must return an Element')
        return result
    return factory


for _name in HTML_TAGS:
    globals()[_name] = Element(_name)

__all__ = HTML_TAGS + ['Element', 'RawHTML', 'component']

