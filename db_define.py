from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
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
class msgs(Base):
   __tablename__ = 'msgs'
   sess_id = Column(Integer, ForeignKey('chat_sess.sess_id'), primary_key = True)
   time = Column(DateTime, primary_key = True)
   sender_id = Column(Integer, ForeignKey('db_usrs.usr_id'))
   msg_body = Column(String)
                        