import os, json

from flask import Flask, render_template, request, redirect, flash , url_for , jsonify
from flask import session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from helpers import login_required
app = Flask(__name__)
Session(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



# Set up database
engine = create_engine(os.getenv ("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
app.secret_key=("bananas")


@app.route("/")
@login_required
def index():

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log user in """

    # Forget any user_id
    session.clear()

    username  = request.form.get("username")


    if request.method == "POST":


        if not request.form.get("username"):
            return render_template("error.html", message="must provide username")


        elif not request.form.get("password"):
            return render_template("error.html", message="must provide password")


        logquery = db.execute("SELECT * FROM usernames WHERE username = :username ",
                          {"username": username })

        result = logquery.fetchone()

        if result == None or not  request.form.get("password"):
            return render_template("error.html", message="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = result.id
        session["user_name"] = username

        # Redirect user to home page
        return redirect("/")

    # if User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    session.clear()
    session.pop('user_id', None)

    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Register user """
    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("error.html", message="must provide username")

        # Query database for username
        userChecker = db.execute("SELECT * FROM usernames WHERE username = :username",
                               {"username": request.form.get("username")}).fetchone()

        # Check if username already exist
        if userChecker:
            return render_template("error.html", message="username already exist")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="must provide password")

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return render_template("error.html", message="must confirm password")

        # Check passwords are equal
        elif not request.form.get("password") == request.form.get("confirmation"):
            return render_template("error.html", message="passwords didn't match")

        # Insert register into DB
        db.execute("INSERT INTO usernames (username, password) VALUES (:username, :password)",
		    {"username": request.form.get("username"),
                    "password": request.form.get("password")})

        # Commit changes to database
        db.commit()

        flash('Account created', 'info')

        # Redirect user to login page
        return redirect("/login")


    if request.method=="GET":
        return render_template("register.html")


@app.route("/search", methods=["GET"])
@login_required
def search():
    """ Get books results """

    # Check if book id was given
    if not request.args.get("book"):
        return render_template("error.html", message="you must provide a book.")

    # Take input and add a wildcard
    query = "%" + request.args.get("book") + "%"

    query = query.title()

    searchquery = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                      {"query": query})

    if searchquery.rowcount == 0:
        return render_template("error.html", message="we can't find books with that description.")
    books = searchquery.fetchall()

    return render_template("result.html", books=books)

@app.route("/book/<string:isbn>", methods=['GET', 'POST'])
@login_required
def book(isbn):
    """ Save user review and load the page with reviews."""

    if request.method == "POST":

        # Save current user info
        currentuser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        # Search book_id by ISBN
        bookidquery = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                         {"isbn": isbn})

        # Save id into variable
        rowans = bookidquery.fetchone()
        rowans= rowans[0]


        reviewsquery= db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND book_id = :book_id",{"user_id": currentuser,"book_id": rowans})


        if reviewsquery.rowcount == 1:
            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        # Convert to save into DB
        rating = int(rating)

        db.execute("INSERT INTO reviews (user_id, book_id, comment, rating) VALUES \
                    (:user_id, :book_id, :comment, :rating)",
                   {"user_id": currentuser,
                    "book_id": rowans,
                    "comment": comment,
                    "rating": rating})

        # Commit transactions to DB and close the connection
        db.commit()

        flash('Review submitted!', 'info')

        return redirect("/book/" + isbn)

    # Take the book ISBN and redirect to his page (GET)
    else:

        row = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                         {"isbn": isbn})

        bookInfo = row.fetchall()

        """ GOODREADS reviews """


        key = os.getenv("85NcYZmypAf5sisp0xBJgg")

        query = requests.get("https://www.goodreads.com/book/review_counts.json",params ={key: key, "isbns": isbn})

        # Convert the response to JSON
        res = query.json()
        res= res['books'][0]

        # Append it as the second element on the list. [1]
        bookInfo.append(res)

        """ Users reviews """

        # Search book_id by ISBN
        row = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                         {"isbn": isbn})

        # Save id into variable
        book = row.fetchone()  # (id,)
        book = book[0]

        # get book reviews
        results = db.execute("SELECT usernames.username, comment,rating \
                            FROM reviews \
                            INNER JOIN usernames \
                            ON user_id = reviews.user_id \
                            WHERE book_id = :book ",
                             {"book": book})

        reviews = results.fetchall()

        return render_template("resultbook.html", bookInfo=bookInfo, reviews=reviews)


@app.route("/api/<string:isbn>")
def book_api(isbn):
	# get the book value
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	if book is None:
		return render_template("404.html"), 404
	ratings = db.execute("SELECT count(*), AVG(rating) FROM books INNER JOIN reviews on books.id =reviews.book_id WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	average = 0
	count = 0
	if ratings.count > 0:
		average = ratings.avg
		count = ratings.count
	# res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "1joi2uk4Xi7Orewmw7RA", "isbns": book.isbn})
	# if res.status_code == 200:
	# 	data = res.json()
	# 	reviewdata = data['books'][0]
	# 	average = (count*average + reviewdata['work_ratings_count']*float(reviewdata['average_rating']))/(count+reviewdata['work_ratings_count'])
	# 	count += reviewdata['work_ratings_count']
	return jsonify(
		title= book.title,
		author= book.author,
		year= book.year,
		isbn= book.isbn,
		review_count= count,
		average_score= float(average)
	)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404