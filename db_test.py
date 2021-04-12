from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

from db_define import *

engine = create_engine('sqlite:///DBs/msg.sqlite', echo=False)
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()
"""
msgEntry = msgs(sess_id=1, time=datetime.now(), sender_id=111, msg_body="Hi" )
session.add(msgEntry)

temp = db_usrs(usr_id = 2, name = "Amy", pwd = 'pass')
session.add(temp)
session.add_all([
    chat_sess(sess_id = 1, usr_id1 = 1, usr_id2 = 2),
    chat_sess(sess_id = 2, usr_id1 = 2, usr_id2 = 1),
    db_usrs(usr_id = 3, name = "Arie", pwd = 'passw'),
    chat_sess(sess_id = 3, usr_id1 = 2, usr_id2 = 3)
])

msgEntry = msgs(sess_id=1, time=datetime.now(), sender_id=111, msg_body="Hi 2" )
session.add(msgEntry)
result = session.query(msgs).all()
"""
"""
result = session.query(db_usrs).all()
"""
result = session.query(chat_sess).all()
for row in result:
    #print(row.sess_id, row.time, row.sender_id, row.msg_body)
    print(row.sess_id, row.usr_id1, row.usr_id1)

listExistingSessionIDs = [r for r, in session.query(chat_sess.sess_id)]
print(listExistingSessionIDs)