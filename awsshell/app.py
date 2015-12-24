"""AWS Shell application.

Main entry point to the AWS Shell.

"""
from __future__ import unicode_literals
import os
import subprocess
import logging
import sys

from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Always
from prompt_toolkit.interface import CommandLineInterface, Application
from prompt_toolkit.interface import AbortAction, AcceptAction
from prompt_toolkit.utils import Callback
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory, FileHistory

from awsshell.ui import create_default_layout
from awsshell.config import Config
from awsshell.keys import KeyManager
from awsshell.style import StyleFactory
from awsshell.toolbar import Toolbar
from awsshell.utils import build_config_file_path, temporary_file
from awsshell import compat


LOG = logging.getLogger(__name__)


def create_aws_shell(completer, model_completer, docs):
    return AWSShell(completer, model_completer, docs)


class InputInterrupt(Exception):
    """Stops the input of commands.

    Raising `InputInterrupt` is useful to force a cli rebuild, which is
    sometimes necessary in order for config changes to take effect.
    """
    pass


class EditHandler(object):
    def __init__(self, popen_cls=None, env=None):
        if popen_cls is None:
            popen_cls = subprocess.Popen
        self._popen_cls = popen_cls
        if env is None:
            env = os.environ
        self._env = env

    def _get_editor_command(self):
        if 'EDITOR' in self._env:
            return self._env['EDITOR']
        else:
            return compat.default_editor()

    def run(self, command, application):
        """Open application's history buffer in an editor.

        :type command: list
        :param command: The dot command as a list split
            on whitespace, e.g ``['.foo', 'arg1', 'arg2']``

        :type application: AWSShell
        :param application: The application object.

        """
        all_commands = '\n'.join(
            ['aws ' + h for h in list(application.history)
             if not h.startswith(('.', '!'))])
        with temporary_file('w') as f:
            f.write(all_commands)
            f.flush()
            editor = self._get_editor_command()
            p = self._popen_cls([editor, f.name])
            p.communicate()


class DotCommandHandler(object):
    HANDLER_CLASSES = {
        'edit': EditHandler,
    }

    def __init__(self, output=sys.stdout, err=sys.stderr):
        self._output = output
        self._err = err

    def handle_cmd(self, command, application):
        """Handles running a given dot command from a user.

        :type command: str
        :param command: The full dot command string, e.g. ``.edit``,
            of ``.profile prod``.

        :type application: AWSShell
        :param application: The application object.

        """
        parts = command.split()
        cmd_name = parts[0][1:]
        if cmd_name not in self.HANDLER_CLASSES:
            self._unknown_cmd(parts, application)
        else:
            # Note we expect the class to support no-arg
            # instantiation.
            self.HANDLER_CLASSES[cmd_name]().run(parts, application)

    def _unknown_cmd(self, cmd_parts, application):
        self._err.write("Unknown dot command: %s\n" % cmd_parts[0])


