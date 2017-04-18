# -*- coding: utf8 -*-

# Copyright (C) 2015 Stanisław Szcześniak

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

import logging
import random

from bbschema import create_all
from werkzeug.test import Headers

from bbws import create_app, db
from requests_tests.delete_testing import DeleteTests
from requests_tests.get_id_testing import GetIDTests
from requests_tests.get_list_testing import GetListTests
from requests_tests.post_testing import PostTests
from requests_tests.put_testing import PutTests
from .fixture import load_data


class EntityTests(GetIDTests, GetListTests, DeleteTests, PutTests, PostTests):
    """This class gathers testing of multiple requests for Entity objects.

    See class_diagram.png for a graphical view of the classes
    EntityTests class inherits from and the classes that inherits
    from this class.

    Tested requests:
        -get/:id
        -get list
        -put
        -post
        -delete

    """
    def create_app(self):
        self.app = create_app('../config/test.py')
        return self.app

    # noinspection PyPep8Naming
    def setUp(self):

        logging.basicConfig(level=logging.INFO)
        db.engine.execute("DROP SCHEMA IF EXISTS bookbrainz CASCADE")
        db.engine.execute("CREATE SCHEMA bookbrainz")
        create_all(db.engine)

        random.seed()
        load_data(db)

        response = self.client.post(
            '/oauth/token',
            data={
                'client_id': '9ab9da7e-a7a3-4f86-87c6-bf8b4b8213c7',
                'username': 'Bob',
                'password': "bb",
                'grant_type': 'password'
            })

        self.assert200(response)
        oauth_access_token = response.json.get(u'access_token')

        self.request_default_headers = Headers(
            [('Authorization', 'Bearer ' + oauth_access_token),
             ('Content-Type', 'application/json')])

        self.specific_setup()

        """
         Specific names are names of the attributes/keys that
         change with different types of entities.
         Keys:
          'entity_class': some class which inherits from Entity (like Creator)
          'type_name': name as a type (like u'Creator')
          'ws_name': name in the web service urls(like 'creator')
          'entity_type_class': (like CreatorType)
          'entity_type': (like 'work_type')
          'entity_type_id': (like 'work_type_id')
        """
        self.specific_names = {}
        self.set_specific_names()
        self.check_specific_names()

    # noinspection PyPep8Naming
    def tearDown(self):
        db.session.remove()
        db.engine.execute("DROP SCHEMA IF EXISTS bookbrainz CASCADE")

    def specific_setup(self):
        raise NotImplementedError

    def set_specific_names(self):
        raise NotImplementedError

    def prepare_put_data(self, instance):
        """ Generates data for put request that is valid when used on instance
        @param instance(Entity): some entity
        @return(dict): JSON formatted data
        """
        raise NotImplementedError

    def prepare_post_data(self):
        """ Generates data for post request
        @param instance(Entity): some entity
        @return(dict): JSON formatted data
        """
        raise NotImplementedError

    def bbid_one_get_tests_specific_check(self, instance, response):
        """ Checks if entity specific data from get/:id response is correct
        @param instance(Entity): Entity for which the last get request was made
        @param response: Response from the last get request
        @return: None
        """
        raise NotImplementedError

    def post_data_check_specific(self, json_data, data):
        """ Checks if entity specific data was changed properly after post
        @param json_data(dict): JSON data that was used for the post request
        @param data(EntityData): EntityData of the recently created Entity
        @return: None
        """
        raise NotImplementedError

    def put_data_check_specific(self, json_data, data_old, data_new):
        """ Checks if entity specific data was changed properly after put
        @param json_data(dict): JSON data that was used for the put request
        @param data_old(EntityData): EntityData of the recently updated Entity
         before the request
        @param data_new(EntityData): EntityData of the recently updated Entity
         after the request:
        @return: None
        """
        raise NotImplementedError

    def get_specific_name(self, key):
        return self.specific_names[key]

    def get_request_default_headers(self):
        return self.request_default_headers

    def check_specific_names(self):
        keys = ['entity_class', 'type_name', 'ws_name', 'entity_type_id',
                'entity_type', 'entity_type_class']
        for key in keys:
            self.assertTrue(key in self.specific_names)
