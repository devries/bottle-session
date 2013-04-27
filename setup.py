#!/usr/bin/env python
from distutils.core import setup

setup(
        name = 'bottle-session',
        version = '0.2',
        description = 'Redis based sessions for bottle.',
        long_description = open('README.md').read(),
        author = 'Christopher De Vries',
        author_email = 'devries@idolstarastronomer.com',
        license = 'Artistic',
        py_modules = [ 'bottle_session' ],
        url = 'https://bitbucket.org/devries/bottle-session',
        install_requires = [
            'bottle >=0.9',
            'redis'
            ],
        classifiers = [
            'Development Status :: 4 - Beta',
            'Framework :: Bottle',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Artistic License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
            ]
        )
