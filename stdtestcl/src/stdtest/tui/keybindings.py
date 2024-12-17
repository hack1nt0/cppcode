
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition, has_focus, vi_insert_mode, vi_navigation_mode
from prompt_toolkit.application import get_app

# Key bindings.
bindings = KeyBindings()


@bindings.add("c-c")
def _(event):
    "Quit."
    event.app.exit()

# Filters.
@Condition
def vi_buffer_focussed():
    app = get_app()
    return app.layout.has_focus(text_area)

in_insert_mode = vi_insert_mode & vi_buffer_focussed
in_navigation_mode = vi_navigation_mode & vi_buffer_focussed

@bindings.add("j", )
def _(event):
    # import sys
    # print(dir(event), file=sys.stderr, flush=True)
    b = event.app.current_buffer
    b.cursor_down()