from api.route import app
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8888
    host_port = (host, port)

    server = WSGIServer(
        host_port,
        app,
        handler_class=WebSocketHandler,
        certfile='data/ssl/server.crt',
        keyfile='data/ssl/server.key',
    )
    server.serve_forever()
