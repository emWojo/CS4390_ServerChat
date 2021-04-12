from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

from db_define import *

engine = create_engine('sqlite:///DBs/msg.sqlite', echo=False)
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()

session.query(msgs).delete()
session.query(chat_sess).delete()
session.query(db_usrs).delete()
session.commit()

