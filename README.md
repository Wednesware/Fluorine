> ### Note
> This Document2.0 formatted README.md file was provided by dannywoof, the maintainer of this library. If you have any questions or feedback, feel free to reach out via [bluesky](https://bsky.app/profile/danny.wednesware.org) or [email](mailto:danny@wednesware.org).

[![Wednesware](wednesware.png)](https://wednesware.org)

# Fluorine

A Python webpage framework with built-in structuring, styling, and scripting capabilities.

## Installation

> `n2 get fluorine`

If you don't have Nitrogen: `pipx install wwn` first.

## Quick start

### Basic website

```python
from ww.f import Page
from ww.f.structuring import title, h1

page: Page = Page("index")

page.head(title("Home"))

page.body(h1("Welcome"))

page.build()
```

### Styling

```python
from ww.f import Page
from ww.f.structuring import h1, p
from ww.f.styling import Style

page: Page = Page("index")

page.style("#title",
    color="red",
    background_color=(255, 100, 100)
)

page.body(
    h1("Welcome", id="title"),
    p("This is a styled paragraph.", style=Style(
        padding_top="10px",
        color="#121212"
    )),
)

page.build()
```

### Scripting

```python
from ww.f import Page
from ww.f.structuring import p, button
from ww.f.scripting import Script

page: Page = Page("index")

page.script(Script(
    "console.log('Hello World!')"
))

my_script: Script = Script()
my_script.i = 1
page.script(my_script)

@page.script # Adds the generated Script object to the page
@Script.function # Generates a Script object from the function
def onButtonClick(script: Script) -> None:
    script("i++", "console.log(i)")

page.body(
    p("Click the button to increment i"),
    button("Increment", onclick=onButtonClick),
)

page.build()
```

### Live Reload

```python
from ww.f import Page
from ww.f.livereload import liveReload

liveReload(__file__)

page: Page = Page("index")
page.build()
```

## Dependencies

- Python 3.12+
- [Magnesium](https://github.com/Wednesware/Magnesium)

Install dependencies faster with Nitrogen:

> `n2 getdep fluorine`

# Definitions

## `fluorine`

From the base library, you can import two base classes: `Page` and `Site`.

> `from ww.f import Page, Site`

### `fluorine:Page(name: str = "index")`

A Page is the base of any Fluorine webpage. You can use methods such as `head`, `body`, and `style` to add content to the page. You can also use the `build` method to generate the HTML file.

> `page: Page = Page("about")`

#### `fluorine:Page.head(*contents: str | Element, **args: str)`

Adds content to the head of the page. Should only be called once per page.

> `page.head(title("About Us"), id="page-head")`

#### `fluorine:Page.body(*contents: str | Element, **args: str)`

Adds content to the body of the page. Should only be called once per page.

> `page.body(h1("About Us"), p("Welcome to our website!"), id="page-body")`

#### `fluorine:Page.style(identifier: str = "*", *style_objects: Style, **styles: str)`

Adds a style block to the page. You can either pass `key=value` styling pairs or `Style` objects directly. The identifier is used to specify which elements the styles should apply to. If no identifier is provided, the styles will apply to all elements.

Example identifiers:
1. `*` - all elements
2. `h1` - all `h1` elements
3. `#my-id` - the element with the id `my-id`
4. `.my-class` - all elements with the class `my-class`
5. `div > p` - all `p` elements that are direct children of a `div` element
6. See [CSS Selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) for more information.

Styles also support tuples of RGB values for color specifications.

> `page.style(".styled-text", my_style_object, my_other_style_object, color=(255, 0, 0), font_size="16px")`

#### `fluorine:Page.script(script: Script)`

Adds a script block to the page. If the script was created using `Script.function`, this method returns the original source function.

> `page.script(myScript)`

Can also be used as a decorator when paired with `Script.function`.

> `@page.script`

> `@Script.function`

> `def myScript(script: Script):`

> `    script("console.log('Hello World!')")`

**The `@page.script` decorator must be used first as it expects the script object that `Script.function` returns.**

Because `page.script` returns the original source function, functions created with these decorators can be used as values for attributes such as `onclick`.

> `button("Click Me", onclick=myScript)`

More info on this in the `fluorine.scripting:Script.function` section.

#### `fluorine:Page.build(to: str | FilePath | None = None)`

Generates the HTML file for the page. If no `to` argument is provided, the file will be generated in the current working directory with the name of the page as the filename.

> `page.build("output/about.html")`

### `fluorine:Site(*pages: Page)`

Creates a simple collection of pages. Each page can be retrieved with `Site["page_name"]`.

> `site: Site = Site(page1, page2)`

> `page1 = site["page1"]`

> `for page in site: ...`

## `fluorine.structuring`

A library of all elements and the `Element` base class.

> `from ww.f.structuring import *`

### `fluorine.structuring:Element(tag: str, *contents: str | Element, **args: str)`

The base class for all elements. You can pass the tag and contents + arguments in one declaration like this:

> `my_element: Element = Element("div", "Hello World!", id="my-div")`

Or create an empty element and provide the contents and arguments later like this:

> `my_element_base: Element = Element("div")`

> `my_element = my_element_base("Hello World!", id="my-div")`

### `fluorine.structuring:<element>(*contents: str | Element, **args: str)`

The library also includes an empty Element object for each of the 112 default HTML tags. You can use these to create elements without having to specify the tag name each time.

> `from ww.f.structuring import h1, p, div`

> `h1("Hello World!")`

## `fluorine.styling`

A library for creating CSS styles. You can create a `Style` object and pass it to the `Page.style` method or as a value to a `style=` argument in an `Element` object or `Page.body`/`Page.head` method.

> `from ww.f.styling import Style`

### `fluorine.styling:Style(**styles: str)`

Simple object that converts `key=value` pairs into CSS styles. To convert a `Style` object into a string, you can simply use the `str()` function.

Styles also support tuples of RGB values for color specifications.

> `my_style: Style = Style(color=(255, 0, 0), font_size="16px")`

> `my_style_str: str = str(my_style)`

> `h1("Hello World!", style=my_style)`

## `fluorine.scripting`

A library for creating and managing JavaScript scripts via "fluoscripting".

> `from ww.f.scripting import Script`

### `fluorine.scripting:Script(*lines: str)`

Creates a new script object. You can pass multiple lines of JavaScript code as strings to this constructor.

> `my_script: Script = Script("console.log('Hello, world!')")`

**Scripts can be called after they're initialized. Calling a script object has the same arguments as the constructor.**

> `my_script("console.log('Hello, again!')")`

**By setting an attribute that does not begin with _ on a `Script` object, the provided value is converted to JavaScript and the variable is then available in future lines.**

> `my_script.my_variable = [42, "hello", None]`

> `my_script("console.log(my_variable)")`

> Output: `Array(3) [ 42, "hello", null ]`

### `@fluorine.scripting:Script.function`

This is a **classmethod** (which means you should run `Script.function` on the class itself, not an instance) meant to be used primarily as a decorator.

`Script.function` creates a new JavaScript function and any additions to the script object will be included within the function body.

When used as a decorator, the function right after should expect one argument, `script`, which is a new script object. **The name of the function is important, as it will be used as the name of the JavaScript function in the generated script.**

Using this decorator transforms the function into a `Script` object with the source function located in the `_source_fn` attribute.

## `fluorine.livereload`

A library meant primarily for testing and development. It allows your script to run every time a change is made to it, and is highly recommended to be used alongside the `Five Server` or `Live Server` extensions for VS Code, neither of which are affiliated with Wednesware or Fluorine.

Fluorine's live reload feature works seamlessly with these extensions.

> `from ww.f.livereload import liveReload`

### `fluorine.livereload:liveReload(path: str)`

The `path` argument of this function should always be `__file__`.

Add this function call before any code runs (not including imports):

> `liveReload(__file__)`

You must use the `--livereload` flag when running your script to enable this feature.

> `python my_script.py --livereload`

You can use the `--lrsilent` flag to disable the console output of this function.

> `python my_script.py --livereload --lrsilent`

`liveReload` normally listens for changes every 0.1 seconds, but this can be tweaked if you modify the library code yourself.

# Also check out

- [Nitrogen](https://github.com/Wednesware/Nitrogen) - Easily install Fluorine and ALL other Wednesware publications in a short and simple command.

> `n2 get <publication>`

- [Sulfur](https://github.com/Wednesware/Sulfur) - Convert your Fluorine webpage to a Bue desktop app in two lines using Sulfur.

> `from ww.s.bue import Bue`

> `Bue(page).open()`