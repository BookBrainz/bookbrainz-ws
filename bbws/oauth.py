# -*- coding: utf8 -*-

# Copyright (C) 2014-2015  Ben Ockmore

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import bcrypt
import datetime
import uuid

from flask import request as global_request

from bbschema import OAuthClient, User
from flask_oauthlib.provider import OAuth2RequestValidator
from sqlalchemy.orm.exc import NoResultFound

from . import cache, db, oauth_provider


class Grant(object):
    def __init__(self, client_id, user_id, code, redirect_uri, expires,
                 scopes):
        self.client_id = client_id
        self.user_id = user_id
        self.code = code
        self.redirect_uri = redirect_uri
        self.expires = expires
        self.scopes = scopes

    @classmethod
    def load(cls, code):
        r = cache.hgetall(code)
        if r is None:
            return None

        expires = datetime.datetime.strptime(r['expires'], '%Y-%m-%d %H:%M:%S')
        return cls(r['client_id'], r['user_id'], code, r['redirect_uri'],
                   expires, r['scopes'].split())

    def save(self):
        self.expires = self.expires.replace(microsecond=0)

        cache.hmset(self.code, {
            'client_id': self.client_id,
            'user_id': self.user_id,
            'redirect_uri': self.redirect_uri,
            'expires': str(),
            'scopes': ' '.join(self.scopes)
        })
        dt = datetime.datetime.now() - self.expires
        cache.expire(self.code, dt.seconds)

    def delete(self):
        cache.delete(self.code)
        return self


class BearerToken(object):
    def __init__(self, client_id, scopes, expires,
                 user_id, access_token=None, refresh_token=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.scopes = scopes
        self.expires = expires
        self.user_id = user_id

    @classmethod
    def load(cls, access_token=None, refresh_token=None):
        if access_token is not None:
            r = cache.hgetall(access_token)
        elif refresh_token is not None:
            r = cache.hgetall(refresh_token)
        else:
            return None

        if not r:
            return None

        expires = datetime.datetime.strptime(r['expires'], '%Y-%m-%d %H:%M:%S')

        return cls(
            client_id=r['client_id'],
            scopes=r['scopes'].split(),
            expires=expires,
            user_id=r['user_id'],
            access_token=r['access_token'],
            refresh_token=r['refresh_token']
        )

    def save(self):
        self.expires = self.expires.replace(microsecond=0)

        data = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'user_id': self.user_id,
            'expires': str(self.expires),
            'scopes': ' '.join(self.scopes)
        }

        cache.hmset(self.access_token, data)
        cache.hmset(self.refresh_token, data)

        dt = datetime.datetime.now() - self.expires
        cache.expire(self.access_token, dt.seconds)
        cache.expire(self.refresh_token, dt.seconds)

    @property
    def user(self):
        return db.session.query(User).filter_by(user_id=self.user_id).first()

    def delete(self):
        cache.delete(self.access_token)
        cache.delete(self.refresh_token)
        return self


class MyRequestValidator(OAuth2RequestValidator):
    """ Defines a custom OAuth2 Request Validator based on the Client, User
        and Token models.
        :param OAuth2RequestValidator: Overrides the OAuth2RequestValidator.
    """
    def __init__(self):
        pass

    def _clientgetter(self, client_id):
        return db.session.query(OAuthClient).filter_by(
            client_id=uuid.UUID(hex=client_id)
        ).first()

    def _usergetter(self, username, password, *args, **kwargs):
        user = db.session.query(User).filter_by(name=username).first()

        if user.password == '':
            return None

        password = password.encode('utf-8')
        cur_hash = user.password.encode('utf-8')

        # Ensure password matches the hash in the database
        if (cur_hash == bcrypt.hashpw(password, cur_hash)):
            return user

        return None

    def _tokengetter(self, access_token=None, refresh_token=None):
        if access_token:
            return BearerToken.load(access_token=access_token)
        elif refresh_token:
            return BearerToken.load(refresh_token=refresh_token)

    def _tokensetter(self, token, request):
        existing = cache.get(request.user.user_id)
        if existing is not None:
            stored_token = BearerToken.load(access_token=existing)
            stored_token.delete()

        expires_in = token.pop(u'expires_in')
        expires = (datetime.datetime.utcnow() +
                   datetime.timedelta(seconds=expires_in))

        print token[u'scope']
        tok = BearerToken(
            access_token=token[u'access_token'],
            refresh_token=token[u'refresh_token'],
            scopes=token[u'scope'].split(),
            expires=expires,
            client_id=request.client.client_id,
            user_id=request.user.user_id,
        )
        tok.save()
        return tok


def init(app):
    oauth_provider._validator = MyRequestValidator()

    @app.route('/ws/oauth/token', methods=['POST'])
    @oauth_provider.token_handler
    def access_token(*args, **kwargs):
        return None
