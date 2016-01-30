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
import random
import uuid

from werkzeug.test import Headers
from flask_testing import TestCase
from bbws import db


class DeleteTests(TestCase):
    """Class that gathers tests for delete requests

    See class_diagram.png to see how it is related to other classes.
    """
    def get_specific_name(self, key):
        raise NotImplementedError

    def get_request_default_headers(self):
        raise NotImplementedError

    def is_debug_mode(self):
        raise NotImplementedError

    def good_delete_tests(self):
        logging.info(
            'DELETE request tests for {} good tests:{}'
            .format(self.get_specific_name('type_name'), 1, 1)
        )

        logging.info(' Good test #{}'.format(1))

        actual_list = \
            db.session.query(self.get_specific_name('entity_class')).all()

        while actual_list:
            self.delete_random_entity(actual_list)
            self.check_if_not_deleted(actual_list)

    def delete_random_entity(self, entity_list):
        random_instance = random.choice(entity_list)
        response = self.correct_delete_request(random_instance.entity_gid)

        self.assert200(response)
        entity_list.remove(random_instance)

    def check_if_not_deleted(self, entities):
        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()
        instances_by_id = dict([(x.entity_gid, x) for x in instances])

        for entity in entities:
            entity_from_db = instances_by_id[entity.entity_gid]
            self.assertIsNotNone(entity_from_db.master_revision.entity_data)

    def bad_delete_tests(self):
        logging.info(
            'DELETE request tests for {} bad tests:{}'
            .format(self.get_specific_name('type_name'), 1, 1)
        )

        logging.info(' Bad test #{}'.format(1))

        self.bad_uuid_delete_tests()
        self.bad_format_delete_tests()
        self.bad_double_delete_tests()
        self.bad_authentication_delete_tests()

    def bad_uuid_delete_tests(self):
        instances_db = \
            db.session.query(self.get_specific_name('entity_class')).all()
        initial_size = len(instances_db)
        for i in range(10):
            entity_gid = uuid.uuid4()
            response_ws = self.client.delete(
                '/{entity_type}/{entity_gid}/'.format(
                    entity_type=self.get_specific_name('ws_name'),
                    entity_gid=entity_gid),
                headers=self.get_request_default_headers(),
                data="{\"revision\": {\"note\": \"A Test Note\"}}")
            self.assert404(response_ws)

            instances_db = \
                db.session.query(self.get_specific_name('entity_class')).all()
            for instance in instances_db:
                self.assertNotEquals(
                    instance.master_revision.entity_data,
                    None
                )
            self.assertEquals(len(instances_db), initial_size)

    def bad_format_delete_tests(self):
        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()
        random_instance = random.choice(instances)

        self.bad_format_delete_tests_404(random_instance)

        self.bad_format_delete_single_test(
            '/{ent_type}/'
            .format(
                ent_type=self.get_specific_name('ws_name')),
            405)

        self.bad_format_delete_single_test(
            '/{ent_type}'
            .format(
                ent_type=self.get_specific_name('ws_name')),
            301)

        self.bad_format_delete_single_test(
            '{ent_type}/{ent_gid}/'
            .format(
                ent_type=self.get_specific_name('ws_name'),
                ent_gid=unicode(random_instance.entity_gid)),
            401)

    def bad_format_delete_tests_404(self, random_instance):
        self.bad_format_delete_single_test(
            '/creature/{ent_gid}/'
            .format(
                ent_gid=unicode(random_instance.entity_gid)),
            404)

        self.bad_format_delete_single_test(
            '//////{ent_gid}'
            .format(
                ent_gid=unicode(random_instance.entity_gid)),
            404)

        self.bad_format_delete_single_test(
            '/{ent_gid}'
            .format(
                ent_gid=unicode(random_instance.entity_gid)),
            404)

        self.bad_format_delete_single_test(
            '/{ent_gid}/'
            .format(
                ent_gid=unicode(random_instance.entity_gid)),
            404)

        self.bad_format_delete_single_test(
            '{ent_gid}'.format(
                ent_gid=unicode(random_instance.entity_gid)),
            404)

        self.bad_format_delete_single_test(
            '/{ent_gid}/{ent_type}/'.format(
                ent_gid=unicode(random_instance.entity_gid),
                ent_type=self.get_specific_name('ws_name')),
            404)

    def bad_format_delete_single_test(self, delete_uri, expected_http_status):
        instances_db = \
            db.session.query(self.get_specific_name('entity_class')).all()

        response_ws = self.client.delete(delete_uri, )
        self.assert_status(response_ws, expected_http_status)

        instances_db_after = \
            db.session.query(self.get_specific_name('entity_class')).all()

        self.assertTrue(len(instances_db), len(instances_db_after))
        for instance in instances_db_after:
            self.assertIsNotNone(instance.master_revision.entity_data)

    def bad_double_delete_tests(self):
        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()
        random_instance = random.choice(instances)

        for i in range(4):
            response = self.correct_delete_request(random_instance.entity_gid)
            if i == 0:
                self.assert200(response)
            else:
                self.assert405(response)

    def bad_authentication_delete_tests(self):
        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()
        random_instance = random.choice(instances)

        headers = Headers(
            [('Authorization', 'Bearer ' + 'Monty Python'),
             ('Content-Type', 'application/json')])

        response = self.client.delete(
            '/{entity_type}/{entity_gid}/'
            .format(
                entity_type=self.get_specific_name('ws_name'),
                entity_gid=random_instance.entity_gid
            ),
            headers=headers,
            data=''
        )
        self.assert_status(response, 401)

    def correct_delete_request(self, entity_gid):
        return self.client.delete(
            '/{entity_type}/{entity_gid}/'
            .format(
                entity_type=self.get_specific_name('ws_name'),
                entity_gid=entity_gid
            ),
            headers=self.get_request_default_headers(),
            data="{\"revision\": {\"note\": \"A Test Note\"}}"
        )
