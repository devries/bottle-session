"""
Documentation goes here.
"""

__version__ = '0.1'

import redis
import inspect
from bottle import PluginError
from bottle import request
from bottle import response
import uuid

try:
    from Crypto.Random import get_random_bytes
    def getUuid():
        return uuid.UUID(bytes=get_random_bytes(16))

except ImportError:
    def getUuid():
        return uuid.uuid4()

MAX_TTL = 7*24*3600 # 7 day maximum cookie limit for sessions

class SessionPlugin(object):
    name = 'session'
    api = 2

    def __init__(self,host='localhost',port=6379,db=0,cookie_name='bottle.session',cookie_lifetime=300,keyword='session'):
        self.host = host
        self.port = port
        self.db = db
        self.cookie_name = cookie_name
        self.cookie_lifetime = cookie_lifetime
        self.keyword = keyword
        self.connection_pool = None

    def setup(self,app):
        for other in app.plugins:
            if not isinstance(other, SessionPlugin): continue
            if other.keyword == self.keyword:
                raise PluginError("Found another session plugin with "\
                        "conflicting settings (non-unique keyword).")

            if self.connection_pool is None:
                self.connection_pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db)

    def apply(self,callback,context):
        conf = context.config.get('session') or {}
        args = inspect.getargspec(context.callback)[0]

        if self.keyword not in args:
            return callback

        def wrapper(*args,**kwargs):
            r = redis.Redis(connection_pool=self.connection_pool)
            kwargs[self.keyword] = Session(r,self.cookie_name,self.cookie_lifetime)
            rv = callback(*args,**kwargs)
            return rv
        return wrapper


class Session(object):
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
        self.rdb.delete(self.session_hash)
        self.new_session_id()

    def regenerate(self):
        oldhash = self.session_hash
        self.new_session_id()
        try:
            self.rdb.rename(oldhash,self.session_hash)
            self.rdb.expire(self.session_hash,self.ttl)
        except:
            pass

    def __contains__(self,key):
        return self.rdb.hexists(self.session_hash,key)

    def __delitem__(self,key):
        self.rdb.hdel(self.session_hash,key)

    def __getitem__(self,key):
        self.rdb.expire(self.session_hash,self.ttl)
        return self.rdb.hget(self.session_hash,key)

    def __setitem__(self,key,value):
        self.rdb.hset(self.session_hash,key,value)
        self.rdb.expire(self.session_hash,self.ttl)

    def __len__(self):
        return self.rdb.hlen(self.session_hash)

    def __iter__(self):
        all_items = self.rdb.hgetall(self.session_hash)
        for t in all_items.items():
            yield t

    def get(self,key,default=None):
        retval = self.__getitem__(key)
        if not retval:
            retval = default

        return retval

    def has_key(self,key):
        return self.__contains__(key)

    def items(self):
        all_items = self.rdb.hgetall(self.session_hash)
        return all_items.items()

    def keys(self):
        all_items = self.rdb.hgetall(self.session_hash)
        return all_items.keys()

    def values(self):
        all_items = self.rdb.hgetall(self.session_hash)
        return all_items.values()

