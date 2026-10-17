"""Fluorine: Python-authored HTML with a mutable element tree."""
import re
import json
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from types import MappingProxyType
from .structuring import Element, RawHTML, component, head as head_tag, body as body_tag
from .styling import Style, look
from .scripting import Script, document, event

__version__ = '26.7'

try:
    from nitrogen import require
    FilePath = require('magnesium.filepath').FilePath
    Color = require('magnesium.color').Color
except ImportError:
    FilePath = Path
    class Color:
        gray = reset = ''


class Site:
    def __init__(self, *pages): self.pages = list(pages)
    def __truediv__(self, name): return self[name]
    def __iter__(self): return iter(self.pages)
    def __getitem__(self, name):
        for page in self.pages:
            if page.name == name: return page
        raise KeyError(f'Page with name {name!r} not found')


class _HTMLTreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element('html')
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        from .structuring import VOID_TAGS
        node = Element(tag, **dict(attrs))
        self.stack[-1].append(node)
        if tag not in VOID_TAGS: self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        # Self-closing tags must not remain on the parser stack.
        self.stack[-1].append(Element(tag, **dict(attrs)))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break
    def handle_data(self, data):
        # HTMLParser does not decode raw-text contents in script/style tags.
        if self.stack[-1].tag in ('script', 'style'):
            self.stack[-1].append(RawHTML(data))
        else:
            self.stack[-1].append(data)
    def handle_entityref(self, name): self.stack[-1].append(RawHTML('&'+name+';'))
    def handle_charref(self, name): self.stack[-1].append(RawHTML('&#'+name+';'))
    def handle_comment(self, data): self.stack[-1].append(RawHTML('<!--'+data+'-->'))


