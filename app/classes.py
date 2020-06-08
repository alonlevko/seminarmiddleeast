import threading
import jsonpickle
from cloudant.client import Cloudant
from cloudant.error import CloudantException
from cloudant.query import Query, QueryResult
from cloudant.result import Result, ResultByKey
from requests import adapters
from cloudant.adapters import Replay429Adapter
from datetime import datetime, timedelta
from dateutil.parser import parse
from ibm_watson import ApiException
from searchtweets import ResultStream, gen_rule_payload, load_credentials, collect_results
import twitter
import time
from tweet_parser.tweet import Tweet
from ibm_watson import NaturalLanguageUnderstandingV1, LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, ConceptsOptions,\
    SentimentOptions, CategoriesOptions

authenticator = IAMAuthenticator('9n3VYaaZ21KNmQucbNt7yHmc6oUQBwVFg8SNeEwNSKYS')
NLU = NaturalLanguageUnderstandingV1(version='2019-07-12', authenticator=authenticator)
NLU.set_service_url('https://api.eu-gb.natural-language-understanding.watson.cloud.ibm.com')

authenticator_translator = IAMAuthenticator('sLinauWRqI9VUnh_K6uwwF08Y0y5qYixvheGnCpLIDW9')
NLT = LanguageTranslatorV3(version='2019-07-12', authenticator=authenticator_translator)
NLT.set_service_url('https://api.eu-gb.language-translator.watson.cloud.ibm.com/instances/6ce5753f-3c76-4ac1-bc49-bee5ca7909a9')

serviceUsername = "7128478b-2062-4009-9051-186404f4ac8b-bluemix"
servicePassword = "786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd"
serviceURL = "https://7128478b-2062-4009-9051-186404f4ac8b-bluemix:786002d3934d952c603f32df1c65be0f5bdd15806211159e71c3bbdfba50fdbd@7128478b-2062-4009-9051-186404f4ac8b-bluemix.cloudantnosqldb.appdomain.cloud"
httpAdapter = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)

httpAdapter2 = adapters.HTTPAdapter(pool_connections=15, pool_maxsize=100)
clientSearch = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter2)

user_database_name = "users_db"
tweet_database_name = "new_tweet_db"
new_tweet_database_name = "new_tweet_db"
twitter_users_database_name = "new_twitter_users_db"
new_tweeter_users_database_name = "new_twitter_users_db"
search_args = load_credentials("twitter_keys.yaml", yaml_key="search_tweets_premium", env_overwrite=False)

api = twitter.Api(consumer_key="eQxlDqvdHmAiK3KYHjCiPscCB",
                      consumer_secret="iaFXHrksMFAca4CZyzYh8LryDObernmZfUNyNUk2TQH5iglLpd",
                      access_token_key="982862636298719232-yowxgKT2N3bhe0OIm4vbDdLCRPrtRGe",
                      access_token_secret="mZ7LpZiSUIdzJYO16DFVclIViJTHxFcZ2cMoFPCV6cgdp",
                      sleep_on_rate_limit=True)


def get_api():
    return api


def extract_text_from_tweets(tweet_list):
    print("extract_text_from_tweets")
    tweets_text_list = []
    for tweet in tweet_list:
        tweets_text_list.append(tweet.text)
    print("extract_text_from_tweets")
    return tweets_text_list


