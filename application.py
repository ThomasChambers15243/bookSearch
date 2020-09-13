import os

import sys
import re
from bookLookup import bookSearchISBN, timeToReadBook
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import mkdtemp

from extraFuncs import alertErrors

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///pro.db")


####   MAIN PAGES   ###





@app.route("/")
def index():



    return redirect("/bookSearchISBN")



@app.route("/bookSearchISBN", methods=["GET","POST"])
def bookSearchISBN_MAINAPP():
    if request.method == "GET":
        return render_template("bookSearchISBN.html",  searchError=alertErrors("false", "none"))
    else:
        #bookISBN = "9780155658110"
        #"9780141187761" my copy of 1984

        if not request.form.get("bookISBN").isdecimal():
            return render_template("bookSearchISBN.html", searchError=alertErrors("true", "invalidFormat"))

        bookISBN = request.form.get("bookISBN").strip()

        if not bookSearchISBN(bookISBN):
            return render_template("bookSearchISBN.html", searchError=alertErrors("true", "noItems"))
        session["book_ISBN"] = bookISBN

        bookINFO = bookSearchISBN(bookISBN)

        session["book_details"] = bookINFO
        timeToRead = timeToReadBook(279, bookINFO["pageCount"])

        return render_template("resultsISBN.html", bookINFO=bookINFO, timeToRead=timeToRead)


##Handles saving a book to users account and inserting that book (if its new) to the bookDetailes table, all data passed from book search results##

@app.route("/userBooks", methods = ["GET", "POST"])
def userBooks():

    if request.method == "POST":
        if session.get("user_id"):

            #checks if the user has the book or not
            if len(db.execute("SELECT * FROM usersBooks WHERE user_id = :user_id and book_ISBN=:book_ISBN", user_id=session["user_id"], book_ISBN=session["book_ISBN"])) == 1:

                #if the user clicks save book with the option "read" selected AND the book is already in the state "to_read", then the state is updated. Else the users is returned to their account
                bookCheck = db.execute("SELECT * FROM usersBooks WHERE user_id = :user_id and book_ISBN=:book_ISBN", user_id=session["user_id"], book_ISBN=session["book_ISBN"])

                if request.form.get("saveBook") == "read" and bookCheck[0]["book_state"] == "to_read" :
                    print("hello")
                    db.execute("UPDATE usersBooks SET book_state = 'read' where user_id=:user_id and book_ISBN=:book_ISBN",user_id=session["user_id"], book_ISBN=session["book_ISBN"])
                else:
                    return redirect("/account")

            else:
                #Inserts the user and their book into the db usersBooks with whatever book_state they chose

                db.execute("INSERT INTO usersBooks (user_id, book_ISBN, book_state) VALUES (:user_id, :book_ISBN, :book_state)", user_id=session["user_id"], book_ISBN=session["book_ISBN"], book_state=request.form.get("saveBook"))

                #Check book isnt in bookDetails database

                isbnCheck = db.execute("SELECT ISBN FROM bookDetailes")
                if len(db.execute("SELECT ISBN FROM bookDetailes")) >= 1 :
                    ISBNcheck = db.execute("SELECT ISBN FROM bookDetailes")

                    for i in range(len(ISBNcheck)):

                        if ISBNcheck[i]["ISBN"] == session["book_ISBN"]:
                            return redirect("/account")

                    #INSERT new book INTO bookDetailes table

                db.execute("INSERT INTO bookDetailes VALUES(:ISBN, :title, :full_des, :page_count, :authors, :public_domain, :publisher, :language, :isEbook, :img)", ISBN=session["book_ISBN"], title=session["book_details"]["title"], full_des=session["book_details"]["fullDescription"], page_count=session["book_details"]["pageCount"], authors=session["book_details"]["author(s)"], public_domain=session["book_details"]["isInPublicDomain"], publisher=session["book_details"]["publisher"], language=session["book_details"]["language"], isEbook=session["book_details"]["isEBook"], img=session["book_details"]["img"])
            return redirect("/account")
        else:
            return redirect("/bookSearchISBN")

##Users Account##

