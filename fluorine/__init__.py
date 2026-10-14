"""Fluorine: Python-authored HTML with a mutable element tree."""
import re
from html.parser import HTMLParser
from pathlib import Path
from .structuring import Element, RawHTML, component, head as head_tag, body as body_tag
from .styling import Style, look
from .scripting import Script, document, event

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
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break
    def handle_data(self, data): self.stack[-1].append(data)
    def handle_entityref(self, name): self.stack[-1].append(RawHTML('&'+name+';'))
    def handle_charref(self, name): self.stack[-1].append(RawHTML('&#'+name+';'))
    def handle_comment(self, data): self.stack[-1].append(RawHTML('<!--'+data+'-->'))


class Page:
    def __init__(self, name):
        self.name = name
        self.content = [head_tag(), body_tag()]
        self._python_handlers = {}
        self._handler_ids = {}
        self._window = None
        self._queued_js = []
        self._uid_counter = 0
        self.style = self._StyleSetting(self)
        document._page = self

    @classmethod
    def from_html(cls, path, name=None):
        path = Path(str(path))
        parser = _HTMLTreeParser()
        parser.feed(path.read_text(encoding='utf-8'))
        parser.close()
        page = cls(name or path.stem)
        parsed = parser.root.contents
        html_nodes = [c for c in parsed if isinstance(c, Element) and c.tag == 'html']
        page.content = html_nodes[0].contents if html_nodes else parsed
        for tag in ('head', 'body'):
            if not any(isinstance(c, Element) and c.tag == tag for c in page.content):
                page.content.append(Element(tag))
        return page

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
        self._window = window
        for script in self._queued_js:
            if hasattr(window, 'evaluate_js'): window.evaluate_js(script)
        self._queued_js.clear()

    def register_python_handler(self, handler):
        if not callable(handler): raise TypeError('Expected callable')
        key = id(handler)
        if key not in self._handler_ids:
            base = re.sub(r'\W', '_', getattr(handler, '__name__', 'handler'))
            name = f'_fl_{base}_{len(self._python_handlers)}'
            self._python_handlers[name] = handler
            self._handler_ids[key] = name
            setattr(self, name, handler)
        return f'window.pywebview.api.{self._handler_ids[key]}()'

    def log(self, message): print(f'{message} {Color.gray}(log from page {self.name!r}){Color.reset}')

    def connect(self, path):
        path = Path(str(path))
        extension = path.suffix.lower()
        if extension == '.html':
            parser = _HTMLTreeParser(); parser.feed(path.read_text(encoding='utf-8'))
            for node in parser.root.contents:
                if isinstance(node, Element) and node.tag in ('html', 'head', 'body'):
                    for part in (node.contents if node.tag == 'html' else [node]):
                        if isinstance(part, Element) and part.tag in ('head', 'body'):
                            self._get_tag(part.tag).append(*part.contents)
                        else: self.body(part)
                else: self.body(node)
        elif extension == '.css':
            self.head(Element('style', RawHTML(path.read_text(encoding='utf-8'))))
        elif extension == '.js':
            self.body(Element('script', RawHTML(path.read_text(encoding='utf-8'))))
        else: raise ValueError(f'Unsupported file type: {path}')

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
        def __init__(self, page, prefix=''): self.page, self.prefix = page, prefix
        def __getattr__(self, name): return type(self)(self.page, self.prefix+'.'+name)
        def __call__(self, identifier='*', *styles, **kwargs):
            selector = (self.prefix + identifier) if identifier != '*' else (self.prefix or '*')
            declarations = ''.join(str(s) for s in (*styles, Style(**kwargs)))
            self.page.head(Element('style', RawHTML(f'{selector} {{ {declarations} }}')))

    def script(self, script):
        self.body(Element('script', RawHTML('; '.join(script._js_lines) if isinstance(script, Script) else str(script))))

    def bind(self, element, event_name, handler):
        return element.bind(event_name, handler)

    def validate(self):
        issues = []
        ids = set()
        for tag in ('head', 'body'):
            if sum(isinstance(c, Element) and c.tag == tag for c in self.content) != 1:
                issues.append(f'Expected exactly one {tag} element')
        from .structuring import VOID_TAGS
        def walk(node, parent=None):
            if not isinstance(node, Element): return
            ident = node.args.get('id')
            if ident:
                if ident in ids: issues.append(f'Duplicate id: {ident}')
                ids.add(ident)
            if node.tag in VOID_TAGS and node.contents: issues.append(f'Void element <{node.tag}> has children')
            if parent == 'p' and node.tag in ('div', 'p', 'section', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                issues.append(f'Block <{node.tag}> inside <p>')
            for child in node.contents: walk(child, node.tag)
        for node in self.content: walk(node)
        return issues

    def build(self, to=None):
        path = FilePath(to or f'{self.name}.html')
        html = '<!DOCTYPE html><html>' + ''.join(node.__build__(self) if isinstance(node, Element) else str(node) for node in self.content) + '</html>'
        if hasattr(path, 'write'): path.write(html)
        else: Path(str(path)).write_text(html, encoding='utf-8')
        return path


__all__ = ['Site', 'Page', 'Style', 'look', 'Script', 'document', 'event', 'Element', 'component']
