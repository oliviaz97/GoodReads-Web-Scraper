"""
This module defines functions needed to scrape information about book authors from urls
Then store the data into json or db
"""
import os
from urllib.request import urlopen
from bs4 import BeautifulSoup
import settings
from db import update_db_from_data
from scrape_books import get_id, get_book_by_url

curr_dir = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.join(curr_dir, "logs", "scrape_authors_log.log")
LOG_FILE = open(log_path, "w+")


def scrape_one_author(index):
    """
    Scraps info about one author at settings.authors[index]
    name, author_url, author_id, rating, rating_count, review_count, image_url
    related_authors, author_books
    """
    global curr_url
    author = settings.authors[index]
    url = author["author_url"]
    curr_url = url

    try:
        page = urlopen(url)
    except:
        LOG_FILE.write("Error opening book url: " + url + "\n")  # log bad urls
        return None

    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    author["author_id"] = get_id(url)
    author["rating"] = get_author_rating(soup)
    author["rating_count"] = get_author_rating_count(soup)
    author["review_count"] = get_author_review_count(soup)
    author["image_url"] = get_author_image_url(soup, author["name"])
    author["related_authors"] = get_related_authors(soup)
    author["author_books"] = get_author_books(soup)

    if real_time:
        update_db_from_data(author, "authors")

    # If not real time, write into json after all the scraping, update db in main from json

    return author


def get_author_rating(soup):
    """
    Gets author rating
    :param soup: soup object
    :return: author rating as string
    """

    try:
        rating_tag = soup.find("span", class_="average")
        rating = rating_tag.contents[0]
    except:
        LOG_FILE.write("Error getting author rating at: " + curr_url + "\n")
        return ""
    return rating


def get_author_rating_count(soup):
    """
    Gets author rating count
    :param soup: soup object
    :return: author rating count as string
    """
    try:
        rating_count_tag = soup.find("span", itemprop="ratingCount")
        rating_count = rating_count_tag["content"]
    except:
        LOG_FILE.write("Error getting author rating count at: " + curr_url + "\n")
        return ""
    return rating_count


def get_author_review_count(soup):
    """
    Gets author review count
    :param soup: soup object
    :return: author review count as string
    """
    try:
        review_count_tag = soup.find("span", itemprop="reviewCount")
        review_count = review_count_tag["content"]
    except:
        LOG_FILE.write("Error getting author review count at: " + curr_url + "\n")
        return ""
    return review_count


def get_author_image_url(soup, name):
    """
    Gets author image url
    :param soup: soup object
    :param name: author name
    :return: author image url as string
    """
    try:
        image_url_tag = soup.find("img", alt=name)
        image_url = image_url_tag["src"]
    except:
        LOG_FILE.write("Error getting author image url at: " + curr_url + "\n")
        return ""
    return image_url


def get_related_authors(soup):
    """
    Gets a list of related authors urls
    :param soup: soup object
    :return: list of related authors
    """
    try:
        related_authors_tag = soup.find("a", text="Similar authors")
        path = related_authors_tag["href"]
        url = "https://goodreads.com" + path
        related_authors_soup = get_soup(url)
        author_name_tags = related_authors_soup.find_all("span", itemprop="name")
        related_authors = [] # list of related author urls

        for i in range(1, len(author_name_tags)):
            tag = author_name_tags[i]
            name = tag.contents
            author = if_author_exists(name)
            if not author:
                author = {"name": name}
                settings.authors.append(author) # create new entries for new authors
            author_url = get_author_url(tag)
            author["author_url"] = author_url
            if author not in related_authors: # avoid adding duplicate authors
                related_authors.append(author_url)

    except:
        LOG_FILE.write("Error getting related author at: " + curr_url + "\n")
        return []

    return related_authors


def get_soup(url):
    """
    Gets the soup (parsed html) from a url
    :param url: url to get soup of
    :return: soup of the given url
    """
    page = urlopen(url)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    return soup


def if_author_exists(name):
    """
    Checks if the author with the given name already exists in settings.author
    :param name: name of author
    :return: author object if exists, None otherwise
    """
    for author in settings.authors:
        if author["name"] == name:
            return author
    return None


def get_author_url(tag):
    """
    Gets author url
    :param tag: tag to get author url from
    :return: url of author as string
    """
    parent_tag = tag.parent
    return parent_tag["href"]


def get_author_books(soup):
    """
    Gets all the books written by this author
    :param soup: soup object
    :return: list of books written by the author
    """
    try:
        parents = soup.find_all("tr", itemtype="http://schema.org/Book")
        similar_books = []

        for parent in parents:
            tag = parent.find("span", itemprop="name")
            path = tag.parent["href"]
            url = "https://goodreads.com" + path
            # update settings.book
            book = get_book_by_url(url)
            if not book:
                book = {"book_url": url} # create new book object with url
                settings.books.append(book)

            similar_books.append(url)

    except:
        LOG_FILE.write("Error getting author books at: " + curr_url + "\n")  # log bad author books
        return []

    return similar_books


def scrape_n_authors(num_authors, real_time_update):
    """
    Scrapes num_authors number of authors
    Updates db after every scraping if real_time_update is on
    :param num_authors: number of authors to scrape
    :param real_time_update: whether or not db is updated after every scrape
    """
    global LOG_FILE
    global real_time
    real_time = real_time_update

    index = 0
    while index < num_authors:
        scrape_one_author(index)
        index += 1
