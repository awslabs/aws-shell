import json
from pygments.lexers import find_lexer_class
from prompt_toolkit.keys import Keys
from prompt_toolkit.token import Token
from prompt_toolkit.filters import IsDone
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.interface import Application
from prompt_toolkit.filters import to_simple_filter
from prompt_toolkit.layout.screen import Point, Char
from prompt_toolkit.shortcuts import run_application
from prompt_toolkit.layout.lexers import PygmentsLexer
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.buffer import Buffer, AcceptAction
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.layout.controls import UIControl, UIContent, FillControl
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ScrollOffsets, \
    ConditionalContainer

"""An implementation of a selection menu using prompt toolkit.

This is very similar to the original prompt provided by prompt toolkit but has
a few tweaks that are not possible through the parameters exposed by the
library itself.  Selecting an option from a set of options is a different
enough use case that the following features were required: forcing the
selection of one of the options, not allowing the editing of options once
selected, and showing the prompt without any input from the user. Additionally,
it allows us to modify the layout and begin adding a meta information window
similar to the shell's docs.
"""


class SelectMenuControl(UIControl):
    """Given a list, display that list as a drop down menu."""

    # 7 because that's what the default prompt uses
    MIN_WIDTH = 7

    def __init__(self, options):
        self.token = Token.Menu.Completions
        self._options = options
        # Add two to give the list some breathing room
        self.width = max(get_cwidth(o) for o in self._options) + 2
        self.width = max(self.width, self.MIN_WIDTH)
        self.height = len(options)
        self._selection = None

    def get_index(self):
        return self._selection

    def get_selection(self):
        """Return the currently selected option, if there is one."""
        if self._selection is not None:
            return self._options[self._selection]
        else:
            return None

    def select_down(self, event=None):
        """Cycle down the list of options by one."""
        if self._selection is not None:
            self._selection = (self._selection + 1) % self.height
        else:
            self._selection = 0
        self._insert_text(event)

    def select_up(self, event=None):
        """Cycle up the list of options by one."""
        if self._selection is not None:
            self._selection -= 1
            if self._selection < 0:
                self._selection = self.height - 1
        else:
            self._selection = self.height - 1
        self._insert_text(event)

    def _insert_text(self, event):
        if event is not None:
            event.current_buffer.reset()
            event.current_buffer.document = Document(self.get_selection())

    def preferred_width(self, cli, max_available_width):
        """Return the preferred width of this UIControl."""
        return self.width

    def preferred_height(self, cli, width, max_available_height, wrap_lines):
        """Return the preferred height of this UIControl."""
        return self.height

    def create_content(self, cli, width, height):
        """Generate the UIContent for this control.

        Create a get_line function that returns how each line of this control
        should be rendered.
        """
        def get_line(i):
            c = self._options[i]
            is_current = (i == self._selection)
            # Render the line a list of tokens for highlighting
            return self._get_menu_item_tokens(c, is_current)

        return UIContent(
            get_line=get_line,
            line_count=self.height,
            default_char=Char(' ', self.token),
            cursor_position=Point(x=0, y=self._selection or 0)
        )

    def _get_menu_item_tokens(self, option, is_current):
        """Given an option, generate the proper token list for highlighting."""
        # highlight the current selection with a different token
        if is_current:
            token = self.token.Completion.Current
        else:
            token = self.token.Completion
        # pad all lines to the same width
        padding = ' ' * (self.width - len(option))
        return [(token, ' %s%s ' % (option, padding))]


