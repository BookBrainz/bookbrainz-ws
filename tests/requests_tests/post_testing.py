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

from flask_testing import TestCase

from ..check_helper_functions import *
from ..constants import *


class PostTests(TestCase):
    """Class that gathers tests for post requests

    See class_diagram.png to see how it is related to other classes.
    """
    def get_specific_name(self, name):
        raise NotImplementedError

    def get_request_default_headers(self):
        raise NotImplementedError

    def prepare_post_data(self):
        raise NotImplementedError

    def post_data_check_specific(self, json_data, data):
        raise NotImplementedError

    def post_tests(self):
        logging.info(
            'POST request tests for {} good tests:{} bad tests:{}'
            .format(
                self.get_specific_name('type_name'),
                POST_TESTS_GOOD_COUNT,
                POST_TESTS_BAD_COUNT
            )
        )
        for i in range(POST_TESTS_GOOD_COUNT):
            logging.info(' Correct input test #{}'.format(i + 1))
            self.post_good_test()

        for i in range(POST_TESTS_BAD_COUNT):
            logging.info(' Incorrect input test #{}'.format(i + 1))
            incorrect_data_put_and_post_tests(self, 'post')

    def make_post(self, data_dict, correct_result=True):
        response_ws = self.client.post(
            '/{}/'.format(self.get_specific_name('ws_name')),
            headers=self.get_request_default_headers(),
            data=json.dumps(data_dict)
        )

        if correct_result:
            self.assert200(response_ws)

        return response_ws

    def post_good_test(self):
        instances_db = \
            db.session.query(self.get_specific_name('entity_class')).all()

        data_to_pass = self.prepare_post_data()
        self.make_post(data_to_pass)

        instances_db_after = \
            db.session.query(self.get_specific_name('entity_class')).all()

        self.assertEquals(len(instances_db) + 1, len(instances_db_after))

        new_instances = \
            [x for x in instances_db_after if x not in instances_db]
        self.assertEquals(len(new_instances), 1)
        new_instance = new_instances[0]

        instances_db.sort(key=lambda x: x.entity_gid)
        instances_db_after.sort(key=lambda x: x.entity_gid)

        self.assertEquals(len(instances_db) + 1, len(instances_db_after))

        self.post_data_check(data_to_pass, new_instance)

    def post_data_check(self, json_data, data):
        self.post_data_check_basic(json_data, data)
        self.post_data_check_specific(json_data, data)

    def post_data_check_basic(self, json_data, data):
        ent_data = data.master_revision.entity_data

        check_entity_type_json(self, json_data, data)

        assert_equals_or_both_none(
            self,
            json_data,
            'disambiguation',
            getattr(ent_data.disambiguation, 'comment', None)
        )
        assert_equals_or_both_none(
            self,
            json_data,
            'annotation',
            getattr(ent_data.annotation, 'content', None)
        )
        assert_equals_or_both_none(
            self,
            json_data,
            'aliases',
            ent_data.aliases,
            self.post_check_aliases_json,
            empty_list_allowed=True
        )
        assert_equals_or_both_none(
            self,
            json_data,
            'identifiers',
            ent_data.identifiers,
            self.post_check_identifiers_json,
            empty_list_allowed=True
        )

    def post_check_aliases_json(self, json_aliases, aliases):
        self.assertEquals(len(json_aliases), len(aliases))
        json_aliases.sort(key=lambda x: x['name'])
        aliases.sort(key=lambda x: x.name)
        for i in range(len(json_aliases)):
            check_single_alias_json(self, json_aliases[i], aliases[i])

    def post_check_identifiers_json(self, json_identifiers, identifiers):
        self.assertEquals(len(json_identifiers), len(identifiers))
        json_identifiers.sort(key=lambda x: identifier_hash(x, True))
        identifiers.sort(key=lambda x: identifier_hash(x, False))
        for i in range(len(json_identifiers)):
            self.assertEquals(
                identifier_hash(json_identifiers[i], True),
                identifier_hash(identifiers[i], False)
            )

    def post_check_languages_json(self, json_data, data):
        assert_equals_or_both_none(
            self,
            json_data,
            'languages',
            data.languages,
            self.post_check_languages_json_internal,
            empty_list_allowed=True
        )

    def post_check_languages_json_internal(self, json_languages, languages):
        self.assertEquals(len(json_languages), len(languages))
        json_languages.sort(key=lambda x: x['language_id'])
        languages.sort(key=lambda x: x.id)
        for i in range(len(json_languages)):
            self.assertEquals(
                json_languages[i]['language_id'],
                languages[i].id
            )

    def put_post_check_date_json(self, json_date, date, date_precision):
        check_date_json(
            self,
            json_date,
            ['YEAR', 'MONTH', 'DAY'][len(json_date.split('-')) - 1],
            date,
            date_precision
        )
