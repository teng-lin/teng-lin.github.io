import sys
import subprocess
import json
import re
import pandas as pd
from pandas import ExcelWriter


_id_offset_pattern = re.compile(u'id=(\d+)&offset=(\d+)')


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


def _parse_json(fileobj):
    data = json.load(fileobj, object_hook=_decode_dict)
    content = data['content']

    connections = []

    if 'connections' in content:
        if 'connections' in content['connections']:
            connections = content['connections']['connections']

    return connections


def get_id_offset(url):
    """
    parse id and offset from the url
    :param url:
    :return: id and offset as two element tuple
    """
    id = None
    offset = None
    match = re.search(_id_offset_pattern, url)

    if match:
        id = match.group(1)
        offset = match.group(2)

    return id, offset


def set_id_offset(url, id, offset):
    """
    change id and offset in url
    """
    new_url = re.sub(_id_offset_pattern, u'id=%s&offset=%s' % (id, offset), url)
    return new_url


def retrive_connection(cmd, id, offset):
    """
    Retreive connections for specific linkedin id from offset
    :param cmd: curl command as a list of string
    :param id: Linkedin id
    :param offset:

    :return: a list of connections

    Below is an example of the curl command copied from Chrome's developer tool
    curl_command = [
    "curl",
    'https://www.linkedin.com/profile/profile-v2-connections?id=14271099&offset=90&count=10&distance=1&type=INITIAL&_=1434080930325' ,
    "-H",
    'Cookie: bcookie="v=2&6789ccca-a705-4829-8306-6555c44011e5"; visit="v=1&M"; __qca=P0-341338068-1407868716823; VID=V_2014_10_31_02_1849;
    "-H",
    'DNT: 1',
    "-H",
    'Accept-Encoding: gzip, deflate, sdch',
    "-H",
    'Accept-Language: en-US,en;q=0.8',
    "-H",
    'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36',
    "-H",
    'Accept: text/plain, */*; q=0.01',
    "-H",
    'Referer:https://www.linkedin.com/profile/view?id=14271099&authType=NAME_SEARCH&authToken=ig21&locale=en_US&srchid=142710991434080925044
    "-H",
    'X-Requested-With: XMLHttpRequest' ,
    "-H",
    'Connection: keep-alive',
    "--compressed"
    ]

    """

    command = cmd[:]

    # modify url
    command[1] = set_id_offset(command[1], id, offset)

    print command[1]

    # run curl command and redirect response json to stdout
    proc = subprocess.Popen(command, stdout=subprocess.PIPE)
    proc.wait()

    return _parse_json(proc.stdout)


if __name__ == '__main__':
    bashCommand = sys.argv[1:]

    url = bashCommand[1]

    uid, offset = get_id_offset(url)

    all_connections = []
    offset = 0
    count = 10  # the number of connections is hard-coded to 10

    # call "unofficial" Linkedin API to retrieve all second degree connection of specific user
    while True:
        connections = retrive_connection(bashCommand, uid, offset)
        if len(connections) == 0:
            break
        all_connections.extend(connections)
        offset += count

    print "total number of connections: %d" % len(all_connections)

    excel = '%s.xlsx' % uid
    print "writing %s" % excel

    # Save all connections to excel spreadsheet
    df = pd.DataFrame(all_connections)
    writer = ExcelWriter(excel)
    df.to_excel(writer, 'Connection', index=False)
    writer.save()
