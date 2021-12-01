import json
import gevent

from api.models.ReversiGame import ReversiGame


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
