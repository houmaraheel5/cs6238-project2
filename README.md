# cs6238-project2

sudo apt-get install libffi-dev
sudo apt-get install libssh-dev
sudo ln -s /usr/include/x86_64-linux-gnu/openssl/opensslconf.h
/usr/include/openssl/

## Client Installation
```
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

