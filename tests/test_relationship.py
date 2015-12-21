# -*- coding: utf8 -*-

# Copyright (C) 2014-2015  Ben Ockmore, Stanisław Szcześniak

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

from bbws import create_app, db
from bbschema import Relationship, create_all
from flask_testing import TestCase

from .fixture import load_data


class TestRelationshipViews(TestCase):
    def create_app(self):
        return create_app('../config/test.py')

    def setUp(self):
        db.engine.execute("DROP SCHEMA IF EXISTS bookbrainz CASCADE")
        db.engine.execute("CREATE SCHEMA bookbrainz")
        create_all(db.engine)
        load_data(db)

    def test_relationship_get_single(self):
        relationship_to_test = 3
        db_response = db.session.query(Relationship).filter(Relationship.relationship_id == relationship_to_test).one()
        response = self.client.get('/relationship/' + str(relationship_to_test))
        self.assertEquals(response.json.get('relationship_id'), relationship_to_test)
        self.assertEquals(response.json.get('uri'),
                          'http://localhost/relationship/' + str(relationship_to_test))
        self.assertEquals(response.json.get('master_revision_id'), db_response.master_revision_id)
        self.assertTrue('last_updated' in response.json)
        self.assertEquals(len(response.json.get('entities', [])), 1)
        self.assertEquals(len(response.json.get('texts', [])), 1)

    def test_relationship_get_many(self):
        response = self.client.get('/relationship/')
        db_numer_of_relationships = len(db.session.query(Relationship).all())
        self.assertEquals(response.json.get('count'), db_numer_of_relationships)
        self.assertEquals(response.json.get('offset'), 0)
        self.assertEquals(len(response.json.get('objects', [])), db_numer_of_relationships)
