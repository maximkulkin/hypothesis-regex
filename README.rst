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
