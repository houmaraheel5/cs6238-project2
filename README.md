# cs6238-project2
## Client Installation
```
sudo apt-get install python-m2crypto
pip install virtualenv
git clone https://github.com/kylekoza/cs6238-project2.git kozalummis
cd kozalummis
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

## Create a new client workspace
The client workspace will have a certificate, key, and client Python program
```
cd client
python clientClient.py <name>
cd <name>
```

## Client Instructions
The client application supports most operations, but does not allow you to
update an already existing file. You will also have to checkout and delegate
by document_id (a hash that is provided using the list function).
```
> python client.py -h
usage: client.py [-h] {checkout,list,checkin,delete,delegate} ...

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  {checkout,list,checkin,delete,delegate}
    checkout            Check out a document.
    list                List users and document ids.
    checkin             Check in a document.
    delete              Delete a document
    delegate            Delegate permissions to the document

> python client.py checkout -h
usage: client.py checkout [-h] document_id

positional arguments:
  document_id  The id of the document to check out.

> python client.py checkin -h
usage: client.py checkin [-h] [--flag {confidentiality,integrity}] document

positional arguments:
  document              Path to the document.

optional arguments:
  -h, --help            show this help message and exit
  --flag {confidentiality,integrity}

> python client.py list -h
usage: client.py list [-h] {documents,users}

positional arguments:
  {documents,users}  documents or users

> python client.py delete -h
usage: client.py delete [-h] document_id

positional arguments:
  document_id  The id of the document to delete.

> python client.py delegate -h
usage: client.py delegate [-h] [--time TIME] [--propagate]
                          document_id client_id {read,write,ownership}

positional arguments:
  document_id           The id of the document to delegate
  client_id             The id of the client to delegate to
  {read,write,ownership}

optional arguments:
  -h, --help            show this help message and exit
  --time TIME           Number of days to grant access
  --propagate           Can the user propagate the granted permission.
```

## Server Installation
### Prerequisites
```
sudo apt-get install libffi-dev libssl-dev nginx swig python-pip python-dev build-essential
sudo ln -s /usr/include/x86_64-linux-gnu/openssl/opensslconf.h /usr/include/openssl/
sudo useradd flask
```

As the new `flask` user, create a Python virtual environment in your home
folder and download the project.
```
pip install virtualenv
git clone https://github.com/kylekoza/cs6238-project2.git
cd kozalummis
virtualenv proj2
source proj2/bin/activate
pip install -r requirements.txt
```

### Create server certificates
```
cd server
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 365 -key ca.key -out ca.crt
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt
```

### Copy CA certificates to sub-ca for Python-tlsauth
```
cp ca.crt sub-ca/public/root.pem
cp ca.key sub-ca/private/root.pem
```

### Copy the nginx configuration to /etc/nginx/sites-available
`sudo cp server/nginx.conf /etc/nginx/sites-available/cs6238-project2`

### Enable the site
`sudo ln -s /etc/nginx/sites-available/cs6238-project2
/etc/nginx/sites-enabled/cs6238-project2`

### Copy cs6238.conf to /etc/init/
`sudo cp server/cs6238.conf /etc/init/`

## Start the server
```
sudo service cs6238 start
sudo service nginx start
```

## API Endpoints
See client.py and test.py for examples of the below endpoints.
### Register
```
Method: get
Authentication not required
Endpoint: /register/<name>
```
### List clients and client ids
```
Method: get
Authentication required
Endpoint: /get_users/
```
### List documents and document_ids available to you
```
Method: get
Authentication required
Endpoint: /get_entitlements/
```
### Checkin document
```
Method: post
Authentication required
```
#### Endpoints
To check in a document with a security flag:
`/check_in/<document_id>/<flag>`
`flag` must be either integirty, confidentiality, or none (default)

To check in a document with the default flag:
`/check_in/<document_id>/`

To check in a new document that has not yet been assigned a document_id:
`/check_in/`

All of these require the document to be posted as a file.
### Checkout document
```
Method: get
Authentication required
Endpoint: /check_out/<document_id>
```
### Delegate access
```
Method: post
Authentication required
Endpoint: /delegate/<document_id>/
```
This endpoint expects parameters posted in json format. 
```
Client: the client_id (can be obtained via /get_users/ endpoint
Propagate: true or false (default)
Until: A string representation of the time access should be revoked
(defaults to 30 days after access is granted)
Permission: READ, WRITE, OWNER
```
Example:
{"client": "<client_id>", "propagate": true, "until": "2015-12-09 23:04:04.261565", "permission": "READ"}
