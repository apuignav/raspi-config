#!/usr/bin/env python
# =============================================================================
# @file   Containers.py
# @author Albert Puig (albert.puig@epfl.ch)
# @date   24.07.2013
# =============================================================================
"""Container objects with special properties:
  * Dictionary with case-insensitive keys (CaseInsensitiveDict).
  * Dictionary where keys have a definite timespan (TimedDict and the locking
    TimedLockingDict) and a list
  * Dictionary with a limited number of items (Limitedlist).

"""

import collections
from threading import Lock
import datetime


class CaseInsensitiveDict(collections.MutableMapping):
    """
    A case-insensitive ``dict``-like object.

    Taken from https://github.com/kennethreitz/requests.
    Implements all methods and operations of
    ``collections.MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive:

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.

    """
    def __init__(self, data=None, **kwargs):
        self._store = dict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, collections.Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        """Return copy of the CaseInsensitiveDict."""
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, dict(self.items()))


class TimedDict:
    """Dictionary-like class where keys have expiration time.

    When obtaining the keys, their expiration time is checked and if necessary
    they are removed from the pool. There are also functions to sistematically
    clean expired keys.

    """
    def __init__(self, expiration_time, cleanup_func=None):
        """Initialize internal dictionary, time limit and cleanup function.

        @param expiration_time: life span (in s) of the keys
        @type expiration_time: int
        @param cleanup_func: function to execute when the key is expired and removed
        @type cleanup_func: callable

        """
        self._dict = {}
        self._cleanup_func = cleanup_func
        self.expiration_time = expiration_time

    def __iter__(self):
        """Return internal dictionary iterator."""
        return self._dict.__iter__()

    def __len__(self):
        """Return length of internal dictionary."""
        return len(self._dict)

    def __repr__(self):
        """Nice representation of each key, with its expiration time and value."""
        data = []
        for key in self._dict:
            data.append( "%s:" % str( key ) )
            data.append( "    Exp. time: %s" % self._dict[ key ][ 'expiration_time' ] )
            if self._dict[ key ][ 'value' ]:
                data.append( "    Value: %s" % self._dict[ key ][ 'value' ] )
        return "\n".join( data )

    def has_key(self, key):
        """Check if internal dictionary has given key. If the key is expired, delete
        it and return False.

        @param key: key to check
        @type key: object

        @return: bool

        """
        if key in self._dict:
            expiration_time = self._dict[key]['expiration_time']
            if expiration_time > datetime.datetime.now():
                return True
            else:
                self.delete(key)
        return False

    def delete(self, key):
        """Delete a given key and execute the cleanup function.

        The cleanup function should only accept one parameter, and it is the value
        associated to the given key.

        @param key: key to delete
        @type key: object

        """
        if key not in self._dict:
            return
        if self._cleanup_func:
            self._cleanup_func(self._dict[key]['value'])
        del(self._dict[key])

    def delete_expired(self):
        """Delete expired keys.

        Loop over all keys and check if they have expired. If that happens, cleanup
        and delete them.

        """
        for key in self._dict.keys():
            expiration_time = self._dict[key]['expiration_time']
            if expiration_time < datetime.datetime.now():
                self.delete(key)

    def delete_all(self):
        """Clear the internal dictionary."""
        for key in self._dict.keys():
            self.delete(key)

    def add(self, key, value):
        """Add a key to the internal dictionary, setting the expiration time.

        @param key: key to add
        @type key: object
        @param value: value associated to the key
        @type value: object

        """
        exp_time = datetime.datetime.now() + datetime.timedelta(seconds=self.expiration_time)
        entry = {'expiration_time': exp_time, 'value': value}
        self._dict[key] = entry

    def get(self, key, default=None):
        """Get a key from the internal dictionary. If the key is expired, it is not
        returned.

        @param key: key to return
        @type key: object
        @param default: value to return of the key is not valid
        @type default: object

        @return: value associated to the key or default

        """
        if key in self._dict:
            expiration_time = self._dict[key]['expiration_time']
            if expiration_time > datetime.datetime.now():
                self._dict[key]['expiration_time'] = datetime.datetime.now() + datetime.timedelta(seconds=self.expiration_time)
                return self._dict[key]['value']
            else:
                self.delete(key)
        return default

class TimedLockingDict(TimedDict):
    """TimedDict with blocking access to keys.

    Besides the TimedDict methods, one can use get_locking to add lock the file when
    it has been got, and unlock to liberate the key when finished. Note that the usage
    of usual get function will not consider the presence of the lock.

    """
    def add(self, key, value):
        """Add a key to the internal dictionary, setting the expiration time and the lock.

        @param key: key to add
        @type key: object
        @param value: value associated to the key
        @type value: object

        """
        exp_time = datetime.datetime.now() + datetime.timedelta(seconds=self.expiration_time)
        entry = {'expiration_time': exp_time, 'value': value, 'lock': Lock()}
        self._dict[key] = entry

    def get_locking(self, key, default=None, blocking=True):
        """Get a key from the internal dictionary, locking it.

        If the key is expired, it is not returned. If the key is locked, behavior
        will depend on the blocking parameter. If True, the function will block until
        the key is unlocked. Otherwise it will return default.

        @param key: key to return
        @type key: object
        @param default: value to return of the key is not valid
        @type default: object
        @param blocking: block if the key is locked?
        @type blocking: bool

        @return: value associated to the key or default

        """
        if key in self._dict:
            expiration_time = self._dict[key]['expiration_time']
            if expiration_time > datetime.datetime.now():
                self._dict[key]['expiration_time'] = datetime.datetime.now() + datetime.timedelta(seconds=self.expiration_time)
                if not self._dict[key]['lock'].acquire(blocking):
                    return default
                return self._dict[key]['value']
            else:
                self.delete(key)
        return default

    def unlock(self, key):
        """Unlock the given key.

        @param key: key tu unlock
        @type key: object

        """
        if key in self._dict:
            self._dict[key]['lock'].release()

# EOF
