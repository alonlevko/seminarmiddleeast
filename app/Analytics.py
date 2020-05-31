import pandas as pd
# import twitter
import json
from cloudant.client import Cloudant
from cloudant.query import Query, QueryResult
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
from nltk.tokenize import TweetTokenizer
from string import punctuation
from requests import adapters
import jsonpickle
from time import sleep
from calendar import month_name
from ast import literal_eval as str2dict
from warnings import warn

SQLITE = True

if not SQLITE:
    import pyspark
    from pyspark import SparkContext
    from pyspark.sql import Row
    from pyspark.sql import SQLContext
    from pyspark.sql.functions import col
    from pyspark.sql.functions import to_date

    sc = SparkContext()
    sqlContext = SQLContext(sc)

if SQLITE:
    import sqlite3 as lite
    from sqlalchemy import create_engine

# pandas set up
pd.set_option('display.max_colwidth', -1)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)

# stop words that can not be added via file:
STOP_WORDS = ["", " ", "  ", "   "]

# ibmcloud service credentials
serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
# need this for managing connection and stuff
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
# create client object
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
# db names needed to connect to already created databases
user_database_name = "new_twitter_users_db"
tweet_database_name = "new_tweet_db"
new_tweet_database_name = "new_tweet_db"
twitter_users_database_name = "twitter_users_db"


def removekey(d, key):
    '''remove an element from a dict by his key'''
    return d
    r = dict(d)
    del r[key]
    return r


