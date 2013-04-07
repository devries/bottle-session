#!/usr/bin/env python
from distutils.core import setup

setup(
        name = 'bottle-session',
        version = '0.1',
        description = 'Redis based sessions for bottle.',
        author = 'Christopher De Vries',
        author_email = 'devries@idolstarastronomer.com',
        license = 'Artistic',
        py_modules = [ 'bottle_session' ],
        requires = [
            'bottle (>=0.9)',
            'redis'
            ]
        )
