#!/usr/bin/env python

import sqlite3
import calendar
import datetime
import json
from pprint import pprint
import requests

YAHOO_API_KEY = '42ce6cfc281462a7b1c079ebe428bf6b'
FLICKR_API_URL = 'http://api.flickr.com/services/rest'
YAHOO_API_URL = 'http://where.yahooapis.com/v1/places.q'

def get_photo_stats(city, start_date=None, end_date=None):
    '''
    Gets photo stats per city.
    '''
    if not start_date and not end_date:
        end_date = datetime.datetime.now()
        start_date = end_date + datetime.timedelta(days = -7)
    else:
        start_date = datetime.datetime.strptime(start_date, '%m-%d-%Y')
        end_date = datetime.datetime.strptime(end_date, '%m-%d-%Y')

    start = datetime_to_unix(start_date)
    end = datetime_to_unix(end_date)

    lat, lon = get_lat_lon(city)

    params = {
            'method' : 'flickr.photos.search',
            'min_taken_date' : start,
            'max_taken_date' : end,
            'lat': lat,
            'lon': lon,
            'accuracy': 11,
            'api_key': YAHOO_API_KEY,
            'format': 'json',
            }

    r = requests.get(FLICKR_API_URL, params=params)
    formatted_response = format_response(r)
    return formatted_response

def format_response(res):
    '''
    Load json into dict and structure for output in template
    '''
    return res.text

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
    pprint(get_photo_stats('London'))
    #test_flickr_api()

if __name__ == "__main__":
    main()
