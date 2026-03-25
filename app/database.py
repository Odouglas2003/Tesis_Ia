# app/database.py
from pymongo import MongoClient
from config import Config

mongo_client = None


def get_mongo_client():
    global mongo_client
    if mongo_client is None:
        mongo_client = MongoClient(
            Config.MONGO_DB_CONNECTION_STRING,
            maxPoolSize=50,
            minPoolSize=10,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
        )
    return mongo_client


def get_db():
    return get_mongo_client()[Config.MONGO_DB_NAME]
