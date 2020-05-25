from __future__ import unicode_literals
import json
import collections
import string
from datetime import date, timedelta, datetime
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from django.http import Http404
from django.shortcuts import render
import threading
import json
from django.views.decorators.csrf import csrf_exempt
from .forms import NameForm, RegionForm, PlaceForm, GetTweetsForm
from .app_logic import handle_region_form, handle_place_form, get_user, \
    init_tweet_accumulation_tweet_list, handle_search_form,\
    generate_tweet_sendaway, generate_user_sendaway, word_trends_merge_jsons
import jsonpickle
from .Analytics import QueriesManager
from .classes import get_from_db, UserExtension, twitter_users_database_name, TweetExtension


def index(request):
    if request.method == 'POST':
        form_user = NameForm(request.POST)
        if form_user.is_valid():
            name = form_user.cleaned_data['your_name']
            return HttpResponseRedirect('/tweets/' + name)
    # if a GET (or any other method) we'll create a blank form
    else:
        form_user = NameForm()

    return render(request, 'index.html', {'form': form_user})


def dashboard(request, name):
    user = get_user(name)

    if request.method == 'POST':
        form_region = RegionForm(request.POST or None)
        regions = handle_region_form(form_region, user)
        place_form = PlaceForm(request.POST or None)
        handle_place_form(place_form, user)
        search_form = GetTweetsForm(request.POST or None)
        region, place = handle_search_form(search_form)
        if region != "":
            user.remove_location(region, place)
        user.save_me_to_db()
        user = get_user(name)
        regions = collections.OrderedDict(user.get_regions())
        return render(request, 'dashboard.html',
                      {'name': name, 'regions': regions, 'region_form': RegionForm(), 'place_form': PlaceForm(), 'tweets_form': GetTweetsForm()})

    else:
        user = get_user(name)
        regions = collections.OrderedDict(user.get_regions())
        return render(request, 'dashboard.html',
                      {'name': name, 'regions': regions, 'region_form': RegionForm(), 'place_form': PlaceForm(),
                       'tweets_form': GetTweetsForm()})


def help_page(request, name):
    return render(request, 'help.html', {'name': name})


