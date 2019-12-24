import json
import datetime
import time
import pandas as pd
import sqlite3

from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'hoge'
CORS(app)

@app.route('/', methods=['GET'])
def root():
    return 'test'

@app.route('/login', methods=['GET', 'POST'])
def login():
    data = json.loads(request.data.decode('utf-8'))
    conn = sqlite3.connect('api/static/aaa.sqlite3')
    result_table = pd.read_sql_query('SELECT * FROM registration reg where reg.name = "{}";'.format(data['user_name']), conn)
    result_table = result_table.query('password == "{}"'.format(data['password']))
    if len(result_table) > 0:
        expire = int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
        return jsonify({
            'token': True,
            'name': data['user_name'],
            'expire': expire
        })
    else:
        return jsonify({
            'token': False,
            'name': 'Guest',
            'expire': 0
        })

if __name__ == '__main__':
    app.debug = True

    host = '0.0.0.0'
    port = 8889
    host_port = (host, port)

    server = WSGIServer(
        host_port,
        app,
        handler_class=WebSocketHandler
    )
    server.serve_forever()
