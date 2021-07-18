import json
import datetime
import time
import pandas as pd
import sqlite3

import gevent
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_cors import CORS
from flask_sockets import Sockets

from api.models.train_maze import ValueIterTrainer, SarsaLambdaTrainer
from api.models.play_reversi import ReversiGame

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'hoge'
CORS(app)
sockets = Sockets(app)

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
        expire = int((datetime.datetime.now() + datetime.timedelta(days=1)).timestamp())
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

def create_trainer(data):
    if data['algorithm'] == 'valueiter':
        return ValueIterTrainer(
            warm_up_iter_count=data['warm_up_iteration'],
            iter_count=data['max_iteration'],
            max_steps=data['max_step'],
            gamma=data['gamma'],
        )
    elif data['algorithm'] == 'sarsalambda':
        return SarsaLambdaTrainer(
            warm_up_iter_count=data['warm_up_iteration'],
            iter_count=data['max_iteration'],
            max_steps=data['max_step'],
            gamma=data['gamma'],

            alpha=data['alpha'],
            epsilon=data['epsilon'],
            lambda_value=data['lambda'],
        )

@sockets.route('/train_maze')
def train_maze(ws):
    ws.send(json.dumps({'status': 'start_connection'}))
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        if message:
            recieved = json.loads(message)
            if recieved['status'] == 'initialize_trainer':
                trainer = create_trainer(recieved['config'])
                ws.send(json.dumps({'status': 'trainer_construction'}))
            elif recieved['status'] == 'trainer_warm_up':
                trainer.warm_up()
                ws.send(json.dumps({'status': 'finish_warming_up'}))
            elif recieved['status'] == 'trainer_run':
                result = trainer.run()
                ws.send(json.dumps({
                    'status': 'step_maze',
                    'maze_color': result,
                }))


@sockets.route('/play_reversi')
def play_reversi(ws):
    ws.send(json.dumps({'status': 'start_connection'}))
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        if message:
            recieved = json.loads(message)
            if recieved['status'] == 'initialization':
                config = recieved['config']
                time_limit = config['time_limit']
                first_move = config['first_move']
                if first_move == 'player':
                    turn = 'player_turn'
                if first_move == 'cpu':
                    turn = 'cpu_turn'

                reversi_game = ReversiGame(time_limit)
                state = reversi_game.get_state()
                ws.send(json.dumps({
                    'status': turn,
                    'state': state,
                }))
            elif recieved['status'] == 'player_turn':
                place_stone = recieved['place_stone']
                if not reversi_game.can_place_stone(place_stone):
                    ws.send(json.dumps({
                        'status': 'illegal_position',
                    }))
                else:
                    state, done = reversi_game.player_turn(place_stone)
                    if done:
                        ws.send(json.dumps({
                            'status': 'game_finished',
                            'state': state,
                        }))
                    else:
                        if reversi_game.should_skip_turn():
                            turn = 'player_turn'
                            reversi_game.switch_turn()
                        else:
                            turn = 'cpu_turn'
                        ws.send(json.dumps({
                            'status': turn,
                            'state': state,
                        }))
            elif recieved['status'] == 'cpu_turn':
                state, done = reversi_game.cpu_turn()
                if done:
                    ws.send(json.dumps({
                        'status': 'game_finished',
                        'state': state,
                    }))
                else:
                    if reversi_game.should_skip_turn():
                        turn = 'player_skip'
                        reversi_game.switch_turn()
                    else:
                        turn = 'player_turn'
                    ws.send(json.dumps({
                        'status': turn,
                        'state': state,
                    }))
