****************
hypothesis-regex
****************

.. image:: https://img.shields.io/pypi/l/hypothesis-regex.svg
    :target: https://github.com/maximkulkin/hypothesis-regex/blob/master/LICENSE
    :alt: License: MIT

.. image:: https://img.shields.io/travis/maximkulkin/hypothesis-regex.svg
    :target: https://travis-ci.org/maximkulkin/hypothesis-regex
    :alt: Build Status

.. image:: https://img.shields.io/pypi/v/hypothesis-regex.svg
    :target: https://pypi.python.org/pypi/hypothesis-regex
    :alt: PyPI

`Hypothesis <https://hypothesis.readthedocs.io/en/latest/>`_ extension 
to allow generating strings based on regex. Useful in case you have some schema
(e.g. JSON Schema) which already has regular expressions validating data.

Example
=======

.. code:: python

    from hypothesis_regex import regex
    import requests
    import json

    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]{2,}\.[a-zA-Z0-9-.]{2,}$"

    @given(regex(EMAIL_REGEX))
    def test_registering_user(email):
        response = requests.post('/signup', json.dumps({'email': email}))
        assert response.status_code == 201

Features
========

Regex strategy returns strings that always match given regex (this check is
enforced by a filter) and it tries to do that in an effective way so that less
generated examples are filtered out. However, some regex constructs may decrease
strategy efficiency and should be used with caution:

* "^" and "$" in the middle of a string - do not do anything.
* "\\b" and "\\B" (word boundary and not a word boundary) - do not do anything and
  instead just rely on top-level regex match filter to filter out non-matching
  examples.
* positive lookaheads and lookbehinds just generate data they should match (as if
  it was part of preceeding/following parts).
* negative lookaheads and lookbehinds do not do anything so it relies on
  preceeding/following parts to generate correct strings (otherwise the example will
  be filtered out).
* "(?(id)yes-pattern|no-pattern)" does not actually check if group with given id
  was actually used and instead just generates either yes- or no-pattern.

Regex strategy tries to go all crazy about generated data (e.g. "$" at the end of a
string either does not generate anything or generate a newline). The idea is not to
generate a nicely looking strings but instead any craze unexpected combination that
will still match your given regex so you can prepare for those and handle them in
most apropriate way.

You can use regex flags to get more control on strategy:

* re.IGNORECASE - literals or literal ranges generate both lowercase and uppercase
  letters. E.g. `r'a'` will generate both `"a"` and `"A"`, or `'[a-z]'` will generate
  both lowercase and uppercase english characters.
* re.DOTALL - "." char will be able to generate newlines
* re.UNICODE - character categories
  ("\\w", "\\d" or "\\s" and their negations) will generate unicode characters.
  This is default for Python 3, see re.ASCII to reverse it.

There are two ways to pass regex flags:

1. By passing compiled regex with that flags: `regex(re.compile('abc', re.IGNORECASE))`
2. By using inline flags syntax: `regex('(?i)abc')`

Installation
============
::

    $ pip install hypothesis-regex

Requirements
============

- Python >= 2.7 and <= 3.6
- `hypothesis <https://pypi.python.org/pypi/hypothesis>`_ >= 3.8

Project Links
=============

- PyPI: https://pypi.python.org/pypi/hypothesis-regex
- Issues: https://github.com/maximkulkin/hypothesis-regex/issues

License
=======

MIT licensed. See the bundled `LICENSE <https://github.com/maximkulkin/hypothesis-regex/blob/master/LICENSE>`_ file for more details.