@csrf_exempt
def get_regions_places_list(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name', None)
        user = get_user(user_name)
        region_place_dict = user.get_region_place_dict()
        return JsonResponse(region_place_dict, safe=False)
    else:
        empty = {}
        return JsonResponse(empty)


@csrf_exempt
def get_search_words(request):
    if request.method == 'POST':
        user_name = request.POST.get('user_name', None)
        user = get_user(user_name)
        word_to_add = request.POST.get('to_add', None)
        if word_to_add != "":
            word_to_add = word_to_add.replace('"', "")
            user.add_search_word(word_to_add)
        word_to_remove = request.POST.get('to_remove', None)
        if word_to_remove != "":
            word_to_remove = word_to_remove.replace('"', "")
            user.remove_search_word(word_to_remove)
        print(user_name)
        print(word_to_add)
        print(word_to_remove)
        print(user.all_search_words())
        return JsonResponse(user.all_search_words(), safe=False)
    else:
        empty = {}
        return JsonResponse(empty)


@csrf_exempt
def accumulate_tweets(request):
    if request.method == 'POST':
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        user = get_user(name)
        for loc in locations:
            init_tweet_accumulation_tweet_list(user, loc['region'], loc['place'], word_list)
    empty = {}
    return JsonResponse(empty)


@csrf_exempt
def get_query_links(request):
    if request.method == 'POST':
        name = request.POST.get('user_name', None)
        locations = jsonpickle.decode(request.POST.get('locations_list', None))
        user = get_user(name)
        results = []
        for loc in locations:
            results.append(user.get_region(loc['region']).get_place_by_name(loc['place']).get_query_string())
        return JsonResponse(results, safe=False)
    else:
        empty = {}
        return JsonResponse(empty)


def show_tweets_list(request, name):
    user = get_user(name)
    print("in show_tweets_list")
    if request.method == 'POST':
        search_form = GetTweetsForm(request.POST)
        region, place = handle_search_form(search_form)
        #quary = init_tweet_accumulation_tweet_list(user, region, place)
        quary = "I am lish lash"
        region = user.get_region(region)
        place = region.get_place_by_name(place)
        return render(request, 'tweets.html', { 'quary': quary, 'region': region, 'place': place, 'user': name})
    elif request.method == 'GET':
        quary = "I am lish lash"
        region = "Lash"
        place = "Lish"
        return render(request, 'tweets.html', { 'quary': quary, 'region': region, 'place': place, 'user': name})


def show_users_list(request, name):
    user = get_user(name)
    print("show_users_list")
    if request.method == 'POST':
        search_form = GetTweetsForm(request.POST)
        region, place = handle_search_form(search_form)
        quary = init_tweet_accumulation_tweet_list(user, region, place)
        region = user.get_region(region)
        place = region.get_place_by_name(place)
        return render(request, 'users.html', { 'quary': quary, 'region': region, 'place': place, 'user': name})
    elif request.method == 'GET':
        quary = "I am lish lash"
        region = "Lash"
        place = "Lish"
        return render(request, 'users.html', { 'quary': quary, 'region': region, 'place': place, 'user': name})


def popular_users(request, name):
    return render(request, 'popular_users.html', {'user': name})


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


@csrf_exempt
def popular_users_get(request):
    print("popular_users_get")
    users_list = []
    if request.method == 'POST':
        twitter_users, tweets = generate_users_tweets(request, tasdocs=True, uasdocs=True)
        if isinstance(twitter_users, Exception):
            return JsonResponse(str(twitter_users), safe=False, status=500)
        queriesManager = QueriesManager()
        slider_valus = slider_val_transform(jsonpickle.decode(request.POST.get('sliders_data', None)))
        print(len(twitter_users))
        print(len(tweets))
        # ["followers_slider", "retweet_slider", "favorites_slider", "tweets_slider"]
        # ["followers, statusses, favorites (likes), retweets]
        queriesManager = QueriesManager()
        params = ['Opinion_Leaders', [str(slider_valus[0][0])], [str(slider_valus[0][1])],
                  [str(slider_valus[3][0])], [str(slider_valus[3][1])], [str(slider_valus[2][0])], [str(slider_valus[2][1])],
                  [str(slider_valus[1][0])], [str(slider_valus[1][1])]]
        print(params)
        print(twitter_users[0].keys())
        df = queriesManager.call_querie(params, tweets, twitter_users)
        print(df)
        idlist = df['id'].tolist()
        print(idlist)
        users_list = get_from_db(idlist, twitter_users_database_name, UserExtension)
        print(len(users_list))
    return JsonResponse(user_ext_to_json(users_list), safe=False)


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


@csrf_exempt
def tweet_list_place(request):
    print("tweet_list_place")
    if request.method == 'POST':
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        print("word list is: " + str(word_list))
        if start_date is not "" and end_date is not "":
            days_list = generate_days_list(start_date, end_date)
        else:
            days_list = None
        print(days_list)
        total_tweets = []
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            mylist = place.get_tweets_directly(name, loc['region'], days_list, word_list)
            if isinstance(mylist, Exception):
                return JsonResponse(str(mylist), safe=False, status=500)
            #print(mylist)
            json_list = []
            for l in mylist:
                result = generate_tweet_sendaway(l.tweet)
                """ this is the paid data from ibm watson
                result.append(l.category)
                result.append(l.concept)
                result.append(l.entities)
                result.append(l.entities_sentiment)
                result.append(l.keywords)
                result.append(l.keywords_sentiment)
                """
                json_list.append(result)
            total_tweets = total_tweets + json_list
        #print(total_tweets)
        return JsonResponse(total_tweets, safe=False)
    else:
        empty = {}
        return JsonResponse(empty)


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


def user_ext_to_json(user_exten):
    json_list = []
    if user_exten is not None:
        for l in user_exten:
            json_list.append(l.get_view_sendaway())
    return json_list


@csrf_exempt
def show_users_place(request):
    print("show_users_place")
    if request.method == 'POST':
        twitter_users, _ = generate_users_tweets(request)
        if isinstance(twitter_users, Exception):
            return JsonResponse(str(twitter_users), safe=False, status=500)
        return JsonResponse(user_ext_to_json(twitter_users), safe=False)
    else:
        empty = {}
        return JsonResponse(empty)


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


def return_error(exception):
    response = JsonResponse(str(exception), safe=False)
    response.status_code = 500
    return response


def run(params, queriesManager):
    try:
        res = jsonpickle.decode(queriesManager.call_querie(params, test=False, json=True))
    except Exception as ex:
        return return_error(ex), 1
    return res, 0


def single_word_obj(word, wordcolname, df, days_list):
    dates_counter = dict.fromkeys(days_list, 0)
    dates_list = []
    counter_list = []
    res = jsonpickle.decode(df.loc[df[wordcolname] == word].to_json())
    # print(res)
    for i in res['date'].keys():
        # print(res['date'][str(i)])
        # print(res['counter'][str(i)])
        dates_counter[res['date'][str(i)]] += res['counter'][str(i)]
        # print(dates_counter)
    word_result = collections.OrderedDict(sorted(dates_counter.items()))
    for k, v in word_result.items():
        dates_list.append(k)
        counter_list.append(v)
    return {'word': word, 'dates': dates_list, 'counter': counter_list}


@csrf_exempt
def word_trends_get(request):
    print("word_trends_get")
    total_result = []
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        days_list = generate_days_list(start_date, end_date)
        total_tweets = []
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            mylist = place.get_tweets_directly(name, loc['region'], days_list, asdocs=True)
            if isinstance(mylist, Exception):
                return JsonResponse(mylist, safe=False, status=500)
            print(len(mylist))
            total_tweets = total_tweets + mylist
        word_list, pharses_list = filter_strings(word_list)
        params = ["Word_trend", word_list]
        print(params)
        print(len(total_tweets))
        df = queriesManager.call_querie(params, total_tweets, [])
        phrase_dfs = []
        for phrase in pharses_list:
            params = ['Phrase_trend', phrase]
            print(params)
            phrase_dfs.append({"df": queriesManager.call_querie(params, total_tweets, []), "phrase": phrase})
        print(phrase_dfs)
        for word in word_list:
            total_result.append(single_word_obj(word, 'word', df, days_list))
        for dic in phrase_dfs:
            total_result.append(single_word_obj(dic['phrase'], 'phrase', dic["df"], days_list))
        print(total_result)
    return JsonResponse(total_result, safe=False)


def top_words_per_date(request, name):
    return render(request, 'top_words_per_date.html', {'user': name})


@csrf_exempt
def top_words_per_date_get(request):
    print("top_words_per_date_get")
    words_list = []
    counter_list = []
    days_list = []
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, _ = parse_parameters(request)
        days_list = generate_days_list(start_date, end_date)
        dates_counter = dict.fromkeys(days_list)
        print(days_list)
        total_tweets = []
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            mylist = place.get_tweets_directly(name, loc['region'], days_list, asdocs=True)
            if isinstance(mylist, Exception):
                return JsonResponse(mylist, safe=False, status=500)
            print(len(mylist))
            total_tweets = total_tweets + mylist

        for k, _ in dates_counter.items():
            dates_counter[k] = {'word': "", 'count': 0}
        params = ["Popular_word_per_date"]
        print(params)
        print(len(total_tweets))
        df = queriesManager.call_querie(params, total_tweets, [])
        print(df)
        words_list = ["No Tweets"] * len(days_list)
        counter_list = [0] * len(days_list)
        for i, day in enumerate(days_list):
            print(day)
            col = df.loc[df['date'] == day]
            for index, row in col.iterrows():
                words_list[i] = row['popular_word']
                counter_list[i] = row['counter']
        print(days_list)
        print(words_list)
        print(counter_list)
    return JsonResponse({'dates': days_list, 'words': words_list, 'counter': counter_list}, safe=False)


def popularity_of_words(request, name):
    return render(request, 'popularity_of_words.html', {'user': name})


@csrf_exempt
def popularity_of_words_get(request):
    print("popularity_of_words_get")
    df = ""
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        word_list, pharase_list = filter_strings(word_list)
        word_list = word_list + phrase_list_to_word_list(pharase_list)
        total_result = []
        days_list = generate_days_list(start_date, end_date)
        total_tweets = []
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            mylist = place.get_tweets_directly(name, loc['region'], days_list, asdocs=True)
            if isinstance(mylist, Exception):
                return JsonResponse(mylist, safe=False, status=500)
            print(len(mylist))
            total_tweets = total_tweets + mylist
        params = ["Popularity_of_word_bank_per_place", word_list]
        print(params)
        print(len(total_tweets))
        df = queriesManager.call_querie(params, total_tweets, [])
        rows = df.shape[0]
        df = df.to_json()
        df = df[:-1]
        df = df + ', "rows": ' + str(rows)
        df = df + ', "word_list": ' + str(word_list) + '}'
        print(df)
        df = df.replace("'", '"')
        print(df)
    return JsonResponse(df, safe=False)


def most_popular_word(request, name):
    return render(request, 'most_popular_word.html', {'user': name})


@csrf_exempt
def most_popular_word_get(request):
    print("most_popular_word_get")
    df = []
    place_list = []
    word_list = []
    counter_list = []
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, _ = parse_parameters(request)
        days_list = generate_days_list(start_date, end_date)
        total_tweets = []
        for loc in locations:
            place = get_user(name).get_region(loc['region']).get_place_by_name(loc['place'])
            mylist = place.get_tweets_directly(name, loc['region'], days_list, asdocs=True)
            if isinstance(mylist, Exception):
                return JsonResponse(mylist, safe=False, status=500)
            print(len(mylist))
            total_tweets = total_tweets + mylist
        params = ["Popular_word_per_place"]
        df = queriesManager.call_querie(params, total_tweets)
        print(df)
        for i, row in df.iterrows():
            place_list.append(row['place_name'])
            word_list.append(row['popular_word'])
            counter_list.append(row['counter'])
    return JsonResponse({'places': place_list, 'words': word_list, 'counters': counter_list}, safe=False)


def convert_to_iso(full_date):
    # 20200502224035
    dat = datetime(year=int(full_date[0:4]), month=int(full_date[4:6]), day=int(full_date[6:8]),
                   hour=int(full_date[8:10]), minute=int(full_date[10:12]), second=int(full_date[12:14]))
    return dat.isoformat()


@csrf_exempt
def first_time_get(request):
    print("first_time_get")
    df_list = []
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        max_results = request.POST.get('max_results', None)
        total_users, total_tweets = generate_users_tweets(request, use_words=False, tasdocs=True, uasdocs=True)
        if isinstance(total_users, Exception):
            return JsonResponse(total_users, safe=False, status=500)
        print(len(total_tweets))
        print(len(total_users))

        for word in word_list:
            params = ["First_Time", [word], [max_results]]
            print(params)
            df = queriesManager.call_querie(params, total_tweets, total_users)
            print(df)
            row_data = []
            # [id, text, user_id, screen_name, full_date, time_rnk]
            for index, row in df.iterrows():
               row_data.append([row["id"], row["text"], row["screen_name"], convert_to_iso(row["full_date"]),
                                row["time_rnk"]])
            df_list.append({"word": word, "len": df.shape[0], "row_data": row_data})
    return JsonResponse(df_list, safe=False)


@csrf_exempt
def most_retweeted_get(request):
    print("most_retweeted_get")
    row_data = []
    if request.method == 'POST':
        queriesManager = QueriesManager()
        name, locations, start_date, end_date, word_list = parse_parameters(request)
        max_results = request.POST.get('max_results', None)
        total_users, total_tweets = generate_users_tweets(request, use_words=False, tasdocs=True, uasdocs=True)
        if isinstance(total_users, Exception):
            return JsonResponse(str(total_users), safe=False, status=500)
        print(len(total_tweets))
        print(len(total_users))
        for word in word_list:
            params = ["Most_Retweeted", [word], [max_results]]
            print(params)
            df = queriesManager.call_querie(params, total_tweets, total_users)
            print(df)

            # [phrase, id, text, user_id, screen_name, full_date, retweet_count, retweet_rnk
            for index, row in df.iterrows():
               row_data.append([row["id"], row["text"], row["screen_name"], convert_to_iso(row["full_date"]),
                                row["retweet_count"], row["retweet_rnk"], row["phrase"]])
    print(row_data)
    return JsonResponse(row_data, safe=False)


def health(request):
    state = {"status": "UP"}
    return JsonResponse(state)


def handler404(request):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '500.html', status=500)


def run_sql_querry(querie_manager, tweets, users, params):
    table = {'tweets': None, 'tweeter_users': None}
    if tweets is not None:
        table['tweets'] = querie_manager.buildTweetsTable(tweets)
    elif users is not None:
        table['tweeter_users'] = querie_manager.buildUsersTable(users)
    else:
        return None

    return querie_manager.sql(params, table)

