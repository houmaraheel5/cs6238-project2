import os
import sqlite3
from flask import Flask, g, request, redirect, url_for, session, escape
from werkzeug import secure_filename

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(BASE_PATH, "db.db")
UPLOAD_FOLDER = os.path.join(BASE_PATH, "upload")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'CHANGE THIS IN PRODUCTION'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
	db.row_factory = sqlite3.Row
    return db

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
def check_out(document_uid):
    pass

@app.route('/check_in/<document_uid>/<flag>')
def check_in(document_uid, flag=None):
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


@app.route('/delegate/')
def delegate():
    pass

@app.route('/safe_delete/')
def delete():
    pass

@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
