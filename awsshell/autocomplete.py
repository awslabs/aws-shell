EMPTY = {'arguments': [], 'commands': [], 'children': {}}
import logging
logging.basicConfig(filename='/tmp/completions', level=logging.DEBUG)

LOG = logging.getLogger(__name__)


def is_subsequence(search, value):
    iter_value = iter(value)
    for char in search:
        for inner in iter_value:
            if inner == char:
                break
        else:
            return False
    return True


class AWSCLICompleter(object):
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

    @property
    def arg_metadata(self):
        # Returns the required arguments for the current level.
        return self._current['argument_metadata']

    def reset(self):
        # Resets all the state.  Called after a user runs
        # a command.
        self._current_name = self._root_name
        self._current = self._index[self._root_name]
        self._last_position = 0

    def autocomplete(self, line):
        """Given a line, return a list of suggestions."""
        LOG.debug("line: %s", line)
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
            return self._autocomplete_options(last_word)
        return self._score(last_word, self._current['commands'])

    def _score(self, word, corpus):
        # This is a set of heuristics for what makes the
        # most sense to autocomplete.
        # The first thing are straight prefixes.  If anything
        # you specify is an actual prefix, then we'll just
        # stick with that.
        # Note: I have a feeling I'll be messing with this
        # algorithm for a while.  It might make sense to refactor
        # this out.
        prefix = [c for c in corpus if c.startswith(word)]
        if prefix:
            return prefix
        subsequence = [c for c in corpus if is_subsequence(word, c)]
        if subsequence:
            return subsequence
        return []

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
        for i in range(len(self._current_line)):
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
