from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import webview
import threading
from pyngrok import ngrok
import os

app = Flask(__name__, static_folder='./static', template_folder='./templates')
app.secret_key = 'many random bytes'

# MySQL configuration
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Admin@123'
app.config['MYSQL_DB'] = 'flaskcrudedb'
app.config['MYSQL_HOST'] = 'localhost'

# Initialize MySQL
try:
    mysql = MySQL(app)
    print("MySQL connection initialized successfully.")
except Exception as e:
    print(f"Error initializing MySQL connection: {e}")

# Google Sheets configuration
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
keyfile_path = 'C:\\Aman\\CRUDE_Python\\crud\\Keyfile.json'

if os.path.exists(keyfile_path):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key('1e5GFd2zGyuIrRV-wS3ziZWJvCw7IOoUd6SFtlAeaLgg').worksheet('Sheet1')
        print("Google Sheets connection initialized successfully.")
    except Exception as e:
        print(f"Error initializing Google Sheets connection: {e}")
else:
    raise FileNotFoundError(f"The keyfile was not found at path: {keyfile_path}")

@app.route('/')
@app.route('/page/<int:page>')
def Index(page=1):
    per_page = 10
    try:
        cur = mysql.connection.cursor()
        print("MySQL cursor initialized successfully.")
        offset = (page - 1) * per_page
        cur.execute("SELECT * FROM flasktable LIMIT %s OFFSET %s", (per_page, offset))
        data = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM flasktable")
        total = cur.fetchone()[0]
        cur.close()

        total_pages = total // per_page + (1 if total % per_page > 0 else 0)

        return render_template('index2.html', flasktable=data, page=page, total_pages=total_pages)
    except Exception as e:
        flash(f"Error: {e}", "error")
        return render_template('index2.html', flasktable=[], page=page, total_pages=1)

