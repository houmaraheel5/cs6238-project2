import os
import zipfile
import StringIO
import sqlite3
import hashlib
import datetime
import jinja2
import json
import OpenSSL
import shelve
from flask import Flask, g, request, redirect, url_for, session, escape, make_response
from werkzeug import secure_filename
from cryptography.fernet import Fernet
from functools import wraps

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(BASE_PATH, "db.db")
UPLOAD_FOLDER = os.path.join(BASE_PATH, "upload")

application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
application.secret_key = 'CHANGE THIS IN PRODUCTION'
application.debug = True

from tlsauth import CertAuthority
import flask_tlsauth as tlsauth

ca = CertAuthority('sub-ca')

users = ["Users"]

application.jinja_loader = jinja2.ChoiceLoader([
    application.jinja_loader,
    jinja2.FileSystemLoader(os.path.join(BASE_PATH,'templates')),
    ])

application.add_url_rule('/tlsauth/cert/', 'cert', tlsauth.renderCert(ca))
application.add_url_rule('/tlsauth/test/', 'test', tlsauth.testAuth)

def connect_to_database():
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
	db.row_factory = sqlite3.Row
        db.text_factory = sqlite3.OptimizedUnicode
    return db

def init_db():
    with application.app_context():
        db = get_db()
        with application.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_doc_uid(username, docname):
    m = hashlib.sha1(secure_filename(username + docname))
    return m.hexdigest()

def unauthorized_handler():
    return 'Unauthorized'

def login_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if dn in request.environ:
            return func(*args, **kwargs)
        else:
            return unauthorized_handler()
    return decorated

@application.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def is_owner(uid, document_id):
    SQL = "SELECT id from document WHERE id = ? AND owner_uid = ?;"
    parameters = (document_id, uid)
    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    if cur.fetchall():
        return True
    else:
        return False

def is_effective_owner(uid, document_id):
    SQL = "SELECT until from document_owner WHERE document_id = ? and uid = ?;"
    parameters = (document_id, uid)

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

