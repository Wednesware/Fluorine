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
    def __call__(self, *contents: str | Element, **args: str) -> "Element":
        self.contents += contents
        self.args |= args
        return self
    def build(self) -> str:
        attrs: str = " ".join(f'{key}="{value}"' for key, value in self.args.items())
        content: str = "".join([arg.build() if isinstance(arg, Element) else arg for arg in self.contents])
        return f"<{self.tag} {attrs}>{content}</{self.tag}>"

for tag in HTML_TAGS:
    globals()[tag] = Element(tag)
    
__all__ = HTML_TAGS