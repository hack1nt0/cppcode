from prompt_toolkit.shortcuts import radiolist_dialog, yes_no_dialog
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.application.current import get_app
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import AnyContainer, HSplit, VSplit, WindowAlign, VerticalAlign
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.widgets import (
    Box,
    Button,
    CheckboxList,
    Dialog,
    Label,
    ProgressBar,
    RadioList,
    TextArea,
    ValidationToolbar,
    HorizontalLine,
    
)

def tasksdialog(
    tasks: list[tuple],
    condition: str,
) -> Application:
    """
    Display a simple list of element the user can choose amongst.

    Only one element can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """
    
    def nk_handler():
        get_app().exit()

    def wk_handler(task) -> None:
        return lambda: get_app().exit(result=task)

    colwidths = [max((len(str(task[c])) for task in tasks)) for c in range(2)]
    colformat = f'%{colwidths[0]}s %-{colwidths[1]}s'
    btnwidth = max(len(condition) + 6, colwidths[0] + colwidths[1] + 5)
    taskbuttons = [Button(text=(colformat % (task[0], task[1])), handler=wk_handler(task), width=btnwidth) for task in tasks]
    # for btn in taskbuttons:
    #     print(btn.text)
    #     btn.width = len(btn.text) + 5

    ctimeLabel = Label(text='2014-xx-12')
    mtimeLabel = Label('')
    descLabel = Label('')

    dialog = Dialog(
        title=condition.upper(),
        body=HSplit([
            HSplit(taskbuttons, padding=0),
            HorizontalLine(),
            ctimeLabel,
        ]),
        buttons=[
            Button(text='OK', handler=nk_handler, left_symbol='{', right_symbol='}'),
            Button(text='Cancel', handler=nk_handler),
        ],
        with_background=True,
    )

    return _create_app(dialog, None)