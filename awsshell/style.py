# Copyright 2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from pygments.token import Token
from pygments.style import Style
from pygments.util import ClassNotFound
from pygments.styles import get_style_by_name
from prompt_toolkit.styles import default_style_extensions


class StyleFactory(object):
    """Provides styles for the autocomplete menu and the toolbar.

    :type style: :class:`pygments.style.StyleMeta`
    :param style: Contains pygments style info.
    """

    def __init__(self, style_name):
        self.style = self.style_factory(style_name)

    def style_factory(self, style_name):
        """Retrieves the specified pygments style.

        If the specified style is not found, the vim style is returned.

        :type style_name: str
        :param style_name: The pygments style name.

        :rtype: :class:`pygments.style.StyleMeta`
        :return: Pygments style info.
        """
        try:
            style = get_style_by_name(style_name)
        except ClassNotFound:
            style = get_style_by_name('vim')

        class CliStyle(Style):
            """Provides styles for the autocomplete menu and the toolbar.

            :type styles: dict
            :param styles: Contains pygments style info.
            """

            styles = {}
            styles.update(style.styles)
            styles.update(default_style_extensions)
            styles.update({
                Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
                Token.Menu.Completions.Completion: 'bg:#008888 #ffffff',
                Token.Menu.Completions.Meta.Current: 'bg:#00aaaa #000000',
                Token.Menu.Completions.Meta: 'bg:#00aaaa #ffffff',
                Token.Menu.Completions.ProgressButton: 'bg:#003333',
                Token.Menu.Completions.ProgressBar: 'bg:#00aaaa',
                Token.Toolbar: 'bg:#222222 #cccccc',
                Token.Toolbar.Off: 'bg:#222222 #696969',
                Token.Toolbar.On: 'bg:#222222 #ffffff',
                Token.Toolbar.Search: 'noinherit bold',
                Token.Toolbar.Search.Text: 'nobold',
                Token.Toolbar.System: 'noinherit bold',
                Token.Toolbar.Arg: 'noinherit bold',
                Token.Toolbar.Arg.Text: 'nobold'
            })

        return CliStyle
