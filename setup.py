#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import print_function
#from distutils.core import setup
import setuptools
import re
import subprocess

modcontents = open('bottle_session.py').read()
version = re.search(r"__version__ = '([^']*)'",modcontents).group(1)
del modcontents

try:
    # Convert README to rst
    p = subprocess.Popen(['pandoc','-f','markdown','-t','rst','README.md'],stdout=subprocess.PIPE)
    readme_list = []
    format_re = re.compile(r':::python')
    for line in p.stdout:
        text_line = line.decode('utf-8')
        if not format_re.search(text_line):
            readme_list.append(text_line)

    readme = ''.join(readme_list)

except:
    # If that it not possible, use Markdown readme
    print("Pandoc command failed, using markdown README")
    readme = open('README.md').read()

setuptools.setup(
        name = 'bottle-session',
        version = version,
        description = 'Redis based sessions for bottle.',
        long_description = readme,
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
            'Development Status :: 5 - Production/Stable',
            'Framework :: Bottle',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Artistic License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: WSGI :: Application'
            ]
        )
