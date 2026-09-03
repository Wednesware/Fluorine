import json


def _js_literal(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return f"'{escaped}'"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_js_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{_js_literal(str(key))}: {_js_literal(item)}" for key, item in value.items()) + "}"
    return _js_literal(str(value))

class _JSValue:
    def __init__(self, page: object | None, expression: str) -> None:
        self._page = page
        self._expression = expression

    @property
    def page(self) -> object | None:
        return self._page

    @property
    def expression(self) -> str:
        return self._expression

    def __repr__(self) -> str:
        return self._expression

    def __str__(self) -> str:
        return self._expression

    def __getattr__(self, name: str) -> "_JSValue":
        js_name = name.replace("ByID", "ById")
        return _JSValue(self._page, f"{self._expression}.{js_name}")

    def __setattr__(self, name: str, value: object) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        if self._page is None:
            raise RuntimeError("This JS value is not bound to a page.")
        self._page._run(f"{self._expression}.{name} = {_js_literal(value)};")

    def __getitem__(self, key: object) -> "_JSValue":
        if isinstance(key, str):
            return _JSValue(self._page, f"{self._expression}.querySelector({_js_literal(key)})")
        return _JSValue(self._page, f"{self._expression}[{_js_literal(key)}]")

    def __setitem__(self, key: object, value: object) -> None:
        if self._page is None:
            raise RuntimeError("This JS value is not bound to a page.")
        self._page._run(f"{self._expression}[{_js_literal(key)}] = {_js_literal(value)};")

    def __call__(self, *args: object, **kwargs: object) -> "_JSValue":
        if self._page is None:
            raise RuntimeError("This JS value is not bound to a page.")
        if kwargs:
            js_args = ", ".join(f"{name}: {_js_literal(value)}" for name, value in kwargs.items())
        else:
            js_args = ", ".join(_js_literal(arg) for arg in args)
        return _JSValue(self._page, f"{self._expression}({js_args})")

class DocumentProxy:
    def __init__(self, page: object | None = None) -> None:
        self._page = page

    def bind(self, page: object) -> "DocumentProxy":
        return DocumentProxy(page)

    def __getattr__(self, name: str) -> _JSValue:
        return _JSValue(self._page, f"document.{name}")

    def __getitem__(self, selector: object) -> _JSValue:
        return _JSValue(self._page, f"document.querySelector({_js_literal(selector)})")

    def __setitem__(self, selector: object, value: object) -> None:
        if self._page is None:
            raise RuntimeError("Document is not bound to a page.")
        self._page._run(f"document.querySelector({_js_literal(selector)}).value = {_js_literal(value)};")

    def __call__(self, *args: object, **kwargs: object) -> _JSValue:
        if self._page is None:
            raise RuntimeError("Document is not bound to a page.")
        if kwargs:
            js_args = ", ".join(f"{name}: {_js_literal(value)}" for name, value in kwargs.items())
        else:
            js_args = ", ".join(_js_literal(arg) for arg in args)
        return _JSValue(self._page, f"document({js_args})")

    def __repr__(self) -> str:
        return "document"

    def __str__(self) -> str:
        return "document"

class Script:
    def __init__(self, *lines: str) -> None:
        self._js_lines: list[str] = list(lines)
        self._source_fn: callable | None = None

    @property
    def handler_name(self) -> str | None:
        if self._source_fn is None:
            return None
        return self._source_fn.__name__

    def as_handler(self) -> str:
        if self._source_fn is None:
            raise ValueError("This Script was not created from Script.function().")
        return f"{self._source_fn.__name__}()"

    def __setattr__(self, name: str, value: any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self(name + " = " + json.dumps(value))

    def __call__(self, *contents: str) -> "Script":
        self._js_lines.extend(contents)
        return self

    def build(self) -> str:
        return f"<script>{'; '.join(self._js_lines)}</script>"

    def __str__(self) -> str:
        return self.build()

class _ScriptEvent:
    def __init__(self, name: str, handler: object) -> None:
        self.name: str = name
        self.handler: object = handler

def event(**events) -> tuple[_ScriptEvent, ...]:
    return tuple(_ScriptEvent(name, handler) for name, handler in events.items())

document: DocumentProxy = DocumentProxy()