def can_propagate_ownership(uid, document_id):
    SQL = "SELECT until from document_owner WHERE document_id = ? and uid = ? and propagate = ?;"
    parameters = (document_id, uid, True)

    cur = get_db().cursor()
    cur.execute(SQL, paramters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

def can_write(uid, document_id):
    SQL = "SELECT until, propagate FROM document_access WHERE document_id = ? AND uid = ? AND permission = ?;"
    parameters = (document_id, uid, "WRITE")

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

def can_propagate_write(uid, document_id):
    SQL = "SELECT until FROM document_access WHERE document_id = ? AND uid = ? AND permission = ? AND propagate = ?;"
    parameters = (document_id, uid, "WRITE", True)

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

def can_read(uid, document_id):
    SQL = "SELECT until, propagate FROM document_access WHERE document_id = ? AND uid = ? AND permission = ?;"
    parameters = (document_id, uid, "READ")

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

def can_propagate_read(uid, document_id):
    SQL = "SELECT until FROM document_access WHERE document_id = ? AND uid = ? AND permission = ? AND propagate = ?;"
    parameters = (document_id, uid, "READ", True)

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.utcnow():
            return True
    return False

@application.route('/')
def index():
    if 'dn' in request.environ:
        return 'Logged in as %s' % escape(request.environ["dn"])
    return 'You are not logged in'

@application.route('/check_out/<document_id>', methods=['GET'])
def check_out(document_id):
    # TODO: what happens if file does not exist?
    uid = request.environ['dn']
    if (is_owner(uid, document_id) or is_effective_owner(uid, document_id) or can_read(uid, document_id)):
        SQL = "SELECT * FROM document WHERE id = ?;"
        parameters = (document_id,)

        cur = get_db().cursor()
        cur.execute(SQL, parameters)
        result = cur.fetchone()
        result_file = bytes(result["file"])
        f = Fernet(result["key"])
        # TODO: catch decrypt exceptions
        result_file = f.decrypt(result_file)

        filename = result["file_name"]

        response = make_response(result_file)
        response.headers["Content-Disposition"] = "attachment; filename={0}".format(filename)
        return response
    else:
        return "Access denied"


@application.route('/check_in/<document_id>/<flag>', methods=['POST'])
@application.route('/check_in/<document_id>/', defaults={'flag': None}, methods=['POST'])
@application.route('/check_in/', defaults={'flag': None, 'document_id': None}, methods=['POST'])
def check_in(document_id, flag):
    if request.method == 'POST':
        file = request.files['file']
        if file:
            blob = file.read()
            uid = request.environ['dn']
            SQL = ""
            parameters = ()
            if document_id != None:
                if not (is_owner(uid, document_id) or is_effective_owner(uid, document_id) or can_write(uid, document_id)):
                    return "{0} can not check in {1}".format(uid, document_id)
                else:
                    SQL = "UPDATE document SET file = ?, key = ? WHERE id = ?;"
                    key = Fernet.generate_key()
                    f = Fernet(key)
                    blob = f.encrypt(blob)
                    parameters = (sqlite3.Binary(blob), key, document_id)
            else:
                if flag == "confidentiality":
                    confidentiality = True
                    integrity = False
                elif flag == "integrity":
                    integrity = True
                    confidentiality = False
                else:
                    integrity = False
                    confidentiality = False

                document_id = hashlib.sha1(secure_filename(request.environ['dn'] + file.filename)).hexdigest()
                filename = secure_filename(file.filename)
                key = Fernet.generate_key()
                f = Fernet(key)
                blob = f.encrypt(blob)
                SQL = "INSERT INTO document (id, integrity_flag, confidentiality_flag, owner_uid, file_name, file, key) VALUES (?, ?, ?, ?, ?, ?, ?);"
                parameters = (document_id, integrity, confidentiality, uid, filename, sqlite3.Binary(blob), key)

            db = get_db()
            cur = db.cursor()
            cur.execute(SQL, parameters)
            db.commit()
            return "{0}".format(document_id)
        else:
            return "Must submit a file"


@application.route('/delegate/<document_id>/', methods=['POST'])
def delegate(document_id):
    # TODO: read in until from text as datetime.datetime
    data = request.get_json()
    if 'client' in data:
        client = data['client']
    else:
        return "Must specify destination client"
    if 'permission' in data:
        permission = data['permission']
    else:
        return "Must specify permission type"
    if 'propagate' in data:
        propagate = data['propagate']
    else:
        propagate = False
    if 'until' in data:
        until = data['until']
    else:
        until = str(datetime.datetime.utcnow() + datetime.timedelta(days=30))
    uid = request.environ['dn']
    if permission.upper() == "READ":
        if (is_owner(uid, document_id) or is_effective_owner(uid, document_id) or can_propagate_read(uid, document_id)):
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO document_access (uid, document_id, until, permission, propagate) VALUES (?, ?, ?, ?, ?);", (client, document_id, until, permission, propagate))

            db.commit()
            return "Successfully delegated read access to {0} for {1}".format(document_id, client)
        else:
            return "{0} is not able to delegate read access to {1}".format(uid, document_id)
    elif permission.upper() == "WRITE":
        if (is_owner(uid, document_id) or is_effective_owner(uid, document_id) or can_propagate_write(uid, document_id)):
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO document_access (uid, document_id, until, permission, propagate) VALUES (?, ?, ?, ?, ?);", (client, document_id, until, permission, propagate))

            db.commit()
            return "Successfully delegated write access to {0} for {1}".format(document_id, client)
        else:
            return "{0} is not able to delegate write access to {1}".format(uid, document_id)
    elif permission.upper() == "OWNER":
        if (is_owner(uid, document_id) or can_propagate_ownership(uid, document_id)):
            db = get_db()
            cur = db.cursor()
            cur.execute("INSERT INTO document_owner (uid, document_id, until, propagate) VALUES (?, ?, ?, ?);", (client, document_id, until, propagate))

            db.commit()
            return "Successfully delegated ownership to {0} for {1}".format(document_id, client)
        else:
            return "{0} is not able to delegate ownership on {1}".format(uid, document_id)
    return "Unsuccessful"

@application.route('/safe_delete/<document_id>', methods=['GET'])
def delete(document_id):
    uid = request.environ['dn']
    if (is_owner(uid, document_id) or is_effective_owner(uid, document_id)):
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT id FROM document WHERE id = ?;", (document_id,))

        if cur.fetchone():
            cur.execute("DELETE FROM document where id = ?;", (document_id,))
            db.commit()
            return "Document deleted"
        else:
            return "Document ({0}) does not exist".format(document_id)
    else:
        return "Unauthorized"


@application.route('/get_entitlements/', methods=['GET'])
def get_entitlements():
    uid = request.environ['dn']
    db = get_db()
    result = []
    cur = db.cursor()
    cur.execute("SELECT id,owner_uid,file_name FROM document WHERE owner_uid = ?;", (uid,))
    for row in cur:
        temp = dict(row)
        temp["document_id"] = temp.pop("id")
        result.append(temp)
    cur.execute("SELECT document_id,permission,propagate,until FROM document_access WHERE uid = ?;", (uid,))
    for row in cur:
        if row["until"] > datetime.datetime.utcnow():
            result.append(dict(row))
    cur.execute("SELECT document_id,until FROM document_owner WHERE uid = ?;", (uid,))
    for row in cur:
        if row["until"] > datetime.datetime.utcnow():
            result.append(dict(row))
    return json.dumps({"status": "success", "entitlements": result})

@application.route('/get_users/', methods=['GET'])
def get_users():
    db = get_db()
    result = []
    cur = db.cursor()
    cur.execute("SELECT uid from users;")
    for row in cur:
        result.append({"uid": row["uid"], "name": row["short_name"]})
    return json.dumps({"status": "success", "users": result})

@application.route('/debug/')
@login_required
def debug():
    return str(request.environ)

@application.route('/register/<name>', methods=['GET'])
def register(name):
    # TODO: check if client already exists, so as not to generate duplicate certs
    with open(os.path.join(BASE_PATH, "sub-ca/public/root.pem"), "rb") as f:
        issuerCert = f.read()
        issuerCert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, issuerCert)

    with open(os.path.join(BASE_PATH, "sub-ca/private/root.pem"), "rb") as f:
        issuerKey = f.read()
        issuerKey = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, issuerKey)

    pkey = OpenSSL.crypto.PKey()
    pkey.generate_key(OpenSSL.crypto.TYPE_RSA, 1024)
    req = OpenSSL.crypto.X509Req()
    req.set_pubkey(pkey)
    fullname = {"C": "US", "ST": "Georgia", "L": "Atlanta", "O": "CS6238", "OU": "Project2", "CN": name}

    subj = req.get_subject()
    for (key, value) in fullname.items():
        setattr(subj, key, value)

    req.sign(pkey, "md5")

    cert = OpenSSL.crypto.X509()

    serial_save = shelve.open('serial.db')
    if serial_save.has_key("serial"):
        serial = serial_save["serial"]
    else:
        serial = 100

    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, "md5")

    outcert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    outkey = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, pkey)

    zip_file = StringIO.StringIO()
    archive = zipfile.ZipFile(zip_file, "w")
    archive.writestr("{0}.crt".format(name), outcert)
    archive.writestr("{0}.key".format(name), outkey)
    archive.close()

    response = make_response(zip_file.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=certificates.zip"

    serial_save["serial"] = serial + 1
    serial_save.close()

    db = get_db()
    cur = db.cursor()
    parameters = ('/C=US/CN={0}/L=Atlanta/O=CS6238/ST=Georgia/OU=Project2'.format(name), name)
    cur.execute("INSERT INTO users (uid, short_name) VALUES (?, ?);", parameters)
    db.commit()

    return response

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    application.run()