class User:
    def __init__(self, my_name):
        self._id = my_name
        self.regions = {}
        self.search_words = []

    def get_name(self):
        return self._id

    def add_region(self, region):
        self.regions[region] = Region(name=region)

    def get_regions(self):
        return self.regions

    def get_region(self, name):
        if name not in self.regions.keys():
            return None
        else:
            return self.regions[name]

    def add_place(self, place_form):
        if place_form['place_name'] != "" and place_form['upper_region_name'] != "" and place_form['latitude'] is not None and place_form['longitude'] is not None and place_form['radius'] is not None and place_form['language'] != "":
            my_place = Place(place_form['place_name'], place_form['latitude'], place_form['longitude'], place_form['radius'], place_form['language'])
            region_name = place_form['upper_region_name']
            if region_name in self.regions.keys():
                self.regions[region_name].add_place(my_place)

    def add_search_word(self, search_word):
        if search_word not in self.search_words:
            self.search_words.append(search_word)
        self.save_me_to_db()

    def remove_search_word(self, search_words):
        for word in search_words:
            if word in self.search_words:
                self.search_words.remove(word)
                self.search_words = list(filter(None, self.search_words))
        self.save_me_to_db()

    def all_search_words(self):
        return self.search_words

    def save_me_to_db(self):
        print("saving: " + self.get_name())
        myclient = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter)
        myclient.connect()
        users_db = myclient.get(user_database_name, remote=True)

        if self.get_name() in users_db:
            print("user " + self.get_name() + "in Db")
            user_doc = users_db[self.get_name()]
            val = jsonpickle.encode(self)
            user_doc['value'] = val
            print("saving user")
            user_doc.save()
        else:
            print("creating new user")
            val = jsonpickle.encode(self)
            document = {
                '_id': self.get_name(),
                'value': val
            }
            users_db.create_document(document)
        myclient.disconnect()

    def remove_location(self, region_name, place_name):
        if place_name == "":
            self.regions[region_name].destroy(self)
            self.regions.pop(region_name)
        else:
            self.regions[region_name].remove_place(self, place_name)

        self.save_me_to_db()

    def get_region_place_dict(self):
        myDict = dict.fromkeys(self.regions.keys(), None)
        for r in myDict.keys():
            myDict[r] = self.regions[r].get_place_name_and_counters_dict()
        return myDict

    def get_all_tweets_for_locations(self, locations_list):
        total_tweets = []
        for loc in locations_list:
            place = self.get_region(loc['region']).get_place_by_name(loc['place'])
            total_tweets += place.get_tweets_directly(self.get_name(), loc['region'])
        return total_tweets

    def get_all_users_for_locations(self, locations_list):
        total_tweet_users = []
        for loc in locations_list:
            place = self.get_region(loc['region']).get_place_by_name(loc['place'])
            total_tweet_users += place.get_users_directly(self.get_name(), loc['region'])
        return total_tweet_users

class Region:
    def __init__(self, name):
        self.places = {}
        self.name = name

    def get_name(self):
        return self.name

    def add_place(self, p):
        self.places[p.get_name()] = p

    def get_place_by_name(self, p):
        if p in self.places.keys():
            return self.places[p]
        else:
            return None

    def get_place_name_and_counters_dict(self):
        out = []
        for name, place in self.places.items():
            out.append({'name': name, 'tweets': place.tweets, 't_users': place.users})
        return out

    def get_places_handle(self):
        return self.places

    def destroy(self, user):
        for place in self.places.values():
            def remove():
                print("started removing")
                place.removeTweets(user, self)
                place.removeUsers(user, self)
                print("finished removing")
            threading.Thread(target=remove).start()

        self.places = {}

    def remove_place(self, user, place_name):
        if place_name in self.places.keys():
            def remove():
                print("started removing")
                self.places[place_name].removeTweets(user, self)
                self.places[place_name].removeUsers(user, self)
                print("finished removing")
            self.places.pop(place_name)
            threading.Thread(target=remove).start()

