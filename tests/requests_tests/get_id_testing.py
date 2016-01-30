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

from bbschema import Relationship, RelationshipEntity, RelationshipRevision, \
    RelationshipData
from flask_testing import TestCase

from ..check_helper_functions import *
from ..constants import *


class GetIDTests(TestCase):
    """Class that gathers tests for get/:id requests

    See class_diagram.png to see how it is related to other classes.
    """
    def get_specific_name(self, key):
        raise NotImplementedError

    def bbid_one_get_tests_specific_check(self, instance, response):
        raise NotImplementedError

    def get_request_default_headers(self):
        raise NotImplementedError

    def bbid_get_tests(self):
        logging.info(
            'GET/:id request tests for {} good tests:{} bad tests:{}'
            .format(
                self.get_specific_name('type_name'),
                GET_BBID_TESTS_GOOD_COUNT,
                GET_BBID_TESTS_BAD_COUNT
            )
        )

        instances = \
            db.session.query(self.get_specific_name('entity_class')).all()

        random.shuffle(instances)

        for i in range(GET_BBID_TESTS_GOOD_COUNT):
            logging.info(' Good test #{}'.format(i + 1))
            self.good_bbid_general_get_tests(instances)

        for i in range(GET_BBID_TESTS_BAD_COUNT):
            logging.info(' Bad test #{}'.format(i + 1))
            self.bad_get_id_tests(instances)

    def good_bbid_general_get_tests(self, instances):
        for instance in instances:
            self.bbid_one_get_test(instance, instance.entity_gid,
                                   correct_result=True)

    # noinspection PyTypeChecker
    def bad_get_id_tests(self, instances):
        random_instance = random.choice(instances)
        entity_gid = str(random_instance.entity_gid)

        gid_bad = entity_gid + '1'
        self.bbid_one_get_test(None, gid_bad, correct_result=False)

        # gid_bad = change_one_character(str(entity_gid))
        # self.bbid_one_get_test(None, gid_bad, correct_result=False)
        # see ws_bugs.md

        gid_bad = entity_gid[:-1]
        self.bbid_one_get_test(None, gid_bad, correct_result=False)

        gid_bad = uuid.uuid4()
        self.bbid_one_get_test(None, gid_bad, correct_result=False)

    def bbid_one_get_test(self, instance, entity_gid, correct_result=True):
        response = self.client.get(
            '/{}/{}/'.format(self.get_specific_name('ws_name'), entity_gid)
        )

        if correct_result:
            self.assert200(response)
        else:
            self.assert404(response)
            return

        self.bbid_one_get_test_basic_check(instance, response)
        self.bbid_one_get_tests_specific_check(instance, response)

    def bbid_one_get_test_basic_check(self, instance, response):
        json_data = response.json
        self.assertEquals(
            json_data.get('_type'),
            self.get_specific_name('type_name')
        )

        self.assertEquals(
            uuid.UUID(json_data.get('entity_gid')),
            instance.entity_gid
        )

        self.assertEquals(
            json_data.get('last_updated'),
            instance.last_updated.isoformat()
        )

        check_entity_type_json(self, json_data, instance)

        self.bbid_one_check_relationships(instance)
        self.bbid_one_check_aliases(instance)
        self.bbid_one_check_disambiguation(instance)
        self.bbid_one_check_annotation(instance)
        self.bbid_one_check_identifiers(instance)

        self.bbid_one_check_uris(instance, json_data)
        self.bbid_one_check_revision(instance, json_data)
        self.bbid_one_check_default_alias(instance, json_data)

    def bbid_one_check_relationships(self, instance):
        response = self.client.get(
            '/entity/{entity_gid}/relationships/'
            .format(
                entity_gid=instance.entity_gid))
        self.assert200(response)
        self.bbid_one_check_relationships_json(response.json, instance)

    def bbid_one_check_aliases(self, instance):
        response = self.client.get(
            '/{ec}/{entity_gid}/aliases'
            .format(
                ec=self.get_specific_name('ws_name'),
                entity_gid=instance.entity_gid))
        self.assert200(response)
        self.bbid_one_check_aliases_json(response.json, instance)

    def bbid_one_check_disambiguation(self, instance):
        response = self.client.get(
            '/entity/{entity_gid}/disambiguation'
            .format(
                entity_gid=instance.entity_gid))
        self.assert200(response)
        if response.json is not None:
            self.assertEquals(
                response.json['comment'],
                instance.master_revision.entity_data.disambiguation.comment
            )
            self.assertEquals(
                response.json['disambiguation_id'],
                instance.master_revision.entity_data.
                disambiguation.disambiguation_id
            )
        else:
            self.assertIsNone(
                instance.master_revision.entity_data.disambiguation)

    def bbid_one_check_annotation(self, instance):
        response = self.client.get(
            '/entity/{entity_gid}/annotation'
            .format(
                entity_gid=instance.entity_gid
            )
        )
        self.assert200(response)
        if response.json is not None:
            self.assertEquals(
                response.json['content'],
                instance.master_revision.entity_data.annotation.content
            )
            self.assertEquals(
                response.json['annotation_id'],
                instance.master_revision.entity_data.annotation.annotation_id
            )
        else:
            self.assertIsNone(
                instance.master_revision.entity_data.annotation)

    def bbid_one_check_identifiers(self, instance):
        response = self.client.get(
            '/entity/{entity_gid}/identifiers'
            .format(
                entity_gid=instance.entity_gid))
        self.assert200(response)
        self.bbid_one_check_identifiers_json(response.json, instance)

    def bbid_one_check_uris(self, instance, json_data):
        ent_gid = instance.entity_gid
        ent_ws = self.get_specific_name('ws_name')
        uri_base = '/{}/{}/'.format(ent_ws, ent_gid)

        pairs = [
            ['aliases_uri', 'aliases'],
            ['disambiguation_uri', 'disambiguation'],
            ['annotation_uri', 'annotation'],
            ['identifiers_uri', 'identifiers'],
            ['uri', '']
        ]
        for pair in pairs:
            check_uri_suffix(
                self,
                json_data[pair[0]],
                uri_base + pair[1]
            )
        # 'relationships/' should be changed to 'relationships'
        # to look like other entities
        # [see ws_bugs.md]
        check_uri_suffix(
            self,
            json_data['relationships_uri'],
            '/{}/{}/'.format('entity', ent_gid) + 'relationships/'
        )

    def bbid_one_check_relationships_json(self, json_data, instance):
        relationships_db = db.session.query(Relationship). \
            join(RelationshipRevision, Relationship.master_revision). \
            join(RelationshipData). \
            join(RelationshipEntity). \
            filter(RelationshipEntity.entity_gid == instance.entity_gid). \
            all()
        self.assertEquals(json_data['count'], len(relationships_db))
        self.assertEquals(len(json_data['objects']), len(relationships_db))
        ws_objects = json_data['objects']
        ws_objects.sort(key=lambda x: x['relationship_id'])
        relationships_db.sort(key=lambda x: x.relationship_id)
        for i in range(len(ws_objects)):
            self.check_single_relationship_ws_db(
                ws_objects[i], relationships_db[i])

    def check_single_relationship_ws_db(self, ws_object, db_object):
        self.assertEquals(
            ws_object['relationship_id'],
            db_object.relationship_id
        )
        self.bbid_check_relationship_entities(
            ws_object['entities'],
            db_object.master_revision.relationship_data.entities
        )
        self.assertEquals(
            ws_object['last_updated'],
            db_object.last_updated.isoformat()
        )
        self.assertEquals(
            ws_object['master_revision_id'],
            db_object.master_revision_id
        )
        self.assertEquals(
            ws_object['relationship_type']['relationship_type_id'],
            db_object.master_revision.relationship_data.relationship_type_id
        )
        self.bbid_check_relationship_texts(
            ws_object['texts'],
            db_object.master_revision.relationship_data.texts
        )

    def bbid_check_relationship_entities(self, ws_entities, db_entities):
        self.assertEquals(len(ws_entities), len(db_entities))
        ws_entities.sort(key=lambda x: x['position'])
        db_entities.sort(key=lambda x: x.position)
        for i in range(len(ws_entities)):
            ws_entity = ws_entities[i]
            db_entity = db_entities[i]
            self.bbid_check_single_relationship_entity(ws_entity, db_entity)

    def bbid_check_single_relationship_entity(self, ws_entity, db_entity):
        if ws_entity is None:
            self.assertIsNone(db_entity)
        else:
            if db_entity.entity is not None:
                self.assertEquals(
                    ws_entity['entity']['_type'],
                    db_entity.entity._type
                )
                self.assertEquals(
                    ws_entity['entity']['entity_gid'],
                    unicode(db_entity.entity_gid)
                )
                check_uri_suffix(
                    self,
                    ws_entity['entity']['uri'],
                    '/{}/{}/'.format(
                        ws_entity['entity']['_type'].lower(),
                        ws_entity['entity']['entity_gid']
                    )
                )
            else:
                self.assertIsNone(ws_entity['entity'])

            self.assertEquals(
                ws_entity['position'],
                db_entity.position
            )

    def bbid_check_relationship_texts(self, json_texts, texts):
        self.assertEquals(len(json_texts), len(texts))
        json_texts.sort(key=lambda x: x['position'])
        texts.sort(key=lambda x: x.position)
        for i in range(len(json_texts)):
            self.bbid_check_single_relationship_text(
                json_texts[i], texts[i]
            )

    def bbid_check_single_relationship_text(self, json_text, text):
        if json_text is None:
            self.assertIsNone(text)
        else:
            self.assertEquals(json_text['text'], text.text)
            self.assertEquals(json_text['position'], text.position)

    def bbid_one_check_aliases_json(self, json_data, instance):
        json_aliases_list = json_data['objects']
        aliases = instance.master_revision.entity_data.aliases

        self.assertEquals(len(aliases), json_data['count'])

        self.bbid_check_aliases_json(
            json_aliases_list,
            aliases
        )

    def bbid_one_check_identifiers_json(self, json_data, instance):
        identifiers = instance.master_revision.entity_data.identifiers
        json_identifiers_list = json_data['objects']

        self.assertEquals(len(identifiers), json_data['count'])
        self.assertEquals(len(identifiers), len(json_identifiers_list))

        json_identifiers_list.sort(key=lambda x: x['identifier_id'])
        identifiers.sort(key=lambda x: x.identifier_id)

        for i in range(len(identifiers)):
            self.bbid_one_check_single_identifier_json(
                json_identifiers_list[i],
                identifiers[i]
            )

    def bbid_one_check_single_identifier_json(self, json_identifier,
                                              identifier):
        self.assertEquals(json_identifier['identifier_id'],
                          identifier.identifier_id)
        self.assertEquals(json_identifier['value'],
                          identifier.value)
        if 'identifier_type' in json_identifier and \
                json_identifier['identifier_type'] is not None:
            identifier_type = identifier.identifier_type
            self.assertEquals(
                json_identifier['identifier_type']['identifier_type_id'],
                identifier_type.identifier_type_id
            )
            self.assertEquals(
                json_identifier['identifier_type']['label'],
                identifier_type.label
            )
        else:
            self.assertIsNone(identifier.identifier_type)

    def bbid_one_check_revision(self, instance, json_data):
        json_revision = json_data['revision']
        inst_revision = instance.master_revision

        self.assertEquals(json_revision['created_at'],
                          inst_revision.created_at.isoformat())

        self.assertEquals(json_revision['entity_data_id'],
                          inst_revision.entity_data_id)

        self.assertEquals(json_revision['entity_uri'],
                          json_data['uri'])

        self.assertEquals(json_revision['note'],
                          inst_revision.note)

        self.assertEquals(json_revision['parent_id'],
                          inst_revision.parent_id)

        self.assertEquals(json_revision['revision_id'],
                          inst_revision.revision_id)

        self.assertEquals(json_revision['user']['user_id'],
                          inst_revision.user.user_id)

    def bbid_one_check_default_alias(self, instance, json_data):
        if 'default alias' in json_data and \
                not json_data['default_alias'] is None:
            json_def = json_data['default_alias']
            bbid_check_single_alias_json(
                self,
                json_def,
                instance.master_revision.entity_data.default_alias
            )

        else:
            self.assertIsNone(
                instance.master_revision.entity_data.default_alias)

    def bbid_check_aliases_json(self, json_aliases, aliases):
        self.assertEquals(len(aliases), len(json_aliases))

        json_aliases.sort(key=lambda x: x['alias_id'])
        aliases.sort(key=lambda x: x.alias_id)

        for i in range(len(aliases)):
            bbid_check_single_alias_json(
                self,
                json_aliases[i],
                aliases[i],
            )
