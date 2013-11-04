#!/usr/bin/env python

import sqlite3
import calendar
import datetime
from pprint import pprint
import threading
import Queue
import requests
import sys
import time
from collections import OrderedDict

YAHOO_API_KEY = '42ce6cfc281462a7b1c079ebe428bf6b'
FLICKR_API_URL = 'http://api.flickr.com/services/rest'
YAHOO_API_URL = 'http://where.yahooapis.com/v1/places.q'
MAX_WORKER_THREADS = 10

def get_photo_stats(data):
    '''
    Gets photo stats per city.
    TODO: Fix timezone synchronosity
    '''
    if 'start_date' not in data or 'end_date' not in data:
        end_date = datetime.datetime.now()
        start_date = end_date + datetime.timedelta(days = -7)
    else:
        start_date = datetime.datetime.strptime(data['start_date'], '%m-%d-%Y')
        end_date = datetime.datetime.strptime(data['end_date'], '%m-%d-%Y')

    lat, lon = get_lat_lon(data['city'])

    group_by_tags = True if 'tags' in data else False

    photos = make_api_calls(start_date, end_date, lat, lon,\
            group_by_tags)

    results = construct_result_dict(start_date, end_date, group_by_tags)

    if group_by_tags:
        group_by_dates_and_tags(results, photos)
    else:
        group_by_dates(results, photos)

    return results

def make_api_calls(start_date, end_date, lat, lon, tags):
    '''
    Make threaded API calls.
    '''

    photos = get_photos(start_date, end_date, lat, lon)

    photo_data_queue = Queue.Queue()

    for photo in photos:
        photo_in_db = check_db(photo)
        if photo_in_db:
            load_db_data(photo)
        else:
            photo_data_queue.put((photo, tags))

    for i in range(MAX_WORKER_THREADS):
        q = PhotoDataManager(photo_data_queue)
        q.daemon = True
        q.start()

    photo_data_queue.join()

    return photos


def get_lat_lon(location):
    location_param = '({});'.format(location)
    num_results = 'count=1'
    yahoo_url = YAHOO_API_URL + location_param + num_results
    params = {
            'appid': YAHOO_API_KEY,
            'format': 'json'
            }
    r = requests.get(yahoo_url, params=params)
    res = r.json()
    return res['places']['place'][0]['centroid']['latitude'], \
            res['places']['place'][0]['centroid']['longitude']

def datetime_to_unix(d):
    '''
    Convert python datetime to unix timestamp.
    '''
    return calendar.timegm(d.timetuple())


class PhotoDataManager(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            try:
                item, tags = self.queue.get(True, timeout=4)
            except Queue.Empty:
                print('Empty Tag queue')
            finally:
                get_photo_data(item, tags)
                self.queue.task_done()


def get_photos(start, end, lat, lon):
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
    try:
        result = r.json()
        photos = process_photos(result['photos']['photo'])
    except:
        print 'API error in get_photos.'
        pprint(result)

    return photos

def process_photos(photos):
    '''
    Creates a list of photo objects
    '''
    photo_objects = []
    for photo in photos:
        photo_objects.append(Photo(photo['id']))

    return photo_objects


class Photo:
    def __init__(self, pid):
        self.pid = pid
        self.date = 0
        self.time = 0

    def get_datetime(self, api_result):
        date, time = api_result['photo']['dates']['taken'].split(' ')
        # remove encoding
        self.date = str(date)
        self.time = str(time)

    def get_tags(self, api_result):
        self.tags = []
        for tag in api_result['photo']['tags']['tag']:
            if tag:
                self.tags.append(tag['_content'])


def get_photo_data(photo, tags):
    '''
    Make api call to load all needed photo data.
    '''
    params = {
            'method' : 'flickr.photos.getInfo',
            'photo_id': photo.pid,
            'nojsoncallback': 1,
            'api_key': YAHOO_API_KEY,
            'format': 'json',
            }
    r = requests.get(FLICKR_API_URL, params=params)
    try:
        result = r.json()
        photo.get_datetime(result)
        if tags:
            photo.get_tags(result)
    except:
       print "API Error in get_photo_data."
       pprint(result)


def check_db(photo):
    return False

def load_photo_data(photo):
    pass

def construct_result_dict(start_date, end_date, tags):
    results = OrderedDict()
    date_diff = end_date - start_date
    for x in range(0,date_diff.days):
        key = datetime.datetime.strftime(start_date + datetime.timedelta(days=x), '%Y-%m-%d')
        val = {} if tags else 0
        results[key] = val

    return results

def group_by_dates_and_tags(results, photos):
    errors = 0
    notag = 0
    for photo in photos:
        if photo.date:
            if photo.tags:
                for tag in photo.tags:
                    if tag in results[photo.date]:
                        results[photo.date][tag] += 1
                    else:
                        results[photo.date][tag] = 1
            else:
                notag += 1
            results[photo.date]['No Tags'] = notag
        else:
            errors += 1
    print("Date unavailable for {} photos".format(errors))

def group_by_dates(results, photos):
    errors = 0
    for photo in photos:
        if photo.date:
            results[photo.date] += 1
        else:
            errors += 1

    results['Errors'] = errors

def main():
    params = {
            'city': 'Los Angeles',
            'start_date': '01-30-2012',
            'end_date': '02-01-2012',
            'tags' : 1,
            }
    results = get_photo_stats(params)
    pprint(results)

if __name__ == "__main__":
    main()
