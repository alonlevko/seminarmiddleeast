from .classes import User, client, twitter_users_database_name, tweet_database_name, user_database_name, get_api
from cloudant.query import Query, QueryResult
import twitter
import collections
from tweet_parser.tweet import Tweet
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import jsonpickle
from dateutil.parser import parse
from requests import adapters

serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)

user_dictionary = {}

def word_trends_merge_jsons(left, right):
    print(left)
    print(right)


def get_user(name):
    if name not in user_dictionary.keys():  # we need to handle the creation of a new user
        user = User(my_name=name)
        user_dictionary[name] = user
        user.save_me_to_db()
    else:
        myclient = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
        myclient.connect()
        users_db = myclient.get(user_database_name, remote=True)
        #if users_db is not None:
        users_returned = QueryResult(Query(users_db, selector={'_id': {'$eq': name}}))
        if users_returned is not None:
            list = users_returned.all()
            for u in list:
                t1 = u['_id']
                t2 = str(u['value'])
                # print(t2)
                dec = jsonpickle.decode(t2)
                user_dictionary[t1] = dec
        myclient.disconnect()
    return user_dictionary[name]


def handle_region_form(form_region, user):
    if form_region.is_valid():
        str = form_region.cleaned_data['region_name']
        if str != "":
            user.add_region(str)

    return collections.OrderedDict(user.get_regions())


def handle_place_form(place_form, user):
    if place_form.is_valid():
        data = place_form.cleaned_data
        if len(data) == 6:
            user.add_place(data)


def handle_search_form(search_form):
    if search_form.is_valid():
        region = search_form.cleaned_data['from_region']
        place = search_form.cleaned_data['from_place']
    else:
        region = ""
        place = ""
    return region, place


def get_single_tweet_list(place):
    names_dictionary = {}
    tweet_list = []
    id_list = []
    quary = "q=" + place.get_query_string() + "lang%3Aar&count=100&src=typed_query"
    results = api.GetSearch(raw_query=quary)
    for r in results:
        tweet_list.append(r)
        names_dictionary[r.user.id] = r.user
        id_list.append(r.id)
    max_id = min(id_list)
    while len(results) > 0:
        id_list = []
        querry_str = "q=" + place.get_query_string() + "lang%3Aar&count=100&max_id=" + str(
            max_id) + "&src=typed_query"
        results = api.GetSearch(raw_query=querry_str)
        for r in results:
            tweet_list.append(r)
            names_dictionary[r.user.id] = r.user
            id_list.append(r.id)
            max_id = min(id_list)

    return tweet_list, names_dictionary


def init_tweet_accumulation_tweet_list(user, region_name, place_name, word_list=None):
    region = user.get_region(region_name)
    place_list = []
    if place_name == "" or None:
        print("place is none")
        place_list = region.get_places_handle().values()

    else:
        place_list = []
        place_list.append(region.get_place_by_name(place_name))

    qrts = []
    print(place_list)
    for p in place_list:
        print(p)
        p.init_stand_tweet_collection(get_api(), user, region, word_list)
        qrts.append(p.get_query_string())

    return qrts


def generate_tweet_sendaway(t):
    cordinates = "0"
    if isinstance(t, Tweet):
        t = twitter.Status().NewFromJsonDict(t)
    if t.coordinates is not None:
        cordinates = str(t.coordinates['coordinates'])
    place = "none"
    if t.place is not None:
        place = str(t.place['full_name'])
    location = "none"
    if t.user.location is not None:
        location = str(t.user.location)
    list = [str(t.id), str(t.text), str(t.user.screen_name), location, cordinates,
            place, str(t.created_at)]
    return list


def load_from_db():
    print("loading..")
    client.connect()
    users_db = client.get(user_database_name, remote=True)
    if users_db is not None:
        users_returned = Result(users_db.all_docs, include_docs=True)
        if users_returned is not None:
            for u in users_returned:
                t1 = u['id']
                t2 = str(u['doc']['value'])
                dec = jsonpickle.decode(t2)
                user_dictionary[t1] = dec
    client.disconnect()


def generate_user_sendaway(tuser):
    name = "0"
    if tuser.name is not None:
        name = str(tuser.name)
    followers_count = "0"
    if tuser.followers_count is not None:
        followers_count = str(tuser.followers_count)
    location = "none"
    if tuser.location is not None:
        location = str(tuser.location)
    list = [str(tuser.id), str(tuser.description), str(tuser.screen_name), location, name,
            followers_count, str(tuser.created_at)]
    return list


def iterate_over_all_places(func):
    for user in user_dictionary.values():
        regions = user.get_regions()
        for region in regions.values():
            places = region.get_places_handle()
            for p in places.values():
                func(p)


def restart(p):
    p.set_collector(0)


def change(p):
    p.convert_user_as_num_to_string()


def remove_tweets(p):
    p.tweets = []
    p.max_id = 0
    date = 'Fri May 10 00:44:04 +0000 2019'
    p.last_tweet_date = parse(date)
    p.users = []


def update_last_date(p):
    if not hasattr(p, 'last_tweet_date'):
        p.config_last_tweet_date()
    p.calculate_last_tweet_date()


def update_lat_dates_all():
    iterate_over_all_places(update_last_date)


def zero_tweets_in_places():
    iterate_over_all_places(remove_tweets)


def zero_collectors():
    iterate_over_all_places(restart)


def renew_tweet_db():
    print("renew_tweet_db:")
    for user in user_dictionary.values():
        regions = user.get_regions()
        for region in regions.values():
            places = region.get_places_handle()
            for p in places.values():
                p.update_my_tweet_list(user, region)


def renew_tweet_user_db():
    print("renew_tweet_user_db:")
    for user in user_dictionary.values():
        regions = user.get_regions()
        for region in regions.values():
            places = region.get_places_handle()
            for p in places.values():
                p.update_my_users_list(user.get_name(), region.get_name())


def extract_text_from_tweets(tweet_list):
    print("extract_text_from_tweets")
    tweets_text_list = []
    for tweet in tweet_list:
        tweets_text_list.append(tweet.text)
    print("extract_text_from_tweets")
    return tweets_text_list


def convert_twitter_users_from_numbers():
    iterate_over_all_places(change)


def add_searchwords():
    for user in user_dictionary.values():
        user.search_words = []
        user.save_me_to_db()
