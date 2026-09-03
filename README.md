> ### Note
> This Document2.0 formatted README.md file was provided by dannywoof, the maintainer of this library. If you have any questions or feedback, feel free to reach out via [bluesky](https://bsky.app/profile/danny.wednesware.org) or [email](mailto:danny@wednesware.org).

[![Wednesware](wednesware.png)](https://wednesware.org)

# Fluorine

A Python webpage framework with built-in structuring, styling, and scripting capabilities.

## Installation

> `n2 get fluorine`

If you don't have Nitrogen: `pipx install wwn` first.

## Quick start

### Basic page

```python
from ww.f import Page
from ww.f.structuring import h1, p

page = Page("index")
page.body(
    h1 ("Hello, world!"),
    p ("This page was generated with Fluorine.")
)
page.build("index.html")
```

### Styling

```python
from ww.f import Page
from ww.f.structuring import h1, p

page = Page("demo")
page.style .title (
    color="gold",
    font_size="32px"
)
page.style("p", color="#d9d9d9")
page.style("#p", color="#ff0000")

page.body(
    h1 .title ("Welcome"),
    p ("A styled paragraph.", id="text")
)
page.build("demo.html")
```

### Event handling and DOM updates

```python
from ww.f import Page
from ww.f.structuring import h1, p, button
from ww.f.scripting import document, event

page = Page("demo")


def handle_click():
    document.getElementById("title").innerHTML = "Updated from Python"
    document["#status"].textContent = "The button worked."
    page.run("document.body.style.background = '#111';")

page.body(
    h1 ("Hello", id="title"),
    p ("Waiting for a click...", id="status"),
    button ("Click me!") @ event(onclick=handle_click),
)

page.build("demo.html")
```

## Dependencies

- Python 3.12+
- pywebview
- Magnesium / ww.mg26_12 utilities

# Definitions

## `fluorine`

From the base library, you can import the core page objects and helpers.

> `from ww.f import Page, Site`

### `fluorine:Page(name: str)`

The `Page` object represents one HTML document. It stores the generated page content, manages event handlers, and can be written to a file with `build()`.

> `page = Page("index")`

#### `fluorine:Page.head(*contents: str | Element, **attrs: str)`

Adds content to the document head.

> `page.head(title ("My page"), id="page-head")`

#### `fluorine:Page.body(*contents: str | Element, **attrs: str)`

Adds content to the document body.

> `page.body(h1 ("Hello"), p ("World"), id="main")`

#### `fluorine:Page.style(selector: str = "*", *style_objects: Style, **styles: str)`

Adds CSS rules to the page. The selector can target tags, ids, classes, or any CSS selector.

> `page.style("h1", color="gold", font_size="32px")`

#### `fluorine:Page.connect(path: str | FilePath)`

Includes an external HTML, CSS, or JavaScript file in the page output.

> `page.connect("styles.css")`

#### `fluorine:Page.script(script: Script)`

Adds a script block to the page.

> `page.script(Script("console.log('ready');"))`

#### `fluorine:Page.bind(element: Element, event_name: str, handler: callable)`

Registers a Python callable against a DOM event for a given element.

> `page.bind(button ("Run"), "onclick", handle_click)`

#### `fluorine:Page.document`

Exposes a page-bound JavaScript document proxy so Python can target DOM elements directly.

> `page.document.getElementById("title").innerHTML = "Updated title"`

#### `fluorine:Page.run(script: str)`

Queue or execute a JavaScript snippet immediately when a window is attached.

> `page.run("document.body.style.background = '#111';")`

#### `fluorine:Page.log(message: str)`

Prints a log message to the console.

> `page.log("Page initialized")`

#### `fluorine:Page.build(to: str | FilePath | None = None)`

Builds the HTML file and returns the target path.

> `page.build("output/index.html")`

### `fluorine:Site(*pages: Page)`

A simple collection of pages that can be accessed by name. Pages can be retrieved using `site / "page_name"` or `site["page_name"]`.

> `site = Site(home, about)`

## `fluorine.structuring`

From the structuring library, you can import the HTML element builder helpers.

> `from ww.f.structuring import Element, h1, p, button, div`

### `fluorine.structuring:Element(tag: str, *contents: str | Element, **attrs: str)`

The base HTML element builder used by all generated tag helpers. You can bind an event to an element with `@event(name=handler)`. `event` can be imported from the `scripting` module.

> `row = Element("div", "Hello", id="row")`

### `fluorine.structuring:<element>(*contents: str | Element, **attrs: str)`

Fluorine exposes a generated object for common HTML tags, including `h1`, `p`, `button`, `div`, `span`, `section`, `table`, and more.

> `heading = h1 ("Hello")`

## `fluorine.styling`

From the styling library, you can import the CSS helper object.

> `from ww.f.styling import Style`

### `fluorine.styling:Style(**styles: str)`

Creates a CSS declaration block from keyword arguments.

> `style = Style(color="gold", padding="10px")`

#### `fluorine.styling:Style.__str__()`

Returns the serialized CSS string.

> `css = str(style)`

## `fluorine.scripting`

From the scripting library, you can import JavaScript helpers and DOM accessors.

> `from ww.f.scripting import Script, event, document`

### `fluorine.scripting:Script(*lines: str)`

Builds a JavaScript snippet or script block.

> `script = Script("console.log('ready');")`

#### `fluorine.scripting:Script.__call__(*contents: str)`

Adds more JavaScript lines to the script.

> `script("count += 1", "console.log(count)")`

#### `fluorine.scripting:Script.__setattr__(name: str, value: object)`

Assigns Python values to generated JavaScript variables.

> `script.count = 0`

### `fluorine.scripting:event(**events)`

Creates a tuple of event metadata objects that can be applied to an element with `@`.

> `button("Click me!") @ event(onclick=handle_click)`

### `fluorine.scripting:document`

A global document-style proxy that targets browser DOM elements from Python. It supports `getElementById`, `querySelector`, property assignment, and direct JS-like property access. Supports selector lookup through `document["#status"]`.

> `document.getElementById("status").innerHTML = "Updated"`

#### `fluorine.scripting:document.getElementById(element_id: str)`

Returns a JS-like element wrapper for the target DOM node.

> `element = document.getElementById("title")`

## `fluorine.livereload`

From the live reload helper, you can import the development watcher.

> `from ww.f.livereload import live_reload`

### `fluorine.livereload:live_reload(path: str)`

Watches a file for changes and re-runs the script when `--livereload` is passed in.

> `live_reload(__file__)`