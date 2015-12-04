"""Autocompletion integration with python prompt toolkit.

This module integrates the low level autocomplete functionality
provided in awsshell.autocomplete and integrates it with the
interface required for autocompletion in the python prompt
toolkit.

If you're interested in the heavy lifting of the autocompletion
logic, see awsshell.autocomplete.

"""
import logging
from prompt_toolkit.completion import Completer, Completion
from awsshell import fuzzy


LOG = logging.getLogger(__name__)


class AWSShellCompleter(Completer):
    """Completer class for the aws-shell.

    This is the completer used specifically for the aws shell.
    Not to be confused with the AWSCLIModelCompleter, which is more
    low level, and can be reused in contexts other than the
    aws shell.
    """
    def __init__(self, completer, server_side_completer=None):
        self._completer = completer
        if server_side_completer is None:
            server_side_completer = self._create_server_side_completer()
        self._server_side_completer = server_side_completer

    def _create_server_side_completer(self):
        import boto3.session
        from awsshell.resource import index
        session = boto3.session.Session()
        builder = index.ResourceIndexBuilder()
        completer = index.ServerSideCompleter(session, builder)
        return completer

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

    def _convert_to_prompt_completions(self, low_level_completions,
                                       text_before_cursor):
        # Converts the low level completions from the model autocompleter
        # and converts them to Completion() objects used by
        # prompt_toolkit.  We also try to enhance the metadata of the
        # completion by including docs and marking required fields.
        arg_meta = self._completer.arg_metadata
        word_before_cursor = ''
        if text_before_cursor.strip():
            word_before_cursor = text_before_cursor.strip().split()[-1]
        for completion in low_level_completions:
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
                display_meta = '[%s] %s' % (type_name,
                                            arg_meta[completion]['minidoc'])
            else:
                display_text = completion
                display_meta = ''
            if text_before_cursor and text_before_cursor[-1] == ' ':
                location = 0
            else:
                location = -len(word_before_cursor)
            yield Completion(completion, location,
                             display=display_text, display_meta=display_meta)

    def get_completions(self, document, complete_event):
        text_before_cursor = document.text_before_cursor
        completions = self._completer.autocomplete(text_before_cursor)
        prompt_completions = list(self._convert_to_prompt_completions(
            completions, text_before_cursor))
        if (not prompt_completions and self._completer.last_option and
                len(self._completer.cmd_path) == 3):
            # If we couldn't complete anything from the JSON model
            # completer and we're on a cli option (e.g --foo), we
            # can ask the server side completer if it knows anything
            # about this resource.
            LOG.debug("No local autocompletions found, trying "
                      "server side completion.")
            command = self._completer.cmd_path
            service = command[1]
            if service == 's3api':
                # TODO: we need a more generic way to capture renames
                # of commands.  This currently lives in the CLI
                # customization code.
                service = 's3'
            operation = command[2]
            param = self._completer.arg_metadata.get(
                self._completer.last_option, {}).get('api_name')
            if param is not None:
                LOG.debug("Trying to retrieve autcompletion for: "
                          "%s, %s, %s", service, operation, param)
                results = self._server_side_completer\
                    .retrieve_candidate_values(service, operation, param)
                LOG.debug("Results for %s, %s, %s: %s",
                          service, operation, param, results)
                word_before_cursor = text_before_cursor.strip().split()[-1]
                location = 0
                if text_before_cursor[-1] != ' ' and \
                        word_before_cursor and results:
                    # Filter the results down by fuzzy searching what
                    # the user has provided.
                    results = fuzzy.fuzzy_search(word_before_cursor, results)
                    location = -len(word_before_cursor)
                if results is not None:
                    for result in results:
                        # Insert at the end
                        yield Completion(result, location,
                                         display=result,
                                         display_meta='')
        else:
            for c in prompt_completions:
                yield c
