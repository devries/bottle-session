Bottle Sessions with Redis
==========================

Bottle_session is a session manager for the Bottle microframework that uses a
cookie to maintain your web session and stores a hash associated with that
cookie using the redis key-value store. It is designed as a simple Bottle
plugin.

Installation
------------
Install using either pip or easy_install:

~~~~~~~
$ pip install bottle-session
~~~~~~~

or you can download the latest version from bitbucket:

~~~~~~
$ git clone https://devries@bitbucket.org/devries/bottle-session.git
$ cd bottle-session
$ python setup.py install
~~~~~~

Requirements
------------
In order to use bottle-session you must have the both the redis and of course
bottle modules installed. I recommend also installing pycrypto, although it is
not required. If pycrypto is installed, then the pycrypto random number
generator is used to generate session cookies, otherwise python's internal
random number generator is used.


Acknowledgments
---------------
Thanks to Marcel Hellkamp and the bottle community for the framework and to
Sean M. Collins whose bottle-redis package in bottle-extras served as the
inspiration for this bottle plugin.
