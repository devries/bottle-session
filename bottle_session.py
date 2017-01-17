"""
Bottle_session is a session manager for the Bottle microframework that uses a
cookie to maintain your web session and stores a hash associated with that
cookie using the redis key-value store. It is designed as a simple Bottle
plugin.

Examples and additional documentation are available in the README and
on the website: https://bitbucket.org/devries/bottle-session

Copyright (c) 2013, Christopher De Vries.
License: Artistic License 2.0 (see LICENSE.txt)
"""
from __future__ import absolute_import

import redis
from bottle import PluginError
from bottle import request
from bottle import response
import uuid

__version__ = '0.7'

try:
    from Crypto.Random import get_random_bytes
    def getUuid():
        return uuid.UUID(bytes=get_random_bytes(16))

except ImportError:
    def getUuid():
        return uuid.uuid4()

MAX_TTL = 7*24*3600 # 7 day maximum cookie limit for sessions

class SessionPlugin(object):
    """Bottle sessions using redis plugin class.

    This class creates a plugin for the bottle framework which uses cookies
    to handle sessions and stores session information in a redis database.
    """

    name = 'session'
    api = 2

    def __init__(self,host='localhost',port=6379,db=0,cookie_name='bottle.session',cookie_lifetime=300,keyword='session',password=None):
        """Session plugin for the bottle framework.

        Args:
            host (str): The host name of the redis database server. Defaults to
                'localhost'.
            port (int): The port of the redis database server. Defaults to
                6379.
            db (int): The redis database numbers. Defaults to 0.
            cookie_name (str): The name of the browser cookie in which to store
                the session id. Defaults to 'bottle.session'.
            cookie_lifetime (int): The lifetime of the cookie in seconds. When
                the cookie's lifetime expires it will be deleted from the redis
                database. The browser should also cause it to expire. If the
                value is 'None' then the cookie will expire from the redis
                database in 7 days and will be a session cookie on the 
                browser. The default value is 300 seconds.
            keyword (str): The bottle plugin keyword. By default this is
                'session'.
            password (str): The optional redis password.

        Returns:
            A bottle plugin object.
        """

        self.host = host
        self.port = port
        self.db = db
        self.cookie_name = cookie_name
        self.cookie_lifetime = cookie_lifetime
        self.keyword = keyword
        self.password = password
        self.connection_pool = None

    def setup(self,app):
        for other in app.plugins:
            if not isinstance(other, SessionPlugin): continue
            if other.keyword == self.keyword:
                raise PluginError("Found another session plugin with "\
                        "conflicting settings (non-unique keyword).")

        if self.connection_pool is None:
            self.connection_pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db, password=self.password)

    def apply(self,callback,context):
        conf = context.config.get('session') or {}
        args = context.get_callback_args()

        if self.keyword not in args:
            return callback

        def wrapper(*args,**kwargs):
            r = redis.Redis(connection_pool=self.connection_pool)
            kwargs[self.keyword] = Session(r,self.cookie_name,self.cookie_lifetime)
            rv = callback(*args,**kwargs)
            return rv
        return wrapper