def create_select_menu_layout(msg, menu_control,
                              show_meta=False,
                              reserve_space_for_menu=True):
    """Construct a layout for the given message and menu control.

    :type msg: str
    :param msg: The message to be used when showing the prompt.

    :type msg: :class:`SelectMenuControl`
    :param msg: The menu controller that manages the state and rendering of the
    currently selected option.

    :type show_meta: bool
    :param show_meta: (Optional) Whether or not the meta information should be
    displayed below the prompt.

    :type reserve_space_for_menu: bool
    :param reserve_space_for_menu: (Optional) Whether or not the prompt should
    force that there be enough lines for the completion menu to completely
    render.

    :rtype: :class:`prompt_toolkit.layout.containers.Container`
    :return: The layout to be used for a select menu prompt.
    """
    def get_prompt_tokens(cli):
        return [(Token.Prompt, msg)]

    # Ensures that the menu has enough room to display it's options
    def get_prompt_height(cli):
        if reserve_space_for_menu and not cli.is_done:
            return LayoutDimension(min=8)
        else:
            return LayoutDimension()

    input_processors = [DefaultPrompt(get_prompt_tokens)]
    prompt_layout = FloatContainer(
        HSplit([
            Window(
                BufferControl(input_processors=input_processors),
                get_height=get_prompt_height
            )
        ]),
        [
            Float(
                # Display the prompt starting below the cursor
                left=len(msg),
                ycursor=True,
                content=ConditionalContainer(
                    content=Window(
                        content=menu_control,
                        # only display 1 - 7 lines of completions
                        height=LayoutDimension(min=1, max=7),
                        # display a scroll bar
                        scroll_offsets=ScrollOffsets(top=0, bottom=0),
                        right_margins=[ScrollbarMargin()],
                        # don't make the menu wider than the options
                        dont_extend_width=True
                    ),
                    # Only display the prompt while the buffer is relevant
                    filter=~IsDone()
                )
            )
        ]
    )

    # Show meta information when the buffer isn't done and show_meta is True
    meta_filter = ~IsDone() & to_simple_filter(show_meta)
    return HSplit([
        prompt_layout,
        ConditionalContainer(
            filter=meta_filter,
            content=Window(
                height=LayoutDimension.exact(1),
                content=FillControl(u'\u2500', token=Token.Line)
            )
        ),
        ConditionalContainer(
            filter=meta_filter,
            content=Window(
                # Meta information takes up at most 15 lines
                height=LayoutDimension(max=15),
                content=BufferControl(
                    buffer_name='INFO',
                    # pygments dynamically exports, must use their helper
                    lexer=PygmentsLexer(find_lexer_class('JSON'))
                )
            ),
        )
    ])


class SelectMenuApplication(Application):
    """Wrap Application, providing the correct layout, keybindings, etc."""

    def __init__(self, message, options, *args, **kwargs):
        self.menu_control = SelectMenuControl(options)

        # create and apply needed key bindings
        self._initialize_keys()
        kwargs['key_bindings_registry'] = self.kb_manager.registry

        # create and apply the default and info buffers
        options_meta = kwargs.pop('options_meta', None)
        kwargs['buffers'] = self._initialize_buffers(options, options_meta)

        # create and apply the new layout
        kwargs['layout'] = create_select_menu_layout(
            message,
            self.menu_control,
            show_meta=(options_meta is not None)
        )

        super(SelectMenuApplication, self).__init__(*args, **kwargs)

    def _initialize_buffers(self, options, options_meta):
        # Return the currently selected option
        def return_selection(cli, buf):
            selection = self.menu_control.get_selection()
            index = self.menu_control.get_index()
            cli.set_return_value((selection, index))

        buffers = {}

        default_buf = Buffer(
            initial_document=Document(u''),
            accept_action=AcceptAction(return_selection)
        )

        buffers[DEFAULT_BUFFER] = default_buf

        # Optionally show meta information if present
        if options_meta is not None:
            assert len(options) == len(options_meta)
            info_buf = Buffer(is_multiline=True)
            buffers['INFO'] = info_buf

            def selection_changed(cli):
                index = self.menu_control.get_index()
                info = options_meta[index]
                formatted_info = json.dumps(info, indent=4, sort_keys=True,
                                            ensure_ascii=False)
                buffers['INFO'].text = formatted_info
            default_buf.on_text_changed += selection_changed

        return buffers

    def _initialize_keys(self):
        menu_control = self.menu_control
        self.kb_manager = KeyBindingManager(
            enable_system_bindings=True,
            enable_abort_and_exit_bindings=True
        )
        handle = self.kb_manager.registry.add_binding

        @handle(Keys.F10)
        def handle_f10(event):
            event.cli.set_exit()

        @handle(Keys.Up)
        @handle(Keys.BackTab)
        def handle_up(event):
            menu_control.select_up(event=event)

        @handle(Keys.Tab)
        @handle(Keys.Down)
        def handle_down(event):
            menu_control.select_down(event=event)

        @handle(Keys.ControlJ)
        def accept(event):
            buff = event.current_buffer
            selection = menu_control.get_selection()
            if selection is not None:
                buff.accept_action.validate_and_handle(event.cli, buff)

        @handle(Keys.Any)
        # explicitly rebind backspace to override previous bindings
        @handle(Keys.Backspace)
        def _(_):
            pass


def select_prompt(message, options, *args, **kwargs):
    """Construct and run the select menu application, returning the result.

    :type message: str
    :param message: The message to be used when showing the prompt.

    :type options: list of str
    :param options: The options to be displayed in the drop down list.

    :type options_meta: list of dict
    :param options_meta: (Optional) List of detailed objects for each option in
    the list. This list is parallel to options and must equal in length.

    :rtype: tuple of (str, int)
    :return: The tuple containing the selected option, and its index in the
    list of options.
    """
    runner = kwargs.pop('runner', run_application)
    app = SelectMenuApplication(message, options, *args, **kwargs)
    return runner(app)
