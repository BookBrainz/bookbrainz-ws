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

from bbschema import (Alias, Creator, CreatorData, CreatorType, Disambiguation,
                      EntityRevision, Publication, PublicationData,
                      PublicationType, Relationship, RelationshipEntity,
                      RelationshipRevision, RelationshipText, RelationshipData,
                      RelationshipType, User, UserType, OAuthClient)


def load_data(db):
    editor_type = UserType(label=u'Editor')
    db.session.add(editor_type)
    db.session.commit()

    editor = User(name=u'Bob', password=u'$2b$12$AJTVpce37LM9Dk93qzRe.eMSw1ivsAmoa037.eS6VXoLAyK9cy0YG',
                  email=u'bob@bobville.org', user_type_id=editor_type.user_type_id)
    db.session.add(editor)
    db.session.commit()
    client = OAuthClient(client_id='9ab9da7e-a7a3-4f86-87c6-bf8b4b8213c7', owner_id=editor.user_id)
    db.session.add(client)
    db.session.commit()

    pub_type = PublicationType(label=u'Book')
    pub_type2 = PublicationType(label=u'Magazine')
    db.session.add_all((pub_type, pub_type2))
    db.session.commit()

    creator_type = CreatorType(label=u'Author')
    db.session.add(creator_type)
    db.session.commit()

    entity1 = Publication()
    entity2 = Creator()
    entity3 = Creator()
    entity4 = Creator()
    entity5 = Publication()
    entity6 = Creator()
    entity7 = Creator()
    db.session.add_all((entity1, entity2, entity3, entity4, entity5, entity6, entity7))
    db.session.commit()

    pub_data1 = PublicationData(
        publication_type_id=pub_type.publication_type_id
    )
    pub_data2 = PublicationData(
        publication_type_id=pub_type.publication_type_id
    )
    creator_data1 = CreatorData(
        creator_type_id=creator_type.creator_type_id
    )
    creator_data2 = CreatorData(creator_type_id=creator_type.creator_type_id)
    creator_data3 = CreatorData(creator_type_id=creator_type.creator_type_id)
    creator_data4 = CreatorData(creator_type_id=creator_type.creator_type_id)
    creator_data5 = CreatorData(creator_type_id=creator_type.creator_type_id)
    db.session.add_all([pub_data1, pub_data2, creator_data1, creator_data2,
                        creator_data3, creator_data4, creator_data5])

    entity1_alias1 = Alias(name=u'アウト', sort_name=u'アウト')
    entity1_alias2 = Alias(name=u'Out', sort_name=u'Out')
    entity1_alias3 = Alias(name=u'Le quattro casalinghe di Tokyo',
                           sort_name=u'Le quattro casalinghe di Tokyo')
    entity1_alias4 = Alias(name=u'De nachtploeg', sort_name=u'De nachtploeg')
    pub_data1.aliases.extend([entity1_alias1, entity1_alias2, entity1_alias3,
                              entity1_alias4])

    # Aliases
    entity2_alias1 = Alias(name=u'桐野 夏生', sort_name=u'桐野 夏生')
    entity2_alias2 = Alias(name=u'Natsuo Kirino', sort_name=u'Kirino, Natsuo')
    creator_data1.aliases.extend([entity2_alias1, entity2_alias2])

    entity3_alias1 = Alias(name=u'Stephen Snyder',
                           sort_name=u'Snyder, Stephen')
    creator_data2.aliases.append(entity3_alias1)

    entity4_alias1 = Alias(name=u'Franz Kafka',
                           sort_name=u'Kafka, Franz')
    entity4_alias2 = Alias(name=u'Франц Кафка',
                           sort_name=u'Кафка,Франц')
    creator_data3.aliases.extend([entity4_alias1, entity4_alias2])

    entity5_alias1 = Alias(name=u'La Métamorphose',
                           sort_name=u'Métamorphose, La')
    entity5_alias2 = Alias(name=u'Die Verwandlung',
                           sort_name=u'Verwandlung, Die')
    entity5_alias3 = Alias(name=u'Przemiana',
                           sort_name=u'Przemiana')
    pub_data2.aliases.extend([entity5_alias1, entity5_alias2, entity5_alias3])

    # Entity 6 has no aliases (and shouldn't have)

    entity7_alias1 = Alias(name=u'Karel Čapek',
                           sort_name=u'Čapek, Karel')
    entity7_alias2 = Alias(name=u'Карел Чапек',
                           sort_name=u'Чапек, Карел')
    creator_data5.aliases.extend([entity7_alias1, entity7_alias2])

    # Disambiguations
    entity1_disambig = Disambiguation(comment=u'book by Natsuo Kirino')
    pub_data1.disambiguation = entity1_disambig

    entity5_disambig = Disambiguation(comment=u'a book called \"The Metamorphosis\" by Franz Kafka')
    pub_data2.disambiguation = entity5_disambig

    entity6_disambig = Disambiguation(comment=u'American author, known for The Grapes of Wrath')
    creator_data4.disambiguation = entity6_disambig

    entity7_disambig = Disambiguation(comment=u'Czech author Karel Čapek, known for the \"War with the Newts\"')
    creator_data5.disambiguation = entity7_disambig

    db.session.commit()

    # Revisions
    revision1 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity1.entity_gid,
        entity_data_id=pub_data1.entity_data_id
    )
    revision2 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity2.entity_gid,
        entity_data_id=creator_data1.entity_data_id
    )
    revision3 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity3.entity_gid,
        entity_data_id=creator_data2.entity_data_id
    )

    revision4 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity4.entity_gid,
        entity_data_id=creator_data3.entity_data_id
    )

    revision5 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity5.entity_gid,
        entity_data_id=pub_data2.entity_data_id
    )

    revision6 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity6.entity_gid,
        entity_data_id=creator_data4.entity_data_id
    )

    revision7 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity7.entity_gid,
        entity_data_id=creator_data5.entity_data_id
    )

    # Relationships
    relationship_type1 = RelationshipType(
        label=u'First Relationship',
        description=u'A relationship which is first.',
        template=u'<%= subjects[0] %> is authored by <%= subjects[1] %>',
    )

    relationship_type2 = RelationshipType(
        label=u'Second Relationship',
        description=u'A relationship which is second.',
        template=u'<%= subjects[0] %> is translated by <%= subjects[1] %>'
    )

    relationship_type3 = RelationshipType(
        label=u'Third Relationship',
        description=u'A relationship which is third.',
        template=u'<%= subjects[0] %> has profession <%= subjects[1] %>'
    )
    db.session.add_all((relationship_type1, relationship_type2,
                        relationship_type3))
    db.session.commit()

    relationship1 = Relationship()
    relationship2 = Relationship()
    relationship3 = Relationship()
    relationship4 = Relationship()
    relationship5 = Relationship()
    db.session.add_all((relationship1, relationship2, relationship3, relationship4, relationship5))
    db.session.commit()

    relationship_data1 = RelationshipData(
        relationship_type_id=relationship_type1.relationship_type_id
    )
    relationship_data1.entities = [
        RelationshipEntity(entity_gid=entity1.entity_gid, position=1),
        RelationshipEntity(entity_gid=entity2.entity_gid, position=2)
    ]
    relationship_data2 = RelationshipData(
        relationship_type_id=relationship_type2.relationship_type_id
    )
    relationship_data2.entities = [
        RelationshipEntity(entity_gid=entity1.entity_gid, position=1),
        RelationshipEntity(entity_gid=entity3.entity_gid, position=2)
    ]
    relationship_data3 = RelationshipData(
        relationship_type_id=relationship_type3.relationship_type_id
    )
    relationship_data3.entities = [
        RelationshipEntity(entity_gid=entity3.entity_gid, position=1),
    ]
    relationship_data3.texts = [
        RelationshipText(text=u'translator', position=2),
    ]

    relationship_data4 = RelationshipData(
        relationship_type_id=relationship_type1.relationship_type_id
    )
    relationship_data4.entities = [
        RelationshipEntity(entity_gid=entity5.entity_gid, position=5),
        RelationshipEntity(entity_gid=entity4.entity_gid, position=4)
    ]

    # in fact Karel Capek was not the author of Die Verwandlung
    relationship_data5 = RelationshipData(
        relationship_type_id=relationship_type1.relationship_type_id
    )
    relationship_data5.entities = [
        RelationshipEntity(entity_gid=entity5.entity_gid, position=5),
        RelationshipEntity(entity_gid=entity7.entity_gid, position=4)
    ]

    db.session.add_all([relationship_data1, relationship_data2,
                        relationship_data3, relationship_data4, relationship_data5])
    db.session.commit()

    revision_r1 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship1.relationship_id,
        relationship_data_id=relationship_data1.relationship_data_id
    )

    revision_r2 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship2.relationship_id,
        relationship_data_id=relationship_data2.relationship_data_id
    )

    revision_r3 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship3.relationship_id,
        relationship_data_id=relationship_data3.relationship_data_id
    )

    revision_r4 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship4.relationship_id,
        relationship_data_id=relationship_data4.relationship_data_id
    )

    revision_r5 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship5.relationship_id,
        relationship_data_id=relationship_data5.relationship_data_id
    )

    entity1.master_revision = revision1
    entity2.master_revision = revision2
    entity3.master_revision = revision3
    entity4.master_revision = revision4
    entity5.master_revision = revision5
    entity6.master_revision = revision6
    entity7.master_revision = revision7
    relationship1.master_revision = revision_r1
    relationship2.master_revision = revision_r2
    relationship3.master_revision = revision_r3
    relationship4.master_revision = revision_r4
    relationship5.master_revision = revision_r5

    db.session.add_all([revision1, revision2, revision3, revision4, revision5, revision6, revision7,
                        revision_r1, revision_r2, revision_r3, revision_r4, revision_r5])
    db.session.commit()
