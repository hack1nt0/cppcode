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
            settest(id)
        return f

    testcases_checkbox = CheckboxList(values=[
        (0, 'NO. 1'),
        (1, 'NO. 2'),
    ])
    testcases_checkbox = CheckboxList(values=[
        (0, 'NO. 1'),
        (1, 'NO. 2'),
    ])
    testcases_input = HSplit([
        TextArea(multiline=False, focus_on_click=True, ),
        TextArea(multiline=False, focus_on_click=True, ),
    ], )
    testcases_answer = HSplit([
        TextArea(multiline=False, focus_on_click=True, ),
        TextArea(multiline=False, focus_on_click=True, ),
    ],)

    testcases_edit_buttons = [
        Button(text='NO. 1', handler=et_handler(0), ),
        Button(text='NO. 2', handler=et_handler(1)),
    ]
    testcases_sel_buttons = [
        Button(text='+', handler=et_handler(0), width=3),
        Button(text='-', handler=et_handler(0), width=3),
    ]
    testcases_del_buttons = [
        Button(text='X', handler=et_handler(0), width=3),
        Button(text='X', handler=et_handler(1), width=3),
    ]

    dialog = Dialog(
        title=task['name'].upper(),
        body=HSplit([
                HSplit([
                    Label(text='solver', dont_extend_height=True), 
                    TextArea(multiline=False, focus_on_click=True),
                ], padding=0),
                VSplit([
                    Label(text='cpu (s):', dont_extend_height=True, dont_extend_width=True), 
                    TextArea(multiline=False, focus_on_click=True, ),
                    Label(text='memory (mb):', dont_extend_height=True, dont_extend_width=True), 
                    TextArea(multiline=False, focus_on_click=True),
                ], padding=1),
                HorizontalLine(),
                # Label(text="tests", align=WindowAlign.CENTER),
                Box(HSplit([
                Label(text="C   tests"),
                testcases_checkbox,
                ])),
                # Button(text='new test', handler=nt_handler),
            ],
            padding=1,
            
        ),
        buttons=[
            Button(text='OK', handler=ok_handler, left_symbol='{', right_symbol='}'),
            Button(text='Cancel', handler=nk_handler),
        ],
        with_background=True,
    )

    return _create_app(dialog, None)