from app import kmeans
from app import app_logic
import jsonpickle
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey

serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"

client = Cloudant(serviceUsername, servicePassword, url=serviceURL)
user_database_name = "users_db"
tweet_database_name = "tweet_db"
twitter_users_database_name = "twitter_users_db"

client.connect()
tweet_db = client.get(tweet_database_name, remote=True)
tweet_list = []
index = 0
print("for doc in tweet_db:")
for doc in tweet_db:
    index += 1
    #print(doc)
    dec = jsonpickle.decode(str(doc['value']))
    tweet_list.append(dec)
    if index > 10:
        break

texts = app_logic.extract_text_from_tweets(tweet_list)
kmeans.apply_kmeans(5, texts)
client.disconnect()
