import os
import bottle
import bottle_session
try:
    import urlparse
except:
    from urllib import parse as urlparse
import random
import redis
import string
import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

app = bottle.app()
session_plugin = bottle_session.SessionPlugin(cookie_lifetime=bottle_session.MAX_TTL, cookie_secure=True, cookie_httponly=True)

#redis_url = os.environ.get('REDIS_URL','http://:foobared@localhost:6379')

#parsed_url = urlparse.urlparse(redis_url)

#connection_pool = redis.ConnectionPool(host=parsed_url.hostname, port=parsed_url.port, password=parsed_url.password)

#session_plugin.connection_pool = connection_pool

app.install(session_plugin)

@bottle.route('/')
def get_main_page(session):
    csrf = ''.join(random.choice(string.ascii_uppercase+string.ascii_lowercase+string.digits) for x in range(32))

    session['csrf'] = csrf

    logger.debug("Items")
    for k,v in session.items():
        logger.debug("%s:%s",k,v)

    keys = session.keys()
    logger.debug("Keys: %s", ', '.join(keys))

    values = session.values()
    logger.debug("Values: %s", ', '.join(values))

    if session.get('name') is None:
        context = {'csrf_token': csrf}

        return bottle.template('set_name', **context)

    else:
        context = {'csrf_token': csrf,
                'name': session.get('name')
                }

        return bottle.template('has_name', **context)

@bottle.route('/submit', method='POST')
def set_name(session):
    keys = bottle.request.forms.keys()

    session['name'] = bottle.request.forms.name.strip()
    csrf = bottle.request.forms.get('csrf_token')

    if session['csrf']!=csrf:
        return bottle.template('error', warning_message='Cross-site scripting error.')

    bottle.redirect('/')

@bottle.route('/logout')
def logout(session):
    session.destroy()

    bottle.redirect('/')

if __name__=='__main__':
    bottle.debug(True)
    port = 8080
    bottle.run(app=app,host='127.0.0.1',port=port)
