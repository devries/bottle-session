Bottle Sessions with Redis
==========================

Bottle_session is a session manager for the Bottle microframework that uses a
cookie to maintain your web session and stores a hash associated with that
cookie using the redis key-value store. It is designed as a simple Bottle
plugin.

Installation
------------
Install using either pip or easy_install:

    $ pip install bottle-session

or you can download the latest version from bitbucket:

    $ git clone https://devries@bitbucket.org/devries/bottle-session.git
    $ cd bottle-session
    $ python setup.py install

Requirements
------------
In order to use bottle-session you must have both the redis and of course the
bottle modules installed. I recommend also installing pycrypto, although it is
not required. If pycrypto is installed, then the pycrypto random number
generator is used to generate session cookies, otherwise python's internal
random number generator is used.

Using Bottle-session
--------------------
The first requirement is that you import the bottle_session module:

    :::python
    import bottle_session
    import bottle

Next, initialize the plugin:

    :::python
    app = bottle.app()
    plugin = bottle_session.SessionPlugin(cookie_lifetime=600)
    app.install(plugin)

The `cookie_lifetime` parameter is the lifetime of the cookie in seconds, if
the lifetime is explicitly set to **None** it will last 1 week. The
`SessionPlugin` class initializer takes several optional parameters:

- `host` is the host for the redis instance. It defaults to `localhost`.
- `port` is the port for the redis instance. It defaults to `6379`.
- `db` is the redis database number. It defaults to `0`.
- `cookie_name` is the name of the session cookie. It defaults to
  `bottle.session`.
- `keyword` is the plugin keyword. It defaults to `session`.

To use the plugin, just add the keyword (`session` by default) to the routed
method:

    :::python
    @bottle.route('/')
    def index(session):
        user_name = session.get('name')
        if user_name is not None:
            return "Hello, %s"%user_name
        else:
            return "I don't recognize you."

    @bottle.route('/set/:user_name')
    def set_name(session,user_name=None):
        if user_name is not None:
            session['name']=user_name
            return "I recognize you now."
        else:
            return "What was that?"

    bottle.debug(True)
    bottle.run(app=app,host='localhost',port=8888)

In this example you can set the `name` property of the session cookie to Chris
by visiting the `http://localhost:8888/set/Chris` and then that value is
retrieved when you visit `http://localhost:8888/`. 

Using Bottle-session and Bottle-redis
-------------------------------------
If you are using redis for sessions you are likely using redis to store other
data as well, and likely use the bottle-redis plugin. You can use both plugins
together, and you can even get them to use the same connection pool.
Initialize them by creating a connection pool which you attach to each plugin
object before installing them into the bottle application as shown below:

    :::python
    #!/usr/bin/env python
    import bottle_session
    import bottle_redis
    import bottle
    import redis
    from datetime import datetime

    app = bottle.app()
    session_plugin = bottle_session.SessionPlugin()
    redis_plugin = bottle_redis.RedisPlugin()

    connection_pool = redis.ConnectionPool(host='localhost', port=6379)

    session_plugin.connection_pool = connection_pool
    redis_plugin.redisdb = connection_pool
    app.install(session_plugin)
    app.install(redis_plugin)

    @bottle.route('/')
    def index(session,rdb):
        rdb.incr('visitors')
        visitor = rdb.get('visitors')
        last_visit = session['visit']
        session['visit'] = datetime.now().isoformat()

        return 'You are visitor %s, your last visit was on %s'%(visitor,last_visit)

    bottle.debug(True)
    bottle.run(app=app,host='localhost',port=8888)

Acknowledgments
---------------
Thanks to Marcel Hellkamp and the bottle community for the framework and to
Sean M. Collins whose bottle-redis package in bottle-extras served as the
inspiration for this bottle plugin. Thank you to James Burke for
your contributions.
