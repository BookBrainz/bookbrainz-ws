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

import random
import uuid

from bbschema import Creator, create_all, Relationship, RelationshipEntity, RelationshipData, RelationshipRevision
from flask_testing import TestCase
from werkzeug.test import Headers

from bbws import create_app, db
from .fixture import load_data


class TestCreatorID(TestCase):
    def create_app(self):
        self.app = create_app('../config/test.py')
        return self.app

    def setUp(self):
        db.engine.execute("DROP SCHEMA IF EXISTS bookbrainz CASCADE")
        db.engine.execute("CREATE SCHEMA bookbrainz")
        create_all(db.engine)
        load_data(db)
        random.seed()

        response = self.client.post('/oauth/token',
                                    data={'client_id': '9ab9da7e-a7a3-4f86-87c6-bf8b4b8213c7',
                                          'username': 'Bob', 'password': "bb", 'grant_type': 'password'})
        self.assert200(response)
        self._access_token = response.json.get(u'access_token')

    def tearDown(self):
        db.session.remove()
        db.engine.execute("DROP SCHEMA IF EXISTS bookbrainz CASCADE")

    def test_get_good_bbid(self):
        instances = db.session.query(Creator).all()
        random.shuffle(instances)

        for instance in instances:
            self.assertEquals(instance._type, u'Creator')
            creator_gid = unicode(instance.entity_gid)
            response = self.client.get('/creator/{}/'.format(creator_gid))
            self.assert200(response)

            # Type check
            self.assertEquals(response.json.get(u'_type'), u'Creator')

            # Entity gid
            self.assertEquals(response.json.get(u'entity_gid'), creator_gid)

            # Gender check
            self.assertEquals(response.json.get('gender'), instance.master_revision.entity_data.gender)

            # Default alias check
            self.assertEquals(response.json.get('default_alias'), instance.master_revision.entity_data.default_alias)

            # Last updated
            last_updated = instance.last_updated.isoformat()
            self.assertEquals(response.json.get(u'last_updated'), last_updated)

            # Revision
            # Created at
            created_at = instance.master_revision.created_at.isoformat()
            self.assertEquals(response.json.get(u'revision').get(u'created_at'), created_at)

            # Entity data id
            entity_data_id = instance.master_revision.entity_data_id
            self.assertEquals(response.json.get(u'revision').get(u'entity_data_id'), entity_data_id)

            # Uris
            self.uris_test()

    def uris_test(self):
        instances = db.session.query(Creator).all()
        random.shuffle(instances)
        for instance in instances:
            creator_gid = unicode(instance.entity_gid)
            response = self.client.get('/creator/{}/'.format(creator_gid))
            self.assert200(response)
            for type_of_uri in ['aliases', '', 'annotation', 'relationships', 'identifiers', 'disambiguation']:
                if type_of_uri is not 'relationships':
                    to_search = '/creator/'
                else:
                    to_search = '/entity/'
                to_search += creator_gid + '/' + type_of_uri
                to_get = type_of_uri
                if type_of_uri is not '':
                    to_get += '_'
                to_get += 'uri'
                text = response.json.get(unicode(to_get))
                self.assertTrue(to_search in text)

    def test_get_bad_bbid(self):
        instances = db.session.query(Creator).all()
        if len(instances) > 0:
            creator_gid = str(instances[0].entity_gid)
            # 1
            creator_gid_bad = creator_gid + '1'
            response = self.client.get(('/creator/{}/'.format(creator_gid_bad)))
            self.assert404(response)

            # 2
            creator_gid_bad = change_one_letter(str(creator_gid))
            response = self.client.get(('/creator/{}/'.format(creator_gid_bad)))
            self.assert404(response)

            # 3
            creator_gid_bad = creator_gid[:-1]
            response = self.client.get(('/creator/{}/'.format(creator_gid_bad)))
            self.assert404(response)

    def test_get_bbid_aliases(self):
        instances = db.session.query(Creator).all()
        random.shuffle(instances)

        for instance in instances:
            creator_gid = unicode(instance.entity_gid)
            aliases_response = self.client.get('/creator/{}/aliases'.format(creator_gid))
            self.assert200(aliases_response)

            aliases = instance.master_revision.entity_data.aliases
            aliases.sort(key=lambda x: x.alias_id)

            self.assertEquals(aliases_response.json.get(u'count'), len(aliases))

            aliases_ws_objects_raw = aliases_response.json.get(u'objects')
            aliases_ws_objects = []

            for alias_object in aliases_ws_objects_raw:
                aliases_ws_objects.append(MyAlias(
                    alias_object.get(u'sort_name'),
                    alias_object.get(u'alias_id'),
                    alias_object.get(u'primary'),
                    alias_object.get(u'language'),
                    alias_object.get(u'name'),
                ))
            aliases_ws_objects.sort(key=lambda x: x.alias_id)
            for i in range(len(aliases_ws_objects)):
                aliases_ws_objects[i].test_equality_to_alias(aliases[i], self)

    def test_get_bbid_relationships(self):
        instances = db.session.query(Creator).all()
        if len(instances) == 0:
            return
        random.shuffle(instances)
        for instance in instances:
            creator_gid = unicode(instance.entity_gid)
            relationships_response = self.client.get('/entity/{}/relationships/'.format(creator_gid))
            self.assert200(relationships_response)
            relationships_db = db.session.query(Relationship). \
                join(RelationshipRevision, Relationship.master_revision). \
                join(RelationshipData). \
                join(RelationshipEntity). \
                filter(RelationshipEntity.entity_gid == creator_gid). \
                all()
            relationships_db.sort(key=lambda x: x.relationship_id)
            for relationship in relationships_db:
                relationship.master_revision.relationship_data.entities.sort(key=lambda x: x.position)
            self.assertEquals(relationships_response.json.get(u'count'), len(relationships_db))
            self.assertEquals(len(relationships_response.json.get(u'objects')),
                              relationships_response.json.get(u'count'))
            relationships_ws = []
            for i in range(len(relationships_db)):
                relationship_ws = relationships_response.json.get(u'objects', [])[i]
                relationships_ws.append(MyRelationship(
                    relationship_ws.get(u'master_revision_id'),
                    relationship_ws.get(u'entities', []),
                    relationship_ws.get(u'relationship_id'),
                    relationship_ws.get(u'relationship_type').get(u'description'),
                    relationship_ws.get(u'relationship_type').get(u'relationship_type_id'),
                    relationship_ws.get(u'last_updated')
                ))
            relationships_ws.sort(key=lambda x: x.relationship_id)

            for i in range(len(relationships_db)):
                relationships_ws[i].test_equality_to_relationship(relationships_db[i], self)

    def test_creator_put(self):
        instances = db.session.query(Creator).all()
        instances.sort(key=lambda x: x.entity_gid)
        if len(instances) == 0:
            return
        random_instance = instances[random.randint(0, len(instances) - 1)]
        random_instance_gid = unicode(random_instance.entity_gid)
        # noinspection PyPep8
        response2 = self.client.put('/creator/{}/'.format(random_instance_gid),
                                    headers=Headers([('Authorization', 'Bearer ' + self._access_token),
                                                     ('Content-Type', 'application/json')]),
                                    data="{\"revision\": {\"note\": \"A Test Note\"},"
                                            "\"entity_gid\":\" " + random_instance_gid + "\","
                                            "\"ended\":\"false\","
                                            "\"begin_date\":\"1492-10-12\","
                                            "\"disambiguation\":\"This is some creator, right ?\","
                                            "\"end_date\":\"8888-08-08\","
                                            "\"annotation\":\"Some annotation: PI=3.141592\"}"
#                                            "\"gender\":{gender:{gender_id:2}}}"
                                    )

        self.assert200(response2)
        creator_db = db.session.query(Creator).filter(Creator.entity_gid == random_instance_gid).one()
        self.assertEquals(creator_db.master_revision.entity_data.ended, False)
        self.assertEquals(creator_db.master_revision.entity_data.begin_date.isoformat(), '1492-10-12')
        self.assertEquals(creator_db.master_revision.entity_data.disambiguation.comment,
                          'This is some creator, right ?')
        self.assertEquals(creator_db.master_revision.entity_data.end_date.isoformat(), '8888-08-08')
        self.assertEquals(creator_db.master_revision.entity_data.annotation.content, 'Some annotation: PI=3.141592')
        # Checking if other instances look now as they looked before PUT request
        self.check_changes_without_one_entity(instances, random_instance_gid)

    def test_creator_delete(self):
        instances = db.session.query(Creator).all()
        instances.sort(key=lambda x: x.entity_gid)
        # testing bad bbids
        if len(instances) > 0:
            self.creator_delete_id(instances, unicode(instances[0].entity_gid) + u'1', self._access_token, True)
            self.creator_delete_id(instances, unicode(instances[0].entity_gid)[:-1], self._access_token, True)
            self.creator_delete_id(instances, change_one_letter(str(instances[0].entity_gid)), self._access_token, True)

        # testing good bbids

        if len(instances) > 0:
            for i in range(1):
                random_instance = instances[random.randint(0, len(instances) - 1)]
                random_instance_gid = unicode(random_instance.entity_gid)
                self.creator_delete_id(instances, random_instance_gid, self._access_token)

    def creator_delete_id(self, instances_before_deleting, gid_to_remove, access_token, bad=False):
        response2 = self.client.delete('/creator/{}/'.format(gid_to_remove),
                                       headers=Headers([('Authorization', 'Bearer ' + access_token),
                                                        ('Content-Type', 'application/json')]),
                                       data="{\"revision\": {\"note\": \"A Test Note\"}}")
        # In future, it should be possible to test deletes without revision notes
        if not bad:
            self.assert200(response2)
        else:
            self.assert404(response2)
            return

        request = db.session.query(Creator).filter(Creator.entity_gid == gid_to_remove).all()

        self.assertEquals(len(request), 1)
        self.assertEquals(request[0].master_revision.entity_data, None)
        self.check_changes_without_one_entity(instances_before_deleting, gid_to_remove)

    def check_changes_without_one_entity(self, instances, removed_gid):
        instances_after = db.session.query(Creator).all()
        self.assertEquals(len(instances), len(instances_after))
        instances_after.sort(key=lambda x: x.entity_gid)
        for i in range(len(instances)):
            instance = instances[i]
            instance_after = instances_after[i]
            self.assertEquals(instance.entity_gid, instance_after.entity_gid)
            if str(instance.entity_gid) != str(removed_gid):
                self.equality_test(instance, instance_after)
                self.equality_test(instance.master_revision, instance_after.master_revision)
                self.equality_test(instance.master_revision.entity_data,
                                   instance_after.master_revision.entity_data)
                self.equality_test(instance.master_revision.entity_data.annotation,
                                   instance_after.master_revision.entity_data.annotation)
                self.equality_test(instance.master_revision.entity_data.disambiguation,
                                   instance_after.master_revision.entity_data.disambiguation)
                self.equality_test(instance.master_revision.entity_data.identifiers,
                                   instance_after.master_revision.entity_data.identifiers)
                self.equality_test(instance.master_revision.entity_data.aliases,
                                   instance_after.master_revision.entity_data.aliases)

    def equality_test(self, a, b):
        if a is None and b is None:
            return
        elif (a is not None) and (b is not None):
            self.assertTrue(a.__dict__ == b.__dict__)
        else:
            self.assertTrue(False)


