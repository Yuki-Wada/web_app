import json
import datetime
import pandas as pd
import sqlite3

from flask import request, jsonify

from api import app, sockets

from api.views.maze import visualize_maze_client
from api.views.reversi import play_reversi as play_reversi_impl

trainer = None


@app.route('/', methods=['GET'])
def root():
    return 'test'


@app.route('/login', methods=['GET', 'POST'])
def login():
    data = json.loads(request.data.decode('utf-8'))
    conn = sqlite3.connect('api/static/aaa.sqlite3')

    sql_command = f"""
    SELECT
        *
    FROM REGISTRATIOJ
    WHERE
        NAME = '{data['user_name']}' AND
        PASSWORD = 'data['password']'
    """
    result_table = pd.read_sql_query(sql=sql_command, con=conn)
    if len(result_table) > 0:
        expire = int(
            (datetime.datetime.now() +
             datetime.timedelta(
                days=1)).timestamp())
        json_data = {
            'token': True,
            'name': data['user_name'],
            'expire': expire
        }
        return jsonify(json_data)

    else:
        json_data = {
            'token': False,
            'name': 'Guest',
            'expire': 0
        }

    return jsonify(json_data)


@sockets.route('/train_maze')
def visualize_maze(ws):
    visualize_maze_client(ws)


@sockets.route('/play_reversi')
def play_reversi(ws):
    play_reversi_impl(ws)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8888
    keyfile = "data/ssl/server.key"
    certfile = "data/ssl/server.crt"

    import ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(certfile, keyfile)

    app.run(
        host=host,
        port=port,
        threaded=True,
        debug=True,
        ssl_context=context,
    )
