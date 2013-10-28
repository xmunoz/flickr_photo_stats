#!/usr/bin/env python

import sqlite3
import calendar
import datetime
import os
from pprint import pprint
import threading
import Queue
import requests
import time

YAHOO_API_KEY = '42ce6cfc281462a7b1c079ebe428bf6b'
FLICKR_API_URL = 'http://api.flickr.com/services/rest'
YAHOO_API_URL = 'http://where.yahooapis.com/v1/places.q'
MAX_WORKER_THREADS = 5

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
    api_call_queue = Queue.Queue()

    for i in range(MAX_WORKER_THREADS):
        p = WorkerManager(api_call_queue, results)
        p.daemon = True
        p.start()

    for d in range(0, delta.days):
        start = start_date + datetime.timedelta(days = d)
        end = start + datetime.timedelta(days = 1)
        api_call_queue.put(WorkItem(city, start, end, lat, lon))


    # wait for all of the threads to finish working
    api_call_queue.join()

    return results


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
    return calendar.timegm(d.utctimetuple())

class WorkerManager (threading.Thread):
    def __init__(self, queue, results):
        threading.Thread.__init__(self)
        self.queue = queue
        self.results = results
    def run(self):
        while True:
            item = self.queue.get()
            key, val = item.make_api_call()
            self.results[key] = val
            self.queue.task_done()

class WorkItem:
    def __init__(self, city, start, end, lat, lon):
        self.city = city
        self.start = start
        self.end = end
        self.lat = lat
        self.lon = lon

    def make_api_call(self):
        params = {
                'method' : 'flickr.photos.search',
                'min_taken_date' : datetime_to_unix(self.start),
                'max_taken_date' : datetime_to_unix(self.end),
                'lat': self.lat,
                'lon': self.lon,
                'nojsoncallback': 1,
                'accuracy': 11,
                'api_key': YAHOO_API_KEY,
                'format': 'json',
            }
        r = requests.get(FLICKR_API_URL, params=params)
        key = datetime.datetime.strftime(self.start,'%B %d %Y')
        num_photos = r.json()['photos']['total']
        return key, num_photos

def main():
    pprint(get_photo_stats('London'))

if __name__ == "__main__":
    main()
