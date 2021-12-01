import base64

from api import bigquery_client


def upload_maze_impl(file_stream):
    user = 'test'
    filename = file_stream.filename
    content = file_stream.read()
    b64encoded = base64.b64encode(content).decode()

    query = f"""
    INSERT INTO third-upgrade-315803.maze.file
    VALUES ('{user}', '{filename}', '{b64encoded}')
    """
    bigquery_client.query(query)
