import os
import sqlite3
import hashlib
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

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
	db.row_factory = sqlite3.Row
    return db

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

@app.route('/check_out/<document_uid>')
@login_required
def check_out(document_uid):
    pass

@app.route('/check_in/<document_uid>/<flag>')
@app.route('/check_in/<document_uid>/', defaults={'flag': None})
@login_required
def check_in(document_uid, flag):
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(session['username'] + file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # TODO: save metadata to DB

@app.route('/delegate/')
@login_required
def delegate():
    pass

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
