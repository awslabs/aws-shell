import os
import sys
import jmespath

from six import with_metaclass
from abc import ABCMeta, abstractmethod

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter, PathCompleter

from awsshell.utils import FSLayer


class InteractionException(Exception):
    """Base exception for errors in interactions."""


class Interaction(with_metaclass(ABCMeta, object)):
    """Base Interaction class.

    The base interaction class only has one constraint: an execute method that
    will take some data as input, apply arbirtary logic on that data to perform
    a transformation and then return the resulting data to be used in later
    stages.
    """

    def __init__(self, model, prompt):
        self._model = model
        self.prompt = prompt

    @abstractmethod
    def execute(self, data):
        """Execute the interaction, transforming the data in some way."""


class FilePrompt(Interaction):
    """Prompt the user to select a file.

    Provide completions to the current path by suggesting files or directories
    in the last directory of the current path. Upon selection returns the
    contents of the file as the result of the interaction.
    """

    def __init__(self, model, prompt_msg, prompter=prompt):
        super(FilePrompt, self).__init__(model, prompt_msg)
        self._prompter = prompter

    def get_path(self):
        cmpltr = PathCompleter(expanduser=True)
        selection = self._prompter('%s ' % self.prompt, completer=cmpltr)
        return os.path.expanduser(selection)

    def execute(self, data, fslayer=FSLayer()):
        path = self.get_path()
        return fslayer.file_contents(path)


class SimpleSelect(Interaction):
    """Display a list of options, allowing the user to select one.

    Given a list of one or more items, display them in a dropdown selection
    menu and allows the user to pick one. If a path is present on the
    interaction the path will be applied to each item and the result will be
    used as the string to display in the menu. Upon selection, the related item
    is returned. If no path is present, the list is assumed to be of str and
    used as is.
    """

    def __init__(self, model, prompt_msg, prompter=prompt):
        super(SimpleSelect, self).__init__(model, prompt_msg)
        self._prompter = prompter

    def execute(self, data):
        if not isinstance(data, list) or len(data) < 1:
            raise InteractionException('SimpleSelect expects a non-empty list')
        if self._model.get('Path') is not None:
            display_data = jmespath.search(self._model['Path'], data)
            completer = WordCompleter(
                display_data,
                sentence=True,
                ignore_case=True
            )
            option_dict = dict(zip(display_data, data))
            selected = self._prompter('%s ' % self.prompt, completer=completer)
            return option_dict[selected]
        else:
            cmpltr = WordCompleter(data, ignore_case=True, sentence=True)
            return self._prompter('%s ' % self.prompt, completer=cmpltr)


class SimplePrompt(Interaction):
    """Prompt the user to type in responses for each field.

    Each key on the provided dict is considered a field and the user will be
    prompted for input for each key. The provided input replaces the value for
    each key creating a completed dict of key to user input.
    """

    def __init__(self, model, prompt_msg, prompter=prompt):
        super(SimplePrompt, self).__init__(model, prompt_msg)
        self._prompter = prompter

    def execute(self, data):
        if not isinstance(data, dict):
            raise InteractionException('SimplePrompt expects a dict as data')
        sys.stdout.write('%s \n' % self.prompt)
        sys.stdout.flush()
        for field in data:
            data[field] = self._prompter(field + ': ')
        return data


class InteractionLoader(object):
    """An interaction loader. Create interactions based on their name.

    The class will maintain a dict of ScreenType to Interaction object so
    Interaction objects can be instantiated from their corresponding str.
    """
    _INTERACTIONS = {
        'SimpleSelect': SimpleSelect,
        'SimplePrompt': SimplePrompt,
        'FilePrompt': FilePrompt
    }

    def __init__(self):
        pass

    def create(self, model, prompt):
        """Create an Interaction object given the model and prompt to be used.

        Looks up the name from the given interaction model and returns an
        instance of the corresponding interaction class.

        :type model: dict
        :param model: The model representing the interaction.

        :type prompt: str
        :param prompt: The string to be used when prompting the user.

        :rtype: :class:`Interaction`
        :return: The Interaction object created.

        :raises: :class:`InteractionException`
        """
        name = model.get('ScreenType')
        interaction_class = self._INTERACTIONS.get(name)
        if interaction_class is not None:
            return interaction_class(model, prompt)
        else:
            raise InteractionException('Invalid interaction type: %s' % name)
