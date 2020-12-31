# =========================================================================================
#  Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =========================================================================================

from __future__ import absolute_import
import transaction

import sqlalchemy
from sqlalchemy import Column, Integer, Unicode, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.schema import Index

from sqlalchemy.ext.declarative import declarative_base, declared_attr

from sqlalchemy.sql import and_

from sqlalchemy.orm import scoped_session, sessionmaker, relationship, class_mapper, backref

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from zope.sqlalchemy import register

from offlinetools import syslanguage
import six

DBSession = scoped_session(sessionmaker(expire_on_commit=False))
register(DBSession)

import logging
log = logging.getLogger('offlinetools.models')


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__

Base = declarative_base(cls=Base)


class Language(Base):
    LangID = Column(Integer, primary_key=True)
    LanguageName = Column(Unicode(255), unique=True)
    Culture = Column(Unicode(5), unique=True)
    Active = Column(Boolean)
    ActiveRecord = Column(Boolean)


class LangMixIn(object):
    @declared_attr
    def LangID(cls):
        return Column(Integer, ForeignKey('Language.LangID', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)

    @declared_attr
    def language(cls):
        backref = cls.__name__.split('_')[0].lower() + 's'
        return relationship('Language', cascade="all", primaryjoin='%s.LangID == Language.LangID' % cls.__name__, backref=backref)


class View(Base):
    ViewType = Column(Integer, primary_key=True, index=True)
    names = relationship('View_Name', cascade='all', backref='view')
    # fieldgroups = relationship('FieldGroup', cascade='all', backref='view')
    users = relationship('Users', cascade='all', backref='view')


class View_Name(LangMixIn, Base):
    ViewType = Column(Integer, ForeignKey(View.ViewType, onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)
    ViewName = Column(Unicode(255))


class Community(Base):
    CM_ID = Column(Integer, primary_key=True, index=True)
    ParentCommunity = Column(Integer, ForeignKey('Community.CM_ID', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    names = relationship('Community_Name', cascade='all', backref='community')

    children = relationship(
        "Community", backref=backref('parent', remote_side=[CM_ID]))


class Community_Name(LangMixIn, Base):
    CM_ID = Column(Integer, ForeignKey(Community.CM_ID, onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)
    Name = Column(Unicode(255))


class Publication(Base):
    ListID = Column(Unicode(50), primary_key=True, index=True)
    names = relationship('Publication_Name', cascade='all', backref='publication')
    views = relationship('View', secondary='Publication_View', backref='publications')


class Publication_Name(LangMixIn, Base):
    ListID = Column(Unicode(50), ForeignKey(Publication.ListID, onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)
    Name = Column(Unicode(255))


Publication_View = Table('Publication_View', Base.metadata,
    Column('ListID', Unicode(50), ForeignKey(Publication.ListID, onupdate='CASCADE', ondelete='CASCADE'), index=True),
    Column('ViewType', Integer, ForeignKey(View.ViewType, onupdate='CASCADE', ondelete='CASCADE'), index=True)
    )


FieldGroup_Fields = Table('FieldGroup_Fields', Base.metadata,
    Column('FieldID', Integer, ForeignKey('Field.FieldID', onupdate='CASCADE', ondelete='CASCADE'), index=True),
    Column('DisplayFieldGroupID', Integer, ForeignKey('FieldGroup.DisplayFieldGroupID', onupdate='CASCADE', ondelete='CASCADE'), index=True)
    )


class FieldGroup(Base):
    DisplayFieldGroupID = Column(Integer, primary_key=True, index=True)
    DisplayOrder = Column(Integer)
    ViewType = Column(Integer, ForeignKey(View.ViewType, onupdate='CASCADE', ondelete='CASCADE'), index=True)
    names = relationship('FieldGroup_Name', cascade="all", backref='group')
    views = relationship('View', cascade='all', backref='fieldgroup')


class FieldGroup_Name(LangMixIn, Base):
    DisplayFieldGroupID = Column(Integer, ForeignKey('FieldGroup.DisplayFieldGroupID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True)
    Name = Column(Unicode(255))


class Field(Base):
    FieldID = Column(Integer, primary_key=True, index=True)
    FieldName = Column(Unicode(255), unique=True, index=True)
    DisplayOrder = Column(Integer)
    names = relationship("Field_Name", cascade="all", backref="field")

    groups = relationship('FieldGroup', secondary=FieldGroup_Fields, backref='fields')


class Field_Name(LangMixIn, Base):
    FieldID = Column(Integer, ForeignKey('Field.FieldID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True)
    Name = Column(Unicode(255))


Record_Views = Table('Record_Views', Base.metadata,
    Column('NUM', Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE'), index=True),
    Column('ViewType', Integer, ForeignKey(View.ViewType, ondelete='CASCADE', onupdate='CASCADE'), index=True)
    )


Record_Publication = Table('Record_Publication', Base.metadata,
    Column('NUM', Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE'), index=True),
    Column('ListID', Unicode(50), ForeignKey(Publication.ListID, ondelete='CASCADE', onupdate='CASCADE'), index=True)
    )


Record_Community = Table('Record_Community', Base.metadata,
    Column('NUM', Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE'), index=True),
    Column('CM_ID', Integer, ForeignKey(Community.CM_ID, ondelete='CASCADE', onupdate='CASCADE'), index=True)
    )


class Record(LangMixIn, Base):
    __table_args__ = (Index('ix_Record_OrgName_Cache_NUM', 'OrgName_Cache', 'NUM'),)
    NUM = Column(Unicode(8), primary_key=True, index=True)
    LOCATED_IN_CM = Column(Integer, index=True)

    OrgName_Cache = Column(Unicode(1000))
    LOCATED_IN_Cache = Column(Unicode(255))

    views = relationship('View', secondary=Record_Views, backref='records')
    publications = relationship('Publication', secondary=Record_Publication, backref='records')
    communities = relationship('Community', secondary=Record_Community, backref='records')


class Record_Data(Base):
    NUM = Column(Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True)
    LangID = Column(Integer, ForeignKey('Record.LangID', onupdate='CASCADE', ondelete='CASCADE'), primary_key=True, index=True)
    FieldID = Column(Integer, ForeignKey('Field.FieldID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, index=True)

    Value = Column(Unicode)

    record = relationship('Record', primaryjoin=and_(NUM == Record.NUM, LangID == Record.LangID), backref='fields')
    field = relationship('Field', primaryjoin=FieldID == Field.FieldID)


class Users(LangMixIn, Base):
    UserName = Column(Unicode(50), primary_key=True, index=True)
    PasswordHash = Column(Unicode(33))
    PasswordHashSalt = Column(Unicode(33))
    PasswordHashRepeat = Column(Integer)
    ViewType = Column(Integer, ForeignKey(View.ViewType, onupdate='CASCADE', ondelete='CASCADE'), index=True)


class KeywordCache(LangMixIn, Base):
    Value = Column(Unicode(500), primary_key=True)


class ConfigData(Base):
    id = Column(Integer, primary_key=True)
    update_url = Column(Unicode(255))
    machine_name = Column(Unicode(255))
    site_title = Column(Unicode(255))
    public_key = Column(Unicode(1000))
    private_key = Column(Unicode(1000))
    last_update = Column(DateTime)
    last_update_message = Column(Unicode(500))
    update_log = Column(Unicode)  # do we want this to be a separate table?
    update_failure_count = Column(Integer)


def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)


def get_config(request=None, session=None):

    if session:
        pass
    elif not request or not hasattr(request, 'dbsession'):
        session = DBSession()
    else:
        session = request.dbsession

    try:
        cfg = session.query(ConfigData).one()
    except NoResultFound:
        from offlinetools import keymgmt
        priv_key, pub_key = keymgmt.generate_new_keypair()
        cfg = ConfigData(public_key=six.text_type(pub_key), private_key=six.text_type(priv_key))

        session.add(cfg)
        session.flush()
        transaction.commit()

        cfg = session.query(ConfigData).one()

    return cfg


def initialize_languages(session):

    languages = set(x.LangID for x in session.query(Language.LangID).all())
    log.debug('languages: %s', languages)

    for language in syslanguage._culture_list:
        if language.LangID not in languages:
            ln = Language(**language._asdict())
            session.add(ln)

    session.flush()

    languages = session.query(Language).all()
    syslanguage.update_cultures(asdict(l) for l in languages)


def on_connect_set_pragmas(dbapi_connection, connection_record):
    try:
        dbapi_connection.execute('PRAGMA cache_size=50000')
        dbapi_connection.execute('PRAGMA synchronous = OFF')
        dbapi_connection.execute('PRAGMA journal_mode = MEMORY')
    except Exception as e:
        log.exception(e)


def initialize_sql(engine):
    sqlalchemy.event.listen(sqlalchemy.pool.Pool, 'connect', on_connect_set_pragmas)
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    log.debug('About to create SQL Tables *****************************************')
    Base.metadata.create_all(engine)
    session = DBSession()
    connection = session.connection()
    connection.execute('PRAGMA cache_size=50000')
    connection.execute('PRAGMA synchronous = OFF')
    connection.execute('PRAGMA journal_mode = MEMORY')
    try:
        get_config()
    except IntegrityError:
        transaction.abort()
        return

    try:
        initialize_languages(session)
    except IntegrityError:
        transaction.abort()
        return

    transaction.commit()
