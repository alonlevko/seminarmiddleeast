from django.urls import path
from django.conf.urls.static import static
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from . import views


urlpatterns = [
               path('', views.index, name='index'),
               path('your-name/', views.index, name='index'),
               path('dashboard/<slug:name>', views.dashboard, name='dashboard'),
               path('tweets/<slug:name>', views.show_tweets_list, name="tweets_list"),
               path('help/<slug:name>', views.help_page, name="help_page"),
               path('tweets-get', views.tweet_list_place, name="tweets_get"),
               path('users-get', views.show_users_place, name="users_get"),
               path('popular_users_get', views.popular_users_get, name="popular_users_get"),
               path('get_regions_places', views.get_regions_places_list, name='get_regions_places_list'),
               path('get_search_words', views.get_search_words, name='get_search_words'),
               path('get_query_links', views.get_query_links, name='get_query_links'),
               path('accumulate_tweets', views.accumulate_tweets, name='accumulate_tweets'),
               path('word_trends_get', views.word_trends_get, name='word_trends_get'),
               path('top_words_per_date_get', views.top_words_per_date_get, name='top_words_per_date_get'),
               path('popularity_of_words_get', views.popularity_of_words_get, name='popularity_of_words_get'),
               path('most_popular_word_get', views.most_popular_word_get, name='most_popular_word_get'),
               path('first_time_get', views.first_time_get, name='first_time_get'),
               path('most_retweeted_get', views.most_retweeted_get, name='most_retweeted_get'),
               path('health', views.health, name='health'),
               path('404', views.handler404, name='404'),
               path('500', views.handler500, name='500'),
               ]


urlpatterns = format_suffix_patterns(urlpatterns)
