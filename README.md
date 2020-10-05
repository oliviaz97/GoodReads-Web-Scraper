# Web Scraper

author: Olivia Zhang


### Description

Python script of a web scraper for GoodReads.com.

Scrapes the following information about books and authors:

Books: book_url, title, book_id, isbn, author, author_url, rating, rating_count, review_count, image_url, similar_books

Authors: name, author_url, author_id, rating, rating_count, review_count, image_url, related_authors, author_books

### Database
* The MongoDB database is used for the web scraper's data storage
* The database can be connected through MongoDB Atlas GUI or with PyMongo

### Tests
* Unit tests can be run for scrape_books.py, scrape_authors.py and db.py
* Please refer to the Manual Test Plan for how to test the scraper through the terminal as well as interactions with the database


### Documentation
* Module and function docstrings for all modules and functions