"""Generate HTML; optionally launch it with Sulfur using --desktop."""
from functools import partial
import sys

from fluorine import Element, Page

page = Page('counter')
status = Element('p', 'Count: 0', id='count')
count = 0


def change(amount):
    global count
    count += amount
    status.text = f'Count: {count}'


page.body(Element('h1', 'Counter'), status,
          Element('button', '−', onclick=partial(change, -1)),
          Element('button', '+', onclick=partial(change, 1)))

if '--desktop' in sys.argv:
    from sulfur import App
    App(page, name='Counter', width=420, height=280).open()
else:
    page.build('counter.html')
    print('Wrote counter.html. Python buttons require a host such as Sulfur.')