class TableLoader():
    """
    A class used to create the tables and register them to the sql engine
    """
    type2func = {'int': int, 'str': lambda x: x}
    cureent_tables = {"tweets": pd.DataFrame()}

    def load_stop_words(self):
        """
        load the stop wards from their file
        :return: pd.DataFrame of the stop words
        """
        stop_words = STOP_WORDS
        with open("resources/stop words", encoding='utf-8') as file:
            line = file.readline().strip()
            while line:
                stop_words.append(line)
                line = file.readline().strip()
            file.close()
        return pd.DataFrame(stop_words, columns=['words'], dtype=str)

        # self.registerTable("stop_words", pd.DataFrame(stop_words))
        # R = Row('words')
        # sqlContext.createDataFrame([R(x) for x in stop_words]).registerTempTable("stop_words")

    def load_default_columns(self):
        """
        load the default values for the columns
        :return: a dict of a column to his default value
        """
        defult_coulmns = {}
        with open("resources/defult columns.txt") as file:
            line = file.readline().strip()
            while line:
                parts = line.split()
                defult_coulmns[parts[0]] = self.type2func[parts[2]](parts[1])
                line = file.readline().strip()
            file.close()
        return defult_coulmns

    def __init__(self):
        self.stop_words = self.load_stop_words()
        self.defult_coulmns = self.load_default_columns()

    def registerTable(self, name, table, conn=None):
        """
        register a table to the sql engine so it could be later used in sql quire
        :param name: name of the table
        :param table: pd.DataFrame of the table
        :param conn: the sql engine
        :return: None
        """
        if SQLITE:
            table.to_sql(name, conn)
        else:
            sqlContext.createDataFrame(table).registerTempTable(name)

    def registerStopwords(self, conn):
        """
        register the stop words table to the engine
        :param conn: the sql engine
        :return: None
        """
        self.registerTable('stop_words', self.stop_words, conn)

    def add_table_from_json(self, objects, conn=None):
        """
        use the objects created from the jsons in the value column to create tables and register them.
        the table that are created are:
        - tweets
        - users
        - words
        - dates
        :param objects: objectes (dics) decoded from josons strings in the value column in the tweets db
        :param conn: the sql engine
        :return: None
        """

        def get_user_table(dics):
            out = []
            for dic in dics:
                out.append(dic['user'])
            df = pd.DataFrame(out)
            df = df.drop(['_json'], axis=1)
            return df.astype(str)

        def get_tweets_table(dics):
            df = pd.DataFrame.from_dict(dics)
            if '_json' in df.columns:
                df = df.drop(['_json'], axis=1)
            return df.astype(str)

        def get_places_table(dics):
            dics = [{**d["place"], "id": d["id"]} for d in dics if d["place"] is not None]
            df = pd.DataFrame.from_dict(dics)
            df = df.drop(['attributes', 'bounding_box'], axis=1)
            return sqlContext.createDataFrame(df.astype(str))

        df_tweets = get_tweets_table(objects)
        df_users = get_user_table(objects)
        df_tweets[['user_id']] = df_users[['id_str']]
        self.registerTable("tweets", df_tweets, conn)  # tweets table
        self.registerTable("users", df_users, conn)  # users table

        # words table

        if SQLITE:
            # df = df_tweets
            ser = pd.Series(df_tweets["text"]).str.split(" ")
            df_words = pd.concat([ser.to_frame(), df_tweets['id']], axis=1)
            df_words = df_words.explode('text')
            df_words = df_words.rename(columns={"text": "word"})
            # self.registerTable('words', df_words,conn)

        else:
            tweet_tokenizer = TweetTokenizer()

            def split_tweets(s):
                def check_punctuation(word):
                    if word == "":
                        return False
                    for char in word:
                        if char not in punctuation:
                            return True
                    return False

                if len(s) == 1:
                    s = s[0]
                s = [s[0], s[1].lower().split(" ")]
                return [[word, s[0]] for word in s[1] if check_punctuation(word)]

            df_words = sqlContext.createDataFrame(sqlContext.table("tweets")[["id", "text"]]
                                                  .rdd.map(list)
                                                  .flatMap(split_tweets)
                                                  ).select(col("_2").alias("id"), col("_1").alias("word")).toPandas()

        self.registerTable('words', df_words, conn)

        # dates table
        def change_date_format(date, sep="-", out='date'):
            if date == "":
                return 'null'
            mon2num = {mon[:3]: str(i) for i, mon in enumerate(month_name)}
            date = date.split(" ")
            month = mon2num[date[1]]
            day = date[2]
            hour = date[3].replace(":", "")
            year = date[5]
            if len(month) == 1:
                month = "0" + month
            num_value = year + month + day
            str_value = year + sep + day + sep + month
            if out == 'hour':
                return hour
            elif out == 'full_date':
                return num_value + hour
            elif out == 'date':
                return num_value
            warn(
                "the \"out\" argument didn't match any if the option [\'date\',\'full_date\',\'hour\']. by default used the "
                + "\'date\' option")
            return num_value

        def change_date(id_date, sep="-"):
            if len(id_date) == 1:
                return [id_date[0], "null"]
            if len(id_date) == 3:
                id_date = id_date[:3]
            if len(id_date) == 4:
                id_date = id_date[:3]
            date = str(id_date[1])
            num_value = change_date_format(date, sep=sep, out='date')
            hour = change_date_format(date, sep=sep, out='hour')
            if len(id_date) == 4:
                return [id_date[0], num_value, hour]
            if len(id_date) == 3:
                return [id_date[0], num_value, hour, num_value + hour]
            return [id_date[0], 'null']

        if SQLITE:
            df_dates = df_tweets[['id', 'created_at']].rename(columns={'created_at': 'full_date'})
            df_dates['hour'] = df_dates['full_date'].apply(lambda date: change_date_format(date, out='hour'))
            df_dates['date'] = df_dates['full_date'].apply(lambda date: change_date_format(date, out='date'))
            df_dates['full_date'] = df_dates['full_date'].apply(lambda date: change_date_format(date, out='full_date'))

        else:
            df_dates = sqlContext.createDataFrame(sqlContext.table("tweets").select(
                col("id"), col("created_at"), col("source"), col("source"))
                                                  .rdd.map(list).
                                                  map(change_date)) \
                .select(col("_2").alias("date"), col("_1").alias("id"), col("_3").alias("hour"),
                        col("_4").alias("full_date")).toPandas()

        self.registerTable('dates', df_dates, conn)

    def keys2table(self, table_name, keys, where=None, num=20000, max_req=400, json_col="value", conn=None,
                   docs_list=None):
        """
        create the tables needed for keys (columns) from docs objects and register them.
        if needed, takes the docs from the db.

        :param table_name: the db from with the the docs are given and used to name the table
        :param keys: the columns from the db that are needed
        :param where: used as the selector in cloudant.query.Query in case the docs are taken from the db
        :param num: number of docs objects from with to create the tables
        :param max_req: in case the docs are taken from the db, used to takes break to prevent
               from arriving to the cloud limit
        :param json_col: the column in with the json strings are held,
        :param conn: the sql engine
        :param docs_list: a list of docs, if not given, the docs will be taken from the db
        :return: None
        """
        if len(keys) == 0:
            return False
        docs = []
        if len(docs_list) == 0:
            return
        tweet_db = docs_list
        index = 0
        flag = json_col in keys and table_name == tweet_database_name
        tweet_list_json = []
        remove = '_json'
        for doc in tweet_db:  # db object is iterable so we can just iterate
            if flag:
                tweet_list_json.append(doc[json_col])  # get the jason string of the object
            if keys[0] == 'all_columns':
                keys = list(doc.keys())
            if table_name == user_database_name:
                temp = {}
                for k in keys:
                    if k == json_col:
                        continue
                    if k not in doc.keys() and k in self.defult_coulmns.keys():
                        temp[k] = self.defult_coulmns[k]
                    else:
                        temp[k] = doc[k]
                doc = temp
            else:
                doc = {k: doc[k] for k in keys if k != json_col}
            if len(doc) > 0:
                docs.append(doc)
            index += 1
            if index > num != -1:  # get only 400 tweets for the db
                break
            if index % max_req == 0 and docs_list == None:
                sleep(2)
        if docs_list == None:
            client.disconnect()  # disconnect from db
        # check if docs is empty
        if len(docs) == 0 and len(tweet_list_json) == 0:
            return True

        # now we can use the jsons
        if flag:
            tweet_list_object = []
            for tweet in tweet_list_json:
                # convert json to object
                dct = jsonpickle.decode(tweet)
                if type(dct) != dict:
                    dct = dct.__dict__
                    dct["user"] = dct["user"].__dict__
                tweet_list_object.append(removekey(dct, remove))
            # now we can use the objects
            if len(tweet_list_object) > 0:
                self.add_table_from_json(tweet_list_object, conn)
        if len(docs) > 0:
            self.registerTable("servies_" + table_name, pd.DataFrame.from_dict(docs).astype(str), conn)
        return False


