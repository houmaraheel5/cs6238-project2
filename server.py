import os
import sqlite3
import hashlib
import datetime
import jinja2
from flask import Flask, g, request, redirect, url_for, session, escape
from werkzeug import secure_filename
from cryptography.fernet import Fernet

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

application.add_url_rule('/tlsauth/register/', 'register', tlsauth.renderUserForm(ca), methods=("GET", "POST"))
application.add_url_rule('/tlsauth/cert/', 'cert', tlsauth.renderCert(ca))
application.add_url_rule('/tlsauth/test/', 'test', tlsauth.testAuth)

def connect_to_database():
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
	db.row_factory = sqlite3.Row
    return db

def init_db():
    with application.app_context():
        db = get_db()
        with application.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_doc_uid(username, docname):
    m = hashlib.sha256(username + docname)
    return m.hexdigest()

def unauthorized_handler():
    return 'Unauthorized'

@application.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def is_owner(uid, document_id):
    SQL = "SELECT id from document WHERE id = ? AND owner_id = ?;"
    parameters = (uid, document_id)
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
        if result["until"] > datetime.datetime.now():
            return True
    return False

def can_write(uid, document_id):
    SQL = "SELECT until, propagate FROM document_access WHERE document_id = ? AND uid = ? AND permission = WRITE;"
    parameters = (document_id, uid)

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.now():
            return True, result["propagate"] # This is going to return only the first propagate
    return False

def can_read(uid, document_id):
    SQL = "SELECT until, propagate FROM document_access WHERE document_id = ? AND uid = ? AND permission = READ;"
    parameters = (document_id, uid)

    cur = get_db().cursor()
    cur.execute(SQL, parameters)

    results = cur.fetchall()

    for result in results:
        if result["until"] > datetime.datetime.now():
            return True, result["propagate"] # This is going to return only the first propagate
    return False

@application.route('/')
def index():
    if 'dn' in request.environ:
        return 'Logged in as %s' % escape(request.environ["dn"])
    return 'You are not logged in'

@application.route('/check_out/<document_id>')
def check_out(document_id):
    # TODO: what happens if file does not exist?
    uid = request.environ['dn']
    if (is_owner(uid, document_id) or is_effective_owner(uid, document_id) or can_read(uid, document_id)):
        SQL = "SELECT * FROM document WHERE id = ?;"
        parameters = (document_id)

        cur = get_db().cursor()
        cur.execute(SQL, parameters)
        result = cur.fetchone()
        result_file = result["file"]
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
                    SQL = "INSERT INTO document (file, key) VALUES (?, ?) WHERE id = ?;"
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

                document_id = secure_filename(session['username'] + file.filename)
                filename = secure_filename(file.filename)
                SQL = "INSERT INTO document (id, integrity_flag, confidentiality_flag, owner_uid, file_name, file) VALUES (?, ?, ?, ?, ?, ?, ?);"
                # TODO: add encryption
                parameters = (document_id, integrity, confidentiality, uid, filename, sqlite3.Binary(blob))

            cur = get_db().cursor()
            cur.execute(SQL, parameters)
        else:
            return "Must submit a file"


# TODO: add ability to propagate and time limit
@application.route('/delegate/<document_id>/<client>/<permission>', methods=['GET', 'POST'],
           defaults={'propogate':False, 'until':None})
def delegate(document_id, client, until, propogate):
    if request.method == 'POST':
        pass

@application.route('/safe_delete/')
def delete():
    pass

@application.route('/debug/')
def debug():
    return str(request.environ)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        init_db()
    application.run()
