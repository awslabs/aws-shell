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


def substring_search(word, collection):
    """Find all matches in the `collection` for the specified `word`.

    If `word` is empty, returns all items in `collection`.

    :type word: str
    :param word: The substring to search for.

    :type collection: collection, usually a list
    :param collection: A collection of words to match.

    :rtype: list of strings
    :return: A sorted list of matching words from collection.
    """
    return [item for item in sorted(collection) if item.startswith(word)]