class MyAlias:
    def __init__(self, sort_name, alias_id, primary, language, name):
        self.sort_name = sort_name
        self.alias_id = alias_id,
        self.primary = primary
        self.language = language
        self.name = name

    # is equal to some Alias ?(not MyAlias!)
    def test_equality_to_alias(self, other, test_creator_id_class):
        test_creator_id_class.assertEquals(self.sort_name, other.sort_name)
        test_creator_id_class.assertEquals(self.name, other.name)
        test_creator_id_class.assertEquals(self.alias_id[0], other.alias_id)
        test_creator_id_class.assertEquals(self.primary, other.primary)
        test_creator_id_class.assertEquals(self.language, other.language)


class MyRelationship:
    def __init__(self, master_revision_id, entities, relationship_id,
                 relationship_type_description, relationship_type_id, last_updated):
        self.master_revision_id = master_revision_id
        self.entities = entities
        self.entities.sort(key=lambda x: x.get(u'position'))
        self.relationship_id = relationship_id
        self.relationship_type_description = relationship_type_description
        self.relationship_type_id = relationship_type_id
        self.last_updated = last_updated

    def test_equality_to_relationship(self, other, test_creator_id_class):
        test_creator_id_class.assertEquals(self.master_revision_id, other.master_revision_id)
        test_creator_id_class.assertEquals(self.relationship_id, other.relationship_id)
        test_creator_id_class.assertEquals(self.last_updated, other.last_updated.isoformat())
        test_creator_id_class.assertEquals(self.relationship_type_id,
                                           other.master_revision.relationship_data.relationship_type_id)
        test_creator_id_class.assertEquals(self.relationship_type_description,
                                           other.master_revision.relationship_data.relationship_type.description)
        # Entities checking
        test_creator_id_class.assertEquals(len(self.entities), len(other.master_revision.relationship_data.entities))
        for i in range(len(self.entities)):
            entity_mine = self.entities[i]
            entity_other = other.master_revision.relationship_data.entities[i]
            test_creator_id_class.assertEquals(entity_mine[u'position'], entity_other.position)
            # noinspection PyProtectedMember
            test_creator_id_class.assertEquals(entity_mine[u'entity'][u'_type'], entity_other.entity._type)
            test_creator_id_class.assertEquals(uuid.UUID(entity_mine[u'entity'][u'entity_gid']),
                                               entity_other.entity.entity_gid)


def change_one_letter(uuid_string):
    if len(uuid_string) == 0:
        return uuid_string
    else:
        pos = random.randint(0, len(uuid_string) - 1)
        string_new = uuid_string[:pos] + chr(ord(uuid_string[pos]) + 10) + uuid_string[(pos + 1):]
        return string_new
