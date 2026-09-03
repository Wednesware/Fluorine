from .scripting import _ScriptEvent

HTML_TAGS: list[str] = [
    "a", "abbr", "address", "area", "article", "aside", "audio",
    "b", "base", "bdi", "bdo", "blockquote", "body", "br", "button",
    "canvas", "caption", "cite", "code", "col", "colgroup",
    "data", "datalist", "dd", "del", "details", "dfn", "dialog",
    "div", "dl", "dt",
    "em", "embed",
    "fieldset", "figcaption", "figure", "footer", "form",
    "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup",
    "hr", "html",
    "i", "iframe", "img", "input_", "ins",
    "kbd",
    "label", "legend", "li", "link",
    "main", "map_", "mark", "menu", "meta", "meter",
    "nav", "noscript",
    "object_", "ol", "optgroup", "option", "output",
    "p", "picture", "pre", "progress",
    "q",
    "rp", "rt", "ruby",
    "s", "samp", "script", "search", "section", "select",
    "slot", "small", "source", "span", "strong", "style", "sub",
    "summary", "sup",
    "table", "tbody", "td", "template", "textarea", "tfoot", "th",
    "thead", "time", "title", "tr", "track",
    "u", "ul",
    "var", "video",
    "wbr",
]

class Element:
    def __init__(self, tag: str, *contents: str, **args: str) -> None:
        self.tag: str = tag
        self.contents: tuple[str | Element, ...] = contents
        self.args: dict[str, str] = args
        self._event_handlers: dict[str, callable] = {}

    def clone(self) -> "Element":
        clone = Element(self.tag)
        clone.contents = self.contents
        clone.args = dict(self.args)
        clone._event_handlers = dict(self._event_handlers)
        return clone

    def __getattr__(self, class_name: str) -> "Element":
        clone = self.clone()
        current = clone.args.get("class", "").strip()
        clone.args["class"] = f"{current} {class_name}".strip() if current else class_name
        return clone

    def __call__(self, *contents: str | Element, **args: str) -> "Element":
        clone = self.clone()
        clone.contents += contents
        clone.args |= args
        return clone
    
    def _serialize_attr(self, value: object, page: object | None = None) -> str:
        if value is None:
            return ""
        if callable(value):
            if hasattr(value, "as_handler"):
                return value.as_handler()
            if hasattr(value, "__name__"):
                if page is not None and hasattr(page, "register_python_handler"):
                    return page.register_python_handler(value)
                return f"window.pywebview.api.{value.__name__}()"
            raise TypeError(f"Unsupported callable attribute value: {value!r}")
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def __matmul__(self, script_events: tuple[_ScriptEvent, ...]) -> "Element":
        try:
            clone = self.clone()
            for event in script_events:
                if event.handler is None:
                    raise ValueError("Event handlers cannot be None.")
                clone._event_handlers[event.name] = event.handler
                if callable(event.handler):
                    clone.args[event.name] = f"window.pywebview.api.{getattr(event.handler, '__name__', 'handler')}()"
                else:
                    clone.args[event.name] = event.handler
        except TypeError:
            raise TypeError("to create an event, pass '@event(name=handler)'")
        return clone

    def __build__(self, page: object | None = None) -> str:
        if page is not None and hasattr(page, "register_python_handler"):
            for handler in self._event_handlers.values():
                if callable(handler):
                    page.register_python_handler(handler)
        attrs: str = " ".join(
            f'{key}="{self._serialize_attr(value, page)}"'
            if value is not None else key
            for key, value in self.args.items()
        )
        content: str = "".join([arg.__build__(page=page) if isinstance(arg, Element) else str(arg) for arg in self.contents])
        return f"<{self.tag}{' ' + attrs if attrs else ''}>{content}</{self.tag}>"

for tag in HTML_TAGS:
    globals()[tag] = Element(tag)
    
__all__ = HTML_TAGS