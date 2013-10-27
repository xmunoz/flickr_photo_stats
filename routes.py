#! ~/Envs/mfa/flask/bin/python

'''
A proof-of-concept passwordless multi-factor authentications server.
Formerly an orchestra coding challenge.
'''

from flask import Flask, request, g, render_template
import sqlite3 as db_driver
import json
from utils.process import get_photo_stats

app = Flask(__name__)


def get_db():
    flask_db = getattr(g, '_database', None)
    if flask_db is None:
        flask_db = g._database = db_driver.connect('photo_stats.db')
    return flask_db

def close_db(conn, exception=None):
    flask_db = getattr(g, '_database', None)
    if flask_db is not None:
        conn.close()

@app.route('/', methods = ['GET', 'POST'])
def index():
    '''
    Landing page form or results.
    '''
    method_data = {
            'GET' : request.args,
            'POST': request.form
            }
    #TODO: add CSRF token to improve security.
    return _handle_request(method_data[request.method])

def _handle_request(params):
    conn = get_db()
    c = conn.cursor()
    if params:
        photo_stats = get_photo_stats(params['city'], params['start_date'], params['end_date'])
        close_db(conn)
        return render_template('results.html', data=photo_stats)
    else:
        close_db(conn)
        #load the page for the first time
        return render_template('input_form.html')

if __name__ == '__main__':
    app.run(debug = True)