class QueriesManager():
    """
    used to manage all the queries and as the an api to use outside
    """

    class Querie():
        """
        represent a single querie
        """

        def __init__(self, name):
            """
            load the querie's parameters from it's file
            :param name: the name of the querie
            """
            self.name = name
            with open("resources/Queries/" + name + ".txt") as file:
                self.str = file.readline().strip()
                self.tweet_cols = [s.strip() for s in file.readline().split(",")]
                self.where_tweets = (file.readline().strip())
                self.users_cols = [s.strip() for s in file.readline().split(",")]
                self.where_users = file.readline().strip()
                self.parms = [s.strip() for s in file.readline().split(",")]
                self.info = file.readline().strip()
                file.close()
            if self.tweet_cols[0] == '':
                self.tweet_cols = []

            if self.users_cols[0] == '':
                self.users_cols = []

            if self.parms[0] == '':
                self.parms = []

        def __str__(self):
            return self.str

        def __call__(self, args):
            """
            insert the querie's arguments to create it, and it's where-dict (witch used in the selector of cloudant.query.Query
            :param args: querie's arguments
            :return: a dict with the querie's string with it's arguments inserted, and its where-dict
            """
            querie = self.str
            where_tweets = self.where_tweets
            where_users = self.where_users
            out = {'q': querie}
            if where_tweets != "":
                out['t'] = where_tweets
            if where_users != "":
                out['u'] = where_users
            if len(args) != len(self.parms):
                raise Exception(
                    "args miss much.\n expected " + str(len(self.parms)) + " args, but got " + str(len(args)))
            for arg, parm in zip(args, self.parms):
                if type(arg) == list:
                    for i in out.keys():
                        out[i] = out[i].replace(parm, ",".join(map(lambda s: "\'" + s + "\'", arg)))
                elif type(arg) == str:
                    arg = "\'" + arg + "\'"
                    for i in out.keys():
                        out[i] = out[i].replace(parm, arg)
            if 't' in out.keys():
                dic = str2dict(out['t'])
                out['t'] = {k: {'$in': dic[k]} for k in dic.keys()}
            else:
                out['t'] = {}
            if 'u' in out.keys():
                dic = str2dict(out['u'])
                out['u'] = {k: {'$in': dic[k]} for k in dic.keys()}
            else:
                out['u'] = {}
            out['n'] = {parm: arg for arg, parm in zip(args, self.parms)}
            return out

    # class Querie() END

    def __init__(self, ):
        """
        load all the queries from the file system
        """
        self.queries = {}
        self.tables = TableLoader()
        with open("resources/queries_names.txt") as file:
            q_name = file.readline()
            while q_name:
                self.add_querie(q_name.strip())
                q_name = file.readline()

    def set_sqlite(self, bool):
        """
        set if use sqlite or spark
        :param bool: if True sets to use sqlite, if False sets to use spark
        :return: None
        """
        global SQLITE
        SQLITE = bool

    def sql(self, querie, conn=None):
        """
        run the querie on the tables
        :param params_sql_123:  a dummy
        :param querie: the querie to run
        :param conn: the sql engine
        :return: pd.DataFrame of the result from the querie
        """
        if SQLITE:
            return pd.read_sql_query(querie, conn)
        else:
            return sqlContext.sql(querie).toPandas()

    def connect_sql(self):
        """
        connect to the sql engine
        :return: the sql engine
        """
        if SQLITE:
            return create_engine('sqlite:///:memory:')
        else:
            return sqlContext

    def close_conncetion(self, conn):
        """
        close the connection to the sql
        :param conn: the connection to the sql
        :return: None
        """
        if SQLITE:
            conn.dispose()

    """
    The following functions are used to convert tables to different format 
    """

    def to_html(df):
        if type(df) == str:
            return sqlContext.table(df).toPandas().to_html()
        if type(df) == pd.DataFrame:
            return df.to_html()
        return df.toPandas().to_html()

    def to_json(df):
        if type(df) == str:
            return sqlContext.table(df).toPandas().to_json()
        if type(df) == pd.DataFrame:
            return df.to_json()
        return df.toPandas().to_json()

    def test(self, conn):
        """
        used for debug. get a list of the tables in the sql engine
        :param conn: the sql engine
        :return: list of tables' names
        """
        from sqlalchemy import inspect
        inspector = inspect(conn)
        return list(inspector.get_table_names())

    def call_querie(self, args, tweets=None, users=None, num=-1, max_req=400, test=False, html=False, json=False,
                    test_print_all=False):
        """
        used to run the a querie on the tables from outside. take args as the name of the querie, following with
        it's parameters

        :param args: a list, the first item is the name of the querie, followed by it's parameters. each parameter
               can be a single string or a list of strings. if its the second, the parameter will all of them with
               logic of "or" between them
        :param tweets: a list of docs for the tweets db
        :param users: a list of docs for the users db
        :param num: passed as the num value for TableLoader.keys2table
        :param max_req: passed as the max_req value for TableLoader.keys2table
        :param test: if True, will print the result of the querie to the consols, used for running tests and debug
        :param html: if True, the return value will be in html format
        :param json: if True, the return value will be in json format
        :param test_print_all: if True and test is True, will print all the results (otherwise only print the first 20 rows)
        :return: by defualt return pd.DataFrame of the result, if html is True return in html format, if json is True
                 return in json format, and if both True return a tuple of (html_format, json_format)
        """
        querie = self.queries[args[0]]
        out_dict = querie(args[1:])
        querie_str, where_tweets, where_users = out_dict['q'], out_dict['t'], out_dict['u']
        # create connection to local db
        conn = self.connect_sql()
        # load stop words
        self.tables.registerStopwords(conn)
        # load from tweets db
        self.tables.keys2table(tweet_database_name, querie.tweet_cols, where_tweets, num, max_req,
                               conn=conn, docs_list=tweets)
        # load from users db
        self.tables.keys2table(user_database_name, querie.users_cols, where_users, num, max_req,
                               conn=conn, docs_list=users)

        df = self.sql(querie_str, conn)
        self.close_conncetion(conn)

        if test:
            if test_print_all:
                print(df.to_string())
            else:
                print(df.head(20))
        if html and json:
            return QueriesManager.to_html(df), QueriesManager.to_json(df)
        elif html:
            return QueriesManager.to_html(df)
        elif json:
            return QueriesManager.to_json(df)
        return df

    def summery(self, dict=False, pandas=False):
        summeries = [{
            "name": name,  # querie's name
            "params": self.queries[name].parms,  # querie's params
            "info": self.queries[name].info,  # querie's info
            "querie": str(self.queries[name])  # the querie itself
        } for name in self.queries.keys()]
        if dict and pandas:
            return summeries, pandas.DataFrame.from_dict(summeries)
        elif pandas:
            return pandas.DataFrame.from_dict(summeries)
        elif dict:
            return summeries
        return pd.DataFrame.from_dict(summeries).to_string()

    def add_querie(self, querire):
        if type(querire) == str:
            querire = QueriesManager.Querie(querire)
        self.queries[querire.name] = querire

    def add_from_list(self, querires):
        for q in querires:
            self.add_querie(q)

    def __setitem__(self, key, value):
        self.queries[key] = value

    def __getitem__(self, args, test=False, html=True):
        return self.call_querie(args, test, html)


if __name__ == '__main__':
    from for_noam import tweet_list, users_list

    params_list = [['First_Time', ['a']],
                   ['Most_Retweeted', ['a']],
                   ['Phrase_trend', ['a']],
                   ['Word_trend', ['a']],
                   ['Popular_word_per_date'],
                   ['Popular_word_per_place'],
                   ['Popularity_of_word_bank_per_place', ['a']],
                   ['Opinion_Leaders', ['Nablus'], ['0.05'], ['0.9'], ['0.05'], ['0.9']],
                   ['Opinion_Leaders_by_phrase', ['a'], ['Nablus'], ['0.05'], ['0.9'], ['0.05'], ['0.9']]]
    queriesManager = QueriesManager()
    params = ['Test']
    df = queriesManager.call_querie(params, tweet_list, users_list, num=10)
    print(df.to_string())
