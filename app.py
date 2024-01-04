from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import time

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///database.db")




@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    
    if request.method == "GET":
        return render_template("login.html", page="login")
    
    username = request.form.get("username")
    password = request.form.get("password")

    if username == None or password == None:
        return render_template("login.html", error="Enter the details")
    
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
        return render_template("login.html", error="Invalid login details")
    
    session["user_id"] = rows[0]["id"]
    return redirect(url_for("index"))
    
    
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", error="")
    
    username = request.form.get("username")
    password1 = request.form.get("password")
    password2 = request.form.get("password_confirmation")
    
    #checking for invalid inputs
    if password1 != password2:
        return render_template("register.html", error="Enter the same password")
    
    print(username, password2)
    if username == None or password1 == None or password2 == None:
        return render_template("register.html", error="Enter the details")
    
    else:
        #checking if the username already exists
        existing_users = db.execute("SELECT username from users")
        existing_users_list = []
        for user in existing_users:
            existing_users_list.append(user["username"])
        if username in existing_users_list:
            return render_template("register.html", error="Username already exists")
        
        hashed = generate_password_hash(password1, method='pbkdf2', salt_length=16)

        #updating existing users in the database
        db.execute("BEGIN TRANSACTION")
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, hashed)
        db.execute("COMMIT")
        return redirect(url_for("login"))
    
    
    
    
@app.route("/inbox", methods=["GET", "POST"])
def inbox():
    if request.method == "GET":
        username = db.execute("SELECT username from users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        from_user_list = db.execute("SELECT * from messages WHERE receiver = ? ORDER BY time DESC", username)
        return render_template("inbox.html", page="inbox", from_details = from_user_list)


@app.route("/viewMail", methods=["POST"])
def viewMail():
    if request.method == "POST":
        message_id = request.form.get("mailID")
        mailDetails = db.execute("SELECT * from messages WHERE id = ?", message_id)
        mailDetails = mailDetails[0]
        return render_template("viewMail.html", page="inbox", mailDetails=mailDetails)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/index")
def index():
    if request.method == "GET":
        username = db.execute("SELECT username from users WHERE id = ?", session["user_id"])
        username = username[0]["username"]
        messages = db.execute("SELECT COUNT(message) from messages WHERE receiver = ?", username)
        users = db.execute("SELECT id, username from users")
        print(users)
        return render_template("index.html", messages = messages, page="index", user = username, users = users)
    
 
@app.route("/search_message", methods=["POST", "GET"])
def search_message():
    if request.method == "GET":
        return render_template("search_message.html", page="inbox")
    
    user = db.execute("SELECT username from users WHERE id = ?", session["user_id"])
    user = user[0]["username"]
    username = request.form.get("username")
    message = request.form.get("message")
    message = "%"+message+"%"
    
    if username != None or message != None:
        similar_messages = db.execute("SELECT * from messages WHERE subject LIKE ?", message)
        user_messages = db.execute("SELECT * from messages WHERE sender = ? AND receiver = ?", username, user)
    
    if user_messages == []:
        mails = similar_messages
    elif similar_messages == []:
        mails = user_messages

    mails = [x for x in similar_messages if x in user_messages]
    print(mails)
    
    return render_template("search_message.html", page = "inbox", mails=mails)


 
    
@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "GET":
        return render_template("search.html", page="search")
    
    sender = db.execute("SELECT username from users WHERE id = ?", session["user_id"])
    sender = sender[0]["username"]
    receiver = request.form.get("username")
    message = request.form.get("message")
    subject = request.form.get("subject")
    date_time = datetime.now()
    messages = db.execute("SELECT COUNT(message) from messages WHERE receiver = ?", sender)
    
    if subject == None or message == None:
        return render_template("search.html", page="search", error="Enter the subject and message")
    
    if sender == receiver:
        return render_template("search.html", page="search", error="User is currently logged in")

    #searching for the user in the database
    existing_users = db.execute("SELECT username from users")
    users = []
    for user in existing_users:
        users.append(user["username"])
    
    if receiver not in users:
        return render_template("search.html", page="search", error="User not found")
    
    if message == None or subject == None or receiver == None:
            return render_template("search.html", error="Enter the details", sent = "", page="search")
        
    db.execute("INSERT INTO messages (sender, receiver, message, time, subject) VALUES (?,?,?,?,?)", sender, receiver, message, date_time, subject)
    users = db.execute("SELECT id,username from users")
    return render_template("index.html", page="index", messages=messages, user=sender, users = users)
    


@app.route("/")
def login_default():
    session.clear()
    
    if request.method == "GET":
        return render_template("login.html")
    
    
    
    
    

if __name__ == "__main__":
     app.run(debug=True ,port=8080,use_reloader=False)