"""AWS Shell application.

Main entry point to the AWS Shell.

"""
from __future__ import unicode_literals
import tempfile
import subprocess
import logging

from prompt_toolkit.document import Document
from prompt_toolkit.shortcuts import create_eventloop
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import Always
from prompt_toolkit.interface import CommandLineInterface, Application
from prompt_toolkit.interface import AbortAction, AcceptAction
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.utils import Callback
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from awsshell.ui import create_default_layout
from awsshell.config import Config


LOG = logging.getLogger(__name__)


def create_aws_shell(completer, model_completer, history, docs):
    return AWSShell(completer, model_completer, history, docs)


class AWSShell(object):
    """Encapsulates the ui, completer, command history, docs, and config.

    Runs the input event loop and delegates the command execution to either
    the `awscli` or the underlying shell.

    :type config_obj: :class:`configobj.ConfigObj`
    :param config_obj: Contains the config information for reading and writing.

    :type config_section: :class:`configobj.Section`
    :param config_section: Convenience attribute to access the main section
        of the config.
    """

    def __init__(self, completer, model_completer, history, docs):
        self.completer = completer
        self.model_completer = model_completer
        self.history = history
        self._cli = None
        self._docs = docs
        self.current_docs = u''
        self._init_config()

    def _init_config(self):
        config = Config()
        self.config_obj = config.load('awsshellrc')
        self.config_section = self.config_obj['aws-shell']
        self.model_completer.match_fuzzy = self.match_fuzzy()

    @property
    def cli(self):
        if self._cli is None:
            self._cli = self.create_cli_interface(
                self.show_completion_columns())
        return self._cli

    def run(self):
        while True:
            try:
                document = self.cli.run()
                text = document.text
            except (KeyboardInterrupt, EOFError):
                self.config_obj.write()
                break
            else:
                if text.strip() in ['quit', 'exit']:
                    break
                if text.startswith('.'):
                    # These are special commands.  The only one supported for
                    # now is .edit.
                    if text.startswith('.edit'):
                        # TODO: Use EDITOR env var.
                        all_commands = '\n'.join(
                            ['aws ' + h for h in list(self.history)
                             if not h.startswith(('.', '!'))])
                    with tempfile.NamedTemporaryFile('w') as f:
                        f.write(all_commands)
                        f.flush()
                        p = subprocess.Popen(['vim', f.name])
                        p.communicate()
                else:
                    if text.startswith('!'):
                        # Then run the rest as a normally shell command.
                        full_cmd = text[1:]
                    else:
                        full_cmd = 'aws ' + text
                    self.current_docs = u''
                    self.cli.buffers['clidocs'].reset(
                        initial_document=Document(self.current_docs,
                                                  cursor_position=0))
                    self.cli.request_redraw()
                    p = subprocess.Popen(full_cmd, shell=True)
                    p.communicate()

    def match_fuzzy(self, match_fuzzy=None):
        """Setter/Getter for fuzzy matching mode.

        Used by `prompt_toolkit.KeyBindingManager`, which expects this method to
        be callable so we can't use the standard @property and @attrib.setter.

        :type match_fuzzy: bool
        :param match_fuzzy: (Optional) The match fuzzy flag.

        :rtype: bool
        :return: The match fuzzy flag.
        """
        CFG_FUZZY = 'match_fuzzy'
        if match_fuzzy is not None:
            self.model_completer.match_fuzzy = match_fuzzy
            self.config_section[CFG_FUZZY] = match_fuzzy
        return self.config_section.as_bool(CFG_FUZZY)

    def enable_vi_bindings(self, enable_vi_bindings=None):
        """Setter/Getter for vi mode keybindings.

        If vi mode is off, emacs mode is enabled by default by `prompt_toolkit`.

        TODO: `enable_vi_bindings`, `show_completion_columns`, and `show_help`
        could use a refactor.  `prompt_toolkit.KeyBindingManager` seems to make
        this a little tricky.

        Used by `prompt_toolkit.KeyBindingManager`, which expects this method to
        be callable so we can't use the standard @property and @attrib.setter.

        :type enable_vi_bindings: bool
        :param enable_vi_bindings: (Optional) The enable vi bindings flag.

        :rtype: bool
        :return: The enable vi bindings flag.
        """
        CFG_VI = 'enable_vi_bindings'
        if enable_vi_bindings is not None:
            self.config_section[CFG_VI] = enable_vi_bindings
        return self.config_section.as_bool(CFG_VI)

    def show_completion_columns(self, show_completion_columns=None):
        """Setter/Getter for showing the completions in columns flag.

        Used by `prompt_toolkit.KeyBindingManager`, which expects this method to
        be callable so we can't use the standard @property and @attrib.setter.

        :type show_completion_columns: bool
        :param show_completion_columns: (Optional) The show completions in
            multiple columns flag.

        :rtype: bool
        :return: The show completions in multiple columns flag.
        """
        CFG_COLUMNS = 'show_completion_columns'
        if show_completion_columns is not None:
            self.config_section[CFG_COLUMNS] = show_completion_columns
        return self.config_section.as_bool(CFG_COLUMNS)

    def show_help(self, show_help=None):
        """Setter/Getter for showing the help container flag.

        Used by `prompt_toolkit.KeyBindingManager`, which expects this method to
        be callable so we can't use the standard @property and @attrib.setter.

        :type show_help: bool
        :param show_help: (Optional) The show help flag.

        :rtype: bool
        :return: The show help flag.
        """
        CFG_HELP = 'show_help'
        if show_help is not None:
            self.config_section[CFG_HELP] = show_help
        return self.config_section.as_bool(CFG_HELP)

    def create_layout(self, display_completions_in_columns):
        return create_default_layout(
            self, u'aws> ', reserve_space_for_menu=True,
            display_completions_in_columns=display_completions_in_columns)

    def create_buffer(self, completer, history):
        return Buffer(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            completer=completer,
            complete_while_typing=Always(),
            accept_action=AcceptAction.RETURN_DOCUMENT)

    def create_application(self, completer, history,
                           display_completions_in_columns):
        key_bindings_registry = KeyBindingManager(
            enable_search=True,
            enable_abort_and_exit_bindings=True,
            enable_auto_suggest_bindings=True,
            enable_vi_mode=self.enable_vi_bindings(),
            enable_system_bindings=False,
            enable_open_in_editor=False).registry
        buffers = {
            'clidocs': Buffer(read_only=True)
        }

        return Application(
            layout=self.create_layout(display_completions_in_columns),
            mouse_support=False,
            buffers=buffers,
            buffer=self.create_buffer(completer, history),
            on_abort=AbortAction.RAISE_EXCEPTION,
            on_exit=AbortAction.RAISE_EXCEPTION,
            on_input_timeout=Callback(self.on_input_timeout),
            key_bindings_registry=key_bindings_registry,
        )

    def on_input_timeout(self, cli):
        if not self.show_help():
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
                                      self.history,
                                      display_completions_in_columns)
        cli = CommandLineInterface(application=app, eventloop=loop)
        return cli
