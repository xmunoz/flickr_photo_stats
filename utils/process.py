#!/usr/bin/env python

import sqlite3
import calendar
import datetime
from pprint import pprint
import requests

YAHOO_API_KEY = '42ce6cfc281462a7b1c079ebe428bf6b'
FLICKR_API_URL = 'http://api.flickr.com/services/rest'
YAHOO_API_URL = 'http://api.flickr.com/services/auth'

def get_photo_stats(city, start_date=None, end_date=None):
    '''
    Gets photo stats per city.
    '''
    if not start_date and not end_date:
        end_time = datetime.datetime.now()
        start_time = end_time + datetime.timedelta(days = -7)
    else:
        start_time = datetime.strptime(start_date, '%m-%d-%Y')
        end_time = datetime.strptime(end_date, '%m-%d-%Y')

    start = datetime_to_unix(start_time)
    end = datetime_to_unix(end_time)

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
    return r.text

def get_lat_lon(location):
    return '37.722392', '-122.365723'

def datetime_to_unix(d):
    '''
    Convert python datetime to unix timestamp.
    '''
    return calendar.timegm(d.utctimetuple())


def test_flickr_api():
    params = {
            'api_key': YAHOO_API_KEY,
            'method': 'flickr.test.echo',
            'format': 'json',
            }
    r = requests.get(FLICKR_API_URL, params=params)
    print r.status_code
    pprint(r.text)

def main():
    pprint(get_photo_stats('London'))
    #test_flickr_api()

if __name__ == "__main__":
    main()
