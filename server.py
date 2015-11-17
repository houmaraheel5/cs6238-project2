import os
import sqlite3
import hashlib
import datetime
from flask import Flask, g, request, redirect, url_for, session, escape
import flask.ext.login as flask_login
from werkzeug import secure_filename

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(BASE_PATH, "db.db")
UPLOAD_FOLDER = os.path.join(BASE_PATH, "upload")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'CHANGE THIS IN PRODUCTION'
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class User(flask_login.UserMixin):
    pass

def connect_to_database():
    return sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
	db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_doc_uid(username, docname):
    m = hashlib.sha256(username + docname)
    return m.hexdigest()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

@app.teardown_appcontext
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

@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'

@app.route('/authenticate/', methods=['GET', 'POST'])
@app.route('/login/', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''

@app.route('/check_out/<document_id>')
@login_required
def check_out(document_id):
    pass

@app.route('/check_in/<document_id>/<flag>')
@app.route('/check_in/<document_id>/', defaults={'flag': None})
@login_required
def check_in(document_id, flag):
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(session['username'] + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # TODO: save metadata to DB

@app.route('/delegate/<document_id>/<client>/<permission>', methods=['GET', 'POST'],
           defaults={'propogate':False, 'until':None})
@login_required
def delegate(document_id, client, until, propogate):
    if request.method == 'POST':
        cur = get_db().cursor()
        SQL = "SELECT until FROM document_owner WHERE uid='{0}' and document_id = {1}"

@app.route('/safe_delete/')
@login_required
def delete():
    pass

@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
