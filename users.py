import time
import struct
import base64
import hashlib
from abc import ABCMeta, abstractmethod


SESSION_KEY_EXPIRATION = 600


class Users(object):
    """
    Users object interface
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def login(self, user_id):
        """
        get a new login token
        """
        pass

    @abstractmethod
    def validate(self, token):
        """
        return the user_id if the token is valid or None otherwise
        """
        pass


class UserTokenSigned(object):

    @staticmethod
    def get(user_id, secret):
        """
        Generate a new 224 bits token (encoded in base64) for a given user_id (int)
        user_id (uint32) timestamp(uint32) sha1(160bits)
        """
        timestamp = int(time.time())
        hash_obj = hashlib.sha1('%s:%s:%s' % (user_id, timestamp, secret))
        hash_digest = hash_obj.digest()

        token = struct.pack('!II20B', user_id, timestamp, *[ord(i) for i in hash_digest])
        b64 = base64.urlsafe_b64encode(token)
        return b64

    @staticmethod
    def validate(b64_token, timeout, secret):
        """
        Returns the user_id if the token is valid (correct format and not expired) None otherwise
        """
        try:
            hex_token = base64.urlsafe_b64decode(b64_token)
            token_parts = struct.unpack('!II20B', hex_token)
            user_id = token_parts[0]
            timestamp = token_parts[1]
            hash_digest = ''.join(chr(i) for i in token_parts[2:])
            expected_hash = hashlib.sha1('%s:%s:%s' % (user_id, timestamp, secret))

            if expected_hash.digest() == hash_digest:
                now = time.time()
                if (now - timeout) < timestamp <= now:
                    return user_id
        except:
            pass

        return None


class UsersNonStored(Users):
    """
    Use signed tokens without storing them in memory. More than one token
    per user could be valid in a given time.
    """
    _key = 'secret_key_dadfgwrhghwhgreqhththwmkwrmrgnwkbjk23e3243dada3d"$%&/()=fagagfg34rf4*z<1fg56&'

    def login(self, user_id):
        return UserTokenSigned.get(user_id, self._key)

    def validate(self, token):
        return UserTokenSigned.validate(token, SESSION_KEY_EXPIRATION, self._key)
