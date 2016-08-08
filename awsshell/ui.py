from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER
from prompt_toolkit.filters import IsDone, HasFocus, Always, \
    RendererHeightIsKnown, to_cli_filter, Filter
from prompt_toolkit.layout import Window, HSplit, VSplit, FloatContainer, Float
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, \
    TokenListControl, FillControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.menus import CompletionsMenu, \
    MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import PasswordProcessor, \
    HighlightSearchProcessor, HighlightSelectionProcessor, \
    ConditionalProcessor, AppendAutoSuggestion
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.layout.toolbars import ValidationToolbar, \
    SystemToolbar, ArgToolbar, SearchToolbar
from prompt_toolkit.layout.utils import explode_tokens
from prompt_toolkit.layout.lexers import PygmentsLexer
from pygments.token import Token
from pygments.lexer import Lexer

from awsshell.compat import text_type


# This is borrowed from prompt_toolkit because we actually
# need to mess with the layouts to get documentation pulled up.
def create_default_layout(app, message='',
                          lexer=None, is_password=False,
                          reserve_space_for_menu=False,
                          get_prompt_tokens=None,
                          get_bottom_toolbar_tokens=None,
                          display_completions_in_columns=False,
                          extra_input_processors=None, multiline=False):
    """
    Generate default layout.

    Returns a ``Layout`` instance.

    :param message: Text to be used as prompt.
    :param lexer: Lexer to be used for the highlighting.
    :param is_password: `bool` or `CLIFilter`. When True, display input as '*'.
    :param reserve_space_for_menu: When True, make sure that a minimal height
        is allocated in the terminal, in order to display the completion menu.
    :param get_prompt_tokens: An optional callable that returns the tokens to
        be shown in the menu. (To be used instead of a `message`.)
    :param get_bottom_toolbar_tokens: An optional callable that returns the
        tokens for a toolbar at the bottom.
    :param display_completions_in_columns: `bool` or `CLIFilter`. Display the
        completions in multiple columns.
    :param multiline: `bool` or `CLIFilter`. When True, prefer a layout that is
        more adapted for multiline input. Text after newlines is automatically
        indented, and search/arg input is shown below the input, instead of
        replacing the prompt.
    """
    assert isinstance(message, text_type)
    assert (get_bottom_toolbar_tokens is None or
            callable(get_bottom_toolbar_tokens))
    assert get_prompt_tokens is None or callable(get_prompt_tokens)
    assert not (message and get_prompt_tokens)

    display_completions_in_columns = to_cli_filter(
        display_completions_in_columns)
    multiline = to_cli_filter(multiline)

    if get_prompt_tokens is None:
        get_prompt_tokens = lambda _: [(Token.Prompt, message)]

    get_prompt_tokens_1, get_prompt_tokens_2 = _split_multiline_prompt(
        get_prompt_tokens)

    # `lexer` is supposed to be a `Lexer` instance. But if a Pygments lexer
    # class is given, turn it into a PygmentsLexer. (Important for
    # backwards-compatibility.)
    try:
        if issubclass(lexer, Lexer):
            lexer = PygmentsLexer(lexer)
    except TypeError:
        # Happens when lexer is `None` or an instance of something else.
        pass

    # Create processors list.
    # (DefaultPrompt should always be at the end.)
    input_processors = [
        ConditionalProcessor(
            # By default, only highlight search when the search
            # input has the focus. (Note that this doesn't mean
            # there is no search: the Vi 'n' binding for instance
            # still allows to jump to the next match in
            # navigation mode.)
            HighlightSearchProcessor(preview_search=Always()),
            HasFocus(SEARCH_BUFFER)),
        HighlightSelectionProcessor(),
        ConditionalProcessor(
            AppendAutoSuggestion(), HasFocus(DEFAULT_BUFFER) & ~IsDone()),
        ConditionalProcessor(PasswordProcessor(), is_password)
    ]

    if extra_input_processors:
        input_processors.extend(extra_input_processors)

    # Show the prompt before the input (using the DefaultPrompt processor.
    # This also replaces it with reverse-i-search and 'arg' when required.
    # (Only for single line mode.)
    input_processors.append(ConditionalProcessor(
        DefaultPrompt(get_prompt_tokens), ~multiline))

    # Create bottom toolbar.
    if get_bottom_toolbar_tokens:
        toolbars = [ConditionalContainer(
            Window(TokenListControl(get_bottom_toolbar_tokens,
                                    default_char=Char(' ', Token.Toolbar)),
                   height=LayoutDimension.exact(1)),
            filter=~IsDone() & RendererHeightIsKnown())]
    else:
        toolbars = []

    def get_height(cli):
        # If there is an autocompletion menu to be shown, make sure that our
        # layout has at least a minimal height in order to display it.
        if reserve_space_for_menu and not cli.is_done:
            return LayoutDimension(min=8)
        else:
            return LayoutDimension()

    def separator():
        return ConditionalContainer(
            content=Window(height=LayoutDimension.exact(1),
                           content=FillControl(u'\u2500',
                                               token=Token.Separator)),
            filter=HasDocumentation(app) & ~IsDone())

    # Create and return Layout instance.
    return HSplit([
        ConditionalContainer(
            Window(
                TokenListControl(get_prompt_tokens_1),
                dont_extend_height=True),
            filter=multiline,
        ),
        VSplit([
            # In multiline mode, the prompt is displayed in a left pane.
            ConditionalContainer(
                Window(
                    TokenListControl(get_prompt_tokens_2),
                    dont_extend_width=True,
                ),
                filter=multiline,
            ),
            # The main input, with completion menus floating on top of it.
            FloatContainer(
                Window(
                    BufferControl(
                        input_processors=input_processors,
                        lexer=lexer,
                        # Enable preview_search, we want to have immediate
                        # feedback in reverse-i-search mode.
                        preview_search=Always(),
                        focus_on_click=True,
                    ),
                    get_height=get_height,
                ),
                [
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=16,
                              scroll_offset=1,
                              extra_filter=(HasFocus(DEFAULT_BUFFER) &
                                            ~display_completions_in_columns))),
                    Float(xcursor=True,
                          ycursor=True,
                          content=MultiColumnCompletionsMenu(
                              extra_filter=(HasFocus(DEFAULT_BUFFER) &
                                            display_completions_in_columns),
                              show_meta=Always()))
                ]
            ),
        ]),
        separator(),
        ConditionalContainer(
            content=Window(
                BufferControl(
                    focus_on_click=True,
                    buffer_name=u'clidocs',
                ),
                height=LayoutDimension(max=15)),
            filter=HasDocumentation(app) & ~IsDone(),
        ),
        separator(),
        ValidationToolbar(),
        SystemToolbar(),

        # In multiline mode, we use two toolbars for 'arg' and 'search'.
        ConditionalContainer(ArgToolbar(), multiline),
        ConditionalContainer(SearchToolbar(), multiline),
    ] + toolbars)


def _split_multiline_prompt(get_prompt_tokens):
    """Split prompt tokens into two multiline prompt token functions.

    Take a `get_prompt_tokens` function. and return two new functions instead.
    One that returns the tokens to be shown on the lines above the input, and
    another one with the tokens to be shown at the first line of the input.

    """
    def before(cli):
        result = []
        found_nl = False
        for token, char in reversed(explode_tokens(get_prompt_tokens(cli))):
            if char == '\n':
                found_nl = True
            elif found_nl:
                result.insert(0, (token, char))
        return result

    def first_input_line(cli):
        result = []
        for token, char in reversed(explode_tokens(get_prompt_tokens(cli))):
            if char == '\n':
                break
            else:
                result.insert(0, (token, char))
        return result

    return before, first_input_line


class HasDocumentation(Filter):
    def __init__(self, app):
        self._app = app

    def __call__(self, cli):
        return bool(self._app.current_docs)
