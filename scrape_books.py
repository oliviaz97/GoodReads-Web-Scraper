"""
This module defines functions needed to scrape information about books from urls
Then store the data into json or db
"""
import os
import re
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
import settings
from db import update_db_from_data

curr_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(curr_dir, "logs", "scrape_books_log.log")
LOG_FILE = open(log_path, "w+")


def get_id(url):
    """
    gets book_id (string) from url
    e.g. https://www.goodreads.com/book/show/<book_id>
    :param url:
    :return:
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    id_ = re.search("[0-9]+", path)
    id_ = id_.group()
    return id_


def get_next_book_url(index):
    """
    Gets url of next book in the list
    :param index: current index of book in the list
    """
    return settings.books[index]["book_url"]


def scrape_one_book(url):
    """
    Scrapes info of one book and the author (if doesn't exist already)
    info: book_url, title, book_id, isbn, author, author_url, rating, rating_count
    review_count, image_url, similar_books
    :param url: url of current book
    :return: None when exception, book object with scraped info otherwise
    """
    global CURR_URL
    CURR_URL = url
    global REAL_TIME

    try:
        page = urlopen(url)
    except:
        LOG_FILE.write("Error opening book url: " + url + "\n")  # log bad urls
        return None

    book = get_book_by_url(url)
    if book is None:
        book = {}
        settings.books.append(book)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    book["book_url"] = url
    book["title"] = get_title(soup)
    book["book_id"] = get_id(url)
    book["isbn"] = get_isbn(soup)

    author_names = get_author(soup)
    book["author"] = author_names  # list of author names of this book

    book_author_urls = get_author_url(soup)
    book["author_url"] = book_author_urls

    book["rating"] = get_book_rating(soup)
    book["rating_count"] = get_book_rating_count(soup)
    book["review_count"] = get_book_review_count(soup)
    book["image_url"] = get_book_image_url(soup)
    book["similar_books"] = get_similar_books(soup)  # list of urls of similar books

    # update global lists books and authors
    update_authors(author_names, book_author_urls)

    if REAL_TIME:
        update_db_from_data(book, "books")

    # If not real time, write into json after all the scraping, update db in main from json

    return book


def get_title(soup):
    """
    Extracts and processes book titles
    :param soup: soup object
    :return: title in string
    """
    try:
        title_tag = soup.find("h1", id="bookTitle")
        title = title_tag.contents[0]  # raw title between tags
        title = title.strip()  # remove leading and trailing spaces
    except:
        LOG_FILE.write("Error getting book title at: " + CURR_URL + "\n")
        return ""
    return title


def get_isbn(soup):
    """
    Extracts and processes book isbn's
    isbn could be "null"
    :param soup: soup object
    :return: isbn in string
    """
    try:
        isbn_tag = soup.find("meta", property="books:isbn")
        isbn = isbn_tag["content"]
    except:
        LOG_FILE.write("Error getting book isbn at: " + CURR_URL + "\n")
        return ""
    return isbn


def get_book_rating(soup):
    """
    Extracts and processes book ratings
    :param soup: soup object
    :return: rating in string
    """
    try:
        rating_tag = soup.find("span", itemprop="ratingValue")
        rating = rating_tag.contents[0]
        rating = rating.strip()  # removes leading and trailing newlines and whitespaces
    except:
        LOG_FILE.write("Error getting book rating at: " + CURR_URL + "\n")
        return ""
    return rating


def get_book_rating_count(soup):
    """
    Extracts book rating counts
    :param soup: soup object
    :return: book rating count in string
    """
    try:
        rating_count_tag = soup.find("meta", itemprop="ratingCount")
        rating_count = rating_count_tag["content"]
    except:
        LOG_FILE.write("Error getting book rating count at: " + CURR_URL + "\n")
        return ""
    return rating_count


def get_book_review_count(soup):
    """
    Extracts book review counts
    :param soup: soup object
    :return: book review count in string
    """
    try:
        review_count_tag = soup.find("meta", itemprop="reviewCount")
        review_count = review_count_tag["content"]
    except:
        LOG_FILE.write("Error getting book review count at: " + CURR_URL + "\n")
        return ""
    return review_count


def get_book_image_url(soup):
    """
    Extracts image url for this book
    :param soup: soup object
    :return: book image url in string
    """
    try:
        image_url_tag = soup.find("img", id="coverImage")
        image_url = image_url_tag["src"]
    except:
        LOG_FILE.write("Error getting book image url at: " + CURR_URL + "\n")
        return ""
    return image_url


def get_similar_books(soup):
    """
    Extracts similar books' urls
    :param soup: soup object
    :return: list of urls of similar books
    """
    try:
        related_work_tag = soup.find("div", id=re.compile("^relatedWorks"))
        similar_books_tags = related_work_tag.find_all("li", class_="cover")
    except:
        LOG_FILE.write("Error getting similar books at: " + CURR_URL + "\n")
        return []
    similar_books = []

    for tag in similar_books_tags:
        img_tag = tag.find("img")
        url_tag = img_tag.parent
        url = url_tag["href"]

        book = get_book_by_url(url)
        if book is None:
            book = {"book_url": url}  # create new book object if doesn't exist yet
            settings.books.append(book)  # Add new book to settings.books

        similar_books.append(url)

    return similar_books


def get_book_by_url(url):
    """
    Gets url of book from settings.book
    :param url: url of book
    :return: book object if exists, None otherwise
    """
    for book in settings.books:
        if book["book_url"] == url:
            return book
    return None


def get_author(soup):
    """
    Extracts and processes book's author and author_url
    :param soup:
    :return: list of authors (could have more than one author)
    """
    author_names = []

    try:
        author_tags = soup.find_all("span", itemprop="name")
        for tag in author_tags:
            author_name = tag.contents[0]
            author_names.append(author_name)
    except:
        LOG_FILE.write("Error getting author at: " + CURR_URL + "\n")
        return ""
    return author_names


def get_author_url(soup):
    """
    Extracts author urls from current book page
    Corresponds to entries in the author_names list
    :param soup: soup object
    :return: list of urls corresponding to authors in the list of authors
    """
    try:
        author_urls = []
        url_tags = soup.find_all("a", class_="authorName")

        for tag in url_tags:
            url = tag["href"]
            author_urls.append(url)
    except:
        LOG_FILE.write("Error getting  at: " + CURR_URL + "\n")
        return ""

    return author_urls


def update_authors(names, author_urls):
    """
    Creates author objects for new authors, updates his/her name and url
    Adds new authors and their corresponding urls to authors list
    :param names: names of authors
    :param author_urls: urls of authors
    """
    for i in range(0, len(names)):
        name = names[i]
        if if_new_author(name):
            new_author = {"name": name, "author_url": author_urls[i]}
            settings.authors.append(new_author)


def if_new_author(name):
    """
    Checks if the author is new (not in the authors list already)
    :param name: name of author
    :return: True if author exists in list, False otherwise
    """
    for author in settings.authors:
        if name == author["name"]:
            return False
    return True


def scrape_n_books(num_books, start_url, real_time_update):
    """
    Scrapes info of num_books books and their authors
    Updates db after every scraping if real_time_update is on
    :param num_books: number of books to be scraped
    :param start_url: url to start scraping from
    :param real_time_update: whether or not to update db after every scrape
    """
    global CURR_URL # keeps track of current url
    CURR_URL = ""
    global REAL_TIME
    REAL_TIME = real_time_update

    url = start_url
    index = 0
    # keep scraping until num books have been scraped
    while index < num_books:
        scrape_one_book(url)
        index += 1
        url = get_next_book_url(index)
