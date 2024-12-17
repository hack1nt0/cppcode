from prompt_toolkit.shortcuts import radiolist_dialog, yes_no_dialog
from prompt_toolkit.shortcuts.dialogs import _create_app
from prompt_toolkit.application.current import get_app
from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import AnyContainer, HSplit, VSplit
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
    
)
from ..taskcrud import getlocaltaskmeta

def confdialog(
) -> Application:
    """
    Display a simple list of element the user can choose amongst.

    Only one element can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """

    task = getlocaltaskmeta()
    tests = task['tests']

    def ok_handler() -> None:
        get_app().exit(result=testtypes.current_value)
    
    def nk_handler():
        get_app().exit()

    testtypes = RadioList(values=[
        (1, 'built-in testcases'.title()),
        (2, 'bruteforce mode'.title()),
        (3, 'compare mode'.title()),
        (4, 'check mode'.title()),
    ], default=None)

    testinput = TextArea(multiline=True, focus_on_click=True, scrollbar=True)
    testanswer = TextArea(multiline=True, focus_on_click=True, scrollbar=True)
    def settest(id):
        if id < len(tests):
            testinput.text = tests[id]['input']
            testanswer.text = tests[id]['output']
        else:
            testinput.text = ''
            testanswer.text = ''

    def nt_handler():
        id = len(testcases_checkbox.values)
        testcases_checkbox.values.append(
            # (id, f'NO. {id+1}'),
            (id, None),
        )
    def et_handler(id):
        def f():
            app = get_app()
            focused_before = app.layout.current_window
            yes_no_dialog("HI").run(in_thread=True)
            app.layout.focus(focused_before)
            settest(id)
        return f

    testcases_checkbox = CheckboxList(values=[
        (0, ''),
        # (1, ''),
    ])

    testcases_buttons = HSplit([
        Button(text='NO. 1', handler=et_handler(0), ),
        Button(text='NO. 2', handler=et_handler(1)),
        Button(text='NO. 1', handler=et_handler(0)),
        Button(text='NO. 1', handler=et_handler(0)),
        Button(text='NO. 1', handler=et_handler(0)),
        Button(text='NO. 1', handler=et_handler(0)),
        Button(text='NO. 1', handler=et_handler(0)),
        Button(text='NO. 2', handler=et_handler(1)),
        Button(text='NO. 2', handler=et_handler(1)),
        Button(text='NO. 2', handler=et_handler(1)),
        Button(text='NO. 2', handler=et_handler(1)),
        Button(text='NO. 2', handler=et_handler(1)),
    ])

    dialog = Dialog(
        title=task['name'].upper(),
        body=HSplit([
                Label(text='test type', dont_extend_height=True), 
                testtypes,
                VSplit([
                    Label(text='solver', dont_extend_height=True, width=D.exact(10)), 
                    TextArea(multiline=False, focus_on_click=True),
                ]),
                VSplit([
                    Label(text='checker', dont_extend_height=True, width=D.exact(10)), 
                    TextArea(multiline=False, focus_on_click=True),
                ]),
                VSplit([
                    HSplit([
                        Label(text='Tests'), 
                        VSplit([
                            testcases_buttons,
                            testcases_checkbox,
                        ]),
                        Button(text='new test', handler=nt_handler),

                    ]),
                    HSplit([
                        Label(text='input'), 
                        testinput,
                        Label(text='answer'), 
                        testanswer,
                    ]),
                ], padding=1, )
            ],
            padding=1,
        ),
        buttons=[
            Button(text='OK', handler=ok_handler),
            Button(text='Cancel', handler=nk_handler),
        ],
        with_background=True,
    )

    return _create_app(dialog, None)