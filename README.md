> ### Note
> Hey y'all, I'm working on a new documentation format that offers more in-depth per-class and per-method information rather than just a simple overview + examples. Make sure to [let me know](mailto:danny@wednesware.org) if you have any feedback!

# Wednesware Fluorine

Webpage framework with a full scripting language and easy to understand syntax.

> `n2 get fluorine`

## Dependencies

- Python 3.12+
- [Magnesium](https://github.com/Wednesware/Magnesium)

> `n2 getdep`

# `fluorine`

From the base library, you can import two base classes: `Page` and `Site`.

> `from fluorine import Page, Site`

## `fluorine:Page(name: str = "index")`

A Page is the base of any Fluorine webpage. You can use methods such as `head`, `body`, and `style` to add content to the page. You can also use the `build` method to generate the HTML file.

> `page: Page = Page("about")`

### `fluorine.Page.head(*contents: str | Element, **args: str)`

Adds content to the head of the page. Should only be run once per page.

> `page.head(title("About Us"), id="page-head")`

### `fluorine.Page.body(*contents: str | Element, **args: str)`

Adds content to the body of the page. Should only be run once per page.

> `page.body(h1("About Us"), p("Welcome to our website!"), id="page-body")`

### `fluorine.Page.style(identifier: str = "*", *style_objects: Style, **styles: str)`

Adds a style block to the page. You can either pass `key=value` styling pairs or `Style` objects directly. The identifier is used to specify which elements the styles should apply to. If no identifier is provided, the styles will apply to all elements.

Example identifiers:
1. `*` - all elements
2. `h1` - all `h1` elements
3. `#my-id` - the element with the id `my-id`
4. `.my-class` - all elements with the class `my-class`
5. `div > p` - all `p` elements that are direct children of a `div` element
6. See [CSS Selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) for more information.

> `page.style(my_style_object, my_other_style_object, color="red", font_size="16px")`

### `fluorine.Page.build(to: str | FilePath | None = None) -> FilePath`

Generates the HTML file for the page. If no `to` argument is provided, the file will be generated in the current working directory with the name of the page as the filename.

> `page.build("output/about.html")`

## `fluorine:Site(*pages: Page)`

Creates a simple list of pages that can be retrieved with `Site["page_name"]`

> `site: Site = Site(page1, page2)`

# `fluorine.elements`

A library of all elements and the `Element` base class.

> `from fluorine.elements import *`

## `fluorine.elements:Element(tag: str, *contents: str | Element, **args: str)`

The base class for all elements. You can pass the tag and contents + arguments in one declaration like this:

> `my_element: Element = Element("div", "Hello World!", id="my-div")`

Or create an empty element and provide the contents and arguments later like this:

> `my_element_base: Element = Element("div")`

> `my_element = my_element_base("Hello World!", id="my-div")`

## `fluorine.elements:<element>(*contents: str | Element, **args: str)`

The library also includes an empty Element object for each of the 112 default HTML tags. You can use these to create elements without having to specify the tag name each time.

> `from fluorine.elements import h1, p, div`

> `h1("Hello World!")`

# `fluorine.styling`

A library for creating CSS styles. You can create a `Style` object and pass it to the `Page.style` method or as a value to a `style=` argument in an `Element` object or `Page.body`/`Page.head` method.

> `from fluorine.styling import Style`

## `fluorine.styling:Style(**styles: str)`

Simple object that converts `key=value` pairs into CSS styles. To convert a `Style` object into a string, you can simply use the `str()` function.

> `my_style: Style = Style(color="red", font_size="16px")`

> `my_style_str: str = str(my_style)`

> `h1("Hello World!", style=my_style)`

# `fluorine.livereload`

A library meant primarily for testing and development. It allows your script to run every time a change is made to it, and is highly recommended to be used alongside the `Five Server` or `Live Server` extensions for VS Code, neither of which are affiliated with Wednesware or Fluorine.

Fluorine's live reload feature works seamlessly with these extensions.

> `from fluorine.livereload import liveReload`

## `fluorine.livereload:liveReload(path: str)`

The `path` argument of this function should always be `__file__`.

Add this function call before any code runs (not including imports):

> `liveReload(__file__)`

You must use the `--livereload` flag when running your script to enable this feature.

You can use the `--lrsilent` flag to disable the console output of this function.

`liveReload` normally listens for changes every 0.1 seconds, but this can be tweaked if you modify the library code yourself.