class Place:
    def __init__(self, name, lat, lon, rad, lang, tweets=None, users=None):
        self.name = name
        self.latitude = lat
        self.longitude = lon
        self.radius = rad
        self.language = lang
        self.max_id = 0 # later deal with input tweets case
        self.collector = 0
        self.config_last_tweet_date()
        if tweets is None:
            self.tweets = 0
        else:
            self.tweets = len(tweets)
        if users is None:
            self.users = 0
        else:
            self.users = len(users)

    def add_user(self, tuser):
        self.users += 1

    def get_tweet_number(self):
        return self.tweets

    def get_user_number(self):
        return self.users

    def add_tweet(self, tweet):
        tweet_time = parse(tweet.created_at)
        if tweet_time > self.last_tweet_date:
            self.last_tweet_date = tweet_time

        self.tweets += 1
        if tweet.id > self.max_id:
            self.max_id = tweet.id

    def config_last_tweet_date(self):
        date = 'Fri May 10 00:44:04 +0000 2019'
        self.last_tweet_date = parse(date)

    def add_tweet_list(self, tweet_list, user, region, old_user=False):
        print("in add_tweet_list tweet list len:" + str(len(tweet_list)))
        user_list = []
        for t in tweet_list:
            self.add_tweet(t)
            user_list.append(t.user)
        if old_user is False:
            self.add_user_list(user_list, user, region)
        exten = generate_extensions(tweet_list, user, region, self, TweetExtension)
        print("in add_tweet_list exten list len:" + str(len(exten)))
        save_list_to_db(exten, tweet_database_name, TweetExtension)

    def add_user_list(self, users_list, user, region):
        print("add_user_list")
        users_list = remove_duplicate_users(users_list)
        exten = generate_extensions(users_list,  user, region, self, UserExtension)
        save_list_to_db(exten, twitter_users_database_name, UserExtension)
        for u in users_list:
            self.add_user(u)

    def get_name(self):
        return self.name

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_radius(self):
        return self.radius

    def get_language(self):
        return self.language

    def get_query_string(self):
        return "geocode%3A" + str(self.latitude) + "%2C" + str(self.longitude) + "%2C" + str(self.radius) +\
               "km%20lang%3A" + self.language + "%20since%3A" + self.last_tweet_date.date().isoformat()

    def init_stand_tweet_collection(self, api, user, region, word_list=None):
        if self.collector == 0 or (not self.collector.is_alive()):
            self.collector = threading.Thread(target=self.origin_tweet_collector, args=[api, user, region, word_list])
            self.collector.start()

    def init_premium_tweet_collection(self, user, region, word_list=None):
        print("init_premium_tweet_collection")
        if self.collector == 0 or (not self.collector.is_alive()):
            print("init_premium_tweet_collection - started thread")
            self.collector = threading.Thread(target=self.origin_prem_tweet_collector, args=[user, region])
            self.collector.start()

    # return max id and 100 more tweets
    def get_tweets(self, start, end):
        print("get tweets, start: " + str(start) + " end: " + str(end) + " len: " + str(len(self.tweets)))
        return get_from_db(self.tweets[start: end], tweet_database_name, TweetExtension)

    def get_tweets_directly(self, user_name, region_name, dates=None, word_list=None, asdocs=None):
        print("get_tweets_directly")
        return get_from_db_by_params(user_name, region_name, self.name, new_tweet_database_name, TweetExtension,
                                     dates=dates, word_list=word_list, asdocs=asdocs)

    def get_users_directly(self, user_name, region_name, asdocs=False):
        print("get_users_directly")
        return get_from_db_by_params(user_name, region_name, self.name, new_tweeter_users_database_name, UserExtension, asdocs=asdocs)

    def get_twitter_users(self, start, end):
        print("get users, start: " + str(start) + " end: " + str(end) + " len: " + str(len(self.users)))
        list = get_from_db(self.users[start: end], twitter_users_database_name)
        print(len(list))
        print("leave get users")
        return list

    def origin_prem_tweet_collector(self, user, region, word_list=None):
        toDate = (datetime.today() - timedelta(days=7)).date().isoformat()
        fromDate = self.last_tweet_date.date().isoformat()
        if fromDate > toDate:
            return
        rule = gen_rule_payload("point_radius:[" + str(self.longitude) + " " +  str(self.latitude)+ " " +
                                str(self.radius) + "km] lang:" + self.language
                                , to_date=toDate,
                                from_date=fromDate , results_per_call=100)
        try:
            tweets = collect_results(rule, max_results=1000000, result_stream_args=search_args)
        except Exception as exc:
            print("In origin_prem_tweet_collector:")
            print(exc)
            return

        tweets_paresd = []
        for t in tweets:
            tweets_paresd.append(twitter.Status().NewFromJsonDict(t))
        self.add_tweet_list(tweets_paresd, user, region)
        self.collector = 0
        user.save_me_to_db()
        print("finish - origin_prem_tweet_collector")

    def origin_tweet_collector(self, api, user, region, word_list=None):
        results = {1, 2}
        min_id_query = 0
        print("origin tweet collector start min_id_query:" + str(min_id_query))
        while len(results) > 1:
            id_list = []
            if min_id_query == 0:
                quary = "q=" + self.get_query_string() + "&count=100&src=typed_query"
                results = api.GetSearch(raw_query=quary)
                print("origin_tweet_collector: results len:" + str(len(results)) + "min_id_query:" + str(min_id_query))
                self.add_tweet_list(results, user, region)
                for r in results:
                    id_list.append(r.id)
                if len(id_list)>0:
                    min_id_query = min(id_list)
            else:
                querry_str = "q=" + self.get_query_string() + "lang%3Aar&count=100&max_id=" + str(
                    min_id_query) + "&src=typed_query"
                results = api.GetSearch(raw_query=querry_str)
                print("origin_tweet_collector: results len:" + str(len(results)) + "min_id_query:" + str(min_id_query))
                self.add_tweet_list(results, user, region)
                for r in results:
                    id_list.append(r.id)
                if len(id_list)>0:
                    min_id_query = min(id_list)
        print("origin_tweet_collector finished: results len:" + str(len(results)) + "min_id_query:" + str(min_id_query))
        self.collector = 0
        user.save_me_to_db()
        self.init_premium_tweet_collection(user, region)

    def get_quary_strings(self):
        return "lash"

    def set_collector(self, col):
        self.collector = col

    def update_my_tweet_list(self, user, region):
        if len(self.tweets) > 0:
            print("updating for: " + user.get_name() + " , " + region.get_name() + ", " + self.get_name() + " tweet number:" + str(len(self.tweets)))
            tweetext_list = self.get_tweets(0, len(self.tweets))
            tweet_list = []
            for tweetex in tweetext_list:
                tweet_list.append(tweetex.tweet)
            extensions_list = generate_extensions(tweet_list, user, region, self, TweetExtension)
            save_list_to_db(extensions_list, new_tweet_database_name, TweetExtension)
        else:
            pass

    def update_my_users_list(self, username, regioname):
        if len(self.users) > 0:
            print("updating for: " + username + " , " + regioname + ", " + self.get_name() + " tweet number:" + str(len(self.tweets)))
            users_list = self.get_twitter_users(0, len(self.users))
            extensions_list = generate_extensions(users_list, username, regioname, self.name, UserExtension)
            save_list_to_db(extensions_list, new_tweeter_users_database_name, UserExtension)
        else:
            pass

    def convert_tweet_users_list_to_count(self):
        length = len(self.tweets)
        self.tweets = length
        length = len(self.users)
        self.users = length

    def removeTweets(self, user, region):
        print("removing tweets for %s, %s, %s", user.get_name(), region.get_name(), self.name)
        tweets = get_from_db_by_params(user.get_name(), region.get_name(), self.name, new_tweet_database_name,
                                       TweetExtension, asdocs=True)
        client.connect()
        db = client.get(new_tweet_database_name, remote=True)
        for t in tweets:
            id = t['_id']
            db[str(id)].delete()
        client.disconnect()

    def removeUsers(self, user, region):
        print("removing twitter users for %s, %s, %s", user.get_name(), region.get_name(), self.name)
        tweets = get_from_db_by_params(user.get_name(), region.get_name(), self.name, new_tweeter_users_database_name,
                                       UserExtension, asdocs=True)
        client.connect()
        db = client.get(new_tweeter_users_database_name, remote=True)
        for t in tweets:
            id = t['_id']
            db[str(id)].delete()
        client.disconnect()


