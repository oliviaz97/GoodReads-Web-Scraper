"""
Module handles all db related functions
"""
import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient


def connect_to_db():
    """
    Connects to database (library)
    :return: db, client
    """
    load_dotenv()
    client_string = os.getenv("CLIENT_STRING")
    client = MongoClient(client_string)
    db = client.library
    return db, client


def update_db_from_json(json_file, collection_name):
    """
    Updates the db by importing a json file
    Updates one collection at a time
    :param json_file: json file to write into db
    :param collection_name: collection to add docs into
    """
    client_string = os.getenv("CLIENT_STRING")
    client = MongoClient(client_string)
    db = client.library
    collection = None
    if collection_name == "books":
        collection = db.books
    elif collection_name == "authors":
        collection = db.authors
    else:
        return None # Unacceptable collection name
    insert_into_collection(json_file, collection)
    client.close()


def update_db_from_data(data, collection_name):
    """
    Updates the db by inserting one document (one dictionary object) into db
    Updates one document in one collection at a time
    :param data: dict to write into db
    :param collection_name: name of collection to add doc into
    """
    client_string = os.getenv("CLIENT_STRING")
    client = MongoClient(client_string)
    db = client.library
    collection = None
    if collection_name == "books":
        collection = db.books
    elif collection_name == "authors":
        collection = db.authors
    else:
        return None # Unacceptable collection name
    collection.insert_one(data)  # inserts one document into db.collection
    client.close()


def insert_into_collection(json_file, collection):
    """
    Reads from json file and inserts all the documents
    in the json file into the specified collection
    :param json_file: json file to write into db
    :param collection: collection to write into
    """
    # read json
    with open(json_file) as file:
        data = json.load(file)
    # insert all the docs
    collection.insert_many(data)


def export_from_collection(json_file, collection, filter):
    cursor = collection.find(filter, {'_id': 0})
    list_cur = list(cursor)
    with open(json_file, "a+") as write_file:
        json.dump(list_cur, write_file, indent=4)


def data_to_json(filename, data):
    """
    Dumps data into a json file
    :param filename: filename of the file to dump data into
    :param data: data to be dumped
    """
    with open(filename, "w+") as write_file:
        json.dump(data, write_file, indent=4)
