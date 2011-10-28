import transaction

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import ForeignKey
from sqlalchemy import relationship

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base, declared_attr

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

Base = declarative_base(cls=Base)

class Languages(Base):
    __tablename__ = 'languages'
    lang_id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), unique=True)
    culture = Column(Unicode(5), unique=True)

class LangMixIn(object):
    @declared_attr
    def lang_id(cls):
        return Column(Integer, ForeignKey('languages.lang_id'), primary_key=True)

    @declared_attr
    def language(cls):
        return relationship('Languages', primaryjoin='%s.lang_id == Languages.lang_id' % cls.__name__)

class Field(Base):
    field_id = Column(Integer, primary_key=True)
    field_name = Column(Unicode(255), unique=True)
    names = relationship("Field_Name", backref="field")

class Field_Name(LangMixIn, Base):
    field_id = Column(Integer, ForeignKey('field.field_id'), primary_key=True)
    name = Column(Unicode(255))
    field = relationship(Field, primaryjoin=field_id== Field.field_id)

class FieldGroup(Base):
    field_group_id = Column(Integer, primary_key=True)
    field_order = Column(Integer)
    names = relationship('FieldGroup_Name', backref='group')

class FieldGroup_Name(LangMixIn, Base):
    field_group_id = Column(Integer, ForeignKey('fieldgroup.field_group_id'), primary_key=True)
    name = Column(Unicode(255))
    group = relationship(Field, primaryjoin= field_group_id == FieldGroup.field_group_id)

class Record(Base):
    num = Column(Unicode(8), primary_key=True)

class Record_Fields(LangMixIn, Base):
    num = Column(Unicode(8), ForeignKey('record.num'), primary_key=True)
    field_id = Column(Integer, ForeignKey('field.field_id'), primary_key=True)

    value = Column(Unicode)


class User(LangMixIn, Base):
    user_name = Column(Unicode(50), primary_key=True)
    pwd_hash_repeat = Column(Integer)
    pwd_hash_salt = Column(Unicode(44))
    pwd_hash = Column(Unicode(44))

def populate():
    session = DBSession()
    model = Record_Fields(name=u'root', value=55)
    session.add(model)
    session.flush()
    transaction.commit()

def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    #try:
    #    populate()
    #except IntegrityError:
    #    transaction.abort()
