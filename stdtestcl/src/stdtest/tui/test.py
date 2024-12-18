#!/usr/bin/env python
"""
A simple application that shows a Pager application.
"""

from pygments.lexers.python import PythonLexer

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension as D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea
from prompt_toolkit.filters import Condition, has_focus, vi_insert_mode, vi_navigation_mode
from prompt_toolkit.application import get_app

# Create one text buffer for the main content.

_pager_py_path = __file__


with open(_pager_py_path, "rb") as f:
    text = f.read().decode("utf-8")


def get_toptoolbar_text():
    return [
        ("class:status", _pager_py_path + " - "),
        (
            "class:status.position",
            f"{text_area.document.cursor_position_row + 1}:{text_area.document.cursor_position_col + 1}",
        ),
        ("class:status", " - Press "),
        ("class:status.key", "Ctrl-C"),
        ("class:status", " to exit, "),
        ("class:status.key", "/"),
        ("class:status", " for searching."),
    ]

def get_bottoolbar_text():
    return [
        ("class:status.key", "F4"),
        ("class:status", f" {app.editing_mode.value} [{app.vi_state.input_mode.value}] "),
    ]


search_field = SearchToolbar(
    text_if_not_searching=[("class:not-searching", "Press '/' to start searching.")]
)


text_area = TextArea(
    text=text,
    read_only=False,
    scrollbar=True,
    # line_numbers=True,
    search_field=search_field,
    # lexer=PygmentsLexer(PythonLexer),
    wrap_lines=False,
)


root_container = HSplit(
    [
        # The top toolbar.
        Window(
            content=FormattedTextControl(get_toptoolbar_text),
            height=D.exact(1),
            style="class:status",
        ),
        # The main content.
        text_area,
        search_field,
        # The top toolbar.
        Window(
            content=FormattedTextControl(get_bottoolbar_text),
            height=D.exact(1),
            style="class:status",
        ),
    ]
)


# Key bindings.
bindings = KeyBindings()


@bindings.add("c-c")
def _(event):
    "Quit."
    event.app.exit()

# # Filters.
# @Condition
# def vi_buffer_focussed():
#     app = get_app()
#     return app.layout.has_focus(text_area)

# in_insert_mode = vi_insert_mode & vi_buffer_focussed
# in_navigation_mode = vi_navigation_mode & vi_buffer_focussed


# @bindings.add("j", )
# def _(event):
#     # import sys
#     # print(dir(event), file=sys.stderr, flush=True)
#     b = event.app.current_buffer
#     b.cursor_down()


style = Style.from_dict(
    {
        "status": "reverse",
        "status.position": "#aaaa00",
        "status.key": "#ffaa00",
        "not-searching": "#888888",
    }
)


# create application.
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.enums import EditingMode

app = Application(
    layout=Layout(root_container, focused_element=text_area),
    key_bindings=bindings,
    enable_page_navigation_bindings=True,
    mouse_support=True,
    style=style,
    full_screen=True,
    editing_mode=EditingMode.VI,
)

def run():
    app.run()


if __name__ == "__main__":
    run()
