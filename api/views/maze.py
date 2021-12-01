import json
import gevent
from api.models.train_maze import ValueIterTrainer, SarsaLambdaTrainer


def create_trainer(data):
    maze_text = data['maze'] if 'maze' in data else None
    if data['algorithm'] == 'valueiter':
        return ValueIterTrainer(
            warm_up_iter_count=data['warm_up_iteration'],
            iter_count=data['max_iteration'],
            max_steps=data['max_step'],
            gamma=data['gamma'],
            maze_text=maze_text,
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

            maze_text=maze_text,
        )


def visualize_maze_client(ws):
    ws.send(json.dumps({'status': 'start_connection'}))
    while not ws.closed:
        gevent.sleep(0.1)
        message = ws.receive()
        if message:
            recieved = json.loads(message)
            if recieved['status'] == 'initialize_trainer':
                trainer_config = recieved['config']
                if trainer_config['maze_exists']:
                    ws.send(json.dumps({'status': 'upload_maze'}))
                    message = ws.receive()
                    maze = message.decode()
                    trainer_config['maze'] = maze
                trainer = create_trainer(trainer_config)
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
