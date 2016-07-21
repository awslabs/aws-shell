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
            # Render the line as array of tokens for highlighting
            return self._get_menu_item_tokens(c, is_current)

        return UIContent(
            get_line=get_line,
            line_count=self.height,
            default_char=Char(' ', self.token),
            cursor_position=Point(x=0, y=self._selection or 0)
        )

    def _get_menu_item_tokens(self, option, is_current):
        """Given an option generate the proper token list for highlighting."""
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
    """Construct a layout for the given message and menu control."""
    def get_prompt_tokens(_):
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

    # Show meta information with the buffer isn't done and show_meta is True
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
                    # TODO discuss pygments import voodoo
                    lexer=PygmentsLexer(find_lexer_class('JSON'))
                )
            ),
        )
    ])


class SelectMenuApplication(Application):
    """Wrap Application, providing the correct layout, keybindings, etc."""

    def __init__(self, message, options, *args, **kwargs):
        self._menu_control = SelectMenuControl(options)

        self.kb_manager = KeyBindingManager(
            enable_system_bindings=True,
            enable_abort_and_exit_bindings=True
        )
        menu_control = self._menu_control
        options_meta = kwargs.pop('options_meta', None)

        # Return the currently selected option
        def return_selection(cli, buf):
            cli.set_return_value(menu_control.get_selection())

        buffers = {}

        def_buf = Buffer(
            initial_document=Document(''),
            accept_action=AcceptAction(return_selection)
        )

        buffers[DEFAULT_BUFFER] = def_buf

        show_meta = options_meta is not None
        # Optionally show meta information if present
        if show_meta:
            info_buf = Buffer(is_multiline=True)
            buffers['INFO'] = info_buf

            def selection_changed(cli):
                info = options_meta[buffers[DEFAULT_BUFFER].text]
                formatted_info = json.dumps(info, indent=4, sort_keys=True)
                buffers['INFO'].text = formatted_info
            def_buf.on_text_changed += selection_changed

        # Apply the correct buffers, key bindings, and layout before super call
        kwargs['buffers'] = buffers
        kwargs['key_bindings_registry'] = self.kb_manager.registry
        kwargs['layout'] = create_select_menu_layout(
            message,
            menu_control,
            show_meta=show_meta
        )
        self._bind_keys(self.kb_manager.registry, self._menu_control)
        super(SelectMenuApplication, self).__init__(*args, **kwargs)

    def _bind_keys(self, registry, menu_control):
        handle = registry.add_binding

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
        @handle(Keys.Backspace)
        def _(_):
            pass


def select_prompt(message, options, *args, **kwargs):
    """Construct and run the select menu application, returning the result."""
    app = SelectMenuApplication(message, options, *args, **kwargs)
    return run_application(app)