@app.route("/account")
def account():
    #Check if user is logged in or not. If te session varible "loggin_in" is not set or set to false, the user will be return to the login in page and a error alert will be rendered
    if session.get("logged_in"):
        #Checks to see if acocunt has contents, if not returns account with error noContents
        if len(db.execute("SELECT * FROM usersBooks WHERE user_id=:user_id", user_id=session["user_id"])) < 1:
            return render_template("account.html", userId=session["user_id"], accountError=alertErrors("true","noContents"), contents=0)
        else:#return account with contents
            books = db.execute("SELECT book_ISBN FROM usersBooks WHERE user_id=:user_id", user_id=session["user_id"])
            bookDetails = [] # list of each row of details for each book
            userBook = []    # list of what the user has done with that book (book_state, rating, (time_to_read?) )

            #Loop through each user books and adds it to the list bookDetails and userBookd so bookDetails and userBooks can be past through to /account
            for i in range(len(books)):
                bookDetails.append(db.execute("SELECT * FROM bookDetailes WHERE ISBN=:ISBN", ISBN=books[i]["book_ISBN"]))
                userBook.append(db.execute("SELECT * FROM usersBooks WHERE book_ISBN=:ISBN and user_id=:user_id", ISBN=books[i]["book_ISBN"], user_id=session["user_id"]))
            contents = 1+i #number of books user has
            return render_template("account.html", userId=session["user_id"], accountError=alertErrors("false","none"), books=bookDetails, userBooks=userBook, contents=contents)
    else:
        return render_template("login.html", accountError=alertErrors("true", "notLoggedIn"))


##Sets the rating for the users books

@app.route("/rating",  methods = ["POST"])
def rating():
    db.execute("UPDATE usersBooks SET rating=:rating WHERE user_id=:user_id AND book_ISBN=:book_ISBN", rating=request.form.get("bookRating"), user_id=session["user_id"], book_ISBN=request.form.get("bookISBN"))
    return redirect("/account")



##Login in Page

@app.route("/login", methods = ["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        #Check email was subbmitted
        if not request.form.get("userEmail"):
            return render_template("login.html", accountError=alertErrors("true","emailMissing"))

        #Check password was subbmitted
        elif not request.form.get("password"):
            return render_template("login.html", accountError=alertErrors("true","passwordMissing"))

        userRows = db.execute("SELECT * FROM users WHERE user_email = :user_email", user_email=request.form.get("userEmail"))

        #Check users email and password match one in db pro
        if len(userRows) != 1 or not check_password_hash(userRows[0]["user_password"], request.form.get("password")):
            return render_template("login.html", accountError=alertErrors("true","passOrEmail"))
        #log user in
        session["user_id"] = userRows[0]["user_id"]
        session["logged_in"] = True
        return redirect("/account")

    else:
        return render_template("login.html", accountError=alertErrors("false", "none"))


##Logout Page##

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

##Register Page##

@app.route("/register", methods = ["GET", "POST"])
def register():

    #Just renderig the page
    if request.method == "GET":
        return render_template("register.html", accountError=alertErrors("false", "none"))
    else:
        #Checks if the email was submitted
        if not request.form.get("userEmail"):
            return render_template("register.html", accountError=alertErrors("true", "emailMissing"))

        userCheck = db.execute("SELECT user_email FROM users")

        for i in range (len(userCheck)):
            if request.form.get("userEmail") == userCheck[i]["user_email"]:
                print("ERROR: User_email already in db")
                return render_template("register.html", accountError=alertErrors("true","email"))

        if len(request.form.get("password")) < 8 or re.search('[0-9]', request.form.get("password")) is None or re.search('[A-Z]',request.form.get("password")) is None:
            return render_template("register.html", accountError=alertErrors("true","password"), typedEmail=request.form.get("userEmail"))

        password = generate_password_hash(request.form.get("password"))

        db.execute("INSERT INTO users (user_email, user_password) VALUES (:email, :password)", email=request.form.get("userEmail"), password=password)

        newUser = db.execute("SELECT user_id FROM users WHERE user_email = :email ", email=request.form.get("userEmail"))

        session["user_id"] = newUser[0]["user_id"]
        session["logged_in"] = True

        return redirect("/account")
