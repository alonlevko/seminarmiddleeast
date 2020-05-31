from .classes import User, client, twitter_users_database_name, tweet_database_name, user_database_name, get_api, \
    get_from_db, UserExtension, TweetExtension
from cloudant.query import Query, QueryResult
import twitter
import string
import collections
from tweet_parser.tweet import Tweet
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.result import Result, ResultByKey
import jsonpickle
from dateutil.parser import parse
from requests import adapters
from datetime import date, timedelta, datetime

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
        print(data)
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

def replace_string_character(to_replace):
    result = []
    for word in to_replace:
        result.append(word.replace('"', ""))
    return result

def contains_whitespace(s):
    for c in s:
        if c in string.whitespace:
            return True
    return False

def filter_strings(strings):
    single_words = []
    phrases = []
    for strng in strings:
        if contains_whitespace(strng):
            phrases.append(strng)
        else:
            single_words.append(strng)
    return single_words, phrases


def phrase_list_to_word_list(pharses):
    word_list = []
    for phrase in pharses:
        word_list = word_list + phrase.split()
    return word_list


def get_all_twitter_users_ids(tweetext_list, tasdocs=False):
    userid_set = set()
    for tweetex in tweetext_list:
        if tasdocs:
            userid_set.add(TweetExtension.build_from_document(tweetex).tweet.user.id)
        else:
            userid_set.add(tweetex.tweet.user.id)
    userid_list = []
    for id in userid_set:
        userid_list.append(str(id))
    return userid_list


def slider_val_transform(slider_values):
    result = []
    for value in slider_values:
        result.append([str(float(value[0]) * 0.01), str(float(value[1]) * 0.01)])
    return result

def convert_to_iso(full_date):
    # 20200502224035
    dat = datetime(year=int(full_date[0:4]), month=int(full_date[4:6]), day=int(full_date[6:8]),
                   hour=int(full_date[8:10]), minute=int(full_date[10:12]), second=int(full_date[12:14]))
    return dat.isoformat()

def get_tweet_list(locations, user, days_list, word_list, asdocs=None):
    tweets = []
    for loc in locations:
        place = user.get_region(loc['region']).get_place_by_name(loc['place'])
        mylist = place.get_tweets_directly(user.get_name(), loc['region'], days_list, word_list, asdocs)
        if isinstance(mylist, Exception):
            return mylist
        # print(mylist)
        tweets = tweets + mylist
    return tweets

def user_ext_to_json(user_exten):
    json_list = []
    if user_exten is not None:
        for l in user_exten:
            json_list.append(l.get_view_sendaway())
    return json_list

def single_word_obj(word, wordcolname, df, days_list):
    dates_counter = dict.fromkeys(days_list, 0)
    dates_list = []
    counter_list = []
    res = jsonpickle.decode(df.loc[df[wordcolname] == word].to_json())
    for i in res['date'].keys():
        dates_counter[res['date'][str(i)]] += res['counter'][str(i)]
    word_result = collections.OrderedDict(sorted(dates_counter.items()))
    for k, v in word_result.items():
        dates_list.append(k)
        counter_list.append(v)
    return {'word': word, 'dates': dates_list, 'counter': counter_list}

def generate_days_list(start_date, end_date, with_marks=False):
    sdate = date(year=int(start_date[0:4]), month=int(start_date[4:6]), day=int(start_date[6:]))
    edate = date(year=int(end_date[0:4]), month=int(end_date[4:6]), day=int(end_date[6:]))
    delta = edate - sdate  # as timedelta
    days_list = []
    for i in range(delta.days + 1):
        day = sdate + timedelta(days=i)
        days_list.append(day.isoformat().replace("-", ""))
    return days_list


def parse_parameters(request):
    name = request.POST.get('user_name', None)
    locations = jsonpickle.decode(request.POST.get('locations_list', None))
    start_date = request.POST.get('start_date', None)
    if start_date is not None:
        start_date = start_date.replace("-", "")
    end_date = request.POST.get('end_date', None)
    if end_date is not None:
        end_date = end_date.replace("-", "")
    word_list = request.POST.get('words_list', None)
    if word_list is not None:
        word_list = jsonpickle.decode(word_list)

    return name, locations, start_date, end_date, word_list

def generate_users_tweets(request, use_words=True, tasdocs=False, uasdocs=False):
    twitter_users = []
    total_tweets = []
    name, locations, start_date, end_date, word_list = parse_parameters(request)
    print(start_date)
    print(end_date)
    days_list = None
    flag = False
    if start_date is not "" and end_date is not "":
        days_list = generate_days_list(start_date, end_date)
        flag = True
    if word_list is not None:
        flag = True
    if flag:
        if use_words:
            total_tweets = get_tweet_list(locations, get_user(name), days_list, word_list, tasdocs)
        else:
            total_tweets = get_tweet_list(locations, get_user(name), days_list, None, tasdocs)
        if isinstance(total_tweets, Exception):
            return total_tweets, []
        userids = get_all_twitter_users_ids(total_tweets, tasdocs)
        print(userids[0:10])
        print(len(userids))
        if uasdocs:
            twitter_users = get_from_db(userids, twitter_users_database_name, "asdocs")
        else:
            twitter_users = get_from_db(userids, twitter_users_database_name, UserExtension)
        print(len(twitter_users))
    else:
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            if uasdocs:
                mylist = place.get_users_directly(name, loc['region'], asdocs=True)
            else:
                mylist = place.get_users_directly(name, loc['region'], asdocs=False)
            if isinstance(mylist, Exception):
                return mylist, []
            twitter_users = twitter_users + mylist
    return twitter_users, total_tweets