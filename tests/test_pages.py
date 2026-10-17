import tempfile
import unittest
from functools import partial
from pathlib import Path

from fluorine import Element, Page, component


class Runtime:
    def __init__(self):
        self.scripts = []

    def evaluate_js(self, script):
        self.scripts.append(script)


class PageTests(unittest.TestCase):
    def test_static_html_needs_no_host(self):
        page = Page('static')
        page.body(Element('p', '<hello>', aria_label='Greeting', data_test='text'))
        html = page.render()
        self.assertIn('&lt;hello&gt;', html)
        self.assertIn('aria-label="Greeting"', html)
        self.assertIn('data-test="text"', html)
        self.assertNotIn('window.fluorine', html)
        self.assertEqual(dict(page.callbacks), {})

    def test_callbacks_are_stable_distinct_and_read_only(self):
        page = Page('callbacks')
        calls = []
        left, right = partial(calls.append, 'left'), partial(calls.append, 'right')
        page.body(Element('button', 'Left', onclick=left),
                  Element('button', 'Right', onclick=right),
                  Element('button', 'Again', onclick=left))
        html = page.render()
        callbacks = page.callbacks
        self.assertEqual(len(callbacks), 2)
        self.assertTrue(all(not name.startswith('_') for name in callbacks))
        for handler in callbacks.values():
            handler()
        self.assertEqual(calls, ['left', 'right'])
        with self.assertRaises(TypeError):
            callbacks['other'] = left
        self.assertEqual(html, page.render())
        self.assertEqual(dict(callbacks), dict(page.callbacks))

    def test_bound_method_rebinding_reuses_name(self):
        class Controller:
            def move(self):
                return 'moved'
        controller = Controller()
        page = Page('bound')
        first = page.register_python_handler(controller.move)
        self.assertEqual(first, page.register_python_handler(controller.move))
        self.assertEqual(len(page.callbacks), 1)
        with self.assertRaises(TypeError):
            page.register_python_handler(None)

    def test_non_ascii_function_names_generate_portable_api_names(self):
        def déjà_vu():
            return 7
        page = Page('names')
        page.register_python_handler(déjà_vu)
        name, handler = next(iter(page.callbacks.items()))
        self.assertTrue(name.isascii())
        self.assertEqual(handler(), 7)

    def test_build_creates_parent_and_round_trips_unicode(self):
        page = Page('unicode')
        page.body(Element('h1', 'Treasure ◆'))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'nested' / 'page.html'
            page.build(path)
            self.assertIn('Treasure ◆', path.read_text(encoding='utf-8'))
            restored = Page.from_html(path)
            self.assertEqual(restored['h1'].text, 'Treasure ◆')

    def test_runtime_is_optional_and_queued_updates_flush(self):
        page = Page('queued')
        status = Element('p', 'Initial')
        page.body(status)
        page.render()
        status.text = 'Queued'
        page.run('window.ready = true')
        runtime = Runtime()
        page.attach_runtime(runtime)
        self.assertIn('Queued', runtime.scripts[0])
        self.assertEqual(runtime.scripts[1], 'window.ready = true;')
        page.detach_runtime()
        status.text = 'Detached'
        self.assertEqual(len(runtime.scripts), 2)
        self.assertIn('Detached', page.render())

    def test_boolean_attributes_match_static_and_live_html(self):
        page = Page('boolean')
        button = Element('button', 'Move', disabled=True)
        page.body(button)
        self.assertIn(' disabled', page.render())
        runtime = Runtime()
        page.attach_runtime(runtime)
        button.set(disabled=False)
        self.assertIn('removeAttribute("disabled")', runtime.scripts[-1])
        self.assertNotIn(' disabled', page.render())
        button.set(disabled=True)
        self.assertIn('setAttribute("disabled","")', runtime.scripts[-1])

    def test_dynamic_callbacks_and_replace_children(self):
        page = Page('dynamic')
        parent = Element('div')
        page.body(parent)
        page.render()
        runtime = Runtime()
        page.attach_runtime(runtime)
        button = Element('button', 'New', onclick=lambda: 42)
        parent.replace(button)
        self.assertEqual(len(page.callbacks), 1)
        self.assertIn('window.fluorine =', runtime.scripts[0])
        self.assertIn('innerHTML', runtime.scripts[-1])
        button.bind('click', lambda: 43)
        self.assertIn('setAttribute("onclick"', runtime.scripts[-1])
        self.assertNotIn('function ', runtime.scripts[-1])
        self.assertIn('window.fluorine.call', runtime.scripts[-1])

    def test_components_return_independent_elements(self):
        @component
        def card(title):
            return Element('section', Element('h2', title))
        first, second = card('First'), card('Second')
        first.contents[0].text = 'Changed'
        self.assertEqual(second.contents[0].text, 'Second')
        with self.assertRaises(TypeError):
            component(lambda: 'invalid')()


if __name__ == '__main__':
    unittest.main()