class Page:
    def __init__(self, name):
        self.name = name
        self.content = [head_tag(), body_tag()]
        self.html_attrs = {}
        self._python_handlers = {}
        self._handler_ids = {}
        self._window = None
        self._queued_js = []
        self._uid_counter = 0
        self.style = self._StyleSetting(self)
        document._page = self

    @staticmethod
    def _parse_html(source):
        parser = _HTMLTreeParser()
        parser.feed(source)
        parser.close()
        nodes = list(parser.root.contents)
        # The parser root represents the document; avoid nesting <html> tags.
        html_nodes = [n for n in nodes if isinstance(n, Element) and n.tag == 'html']
        if html_nodes:
            return list(html_nodes[0].contents), dict(html_nodes[0].args)
        return nodes, {}

    @classmethod
    def from_html(cls, path, name=None):
        path = Path(str(path))
        nodes, html_attrs = cls._parse_html(path.read_text(encoding='utf-8'))
        page = cls(name or path.stem)
        page.html_attrs = html_attrs
        page.content = []
        for node in nodes:
            if isinstance(node, Element) and node.tag in ('head', 'body'):
                existing = next((n for n in page.content if isinstance(n, Element) and n.tag == node.tag), None)
                if existing is None:
                    page.content.append(node)
                else:
                    existing.set(**node.args)
                    existing.append(*node.contents)
            else:
                page._get_tag('body').append(node)
        page._normalize_document()
        return page

    def _normalize_document(self):
        # Keep exactly one head and body, in the correct order.
        head = None
        body = None
        extra = []
        for node in self.content:
            if isinstance(node, Element) and node.tag == 'head':
                if head is None: head = node
                else:
                    head.set(**node.args)
                    head.append(*node.contents)
            elif isinstance(node, Element) and node.tag == 'body':
                if body is None: body = node
                else:
                    body.set(**node.args)
                    body.append(*node.contents)
            else:
                extra.append(node)
        head = head or head_tag()
        body = body or body_tag()
        if extra: body.contents[:0] = extra
        self.content = [head, body]

    def _next_uid(self):
        self._uid_counter += 1
        return 'fl-' + str(self._uid_counter)

    def _get_tag(self, tag):
        for node in self.content:
            if isinstance(node, Element) and node.tag == tag: return node
        node = Element(tag)
        self.content.append(node)
        return node

    def __getitem__(self, selector):
        def matches(node):
            if selector.startswith('#'): return node.args.get('id') == selector[1:]
            if selector.startswith('.'): return selector[1:] in str(node.args.get('class', '')).split()
            return node.tag == selector
        def walk(node):
            if isinstance(node, Element):
                if matches(node): return node
                for child in node.contents:
                    found = walk(child)
                    if found is not None: return found
            return None
        for root in self.content:
            found = walk(root)
            if found is not None: return found
        raise KeyError(f'No element matching {selector!r}')

    @property
    def document(self): return document.bind(self)

    def run(self, script):
        script = str(script).rstrip()
        return self._run(script if script.endswith(';') else script+';')

    def _run(self, script):
        if self._window is not None and hasattr(self._window, 'evaluate_js'):
            return self._window.evaluate_js(script)
        self._queued_js.append(script)
        return None

    def _attach_window(self, window):
        # Compatibility alias; hosts can implement just evaluate_js().
        self.attach_runtime(window)

    def attach_runtime(self, runtime):
        """Attach an optional runtime. Sulfur buffers execution until ready."""
        if not callable(getattr(runtime, 'evaluate_js', None)):
            raise TypeError('Runtime must provide evaluate_js(script)')
        window = runtime
        self._window = window
        for script in self._queued_js:
            if hasattr(window, 'evaluate_js'): window.evaluate_js(script)
        self._queued_js.clear()

    def detach_runtime(self):
        """Return to HTML-generation mode without discarding the element tree."""
        self._window = None

    @property
    def callbacks(self):
        """Read-only snapshot of callbacks registered by render() or build()."""
        return MappingProxyType(dict(self._python_handlers))

    def register_python_handler(self, handler):
        if not callable(handler): raise TypeError('Expected callable')
        # Repeated access to a bound method creates a new method object.
        owner = getattr(handler, '__self__', None)
        function = getattr(handler, '__func__', None)
        key = (id(owner), id(function)) if function is not None else id(handler)
        if key not in self._handler_ids:
            base = re.sub(r'\W|^(?=\d)', '_', getattr(handler, '__name__', 'handler'),
                          flags=re.ASCII) or 'handler'
            name = f'fl_{base}_{len(self._python_handlers)}'
            self._python_handlers[name] = handler
            self._handler_ids[key] = name
            setattr(self, name, handler)
            if self._window is not None and len(self._python_handlers) == 1:
                self._run(Path(__file__).with_name('bridge.js').read_text(encoding='utf-8'))
        name = json.dumps(self._handler_ids[key])
        return f'window.fluorine.call({name}).catch(console.error)'

    def log(self, message): print(f'{message} {Color.gray}(log from page {self.name!r}){Color.reset}')

    def connect(self, path):
        path = Path(str(path))
        extension = path.suffix.lower()
        if extension == '.html':
            nodes, _ = self._parse_html(path.read_text(encoding='utf-8'))
            for node in nodes:
                if isinstance(node, Element) and node.tag in ('head', 'body'):
                    self._get_tag(node.tag).set(**node.args).append(*node.contents)
                else:
                    self.body(node)
        elif extension == '.css':
            self.head(Element('style', RawHTML(path.read_text(encoding='utf-8'))))
        elif extension == '.js':
            self.body(Element('script', RawHTML(path.read_text(encoding='utf-8'))))
        else:
            raise ValueError(f'Unsupported file type: {path}')

    def head(self, *contents, **attrs):
        node = self._get_tag('head')
        node.append(*contents)
        node.set(**attrs)
        return node

    def body(self, *contents, **attrs):
        node = self._get_tag('body')
        node.append(*contents)
        node.set(**attrs)
        return node

    class _StyleSetting:
        def __init__(self, page, prefix=''):
            self.page, self.prefix = page, prefix

        def __getattr__(self, name):
            return type(self)(self.page, self.prefix + '.' + name)

        def __call__(self, identifier='*', *styles, **kwargs):
            selector = self.prefix + identifier if identifier != '*' else (self.prefix or '*')
            declarations = ''.join(str(s) for s in (*styles, Style(**kwargs)))
            self.page.head(Element('style', RawHTML(f'{selector} {{ {declarations} }}')))

    def script(self, script):
        self.body(Element('script', RawHTML('; '.join(script._js_lines) if isinstance(script, Script) else str(script))))

    def bind(self, element, event_name, handler):
        return element.bind(event_name, handler)

    def validate(self):
        issues = []
        ids = set()
        from .structuring import VOID_TAGS
        for tag in ('head', 'body'):
            if sum(isinstance(node, Element) and node.tag == tag for node in self.content) != 1:
                issues.append(f'Expected exactly one {tag} element')

        def walk(node, parent=None):
            if not isinstance(node, Element):
                return
            ident = node.args.get('id')
            if ident:
                if ident in ids:
                    issues.append(f'Duplicate id: {ident}')
                ids.add(ident)
            if node.tag in VOID_TAGS and node.contents:
                issues.append(f'Void element <{node.tag}> has children')
            if parent == 'p' and node.tag in ('div', 'p', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                issues.append(f'Block <{node.tag}> inside <p>')
            for child in node.contents:
                walk(child, node.tag)

        for node in self.content:
            walk(node)
        return issues

    def render(self):
        """Generate HTML and collect callbacks without writing a file."""
        self._normalize_document()
        attrs = ''.join(f' {key}="{escape(str(value), quote=True)}"' if value is not None else f' {key}' for key, value in self.html_attrs.items())
        html = '<!DOCTYPE html><html' + attrs + '>' + ''.join(
            node.__build__(page=self) if isinstance(node, Element) else str(node)
            for node in self.content
        ) + '</html>'
        if self._python_handlers:
            bridge = Path(__file__).with_name('bridge.js').read_text(encoding='utf-8')
            html = html.replace('</head>', '<script>' + bridge + '</script></head>', 1)
        return html

    def build(self, to=None):
        """Write a UTF-8 HTML document, creating parent directories as needed."""
        html = self.render()
        path = Path(str(to or f'{self.name}.html'))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding='utf-8')
        return FilePath(str(path))


__all__ = ['Site', 'Page', 'Style', 'look', 'Script', 'document', 'event', 'Element', 'component']
