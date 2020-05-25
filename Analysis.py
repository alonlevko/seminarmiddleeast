import sqlite3
from sqlite3 import Error
import twitter
import sqlalchemy as db
import threading

def create_connection():
    """ create a database connection to a database that resides
        in the memory
    """
    conn = None
    try:
        conn = sqlite3.connect(':memory:')
        print(sqlite3.version)
    except Error as e:
        print(e)
    return conn


def create_table(conn, table_id):
    sql_tweet_table = " CREATE TABLE IF NOT EXISTS "
    sql_tweet_table += str(table_id)
    sql_tweet_table += " (id integer PRIMARY KEY, tweet_text text NOT NULL, created_at text, user_name text); "
    try:
        c = conn.cursor()
        c.execute(sql_tweet_table)
    except Error as e:
        print(e)


def insert_tweets(conn, tweets, taid):
    sql = "INSERT INTO "
    sql += str(taid)
    sql += "(id,tweet_text,created_at,user_name) VALUES(?,?,?,?) "
    cur = conn.cursor()
    for tweet in tweets:
        cur.execute(sql, (str(tweet.tweet.id), str(tweet.tweet.text), str(tweet.tweet.created_at),
                          str(tweet.tweet.user.screen_name)))


def select_all(conn, table_name):
    cur = conn.cursor()
    sql = "SELECT * FROM " + table_name
    cur.execute(sql)

    rows = cur.fetchall()
    return rows


class IdGiver:
    def __init__(self):
        self.id_list_lock = threading.Lock()
        self.id_list = []

    def get_uniqe_id(self):
        with self.id_list_lock:
            length = len(self.id_list)
            if length == 0:
                self.id_list.append(1)
                return 1
            else:
                nid = self.id_list[length - 1] + 1
                self.id_list.append(nid)
                return nid

    def remove_uniqe_id(self, nid):
        with self.id_list_lock:
            self.id_list.remove(nid)


id_giver = IdGiver()


def generate_tweet_table(tweets):
    this_id = id_giver.get_uniqe_id()
    """
    conn = create_connection()
    table_name = "tweets"
    create_table(conn, table_name)
    insert_tweets(conn, tweets, table_name)
    #result = select_all(conn, table_name)
    #return result
    """
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    from sqlalchemy import Column, Integer, String
    class Message(Base):
        __tablename__ = 'messages'

        id = Column(Integer, primary_key=True)
        message = Column(String)
    Base.metadata.create_all(engine)
    message = Message(message="Hello World!")
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    session.add(message)
    session.commit()
    query = session.query(Message)
    instance = query.first()
    print(instance.message)  # Hello World!