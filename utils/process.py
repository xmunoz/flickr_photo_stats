#!/usr/bin/env python

import sqlite3
import calendar
import datetime
import json
import os
from pprint import pprint
import requests
import time

YAHOO_API_KEY = '42ce6cfc281462a7b1c079ebe428bf6b'
FLICKR_API_URL = 'http://api.flickr.com/services/rest'
YAHOO_API_URL = 'http://where.yahooapis.com/v1/places.q'

def get_photo_stats(city, start_date=None, end_date=None):
    '''
    Gets photo stats per city.
    TODO: Fix timezone synchronosity
    '''
    if not start_date and not end_date:
        end_date = datetime.datetime.now()
        start_date = end_date + datetime.timedelta(days = -7)
    else:
        start_date = datetime.datetime.strptime(start_date, '%m-%d-%Y')
        end_date = datetime.datetime.strptime(end_date, '%m-%d-%Y')

    lat, lon = get_lat_lon(city)

    response = make_api_calls(city, start_date, end_date, lat, lon)
    return response

def make_api_calls(city, start_date, end_date, lat, lon):
    '''
    TODO: implement threading or some other kind of async to retrieve data.
    '''
    delta = end_date - start_date
    results = {}
    for d in range(0, delta.days):

        start = start_date + datetime.timedelta(days = d)
        pprint(datetime_to_unix(start))
        end = start + datetime.timedelta(days = 1)
        pprint(datetime_to_unix(end))
        params = {
                'method' : 'flickr.photos.search',
                'min_taken_date' : datetime_to_unix(start),
                'max_taken_date' : datetime_to_unix(end),
                'lat': lat,
                'lon': lon,
                'nojsoncallback': 1,
                'accuracy': 11,
                'api_key': YAHOO_API_KEY,
                'format': 'json',
            }

        r = requests.get(FLICKR_API_URL, params=params)
        key = datetime.datetime.strftime(start,'%B %d %Y')
        results[key] = r.json()['photos']['total']

    return results

def format_response(res):
    '''
    Load json into dict and structure for output in template
    '''
    data = res.json()
    return data

def get_lat_lon(location):
    location_param = '({});'.format(location)
    num_results = 'count=1'
    yahoo_url = YAHOO_API_URL + location_param + num_results
    params = {
            'appid': YAHOO_API_KEY,
            'format': 'json'
            }
    r = requests.get(yahoo_url, params=params)
    res = json.loads(r.text)
    return res['places']['place'][0]['centroid']['latitude'], \
            res['places']['place'][0]['centroid']['longitude']

def datetime_to_unix(d):
    '''
    Convert python datetime to unix timestamp.
    '''
    return calendar.timegm(d.utctimetuple())


def main():
    pprint(get_photo_stats('London', '10-19-2013', '10-26-2013'))
    #test_flickr_api()

if __name__ == "__main__":
    main()
