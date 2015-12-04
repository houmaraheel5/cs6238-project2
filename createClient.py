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
os.chdir(os.path.join(BASEDIR, args['client']))

zip_file = StringIO.StringIO()
r = requests.get(BASEURL + "/register/" + args['client'], verify=False)
zip_file.write(r.content)
archive = zipfile.ZipFile(zip_file, 'r')
archive.extractall()

#TODO: copy in client program
