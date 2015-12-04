from awsshell.fuzzy import fuzzy_search


class AWSCLIModelCompleter(object):
    """Autocompletion based on the JSON models for AWS services.

    This class consumes indexed data based on the JSON models from
    AWS service (which we pull through botocore's data loaders).

    """
    def __init__(self, index_data):
        self._index = index_data
        self._root_name = 'aws'
        self._global_options = index_data[self._root_name]['arguments']
        # These values mutate as autocompletions occur.
        # They track state to improve the autocompletion speed.
        self._current_name = 'aws'
        self._current = index_data[self._root_name]
        self._last_position = 0
        self._current_line = ''
        self.last_option = ''
        # This will get populated as a command is completed.
        self.cmd_path = [self._current_name]

    @property
    def arg_metadata(self):
        # Returns the required arguments for the current level.
        return self._current.get('argument_metadata', {})

    def reset(self):
        # Resets all the state.  Called after a user runs
        # a command.
        self._current_name = self._root_name
        self._current = self._index[self._root_name]
        self._last_position = 0
        self.last_option = ''
        self.cmd_path = [self._current_name]

    def autocomplete(self, line):
        """Given a line, return a list of suggestions."""
        current_length = len(line)
        self._current_line = line
        if current_length == 1 and self._last_position > 1:
            # Reset state.  This is likely from a user completing
            # a previous command.
            self.reset()
        elif current_length < self._last_position:
            # The user has hit backspace.  We'll need to check
            # the current words.
            return self._handle_backspace()
        elif current_length != self._last_position + 1:
            return self._complete_from_full_parse()

        # This position is important.  We only update the _last_position
        # after we've checked the special cases above where that value
        # matters.
        self._last_position = len(line)
        if not line:
            return []
        if line and not line.strip():
            # Special case, the user hits a space on a new line so
            # we autocomplete all the top level commands.
            return self._current['commands']

        last_word = line.split()[-1]
        if last_word in self.arg_metadata or last_word in self._global_options:
            # The last thing we completed was an argument, record
            # this as self.last_arg
            self.last_option = last_word
        if line[-1] == ' ':
            # At this point the user has autocompleted a command
            # or an argument and has hit space.  If they've
            # just completed a command, we need to change the
            # current context and traverse into the subcommand.
            # "ec2 "
            #      ^--here, need to traverse into "ec2"
            #
            # Otherwise:
            # "ec2 --no-validate-ssl "
            #                        ^-- here, stay on "ec2" context.
            if not last_word.startswith('-'):
                next_command = self._current['children'].get(last_word)
                if next_command is not None:
                    self._current = next_command
                    self._current_name = last_word
                    self.cmd_path.append(self._current_name)
            elif last_word in self.arg_metadata and \
                    self.arg_metadata[last_word]['example']:
                # Then this is an arg with a shorthand example so we'll
                # suggest that example.
                return [self.arg_metadata[last_word]['example']]
            # Even if we don't change context, we still want to
            # autocomplete all the commands for the current context
            # in either of the above two cases.
            return self._current['commands'][:]
        elif last_word.startswith('-'):
            # TODO: cache this for the duration of the current context.
            # We don't need to recompute this until the args are
            # different.
            all_args = self._get_all_args()
            return fuzzy_search(last_word, all_args)
        return fuzzy_search(last_word, self._current['commands'])

    def _get_all_args(self):
        if self._current['arguments'] != self._global_options:
            all_args = self._current['arguments'] + self._global_options
        else:
            all_args = self._current['arguments']
        return all_args

    def _handle_backspace(self):
        return self._complete_from_full_parse()

    def _complete_from_full_parse(self):
        # We try to avoid calling this, but this is necessary
        # sometimes.  In this scenario, we're resetting everything
        # and starting from the very beginning and reparsing
        # everything.
        # This is a naive implementation for now.  This
        # can be optimized.
        self.reset()
        line = self._current_line
        for i in range(1, len(self._current_line)):
            self.autocomplete(line[:i])
        return self.autocomplete(line)

    def _autocomplete_options(self, last_word):
        global_args = []
        # Autocomplete argument names.
        current_arg_completions = [
            cmd for cmd in self._current['arguments']
            if cmd.startswith(last_word)]
        if self._current_name != self._root_name:
            # Also autocomplete global arguments.
            global_args = [
                cmd for cmd in self._global_options if
                cmd.startswith(last_word)]
        return current_arg_completions + global_args