class Session(object):
    """A bottle session object.

    This object is a dictionary like object in which you can place data
    associated with the current session. It is created by the bottle
    framework and accessible using the keyword defined when creating
    the plugin.
    """

    def __init__(self,rdb,cookie_name='bottle.session',cookie_lifetime=None):
        self.rdb = rdb
        self.cookie_name = cookie_name
        if cookie_lifetime is None:
            self.ttl = MAX_TTL
            self.max_age = None
        else:
            self.ttl = cookie_lifetime
            self.max_age = cookie_lifetime
        cookie_value = self.get_cookie()
        if cookie_value:
            self.validate_session_id(cookie_value)
        else:
            self.new_session_id()

        
    def get_cookie(self):
        uid_cookie = request.get_cookie(self.cookie_name)
        return uid_cookie

    def set_cookie(self,value):
        response.set_cookie(self.cookie_name,value,max_age=self.max_age,path='/')

    def validate_session_id(self,cookie_value):
        keycheck = 'session:%s'%str(uuid.UUID(cookie_value))
        if self.rdb.exists(keycheck):
            self.session_hash = keycheck
            self.rdb.expire(self.session_hash,self.ttl)
        
        else:
            self.new_session_id()

    def new_session_id(self):
        uid = getUuid()
        self.session_hash = 'session:%s'%str(uid)
        self.set_cookie(uid.hex)

    def destroy(self):
        """Destroy the session.

        This function deletes the current session id from the database along
        with all associated data. It will create a new session id for the
        remainder of the transaction.
        """

        self.rdb.delete(self.session_hash)
        self.new_session_id()

    def regenerate(self):
        """Regenerate the session id.

        This function creates a new session id and stores all information
        associated with the current id in that new id. It then destroys the
        old session id. This is useful for preventing session fixation attacks
        and should be done whenever someone uses a login to obtain additional
        authorizaiton.
        """

        oldhash = self.session_hash
        self.new_session_id()
        try:
            self.rdb.rename(oldhash,self.session_hash)
            self.rdb.expire(self.session_hash,self.ttl)
        except:
            pass

    def __contains__(self,key):
        """Check if a key is in the session dictionary.
        
        Args:
            key (str): The dictionary key.
        """

        return self.rdb.hexists(self.session_hash,key)

    def __delitem__(self,key):
        """Delete an item from the session dictionary.
        
        Args:
            key (str): The dictionary key.
        """

        self.rdb.hdel(self.session_hash,key)

    def __getitem__(self,key):
        """Return a value associated with a key from the session dictionary.
        
        Args:
            key (str): The dictionary key.

        Returns:
            str: The value associate with that key or None if the key is
                not in the dictionary.
        """

        self.rdb.expire(self.session_hash,self.ttl)
        encoded_result = self.rdb.hget(self.session_hash,key)
        if encoded_result is None:
            return None
        else:
            return encoded_result.decode('utf-8')

    def __setitem__(self,key,value):
        """Set an existing or new key, value association.

        Args:
            key (str): The dictionary key.
            value (str): The dictionary value
        """

        self.rdb.hset(self.session_hash,key,value)
        self.rdb.expire(self.session_hash,self.ttl)

    def __len__(self):
        """Get the number of key,value pairs in the dictionary.

        Returns:
            int: Number of key value pairs in the dictionary.
        """

        return self.rdb.hlen(self.session_hash)

    def __iter__(self):
        """Iterate through the key,value pairs.

        Generates:
            (str, str): Key and value tuples in the dictionary.
        """

        all_items = self.rdb.hgetall(self.session_hash)
        for k, v in list(all_items.items()):
            yield (k.decode('utf-8'),v.decode('utf-8'))

    def get(self,key,default=None):
        """Get a value from the dictionary.

        Args:
            key (str): The dictionary key.
            default (any): The default to return if the key is not in the
                dictionary. Defaults to None.

        Returns:
            str or any: The dictionary value or the default if the key is not
                in the dictionary.
        """

        retval = self.__getitem__(key)
        if not retval:
            retval = default

        return retval

    def has_key(self,key):
        """Check if the dictionary contains a key.

        Args:
            key (str): The dictionary key.

        Returns:
            bool: True if the key is in the dictionary. False otherwise.
        """
        return self.__contains__(key)

    def items(self):
        """Return a list of all the key, value pair tuples in the dictionary.

        Returns:
            list of tuples: [(key1,value1),(key2,value2),...,(keyN,valueN)]
        """
        all_items = [(k.decode('utf-8'),v.decode('utf-8')) for k,v in self.rdb.hgetall(self.session_hash)]
        return all_items

    def keys(self):
        """Return a list of all keys in the dictionary.

        Returns:
            list of str: [key1,key2,...,keyN]
        """
        all_keys = [k.decode('utf-8') for k,v in self.rdb.hgetall(self.session_hash)]
        return all_keys

    def values(self):
        """Returns a list of all values in the dictionary.

        Returns:
            list of str: [value1,value2,...,valueN]
        """
        all_values = [v.decode('utf-8') for k,v in self.rdb.hgetall(self.session_hash)]
        return all_values

