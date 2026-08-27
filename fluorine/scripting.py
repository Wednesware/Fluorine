import json


class Script:
    def __init__(self, *lines: str) -> None:
        self._js_lines: list[str] = list(lines)
        self._source_fn: callable | None = None
    @classmethod
    def function(cls, fn: callable) -> Script:
        script: Script = cls()
        script._source_fn = fn
        fn(script)
        script._js_lines.insert(0, f"function {fn.__name__}() {{")
        script._js_lines.append("}")
        return script
    def __setattr__(self, name: str, value: any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self(name + " = " + json.dumps(value))
    def __call__(self, *contents: str) -> Script:
        self._js_lines.extend(contents)
        return self
    def build(self) -> str:
        return f"<script>{'; '.join(self._js_lines)}</script>"