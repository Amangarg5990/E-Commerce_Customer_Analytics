import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config.settings import MONGO_URI, DB_NAME, COLLECTION_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_mongo_client(uri: str = MONGO_URI, timeout_ms: int = 5000) -> MongoClient:
    """Creates and returns a MongoClient instance, verifying connectivity."""
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms)
        # Verify connection
        client.admin.command("ping")
        logger.info(f"Successfully connected to MongoDB at {uri}")
        return client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def get_database(client: MongoClient = None):
    """Returns the database handle."""
    if client is None:
        client = get_mongo_client()
    return client[DB_NAME]


def get_customers_collection(client: MongoClient = None):
    """Returns the customers collection handle."""
    db = get_database(client)
    return db[COLLECTION_NAME]


if __name__ == "__main__":
    client = get_mongo_client()
    db = get_database(client)
    print("Database names:", client.list_database_names())

