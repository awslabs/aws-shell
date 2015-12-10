"""Fuzzy finder for AWS Shell.

This is a fuzzy finder used for the autocompleter
that I've tried to optimize for the AWS CLI set
of commands.

There doesn't seem to be a generic algorithm that
does exactly what I want.  Changing any of these
heuristics so far means that you have to give up
some other component of the idealized matching.

The main things I care about:

* Special weight is given to subsequences on a
  word boundary.  So "drio" scores higher for
  "describe-reserved-instances_offering" than
  "create-spot-datafeed-subscription".
* The more of the word you complete, the higher
  score it has, so given "describe-instance", then
  "describe-instances" should match higher than
  "describe-instance-attribute" because the former
  matches every single character except for one.
* Similar to one, "rinstance" should rank
  "run-instances" higher than "describe-instances"
  because the "r" falls on a word boundary.

High Level Idea
===============

The basic idea is to try to calculate a numeric
score between 0 and 1 given the users's search
string and a possible word in the corpus of words.

You calculate the score for each word and then sort
them appropriately and return the results in order
back to the user.  A score of 1 is the highest
possible score, it would represent an exact match,
and 0 is the lowest meaning these is no possible chance
for the word to be a match.

"""
from __future__ import print_function


def fuzzy_search(user_input, corpus):
    candidates = []
    for word in corpus:
        current_score = calculate_score(user_input, word)
        if current_score > 0:
            candidates.append((word, current_score))
    return [c[0] for c in sorted(candidates, key=lambda x: x[1], reverse=True)]


def calculate_score(search_string, word):
    """Calculate how well the search string matches the word."""
    # See the module docstring for a high level description
    # of what we're trying to do.
    # * If the search string is larger than the word, we know
    #   immediately that this can't be a match.
    if len(search_string) > len(word):
        return 0
    original_word = word
    score = 1
    search_index = 0
    while True:
        scale = 1.0
        search_char = search_string[search_index]
        i = word.find(search_char)
        if i < 0:
            return 0
        if i > 0 and word[i - 1] == '-':
            scale = 0.95
        else:
            scale = 1 - (i / float(len(word)))
        score *= scale
        word = word[i+1:]
        search_index += 1
        if search_index >= len(search_string):
            break
    # The more characters that matched the word, the better
    # so prefer more complete matches.
    completion_scale = 1 - (len(word) / float(len(original_word)))
    score *= completion_scale
    return score
