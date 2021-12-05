from api import bigquery_client


def select_bigquery_test():
    query = "SELECT name, count FROM `{0}.{1}.{2}` ".format(
        'third-upgrade-315803', 'babynames', 'names_2015')

    data = []
    rows = bigquery_client.query(query).result()
    for row in rows:
        data.append(dict([(key, row[key]) for key in row.keys()]))

    return data


def insert_bigquery_test():
    query = "INSERT INTO `{0}.{1}.{2}` (NAME, COUNT) VALUES ('Noah', 2)".format(
        'third-upgrade-315803', 'babynames', 'names_2015')
    bigquery_client.query(query)
