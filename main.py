"""
Main function and helpers
"""
import argparse
import os

from dotenv import load_dotenv
import settings

from db import update_db_from_json, data_to_json, connect_to_db
from scrape_authors import scrape_n_authors
from scrape_books import scrape_n_books


def main():
    """
    Main function that calls the scrape functions and updates db
    When real_time_update is on, update after every scraping
    Otherwise, update after all the scraping is done from json files
    """
    args = get_args()
    scrape_n_books(args.num_books, args.start_url, args.real_time)
    scrape_n_authors(args.num_authors, args.real_time)

    # Update after scraping
    # get path and store data in json
    if not args.real_time:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        books_path = os.path.join(curr_dir, "data", "books.json")
        authors_path = os.path.join(curr_dir, "data", "authors.json")
        data_to_json(books_path, settings.books)
        data_to_json(authors_path, settings.authors)

        update_db_from_json("books.json", "books")
        update_db_from_json("authors.json", "authors")


def restore_collections():
    """
    Restores db collections authors and books from json files
    """
    db, client = connect_to_db()
    books = db.books # creates new books collection
    authors = db.authors # creates new authors collection
    update_db_from_json("books.json", "books")
    update_db_from_json("authors.json", "authors")


def get_args():
    """
    Gets command line inputs from user
    :return: num_books, num_authors, start_url, real_time_update
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("num_books", type=int,
                        help="number of books to scrape")
    parser.add_argument("num_authors", type=int,
                        help="number of authors to scrape")
    parser.add_argument("start_url", help="url to start scraping from", type=str)
    parser.add_argument("--real_time", action="store_true",
                        help="whether to update database in real time (default: False)")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    load_dotenv()
    settings.init()
    main()
