#import classify as cl
#import fuzzy as fuzz
from flask import Flask, render_template, request, redirect, url_for, session
from flask.sessions import NullSession
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import os

try:
	os.remove("db.sqlite3")
	print("Old database removed. Training new database")
except:
	print('No database found. Creating new database.')
    
filenumber = 0
for file in os.listdir('saved_chats'):
    if file.endswith(".txt"):
        filenumber += 1

filenumber = filenumber+1

#saved chat in carebot as file.txt in folder saved_chats
file= open('saved_chats/'+str(filenumber)+'.txt',"w+")
file.write('bot : Hi There! I am a medical CareBot. You can begin conversation by typing in a message and pressing enter.\n')
file.close()
all_answer = list()

app = Flask(__name__)

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mhadb'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/')
def page():
    return render_template('home.html')
    
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' :
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE Username = %s AND Password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in accounts table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            # Redirect to home page
            return 'Logged in successfully!'
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    # Show the login form with message (if any)
    return render_template('login.html', msg=msg)

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/login.html/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))

# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/login.html/register.html', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
                # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO user VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
    # Show registration form with message (if any)
    return render_template('register.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/index.html')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        # User is loggedin show them the home page
        return render_template('index.html', username=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login.html'))

@app.route("/record_userText")
def get_userText():
    get_usertext= request.args.get('usertext')    
    appendfile= open('saved_chats/'+str(filenumber)+'.txt',"a")
    appendfile.write('user : '+get_usertext+'\n')
    appendfile.close()

    return "User Text Saved!"

@app.route("/record_botText")
def get_botText():
    get_bottext= request.args.get('bottext')
    print(get_bottext)
    appendfile= open('saved_chats/'+str(filenumber)+'.txt',"a")
    appendfile.write('bot : '+get_bottext+'\n')
    appendfile.close()

    return "Bot Text Saved!"

@app.route("/gets")

def get_bot_response():
    
    userText = request.args.get('msg')
    cl.train_data()
    cl.preprocess()
    classs = str(cl.classify(str(userText)))
    if classs == "test":
        response = "Please choose a specific type of test"
    else:
        response = classs   
    return response

@app.route("/fuzz")
def getFuzz():
    test = request.args.get('test')
    print(test)
    f = fuzz.fuzzyInput(all_answer[len(all_answer)-7],all_answer[len(all_answer)-6],all_answer[len(all_answer)-5],all_answer[len(all_answer)-4],all_answer[len(all_answer)-3],all_answer[len(all_answer)-2],all_answer[len(all_answer)-1],str(test))
    return fuzz.defuzz(next(iter(f.values())))


@app.route("/answer")
def getAnswer():
    ans = request.args.get('ans')
    try:
        all_answer.append(int(ans))
    except:
        print("here")
    print(all_answer)
    return str(ans)

#----------DISPLAY GRAPH--------------------

@app.route("/graph_stress.html")  
def graphstress(): 
 
    cursor = mysql.connection.cursor() 
    cursor.execute('SELECT * FROM stress') 
    # Fetch one record and return result 
    fetchdata = cursor.fetchall() 
 
    labels  = [row[1] for row in fetchdata] 
    values = [row[2] for row in fetchdata] 
 
    return render_template("graph_stress.html",labels=labels,values=values)

@app.route("/graph_anxiety.html")  
def graphanxiety(): 
 
    cursor = mysql.connection.cursor() 
    cursor.execute('SELECT * FROM anxiety') 
    # Fetch one record and return result 
    fetchdata = cursor.fetchall() 
 
    labels  = [row[1] for row in fetchdata] 
    values = [row[2] for row in fetchdata] 
 
    return render_template("graph_anxiety.html",labels=labels,values=values)

@app.route("/graph_depress.html")  
def graphdepress(): 
 
    cursor = mysql.connection.cursor() 
    cursor.execute('SELECT * FROM depression') 
    # Fetch one record and return result 
    fetchdata = cursor.fetchall() 
 
    labels  = [row[1] for row in fetchdata] 
    values = [row[2] for row in fetchdata] 
 
    return render_template("graph_depress.html",labels=labels,values=values)
    
#----------END NAVIGATION--------------------

if __name__ == "__main__":
    app.run(debug=True)
