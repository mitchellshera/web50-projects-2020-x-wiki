# Project 1
Web Programming with Python and JavaScript

Project 1 - Books (Python, Flask, SQL)

In this project, you’ll build a book review website. Users will be able to register for your website and then log in using their username and password. Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people. You’ll also use the a third-party API by Goodreads, another book review website, to pull in ratings from a broader audience. Finally, users will be able to query for book details and book reviews programmatically via your website’s API.

Start Up commands
$ pip3 install -r requirements.txt


$ set FLASK_APP=application.py


$ set DATABASE_URL=<DATABASE_URL>

$ flask run


To import Books data

$ python3 import.py

Features
User Registration
User registration is required in order to use web features. -register

Login
Registered user can login to web. -login

Search
Users can search for book by ISBN, Book Title or Book Author. -search

Search Result
Search Result shows result based on search criteria (ISBN, Title, Author, Year)-result

Book Details
Details page shows User Review Details (if already submitted by user), Goodreads Review Details section. Details page allows user to submit review only once. -resultbook

API Access
If users make a GET request to your website’s /api/ It returns resulting JSON a valid api or invalid.
