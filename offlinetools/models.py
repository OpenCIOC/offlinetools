import transaction

from sqlalchemy import Column, Integer, Unicode, DateTime, Boolean, ForeignKey, Table

from sqlalchemy.ext.declarative import declarative_base, declared_attr

from sqlalchemy.sql import and_

from sqlalchemy.orm import scoped_session, sessionmaker, relationship, class_mapper

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from zope.sqlalchemy import ZopeTransactionExtension

from offlinetools import syslanguage

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

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
        return Column(Integer, ForeignKey('Language.LangID'), primary_key=True)

    @declared_attr
    def language(cls):
        backref = cls.__name__.split('_')[0].lower() + 's'
        return relationship('Language', cascade="all", primaryjoin='%s.LangID == Language.LangID' % cls.__name__, backref=backref)

class View(Base):
    ViewType = Column(Integer, primary_key=True)
    names = relationship('View_Name', cascade='all', backref='view')
    #fieldgroups = relationship('FieldGroup', cascade='all', backref='view')
    users = relationship('Users', cascade='all', backref='view')

class View_Name(LangMixIn, Base):
    ViewType = Column(Integer, ForeignKey(View.ViewType), primary_key=True)
    ViewName = Column(Unicode(255))


FieldGroup_Fields = Table('FieldGroup_Fields', Base.metadata,
    Column('FieldID', Integer, ForeignKey('Field.FieldID', onupdate='CASCADE', ondelete='CASCADE')),
    Column('DisplayFieldGroupID', Integer, ForeignKey('FieldGroup.DisplayFieldGroupID', onupdate='CASCADE', ondelete='CASCADE'))
)

class FieldGroup(Base):
    DisplayFieldGroupID = Column(Integer, primary_key=True)
    DisplayOrder = Column(Integer)
    ViewType = Column(Integer, ForeignKey(View.ViewType))
    names = relationship('FieldGroup_Name', cascade="all", backref='group')
    views = relationship('View', cascade='all', backref='fieldgroup')

class FieldGroup_Name(LangMixIn, Base):
    DisplayFieldGroupID = Column(Integer, ForeignKey('FieldGroup.DisplayFieldGroupID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name = Column(Unicode(255))

class Field(Base):
    FieldID = Column(Integer, primary_key=True)
    FieldName = Column(Unicode(255), unique=True)
    DisplayOrder = Column(Integer)
    names = relationship("Field_Name", cascade="all", backref="field")

    groups = relationship('FieldGroup', secondary=FieldGroup_Fields, backref='fields')

class Field_Name(LangMixIn, Base):
    FieldID = Column(Integer, ForeignKey('Field.FieldID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    Name = Column(Unicode(255))

Record_Views = Table('Record_Views', Base.metadata,
    Column('NUM', Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE')),
    Column('ViewType', Integer, ForeignKey(View.ViewType, ondelete='CASCADE', onupdate='CASCADE'))
)
    
class Record(LangMixIn,Base):
    NUM = Column(Unicode(8), primary_key=True)
    views = relationship('View', secondary=Record_Views, backref='records')


class Record_Data(Base):
    NUM = Column(Unicode(8), ForeignKey('Record.NUM', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    LangID = Column(Integer, ForeignKey('Record.LangID'), primary_key=True)
    FieldID = Column(Integer, ForeignKey('Field.FieldID', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    Value = Column(Unicode)

    record = relationship('Record', primaryjoin=and_(NUM==Record.NUM, LangID==Record.LangID), backref='fields')




class Users(LangMixIn, Base):
    UserName = Column(Unicode(50), primary_key=True)
    PasswordHash = Column(Unicode(33))
    PasswordHashSalt = Column(Unicode(33))
    PasswordHashRepeat = Column(Integer)
    ViewType = Column(Integer, ForeignKey(View.ViewType))


class ConfigData(Base):
    id = Column(Integer, primary_key=True)
    update_url = Column(Unicode(255))
    machine_name = Column(Unicode(255))
    site_title = Column(Unicode(255))
    public_key = Column(Unicode(1000))
    private_key = Column(Unicode(1000))
    last_update = Column(DateTime)
    last_update_message = Column(Unicode(500))
    update_log = Column(Unicode) #do we want this to be a separate table?
    update_failure_count = Column(Integer)


def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)

def get_config(request = None, session=None):

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
        cfg = ConfigData(public_key=unicode(pub_key), private_key=unicode(priv_key))

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
        


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    session=DBSession()
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
