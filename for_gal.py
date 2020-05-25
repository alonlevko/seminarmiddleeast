from cloudant.client import Cloudant
from requests import adapters
import jsonpickle
import sqlite3
from sqlite3 import Error

# ibmcloud service credentials
serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
# need this for managing connection and stuff
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
# create client object
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
# db names needed to connect to already created databases
user_database_name = "users_db"
tweet_database_name = "new_tweet_db"
twitter_users_database_name = "new_twitter_users_db"


def get_tweets():
    client.connect()  # connect to db
    tweet_db = client.get(tweet_database_name, remote=True)  # get db as python object from remote db
    index = 0
    tweet_list_json = []
    for doc in tweet_db: # db object is iterable so we can just iterate
        tweet_list_json.append(doc['value']) # get the jason string of the object
        index += 1
        if index > 400: # get only 400 tweets for the db
            break

    client.disconnect() # disconnect from db

    tweet_list_object = []
    for tweet in tweet_list_json:
        tweet_list_object.append(jsonpickle.decode(tweet)) # convert json to object
    return tweet_list_object


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


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def insert_tweet(conn, tweet):
    sql = ''' INSERT INTO tweets(id,tweet_text,created_at,user_name)
              VALUES(?,?,?,?) '''
    cur = conn.cursor()
    tweet = (str(tweet.id), str(tweet.text), str(tweet.created_at), str(tweet.user.screen_name))
    cur.execute(sql, tweet)


def select_all_tweets(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM tweets")

    rows = cur.fetchall()

    for row in rows:
        print(row)


def main():
    tweets = get_tweets()
    connection = create_connection()
    sql_tweet_table = """ CREATE TABLE IF NOT EXISTS tweets (
                                        id integer PRIMARY KEY,
                                        tweet_text text NOT NULL,
                                        created_at text,
                                        user_name text
                                    ); """
    if connection is not None:
        create_table(connection, sql_tweet_table)
        for t in tweets:
            insert_tweet(connection, t)
        select_all_tweets(connection)

    else:
        print("Error! cannot create the database connection.")


if __name__ == '__main__':
    main()
