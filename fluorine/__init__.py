from ww.mg26_12.filepath import FilePath

from .elements import Element
from .styling import Style


class Site:
    def __init__(self, *pages: "Page") -> None:
        self.pages: list["Page"] = list(pages)
        
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
        
    def head(self, *contents: str | Element, **args: str) -> None: # type: ignore
        attrs: str = " ".join(f'{key}="{value}"' for key, value in args.items())
        self._html_content += f"<head {(' ' + attrs) if attrs else ''}>{''.join([arg.build() if isinstance(arg, Element) else arg for arg in contents])}</head>"
        
    def body(self, *contents: str | Element, **args: str) -> None: # type: ignore
        attrs: str = " ".join(f'{key}="{value}"' for key, value in args.items())
        self._html_content += f"<body {(' ' + attrs) if attrs else ''}>{''.join([arg.build() if isinstance(arg, Element) else arg for arg in contents])}</body>"
        
    def style(self, identifier: str = "*", *style_objects: Style, **styles: str) -> None:
        style_objects += (Style(**styles),)
        self._html_content += f"<style>{identifier} {{ {''.join([str(style) for style in style_objects])} }}</style>"
        
    def build(self, to: str | FilePath | None = None) -> FilePath:
        to = FilePath(to or f"{self.name}.html")
        html_content = f"<!DOCTYPE html><html>{self._html_content}</html>"
        to.write(html_content)
        return to