def generate_extensions(element_list, user, region, place, obj):
    extensions_list = []
    print("generate_extensions")
    for element in element_list:
        extensions_list.append(obj(element, user, region, place))

    for exten in extensions_list:
        exten.calculate_extensions()

    return extensions_list


class ExtensionInterface:
    @staticmethod
    def build_from_document(doc):
        pass

    def calculate_extensions(self):
        pass

    def build_my_document(self):
        pass


class TweetExtension(ExtensionInterface):
    def __init__(self, tweet, user, region, place, concept=None, entities=None, entities_sentiment=None,
                 keywords=None, keywords_sentiments=None, category = None):
        self.tweet = tweet
        self.user = user
        self.region = region
        self.place = place
        self.concept = concept
        self.entities = entities
        self.entities_sentiment = entities_sentiment
        self.keywords = keywords
        self.keywords_sentiment = keywords_sentiments
        self.category = category
        #datetime.strptime('Tue Mar 17 10:31:07 +0000 2020', '%a %b %d %H:%M:%S +0000 %Y').date().isoformat().replace("-", "")
        self.date = datetime.strptime(self.tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y').date().isoformat().replace("-", "")

    def extract_englishonly_catagories(self, response):
        if 'concepts' in response and len(response['concepts']) > 0:
            self.concept = response['concepts'][0]['text']
        if 'entities' in response and len(response['entities']) > 0:
            self.entities = response['entities'][0]['text']
            self.entities_sentiment = response['entities'][0]['sentiment']['label']
        if 'keywords' in response and len(response['keywords']) > 0:
            self.keywords = response['keywords'][0]['text']
            self.keywords_sentiment = response['keywords'][0]['sentiment']['label']

    def calculate_extensions(self):
        return # need to pass because this cost money that we don't have
        tweet_text = self.tweet.text
        response = "Languange not supported"
        try:
            if self.tweet.lang == 'ar':
                response = NLU.analyze(text=tweet_text, features=Features(categories=CategoriesOptions(limit=1)),
                                       language='ar').get_result()
                if len(response['categories']) > 0:
                    self.category = response['categories'][0]['label']
                translated = NLT.translate(text=tweet_text, model_id='ar-en', source='ar', target='en').get_result()
                translated = translated['translations'][0]['translation']
                response = NLU.analyze(text=translated, features=Features(concepts=ConceptsOptions(limit=1),
                                                                          entities=EntitiesOptions(limit=1, sentiment=True),
                                                                          keywords=KeywordsOptions(limit=1, sentiment=True),
                                                                          ), language='en').get_result()
                self.extract_englishonly_catagories(response)
            elif self.tweet.lang == 'en':
                response = NLU.analyze(text=tweet_text, features=Features(concepts=ConceptsOptions(limit=1),
                                                                          entities=EntitiesOptions(limit=1, sentiment=True),
                                                                          keywords=KeywordsOptions(limit=1, sentiment=True),
                                                                          categories=CategoriesOptions(limit=1),
                                                                          ), language='en').get_result()
                if len(response['categories']) > 0:
                    self.category = response['categories'][0]['label']
                self.extract_englishonly_catagories(response)
        except ApiException as ex:
            print("error in calculate_AI_things")
            print(exc)
            return

    def build_my_document(self):
        val = jsonpickle.encode(self.tweet)
        document = {
            '_id': str(self.tweet.id),
            'value': val,
            'user_name': self.user.get_name(),
            'region_name': self.region.get_name(),
            'place_name': self.place.get_name(),
            'concept': self.concept,
            'entities': self.entities,
            'entities_sentiment': self.entities_sentiment,
            'keywords': self.keywords,
            'keywords_sentiment': self.keywords_sentiment,
            'category': self.category,
            'date': self.date,
            'tdata': self.tweet.text
        }
        return document

    @staticmethod
    def build_from_document(doc):
        return TweetExtension(jsonpickle.decode(str(doc['value'])), str(doc['user_name']), str(doc['region_name']),
                              str(doc['place_name']), str(doc['concept']), str(doc['entities']),
                              str(doc['entities_sentiment']), str(doc['keywords']), str(doc['keywords_sentiment']),
                              str(doc['category']))


class UserExtension(ExtensionInterface):
    def __init__(self, twitter_user, user, region, place, total_retweet_count=0, total_favorites_count=0,
                 total_replies_count=0, total_quoted_count=0):
        self.twitter_user = twitter_user
        self.user = user
        self.region = region
        self.place = place
        self.total_retweet_count = total_retweet_count
        self.total_favorites_count = total_favorites_count
        self.total_replies_count = total_replies_count
        self.total_quoted_count = total_quoted_count


    def get_premium_all_tweets(self):
        rule_str = "from:" + self.twitter_user.screen_name
        print("get_all_twitter_user_tweets: rule_str: " + rule_str)
        rule = gen_rule_payload(rule_str)
        tweets_paresd = []
        try:
            tweets = collect_results(rule, max_results=100, result_stream_args=search_args)
            print("tweets len:" + str(len(tweets)))
            for t in tweets:
                tweets_paresd.append(twitter.Status().NewFromJsonDict(t))
            print("tweets_paresd len:" + str(len(tweets_paresd)))
            self.place.add_tweet_list(tweets_paresd, self.user, self.region, old_user=True)
        except Exception as exc:
            print("In get_all_twitter_user_tweets, Problem loading tweets")
            print(exc)
        return tweets_paresd

    def get_standart_all_tweets(self):
        tweet_list = []
        results = api.GetUserTimeline(screen_name=self.twitter_user.screen_name)
        print("in get_standart_all_tweets, got results:" + str(len(results)) + "from user: " + self.twitter_user.screen_name)
        for tweet in results:
            tweet_list.append(tweet)
        self.place.add_tweet_list(tweet_list, self.user, self.region, old_user=True)
        return tweet_list

    def calculate_extensions(self):
        print("calculate_extensions - UserExtension")
        # this is the non paid version
        tweet_list = self.get_standart_all_tweets()
        self.total_retweet_count = get_total_retweet_number(tweet_list)
        self.total_favorites_count = get_total_favorites_number(tweet_list)
        """ paid version is like:
        if self.twitter_user.followers_count > 200:
            tweet_list = self.get_premium_all_tweets()
            self.total_retweet_count = get_total_retweet_number(tweet_list)
            self.total_favorites_count = get_total_favorites_number(tweet_list)
            self.total_replies_count = get_total_reply_number(tweet_list)
            self.total_quoted_count = get_total_quote_number(tweet_list)
        else:
            tweet_list = self.get_standart_all_tweets()
            self.total_retweet_count = get_total_retweet_number(tweet_list)
            self.total_favorites_count = get_total_favorites_number(tweet_list)
        """
        
    def build_my_document(self):
        val = jsonpickle.encode(self.twitter_user)
        document = {
            '_id': str(self.twitter_user.id),
            'value': val,
            'user_name': self.user.get_name(),
            'region_name': self.region.get_name(),
            'place_name': self.place.get_name(),
            'followers_count': self.twitter_user.followers_count,
            'total_retweet_count': self.total_retweet_count,
            'total_favorite_count': self.total_favorites_count,
            'total_replies_count': self.total_replies_count,
            'total_quoted_count': self.total_quoted_count
        }
        return document

    @staticmethod
    def build_from_document(doc):
        return UserExtension(jsonpickle.decode(str(doc['value'])), str(doc['user_name']), str(doc['region_name']),
                         str(doc['place_name']), doc['total_retweet_count'], doc['total_favorite_count'],
                             doc['total_replies_count'], doc['total_quoted_count'])

    def get_view_sendaway(self):
        name = "0"
        if self.twitter_user.name is not None:
            name = str(self.twitter_user.name)
        followers_count = "0"
        if self.twitter_user.followers_count is not None:
            followers_count = str(self.twitter_user.followers_count)
        location = "none"
        if self.twitter_user.location is not None:
            location = str(self.twitter_user.location)
        #print("verified:" + str(self.twitter_user.verified))
        return [str(self.twitter_user.id), str(self.twitter_user.description), str(self.twitter_user.screen_name),
                location, name,  followers_count, str(self.twitter_user.created_at), str(self.total_retweet_count),
                str(self.total_favorites_count), str(self.twitter_user.statuses_count),
                str(self.twitter_user.verified)]

# if get_extension is true we return the full extension object. else we return the value only.
def get_from_db(id_list, db_name, object_example=None):
        result_list = []
        client_get_from_db = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter2)
        try:
            client_get_from_db.connect()
            db = client_get_from_db.get(db_name, remote=True)
            if db is None:
                print("error: no tweet db ready yet")
                return ""
            query_result = QueryResult(Query(db, selector={'_id': {'$in': id_list}}))
            index = 0
            for doc in query_result:
                if object_example is "asdocs":
                    result_list.append(doc)
                elif object_example is not None:
                    result_list.append(object_example.build_from_document(doc))
                    index = + 1
                else:
                    dec = jsonpickle.decode(str(doc['value']))
                    result_list.append(dec)
                    index =+ 1
            print("query_result len: " + str(index))
        except CloudantException as exc:
            print("CloudantException in save_list_to_db")
            print(exc)
            result_list = []
        except Exception as exc:
            print("non CloudantException exception in save_list_to_db")
            print(exc)
            result_list = []
        finally:
            client_get_from_db.disconnect()
            print("get_from_db id: " + str(db_name) + " len: " + str(len(result_list)))
        return result_list

