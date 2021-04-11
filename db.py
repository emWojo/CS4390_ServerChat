# DB creation
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey

#Connet to db, will create db if no exist
engine = create_engine('sqlite:///DBs/msg.sqlite', echo=True)
connection = engine.connect()

#Define Table objects
metadata = MetaData()
db_usrs = Table(
   'db_usrs', metadata, 
   Column('usr_id', Integer, primary_key = True), 
   Column('name', String), 
   Column('pwd', String), 
)
chat_sess = Table(
   'chat_sess', metadata, 
   Column('sess_id', Integer, primary_key = True), 
   Column('usr_id1', Integer, ForeignKey('db_usrs.usr_id')), 
   Column('usr_id2', Integer, ForeignKey('db_usrs.usr_id')), 
)
msgs = Table(
   'msgs', metadata, 
   Column('sess_id', Integer, ForeignKey('chat_sess.sess_id'), primary_key = True), 
   Column('time', DateTime, primary_key = True), 
   Column('sender_id', Integer, ForeignKey('db_usrs.usr_id')), 
   Column('msg_body', String), 
)

#Create all Table Objects
metadata.create_all(engine)
print(metadata.tables.keys())

########################################
# EXAMPLE INSERTS
########################################
#Insert
"""
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select
Session = sessionmaker(bind=engine)
session = Session()
db_usrs_t = db_usrs()
chat_sess_tclear = chat_sess()
msgs_t = msgs()

stmt = (
    insert(db_usrs.__tablename__).
    values(usr_id = 1, name = "John", pwd = 'password')
)
session.execute(stmt)
"""

#Could make table objects instead with declarative base
"""
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
class db_usrs(Base):
   __tablename__ = 'db_usrs'
   usr_id = Column(Integer, primary_key = True)
   name = Column(String)
   pwd = Column(String)
class chat_sess(Base):
   __tablename__ = 'chat_sess' 
   sess_id = Column(Integer, primary_key = True)
   usr_id1 = Column(Integer, ForeignKey('db_usrs.usr_id')) 
   usr_id2 = Column(Integer, ForeignKey('db_usrs.usr_id'))

temp = db_usrs(usr_id = 2, name = "Amy", pwd = 'pass')
session.add(temp)
session.add_all([
    chat_sess(sess_id = 1, usr_id1 = 1, usr_id2 = 2),
    chat_sess(sess_id = 2, usr_id1 = 2, usr_id2 = 1),
    db_usrs(usr_id = 3, name = "Arie", pwd = 'passw'),
    chat_sess(sess_id = 3, usr_id1 = 2, usr_id2 = 3)
])

result = session.query(db_usrs).all()
for row in result:
    print(row.usr_id, row.name, row.pwd)

result = session.query(chat_sess).filter(((chat_sess.usr_id1 == 1) & (chat_sess.usr_id2 == 2)) | ((chat_sess.usr_id1 == 2) & (chat_sess.usr_id2 == 1)))
for row in result:
    print(row.sess_id, row.usr_id1, row.usr_id2)

# insert more stuff
session.commit()
"""