"""Autocompletion integration with python prompt toolkit.

This module integrates the low level autocomplete functionality
provided in awsshell.autocomplete and integrates it with the
interface required for autocompletion in the python prompt
toolkit.

If you're interested in the heavy lifting of the autocompletion
logic, see awsshell.autocomplete.

"""
from prompt_toolkit.completion import Completer, Completion


class AWSShellCompleter(Completer):
    """Completer class for the aws-shell.

    This is the completer used specifically for the aws shell.
    Not to be confused with the AWSCLIModelCompleter, which is more
    low level, and can be reused in contexts other than the
    aws shell.
    """
    def __init__(self, completer):
        self._completer = completer

    @property
    def completer(self):
        return self._completer

    @completer.setter
    def completer(self, value):
        self._completer = value

    @property
    def last_option(self):
        return self._completer.last_option

    @property
    def current_command(self):
        return u' '.join(self._completer.cmd_path)

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        word_before_cursor = ''
        if text_before_cursor.strip():
            word_before_cursor = text_before_cursor.strip().split()[-1]
        completions = self._completer.autocomplete(text_before_cursor)
        arg_meta = self._completer.arg_metadata
        for completion in completions:
            # Go through the completions and add inline docs and
            # mark which options are required.
            if completion.startswith('--') and completion in arg_meta:
                # TODO: Need to handle merging in global options as well.
                meta = arg_meta[completion]
                if meta['required']:
                    display_text = '%s (required)' % completion
                else:
                    display_text = completion
                type_name = arg_meta[completion]['type_name']
                display_meta = '[%s] %s' % (type_name, arg_meta[completion]['minidoc'])
            else:
                display_text = completion
                display_meta = ''
            if text_before_cursor and text_before_cursor[-1] == ' ':
                location = 0
            else:
                location = -len(word_before_cursor)
            yield Completion(completion, location,
                             display=display_text, display_meta=display_meta)



