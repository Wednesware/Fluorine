import re
import sys

from ww.mg26_12.filepath import FilePath
from ww.mg26_12.color import Color

from .structuring import Element
from .styling import Style
from .scripting import Script, document


class Site:
    def __init__(self, *pages: "Page") -> None:
        self.pages: list["Page"] = list(pages)
        
    def __truediv__(self, page: str) -> Page:
        return self[page]

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, name: str) -> "Page":
        for page in self.pages:
            if page.name == name:
                return page
        raise KeyError(f"Page with name '{name}' not found.")


class Page:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self._html_content: str = ""
        self._python_handlers: dict[str, callable] = {}
        self._window: object | None = None
        self._queued_js: list[str] = []
        self.style = self._StyleSetting(self)
        document._page = self

    @property
    def document(self) -> object:
        return document.bind(self)

    def run(self, script: str) -> object | None:
        script = script.rstrip()
        if not script.endswith(";"):
            script += ";"
        return self._run(script)

    def _run(self, script: str) -> object | None:
        if self._window is not None and hasattr(self._window, "evaluate_js"):
            return self._window.evaluate_js(script)
        self._queued_js.append(script)
        return None

    def _attach_window(self, window: object) -> None:
        self._window = window
        for script in self._queued_js:
            if hasattr(window, "evaluate_js"):
                window.evaluate_js(script)
        self._queued_js.clear()

    def _handler_name(self, handler: callable) -> str:
        name: str = getattr(handler, "__name__", "handler") or "handler"
        name = re.sub(r"\W|^(?=\d)", "_", name)
        if not name or not name.isidentifier():
            name = f"handler_{len(self._python_handlers)}"
        return name

    def register_python_handler(self, handler: callable) -> str:
        if not callable(handler):
            raise TypeError(f"Expected a callable handler, got {handler!r}.")
        name: str = self._handler_name(handler)
        self._python_handlers[name] = handler
        setattr(self, name, handler)
        return f"window.pywebview.api.{name}()"

    def _render_attrs(self, **args: object) -> str:
        rendered: list[str] = []
        for key, value in args.items():
            if value is None:
                continue
            if callable(value):
                if hasattr(value, "as_handler"):
                    rendered.append(f'{key}="{value.as_handler()}"')
                elif hasattr(value, "__name__"):
                    rendered.append(f'{key}="{self.register_python_handler(value)}"')
                else:
                    raise TypeError(f"Unsupported callable attribute value: {value!r}")
            else:
                rendered.append(f'{key}="{value}"')
        return " ".join(rendered)
    
    def log(self, message: str) -> None:
        print(f"{message} {Color.gray}(log from page '{self.name}'){Color.reset}")

    def connect(self, path: FilePath | str) -> None:
        path = FilePath(path)
        match str(path).split(".")[-1].lower():
            case "html":
                self._html_content += path.read()
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
            identifier = f"{self.class_name}{identifier}" if self.class_name and identifier != "*" else self.class_name.strip()
            self.page._html_content += f"<style>{identifier} {{ {''.join([str(style) for style in style_objects])} }}</style>"
            self.class_name = ""

    def script(self, script: Script) -> None:
        self._html_content += script.build()

    def bind(self, element: Element, event_name: str, handler: object) -> Element:
        if callable(handler):
            self.register_python_handler(handler)
        return element.bind(event_name, handler)

    def build(self, to: str | FilePath | None = None) -> FilePath | None:
        to = FilePath(to or f"{self.name}.html")
        html_content = f"<!DOCTYPE html><html>{self._html_content}</html>"
        to.write(html_content)
        return to