class AWSShell(object):
    """Encapsulates the ui, completer, command history, docs, and config.

    Runs the input event loop and delegates the command execution to either
    the `awscli` or the underlying shell.

    :type refresh_cli: bool
    :param refresh_cli: Flag to refresh the cli.

    :type config_obj: :class:`configobj.ConfigObj`
    :param config_obj: Contains the config information for reading and writing.

    :type config_section: :class:`configobj.Section`
    :param config_section: Convenience attribute to access the main section
        of the config.

    :type model_completer: :class:`AWSCLIModelCompleter`
    :param model_completer: Matches input with completions.  `AWSShell` sets
        and gets the attribute `AWSCLIModelCompleter.match_fuzzy`.

    :type enable_vi_bindings: bool
    :param enable_vi_bindings: If True, enables Vi key bindings. Else, Emacs
        key bindings are enabled.

    :type show_completion_columns: bool
    param show_completion_columns: If True, completions are shown in multiple
        columns.  Else, completions are shown in a single scrollable column.

    :type show_help: bool
    :param show_help: If True, shows the help pane.  Else, hides the help pane.

    :type theme: str
    :param theme: The pygments theme.
    """

    def __init__(self, completer, model_completer, docs):
        self.completer = completer
        self.model_completer = model_completer
        self.history = InMemoryHistory()
        self.file_history = FileHistory(build_config_file_path('history'))
        self._cli = None
        self._docs = docs
        self.current_docs = u''
        self.refresh_cli = False
        self.key_manager = None
        self._dot_cmd = DotCommandHandler()

        # These attrs come from the config file.
        self.config_obj = None
        self.config_section = None
        self.enable_vi_bindings = None
        self.show_completion_columns = None
        self.show_help = None
        self.theme = None

        self.load_config()

    def load_config(self):
        """Loads the config from the config file or template."""
        config = Config()
        self.config_obj = config.load('awsshellrc')
        self.config_section = self.config_obj['aws-shell']
        self.model_completer.match_fuzzy = self.config_section.as_bool(
            'match_fuzzy')
        self.enable_vi_bindings = self.config_section.as_bool(
            'enable_vi_bindings')
        self.show_completion_columns = self.config_section.as_bool(
            'show_completion_columns')
        self.show_help = self.config_section.as_bool('show_help')
        self.theme = self.config_section['theme']

    def save_config(self):
        """Saves the config to the config file."""
        self.config_section['match_fuzzy'] = self.model_completer.match_fuzzy
        self.config_section['enable_vi_bindings'] = self.enable_vi_bindings
        self.config_section['show_completion_columns'] = \
            self.show_completion_columns
        self.config_section['show_help'] = self.show_help
        self.config_section['theme'] = self.theme
        self.config_obj.write()

    @property
    def cli(self):
        if self._cli is None or self.refresh_cli:
            self._cli = self.create_cli_interface(self.show_completion_columns)
            self.refresh_cli = False
        return self._cli

    def run(self):
        while True:
            try:
                document = self.cli.run()
                text = document.text
            except InputInterrupt:
                pass
            except (KeyboardInterrupt, EOFError):
                self.save_config()
                break
            else:
                if text.strip() in ['quit', 'exit']:
                    break
                if text.startswith('.'):
                    # These are special commands.  The only one supported for
                    # now is .edit.
                    self._dot_cmd.handle_cmd(text, application=self)
                else:
                    if text.startswith('!'):
                        # Then run the rest as a normally shell command.
                        full_cmd = text[1:]
                    else:
                        full_cmd = 'aws ' + text
                        self.history.append(full_cmd)
                    self.current_docs = u''
                    self.cli.buffers['clidocs'].reset(
                        initial_document=Document(self.current_docs,
                                                  cursor_position=0))
                    self.cli.request_redraw()
                    p = subprocess.Popen(full_cmd, shell=True)
                    p.communicate()

    def stop_input_and_refresh_cli(self):
        """Stops input by raising an `InputInterrupt`, forces a cli refresh.

        The cli refresh is necessary because changing options such as key
        bindings, single vs multi column menu completions, and the help pane
        all require a rebuild.

        :raises: :class:`InputInterrupt <exceptions.InputInterrupt>`.
        """
        self.refresh_cli = True
        self.cli.request_redraw()
        raise InputInterrupt

    def create_layout(self, display_completions_in_columns, toolbar):
        from awsshell.lexer import ShellLexer
        lexer = ShellLexer
        if self.config_section['theme'] == 'none':
            lexer = None
        return create_default_layout(
            self, u'aws> ', lexer=lexer, reserve_space_for_menu=True,
            display_completions_in_columns=display_completions_in_columns,
            get_bottom_toolbar_tokens=toolbar.handler)

    def create_buffer(self, completer, history):
        return Buffer(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=completer,
            complete_while_typing=Always(),
            accept_action=AcceptAction.RETURN_DOCUMENT)

    def create_key_manager(self):
        """Creates the :class:`KeyManager`.

        The inputs to KeyManager are expected to be callable, so we can't
        use the standard @property and @attrib.setter for these attributes.
        Lambdas cannot contain assignments so we're forced to define setters.

        :rtype: :class:`KeyManager`
        :return: A KeyManager with callables to set the toolbar options.  Also
            includes the method stop_input_and_refresh_cli to ensure certain
            options take effect within the current session.
        """

        def set_match_fuzzy(match_fuzzy):
            """Setter for fuzzy matching mode.

            :type match_fuzzy: bool
            :param match_fuzzy: The match fuzzy flag.
            """
            self.model_completer.match_fuzzy = match_fuzzy

        def set_enable_vi_bindings(enable_vi_bindings):
            """Setter for vi mode keybindings.

            If vi mode is off, emacs mode is enabled by default by
            `prompt_toolkit`.

            :type enable_vi_bindings: bool
            :param enable_vi_bindings: The enable Vi bindings flag.
            """
            self.enable_vi_bindings = enable_vi_bindings

        def set_show_completion_columns(show_completion_columns):
            """Setter for showing the completions in columns flag.

            :type show_completion_columns: bool
            :param show_completion_columns: The show completions in
                multiple columns flag.
            """
            self.show_completion_columns = show_completion_columns

        def set_show_help(show_help):
            """Setter for showing the help container flag.

            :type show_help: bool
            :param show_help: The show help flag.
            """
            self.show_help = show_help

        return KeyManager(
            lambda: self.model_completer.match_fuzzy, set_match_fuzzy,
            lambda: self.enable_vi_bindings, set_enable_vi_bindings,
            lambda: self.show_completion_columns, set_show_completion_columns,
            lambda: self.show_help, set_show_help,
            self.stop_input_and_refresh_cli)

    def create_application(self, completer, history,
                           display_completions_in_columns):
        self.key_manager = self.create_key_manager()
        toolbar = Toolbar(
            lambda: self.model_completer.match_fuzzy,
            lambda: self.enable_vi_bindings,
            lambda: self.show_completion_columns,
            lambda: self.show_help)
        style_factory = StyleFactory(self.theme)
        buffers = {
            'clidocs': Buffer(read_only=True)
        }

        return Application(
            layout=self.create_layout(display_completions_in_columns, toolbar),
            mouse_support=False,
            style=style_factory.style,
            buffers=buffers,
            buffer=self.create_buffer(completer, history),
            on_abort=AbortAction.RETRY,
            on_exit=AbortAction.RAISE_EXCEPTION,
            on_input_timeout=Callback(self.on_input_timeout),
            key_bindings_registry=self.key_manager.manager.registry,
        )

    def on_input_timeout(self, cli):
        if not self.show_help:
            return
        document = cli.current_buffer.document
        text = document.text
        LOG.debug("document.text = %s", text)
        LOG.debug("current_command = %s", self.completer.current_command)
        if text.strip():
            command = self.completer.current_command
            key_name = '.'.join(command.split()).encode('utf-8')
            last_option = self.completer.last_option
            if last_option:
                self.current_docs = self._docs.extract_param(
                    key_name, last_option)
            else:
                self.current_docs = self._docs.extract_description(key_name)
        else:
            self.current_docs = u''
        cli.buffers['clidocs'].reset(
            initial_document=Document(self.current_docs, cursor_position=0))
        cli.request_redraw()

    def create_cli_interface(self, display_completions_in_columns):
        # A CommandLineInterface from prompt_toolkit
        # accepts two things: an application and an
        # event loop.
        loop = create_eventloop()
        app = self.create_application(self.completer,
                                      self.file_history,
                                      display_completions_in_columns)
        cli = CommandLineInterface(application=app, eventloop=loop)
        return cli