@app.route('/insert', methods=['POST'])
def insert():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM flasktable WHERE email=%s OR phone=%s", (email, phone))
            existing_record = cur.fetchone()

            if existing_record:
                flash("Email or phone number already exists. Please use a different email or phone number.", "error")
            else:
                cur.execute("INSERT INTO flasktable (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
                mysql.connection.commit()

                cur.execute("SELECT LAST_INSERT_ID()")
                last_id = cur.fetchone()[0]

                # Update Google Sheets
                sheet.append_row([last_id, name, email, phone])
                flash("Data Inserted Successfully", "success")

            cur.close()
        except Exception as e:
            flash(f"Error: {e}", "error")

        return redirect(url_for('Index'))

@app.route('/delete/<string:id_data>', methods=['GET'])
def delete(id_data):
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM flasktable WHERE id=%s", (id_data,))
        mysql.connection.commit()

        # Delete data from Google Sheets
        records = sheet.get_all_records()
        for idx, record in enumerate(records):
            if str(record.get('id')) == id_data:
                sheet.delete_rows(idx + 2)  # Adjust for header row
                break

        flash("Record Has Been Deleted Successfully")
        cur.close()
    except Exception as e:
        flash(f"Error: {e}", "error")

    return redirect(url_for('Index'))

@app.route('/update', methods=['POST', 'GET'])
def update():
    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE flasktable
                SET name=%s, email=%s, phone=%s
                WHERE id=%s
            """, (name, email, phone, id_data))
            mysql.connection.commit()

            # Update data in Google Sheets
            records = sheet.get_all_records()
            for idx, record in enumerate(records):
                if str(record.get('id')) == id_data:
                    sheet.update_cell(idx + 2, 2, name)  # Adjust for header row, column 2 for 'name'
                    sheet.update_cell(idx + 2, 3, email)  # Column 3 for 'email'
                    sheet.update_cell(idx + 2, 4, phone)  # Column 4 for 'phone'
                    break

            flash("Data Updated Successfully")
            cur.close()
        except Exception as e:
            flash(f"Error: {e}", "error")

        return redirect(url_for('Index'))

def start_ngrok():
    url = ngrok.connect(5000)
    print(f" * ngrok tunnel \"{url}\" -> \"http://127.0.0.1:5000/\"")

def start_server():
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=start_ngrok).start()
    threading.Thread(target=start_server).start()

    webview.create_window("My Web App", "http://127.0.0.1:5000")
    webview.start()



# from flask import Flask, render_template, request, redirect, url_for, flash
# from flask_mysqldb import MySQL
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import webview
# import threading
# from pyngrok import ngrok

# app = Flask(__name__, static_folder='./static', template_folder='./templates')
# app.secret_key = 'many random bytes'
# app.config['MYSQL_USER'] = 'root'                      # this is root username here
# app.config['MYSQL_PASSWORD'] = 'Admin@123'           # give the mysql database here
# app.config['MYSQL_DB'] = 'crudapplication'             # here create a database name in mysql workbench
# app.config['MYSQL_HOST'] = 'localhost'

# mysql = MySQL(app)

# # Google Sheets configuration
# scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# creds = ServiceAccountCredentials.from_json_keyfile_name('C://Aman//CRUDE_Python//crud//keyfile', scope)  # login into the google cloud and download json data and give path here
# client = gspread.authorize(creds)
# sheet = client.open_by_key('1e5GFd2zGyuIrRV-wS3ziZWJvCw7IOoUd6SFtlAeaLgg').worksheet('Sheet1')  # here give the google sheet key

# @app.route('/')
# @app.route('/page/<int:page>')
# def Index(page=1):
#     per_page = 10
#     cur = mysql.connection.cursor()
    
#     offset = (page - 1) * per_page
#     cur.execute("SELECT * FROM students LIMIT %s OFFSET %s", (per_page, offset))
#     data = cur.fetchall()
    
#     cur.execute("SELECT COUNT(*) FROM students")
#     total = cur.fetchone()[0]
#     cur.close()
    
#     total_pages = total // per_page + (1 if total % per_page > 0 else 0)
    
#     return render_template('index2.html', students=data, page=page, total_pages=total_pages)

# @app.route('/insert', methods=['POST'])
# def insert():
#     if request.method == "POST":
#         name = request.form['name']
#         email = request.form['email']
#         phone = request.form['phone']

#         # Check if email or phone already exists
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT * FROM students WHERE email=%s OR phone=%s", (email, phone))
#         existing_record = cur.fetchone()

#         if existing_record:
#             flash("Email or phone number already exists. Please use a different email or phone number.", "error")
#         else:
#             flash("Data Inserted Successfully", "success")
#             cur.execute("INSERT INTO students (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
#             mysql.connection.commit()

#             cur.execute("SELECT LAST_INSERT_ID()")
#             last_id = cur.fetchone()[0]

#             # Update Google Sheets
#             sheet.append_row([last_id, name, email, phone])

#         cur.close()

#         return redirect(url_for('Index'))

# @app.route('/delete/<string:id_data>', methods=['GET'])
# def delete(id_data):
#     flash("Record Has Been Deleted Successfully")
#     cur = mysql.connection.cursor()
#     cur.execute("DELETE FROM students WHERE id=%s", (id_data,))
#     mysql.connection.commit()

#     # Delete data from Google Sheets
#     records = sheet.get_all_records()
#     for idx, record in enumerate(records):
#         if str(record.get('id')) == id_data:
#             sheet.delete_rows(idx + 2)  # Adjust for header row
#             break

#     return redirect(url_for('Index'))

# @app.route('/update', methods=['POST', 'GET'])
# def update():
#     if request.method == 'POST':
#         id_data = request.form['id']
#         name = request.form['name']
#         email = request.form['email']
#         phone = request.form['phone']
#         cur = mysql.connection.cursor()
#         cur.execute("""
#                UPDATE students
#                SET name=%s, email=%s, phone=%s
#                WHERE id=%s
#             """, (name, email, phone, id_data))
#         flash("Data Updated Successfully")
#         mysql.connection.commit()

#         # Update data in Google Sheets
#         records = sheet.get_all_records()
#         for idx, record in enumerate(records):
#             if str(record.get('id')) == id_data:
#                 sheet.update_cell(idx + 2, 2, name)  # Adjust for header row, column 2 for 'name'
#                 sheet.update_cell(idx + 2, 3, email)  # Column 3 for 'email'
#                 sheet.update_cell(idx + 2, 4, phone)  # Column 4 for 'phone'
#                 break

#         return redirect(url_for('Index'))

# def start_ngrok():
#     url = ngrok.connect(5000)
#     print(" * ngrok tunnel \"{}\" -> \"http://127.0.0.1:5000/\"".format(url))

# def start_server():
#     app.run(debug=True, use_reloader=False)

# if __name__ == "__main__":
  
#     threading.Thread(target=start_ngrok).start()

#     threading.Thread(target=start_server).start()

#     webview.create_window("My Web App", "http://127.0.0.1:5000")
#     webview.start()
