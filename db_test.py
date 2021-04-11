from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert, select
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from db_define import *

engine = create_engine('sqlite:///DBs/msg.sqlite', echo=False)
connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()

#temp = db_usrs(usr_id = 2, name = "Amy", pwd = 'pass')
#session.add(temp)

result = session.query(db_usrs).filter(db_usrs.usr_id == 2).all()

"""
result = session.query(db_usrs).all()
"""

for row in result:
    print(row.usr_id, row.name, row.pwd)
session.commit()