# if is_extension is true we have full extension object so we write it like that do db.
def save_list_to_db(inlist, db_name, object_example=None):
    print("save_list_to_db:" + db_name + "list len is: " + str(len(inlist)))
    documents = []
    for obj in inlist:
        if object_example is not None:
            document = obj.build_my_document()
        else:
            val = jsonpickle.encode(obj)
            document = {
                '_id': str(obj.id),
                'value': val
            }
        documents.append(document)
    client_save_to_db = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=httpAdapter2)
    try:
        client_save_to_db.connect()
        db = client_save_to_db.get(db_name, remote=True)
        db.bulk_docs(documents)
    except CloudantException as exc:
        print("CloudantException in save_list_to_db")
        print(exc)
        time.sleep(2)
        try:
            client_save_to_db.connect()
            db = client_save_to_db.get(db_name, remote=True)
            db.bulk_docs(documents)
        except Exception as exc:
            print("second exception after CloudantException exception in save_list_to_db")
            print(exc)
    except Exception as exc:
        print("non CloudantException exception in save_list_to_db")
        print(exc)
    finally:
        client_save_to_db.disconnect()

def generate_text_selector(word_list):
    sel_list = []
    for word in word_list:
        sel_list.append({"tdata": {"$regex": word}})
    #return {'$or': sel_list}
    return sel_list

