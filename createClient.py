import zipfile
import requests
import os
import argparse
import StringIO

BASEURL  = "https://vps.kylekoza.com/"
BASEDIR  = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser()
parser.add_argument('client')
args = parser.parse_args()
args = vars(args)

if not os.path.isdir(os.path.join(BASEDIR, args['client'])):
    os.mkdir(os.path.join(BASEDIR, args['client']))

with open('client.py', 'rb') as src:
    with open(os.path.join(BASEDIR, args['client'], 'client.py'), 'wb') as dest:
        dest.write(src.read())

os.chdir(os.path.join(BASEDIR, args['client']))

zip_file = StringIO.StringIO()
r = requests.get(BASEURL + "/register/" + args['client'], verify=False, stream=True)

for chunk in r.iter_content(16):
    zip_file.write(chunk)

archive = zipfile.ZipFile(zip_file, 'r')
archive.extractall()

os.symlink(args['client'] + ".crt", "client.crt")
os.symlink(args['client'] + ".key", "client.key")
