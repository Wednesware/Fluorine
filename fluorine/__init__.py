"""Fluorine: Python-authored HTML with a mutable element tree."""
import re
from html import escape
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
        self._window = window
        for script in self._queued_js:
            if hasattr(window, 'evaluate_js'): window.evaluate_js(script)
        self._queued_js.clear()

    def register_python_handler(self, handler):
        if not callable(handler): raise TypeError('Expected callable')
        key = id(handler)
        if key not in self._handler_ids or self._python_handlers.get(self._handler_ids[key]) is not handler:
            base = re.sub(r'\W|^(?=\d)', '_', getattr(handler, '__name__', 'handler')) or 'handler'
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

    def connect(self, path: FilePath | str) -> None: # type: ignore
        path = str(path)
        match str(path).split(".")[-1].lower():
            case "html":
                with open(path) as file:
                    content: str = file.read()
                self._html_content += content
            case "css":
                self._html_content += f"<link rel=\"stylesheet\" href=\"{path}\">"
            case "js":
                self._html_content += f"<script src=\"{path}\"></script>"
            case _:
                raise ValueError(f"Unsupported file type for connection: {path}")
    
    def head(self, *contents: str | Element, **args: str) -> None:
        attrs: str = self._render_attrs(**args)
        self._html_content += f"<head{(' ' + attrs) if attrs else ''}>{''.join([arg.__build__(page=self) if isinstance(arg, Element) else str(arg) for arg in contents])}</head>"

    def body(self, *contents: str | Element, **args: str) -> None:
        attrs: str = self._render_attrs(**args)
        self._html_content += f"<body{(' ' + attrs) if attrs else ''}>{''.join([arg.__build__(page=self) if isinstance(arg, Element) else str(arg) for arg in contents])}</body>"

    class _StyleSetting:
        def __init__(self, page: "Page") -> None:
            self.page: "Page" = page
            self.class_name: str = ""
            
        def __getattr__(self, class_name: str) -> "_StyleSetting": # type: ignore
            self.class_name += f".{class_name}"
            return self
            
        def __call__(self, identifier: str = "*", *style_objects: Style, **styles: str) -> None:
            style_objects += (Style(**styles),)
            identifier = self.class_name.strip() if self.class_name and identifier == "*" else f"{self.class_name}{identifier}"
            self.page._html_content += f"<style>{identifier} {{ {''.join([str(style) for style in style_objects])} }}</style>"
            self.class_name = ""

    def script(self, script):
        self.body(Element('script', RawHTML('; '.join(script._js_lines) if isinstance(script, Script) else str(script))))

    def bind(self, element, event_name, handler):
        return element.bind(event_name, handler)

    def build(self, to: str | FilePath | None = None) -> FilePath | None: # type: ignore
        to = FilePath(to or f"{self.name}.html")
        html_content = f"<!DOCTYPE html><html>{self._html_content}</html>"
        to.write(html_content)
        return to