def generate_single_place_selector(user_name, region_name, place_name, dates, word_list):
    selector = {'user_name': {'$eq': user_name}, 'region_name': {'$eq': region_name}, 'place_name': {'$eq': place_name}}
    if dates is not None:
        selector['date'] = {'$in': dates}
    if word_list is not None:
        selector['$or'] = generate_text_selector(word_list)
    return selector


def get_from_db_by_params(user_name, region_name, place_name, db_name, object_example, asdocs=False, dates=None, word_list=None):
    print("get_from_db_by_params")
    print(user_name + ";" + region_name + ";" + place_name + ";" + db_name + ";" + str(type(object_example)) + ";" +
                                                                                       str(asdocs))
    get_db_client = Cloudant(serviceUsername, servicePassword, url=serviceURL, adapter=Replay429Adapter(retries=10, initialBackoff=0.01))
    try:
        our_list = []
        get_db_client.connect()
        db = get_db_client.get(db_name, remote=True)
        selector = generate_single_place_selector(user_name, region_name, place_name, dates, word_list)
        print("the selector is: " + str(selector))
        query_result = QueryResult(Query(db, selector=selector))
        if asdocs is True:
            for doc in query_result:
                our_list.append(doc)
        else:
            for doc in query_result:
                our_list.append(object_example.build_from_document(doc))
    except CloudantException as exc:
        print("CloudantException in get_from_db_by_params")
        print(exc)
        return exc
    except Exception as exc:
        print("non CloudantException exception in get_from_db_by_params")
        print(exc)
        return exc
    finally:
        get_db_client.disconnect()
        print("get_from_db_by_params id: " + str(db_name) + " len: " + str(len(our_list)))
    return our_list


def get_total_reply_number(tweet_list):
    reply_count = 0
    for tweet in tweet_list:
        if hasattr(tweet, 'reply_count'):
            print("reply_count:" + str(reply_count))
            print("tweet.reply_count:" + str(tweet.reply_count))
            reply_count += tweet.reply_count
    return reply_count


def get_total_favorites_number(tweet_list):
    print("get_total_favorites_number")
    favorite_count = 0
    for tweet in tweet_list:
        favorite_count += tweet.favorite_count
    return favorite_count


def get_total_retweet_number(tweet_list):
    print("get_total_retweet_number")
    retweet_count = 0
    for tweet in tweet_list:
        retweet_count += tweet.retweet_count
    return retweet_count


def get_total_quote_number(tweet_list):
    print("get_total_quote_number")
    quote_count = 0
    for tweet in tweet_list:
        if hasattr(tweet, 'quote_count'):
            quote_count += tweet.quote_count
    return quote_count


def remove_duplicate_users(user_list):
    result_dict = {}
    for u in user_list:
        result_dict[u.id] = u
    return result_dict.values()
