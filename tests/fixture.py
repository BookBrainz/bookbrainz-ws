# -*- coding: utf8 -*-

from bbschema import (Alias, Creator, CreatorData, CreatorType, Disambiguation,
                      Entity, EntityRevision, Publication, PublicationData,
                      PublicationType, Relationship, RelationshipEntity,
                      RelationshipRevision, RelationshipText, RelationshipData,
                      RelationshipType, User, UserType)


def load_data(db):
    editor_type = UserType(label=u'Editor')
    db.session.add(editor_type)
    db.session.commit()

    editor = User(name=u'Bob', email=u'bob@bobville.org',
                  user_type_id=editor_type.user_type_id)
    db.session.add(editor)

    pub_type = PublicationType(label=u'Book')
    pub_type2 = PublicationType(label=u'Magazine')
    db.session.add_all((pub_type, pub_type2))
    db.session.commit()

    creator_type = CreatorType(label=u'Author')
    db.session.add(creator_type)
    db.session.commit()

    entity1 = Publication()
    entity2 = Publication()
    entity3 = Creator()
    db.session.add_all((entity1, entity2, entity3))
    db.session.commit()

    pub_data1 = PublicationData(
        publication_type_id=pub_type.publication_type_id
    )
    pub_data2 = PublicationData(
        publication_type_id=pub_type.publication_type_id
    )
    creator_data = CreatorData(creator_type_id=creator_type.creator_type_id)
    db.session.add_all([pub_data1, pub_data2, creator_data])

    entity1_alias1 = Alias(name=u'アウト', sort_name=u'アウト')
    entity1_alias2 = Alias(name=u'Out', sort_name=u'Out')
    entity1_alias3 = Alias(name=u'Le quattro casalinghe di Tokyo',
                           sort_name=u'Le quattro casalinghe di Tokyo')
    entity1_alias4 = Alias(name=u'De nachtploeg', sort_name=u'De nachtploeg')
    pub_data1.aliases.extend([entity1_alias1, entity1_alias2, entity1_alias3,
                              entity1_alias4])

    entity2_alias1 = Alias(name=u'桐野 夏生', sort_name=u'桐野 夏生')
    entity2_alias2 = Alias(name=u'Natsuo Kirino', sort_name=u'Kirino, Natsuo')
    pub_data2.aliases.extend([entity2_alias1, entity2_alias2])

    entity3_alias1 = Alias(name=u'Stephen Snyder',
                           sort_name=u'Snyder, Stephen')
    creator_data.aliases.append(entity3_alias1)

    entity1_disambig = Disambiguation(comment=u'book by Natsuo Kirino')
    pub_data1.disambiguation = entity1_disambig

    db.session.commit()

    revision1 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity1.entity_gid,
        entity_data_id=pub_data1.entity_data_id
    )
    revision2 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity2.entity_gid,
        entity_data_id=pub_data2.entity_data_id
    )
    revision3 = EntityRevision(
        user_id=editor.user_id, entity_gid=entity3.entity_gid,
        entity_data_id=creator_data.entity_data_id
    )

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
    db.session.add_all((relationship1, relationship2, relationship3))
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

    db.session.add_all([relationship_data1, relationship_data2,
                        relationship_data3])
    db.session.commit()

    revision4 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship1.relationship_id,
        relationship_data_id=relationship_data1.relationship_data_id
    )

    revision5 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship2.relationship_id,
        relationship_data_id=relationship_data2.relationship_data_id
    )

    revision6 = RelationshipRevision(
        user_id=editor.user_id, relationship_id=relationship3.relationship_id,
        relationship_data_id=relationship_data3.relationship_data_id
    )

    entity1.master_revision = revision1
    entity2.master_revision = revision2
    entity3.master_revision = revision3
    relationship1.master_revision = revision4
    relationship2.master_revision = revision5
    relationship3.master_revision = revision6

    db.session.add_all([revision1, revision2, revision3, revision4, revision5,
                        revision6])
    db.session.commit()
