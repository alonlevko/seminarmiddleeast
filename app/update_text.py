from cloudant.client import Cloudant
from requests import adapters
from cloudant.query import Query, QueryResult
from cloudant.error import CloudantException
from datetime import datetime
import jsonpickle
from time import sleep
serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
tweet_database_name = "new_tweet_db"
twitter_users_database_name = "new_twitter_users_db"

if __name__ == '__main__':
    client.connect()
    db = client.get(tweet_database_name, remote=True)
    index = 0
    for doc in db:
        tweet = jsonpickle.decode(doc['value'])
        #date = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y').date().isoformat().replace("-", "")
        doc['text'] = None
        doc['tdata'] = tweet.text
        doc.save()
        index += 1
        if index % 5000 is 0:
            print("updated " + str(index) + "documents")
            sleep(1)

    client.disconnect()
