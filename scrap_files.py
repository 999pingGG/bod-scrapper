import json
from pathlib import Path
import hashlib
import logging
import re
import requests

base_url = 'http://bike.toyspring.com/getfile.php?f='

logging.root.setLevel(logging.INFO)
files = []

# There's not a lot of files available here.
for i in range(1, 1000):
    if i % 100 == 0:
        logging.info('Downloading file #' + str(i))

    response = requests.get(base_url + str(i))

    if not response.ok:
        continue

    filename = re.findall('filename="(.+)"', response.headers['Content-Disposition'])
    if filename:
        if len(filename) > 0:
            if len(filename) > 1:
                logging.warning('The Content-Disposition header had more than one quoted string: ' + str(filename))
            filename = filename[0]
        else:
            filename = str(filename)
    else:
        filename = str(i)

    filename_tokens = filename.split('.')
    if len(filename_tokens) > 1:
        extension = filename_tokens[len(filename_tokens) - 1]
    else:
        extension = None

    path = 'files/' + hashlib.sha1(response._content).hexdigest()
    if extension:
        path += '.' + extension

    Path(path).write_bytes(response._content)

    files.append({
        'id': i,
        'path': path,
        'name': filename,
    })

    logging.info('Downloaded ' + filename)

with open('files/index.json', "w") as outfile:
    outfile.write(json.dumps(files))
