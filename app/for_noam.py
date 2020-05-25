from cloudant.client import Cloudant
from requests import adapters
from cloudant.query import Query, QueryResult
from cloudant.error import CloudantException

serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
tweet_database_name = "new_tweet_db"
twitter_users_database_name = "new_twitter_users_db"

def generate_single_place_selector(user_name, region_name, place_name):
    return {'user_name': {'$eq': user_name}, 'region_name': {'$eq': region_name}, 'place_name': {'$eq': place_name}, '$text': "1234048774768644097"}

def get_from_db_by_params(user_name, region_name, place_name, db_name, object_example, asdocs):
    print("get_from_db_by_params")
    print(user_name + ";" + region_name + ";" + place_name + ";" + db_name)
    try:
        our_list = []
        client.connect()
        db = client.get(db_name, remote=True)
        query_result = QueryResult(Query(db, selector=generate_single_place_selector(user_name, region_name, place_name)))
        index = 0
        if asdocs:
            for doc in query_result:
                our_list.append(doc)
                index = + 1
        else:
            for doc in query_result:
                our_list.append(object_example.build_from_document(doc))
                index =+ 1
    except CloudantException as exc:
        print("CloudantException in get_from_db_by_params")
        print(exc)
        our_list = []
    except Exception as exc:
        print("non CloudantException exception in get_from_db_by_params")
        print(exc)
        our_list = []
    finally:
        client.disconnect()
        print("get_from_db_by_params id: " + str(db_name) + "len: " + str(len(our_list)))
    return our_list


user_name = 'Ori'
locations = [{'region': 'Ayosh', 'place': "Ramallah"}, {'region':'Ayosh', 'place':'Nablus'}]
tweet_list = get_from_db_by_params(user_name, locations[1]['region'], locations[1]['place'], tweet_database_name, None, True)
users_list = get_from_db_by_params(user_name, locations[1]['region'], locations[1]['place'], twitter_users_database_name, None, True)
#print("tweet list :\n" + str(tweet_list[0:20]))
#print("tweet list :\n" + str(users_list[0:20]))
