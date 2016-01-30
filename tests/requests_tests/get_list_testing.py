# -*- coding: utf8 -*-

# Copyright (C) 2016 Stanisław Szcześniak

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
import uuid

from flask_testing import TestCase

from ..check_helper_functions import *
from ..constants import *


class GetListTests(TestCase):
    """Class that gathers tests for get-list requests

     See class_diagram.png to see how it is related to other classes.
    """
    def get_specific_name(self, name):
        raise NotImplementedError

    def bbid_one_get_tests_specific_check(self, instance, response):
        raise NotImplementedError

    def get_request_default_headers(self):
        raise NotImplementedError

    def list_get_tests(self):
        logging.info(
            'GET-list request tests for {} tests:'
            .format(
                self.get_specific_name('type_name'),
                GET_LIST_TESTS_COUNT
            )
        )
        for i in range(GET_LIST_TESTS_COUNT):
            logging.info(' test #{}'.format(i + 1))
            self.list_get_single_test()

    def list_get_single_test(self):
        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()
        rand_limit = random.randint(-1, len(instances) + 3)
        response_ws = self.client.get(
            '/' + self.get_specific_name('ws_name') + '/',
            headers=self.get_request_default_headers(),
            data='{\"limit\":' + str(rand_limit) + '}'
        )
        if rand_limit > -1:
            self.assert200(response_ws)
        else:
            self.assert400(response_ws)
            return
        rand_limit = min(rand_limit, len(instances))
        self.assertEquals(rand_limit, response_ws.json[u'count'])

        wanted_instances = \
            [instance for instance in instances if
             len([x for x in response_ws.json[u'objects']
                  if uuid.UUID(x[u'entity_gid']) ==
                  instance.entity_gid]) > 0]

        self.list_get_list_correctness_check(
            response_ws.json[u'objects'],
            wanted_instances
        )

    def list_get_list_correctness_check(self, json_list, db_list):
        self.assertEquals(len(json_list), len(db_list))
        json_list.sort(key=lambda x: x['entity_gid'])
        db_list.sort(key=lambda x: x.entity_gid)
        for i in range(len(json_list)):
            self.list_get_object_correctness_check(json_list[i], db_list[i])

    def list_get_object_correctness_check(self, json_object, db_object):
        self.assertEquals(json_object['_type'],
                          self.get_specific_name('type_name'))
        self.assertEquals(uuid.UUID(json_object['entity_gid']),
                          db_object.entity_gid)
        check_uri_suffix(self,
                         json_object['uri'],
                         '/{}/{}/'.format(self.get_specific_name('ws_name'),
                                          json_object['entity_gid']))
