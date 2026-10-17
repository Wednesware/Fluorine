> ### Note
> This Document2.0 formatted README.md file was provided by dannywoof, the maintainer of this library. If you have any questions or feedback, feel free to reach out via [bluesky](https://bsky.app/profile/danny.wednesware.org) or [email](mailto:danny@wednesware.org).

[![Wednesware](wednesware.png)](https://wednesware.org)

# Fluorine

An HTML generator with Python helpers for structure, styling, and JavaScript. Version 26.7.

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

Python event handlers require a running host such as Sulfur 26.9. Building an
HTML file does not embed a Python interpreter or serialize Python functions.
HTML, CSS, and JavaScript work independently in a browser.


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
- Nitrogen 26.59+ (`pip install wwn`)

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


## Callback and host contract (26.7)

`page.render()` returns HTML without writing a file. Both `render()` and `build()`
collect Python handlers into `page.callbacks`, a read-only mapping from public
JavaScript API names to callables. Repeated renders preserve names, and bound
methods are deduplicated. Use `functools.partial` to bind arguments without
writing a closure for each button:

```python
from functools import partial
from fluorine import Element, Page

page = Page('controls')

def move(direction):
    print(direction)

page.body(Element('button', 'Left', onclick=partial(move, 'left')),
          Element('button', 'Right', onclick=partial(move, 'right')))
page.build('output/controls.html')

# Optional desktop host, in the same Python process:
from sulfur import App
App('output/controls.html', callbacks=page.callbacks).open()
```

For live updates to the Python element tree, use `App(page)`; Sulfur builds the
HTML and attaches its runtime automatically. With an already-built file, callbacks
can use `app.run(...)`, or you can explicitly attach `page.attach_runtime(app.runtime)`
when the file was generated from that same page. When building and launching in
separate processes, provide the original callback mapping again. Python functions
are never recovered from HTML. Generated callback names may change if the page's
handler order changes, so keep HTML and registry from the same build together.

Callback-enabled documents include a small helper:
`window.fluorine.call(name, ...args)` returns a Promise, waits up to 10 seconds for
a host connection, and rejects with a useful error if the host or callback is
missing. Generated event attributes report rejections to the console. Custom hosts
can call `window.fluorine.connect(api)` with an object of named functions. A
pywebview adapter is also included in this optional helper for compatibility.
Documents with no Python callbacks do not include it.

`Page.attach_runtime(runtime)` accepts any object with `evaluate_js(script)`;
readiness buffering belongs to the host. `detach_runtime()` stops live delivery.
The previous `_attach_window()` hook remains available for older hosts.

## Less repetitive element updates

- `container.replace(*children)` replaces children with one DOM update.
- `button.bind('click', handler)` works before and after the page loads.
- `button.set(disabled=False)` removes the boolean attribute in HTML and the DOM.
- `aria_label='Move left'` and `data_action='move'` generate hyphenated attributes.
- `page.build('nested/path/index.html')` creates missing parent directories.
- Use the existing `@component` decorator for reusable element factories.

See [examples/callbacks.py](examples/callbacks.py) for a complete counter.
Prefer `page.document` over the global `document` proxy when using multiple pages.

## Development

```sh
PYTHONPATH=. python3 -m unittest discover -s tests -v
node tests/test_bridge.js
python3 tools/build_release.py
```

The build produces `dist/fluorine.zip` with the directory layout expected by
Nitrogen. See [CHANGELOG.md](CHANGELOG.md) for compatibility notes.
