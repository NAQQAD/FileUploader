from flask import *
import time
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import os
from wtforms.validators import InputRequired
from hashlib import sha512
import sqlite3 as sql

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'Files'

#Creating a database

conn = sql.connect('database.db')
#conn.execute('DROP TABLE links')
conn.execute('CREATE TABLE IF NOT EXISTS links (real_name TEXT, hashed_name TEXT, start_date TEXT , end_date TEXT, UNIQUE(real_name, hashed_name))')
conn.close()

"""
try:    
         with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("SELECT * from links")
            con.commit()
            date = cur.fetchall()
            print(date)
except:
         con.rollback()
         msg = "error in insert operation"

"""

# Configuring max file size
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

#Configuring the file extensions
allowed_extensions = ['jpg','png','pdf']

def check_file_extension(filename):
    return filename.split('.')[-1] in allowed_extensions

#Create a new file link
def create_file_link(filename):
    hashed_filename= sha512(secure_filename(filename).encode("utf-8"))
    try:    
         with sql.connect("database.db") as con:
            cur = con.cursor()
            cur.execute("INSERT INTO links (real_name,hashed_name,start_date,end_date) VALUES (?,?,datetime('now','localtime'),datetime('now','+1 minute','localtime'))",(secure_filename(filename),hashed_filename.hexdigest()[:5]))
            con.commit()
    except:
         con.rollback()
         msg = "error in insert operation"
    finally:
         return "127.0.0.1"+"\Files" +"\\"+ hashed_filename.hexdigest()[:5]


class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

@app.route('/', methods=['GET',"POST"])
@app.route('/home', methods=['GET',"POST"])
def home():
    session.pop('_flashes', None)
    form = UploadFileForm()
    if form.validate_on_submit():
        file = form.file.data # First grab the file
        if check_file_extension(file.filename):
           file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)),app.config['UPLOAD_FOLDER'],secure_filename(file.filename))) # Then save the file
           FileLink = create_file_link(file.filename)
           return render_template('result.html', FileLink = FileLink[-11:])
        else:
           flash("File extension is incorrect! Please try again!")
           return render_template('error.html')
           

    return render_template('index.html',form=form)

@app.route('/Files/<path:FileLink>', methods=['GET', 'POST'])
def download(FileLink):
    print(app.root_path)
    full_path = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
    print(full_path)
    try:    
         with sql.connect("database.db") as con:
            cur = con.cursor()
            FileLink = FileLink
            cur.execute("SELECT real_name FROM links WHERE hashed_name=:FileLink AND datetime('now','localtime') < end_date",{"FileLink": FileLink})
            con.commit()
            filename = cur.fetchone()[0]
    except:
         con.rollback()
         msg = "error in insert operation"
    finally:
        is_local_var = "filename" in locals()
        if is_local_var:
            return send_from_directory(full_path, filename,as_attachment=True)
        else:
            flash("This file has expired, it is no more available!")
            cur.execute("SELECT real_name FROM links WHERE hashed_name=:FileLink",{"FileLink": FileLink})
            con.commit()
            filename_to_delete = cur.fetchone()[0]
            os.remove(full_path+"\\"+filename_to_delete)
            cur.execute("DELETE FROM links WHERE datetime('now','localtime') > end_date")
            con.commit()
            return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=False)


