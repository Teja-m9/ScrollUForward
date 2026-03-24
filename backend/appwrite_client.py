from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.users import Users
from appwrite.services.storage import Storage
from config import APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY


def get_client() -> Client:
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    client.set_key(APPWRITE_API_KEY)
    return client


def get_databases() -> Databases:
    return Databases(get_client())


def get_users_service() -> Users:
    return Users(get_client())


def get_storage() -> Storage:
    return Storage(get_client())
