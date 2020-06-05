#-*- coding: utf-8 -*-
from django.apps import AppConfig
from .app_logic import load_from_db, zero_collectors, update_lat_dates_all, convert_twitter_users_from_numbers, \
    renew_tweet_db, zero_tweets_in_places, renew_tweet_user_db, add_searchwords, change_lists_to_counts
import platform
import subprocess
import sys
import os

class MyAppConfig(AppConfig):
    name = 'app'

    def ready(self):
        print("do things on startup!")
        print("Python version:")
        print(sys.version)
        #check()
        os.environ['PATH'] += ":/home/vcap/deps/0/apt/usr/lib/jvm/java-8-openjdk-amd64/jre/bin"
        os.environ['PATH'] += ":/home/vcap/deps/1/python/bin"
        os.environ['PATH'] += ":/home/vcap/deps/1/python"
        import sqlite3
        print("sqlite3.version is: " + str(sqlite3.version))
        print("sqlite3.sqlite_version is: " + str(sqlite3.sqlite_version))
        os.environ['LD_LIBRARY_PATH'] = "/home/vcap/deps/0/apt/usr/bin"
        print(os.environ['PATH'])
        """
        for subdir, dirs, files in os.walk('./'):
            for f in files:
                print(f)
                os.path.abspath(f)
                """
        import sqlite3
        print("sqlite3.version is: " + str(sqlite3.version))
        print("sqlite3.sqlite_version is: " + str(sqlite3.sqlite_version))
        load_from_db()
        zero_collectors()
        #change_lists_to_counts()
        #renew_tweet_user_db()
        #update_lat_dates_all()
        #convert_twitter_users_from_numbers()
        #renew_tweet_db()
        #zero_tweets_in_places()
        #add_searchwords()


