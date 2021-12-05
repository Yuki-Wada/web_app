from google.cloud import bigquery

from flask import Flask
from flask_cors import CORS
from flask_sockets import Sockets

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'hoge'
CORS(app)

sockets = Sockets(app)

bigquery_client = bigquery.Client()
