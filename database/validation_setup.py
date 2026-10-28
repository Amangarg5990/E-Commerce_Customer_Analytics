import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import logging
from pathlib import Path
from config.settings import BASE_DIR, DB_NAME, COLLECTION_NAME
from database.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


def apply_schema_validation(client=None, enforce_strict: bool = True):
    """
    Applies $jsonSchema validation to the MongoDB patients collection.
    If the collection does not exist, it creates it with the validator.
    If it exists, it uses 'collMod' to update the validator.
    """
    if client is None:
        client = get_mongo_client()

    db = client[DB_NAME]
    schema_path = BASE_DIR / "config" / "schema_validation.json"

    with open(schema_path, "r") as f:
        schema_config = json.load(f)

    validation_level = "strict" if enforce_strict else "moderate"
    validation_action = "error" if enforce_strict else "warn"

    existing_collections = db.list_collection_names()

    if COLLECTION_NAME not in existing_collections:
        logger.info(f"Creating collection '{COLLECTION_NAME}' with $jsonSchema validation...")
        db.create_collection(
            COLLECTION_NAME,
            validator=schema_config,
            validationLevel=validation_level,
            validationAction=validation_action,
        )
    else:
        logger.info(f"Collection '{COLLECTION_NAME}' already exists. Applying schema via collMod...")
        db.command({
            "collMod": COLLECTION_NAME,
            "validator": schema_config,
            "validationLevel": validation_level,
            "validationAction": validation_action,
        })

    # Create indexes for Customer 360 queries
    coll = db[COLLECTION_NAME]
    coll.create_index("customer_id", unique=True)
    coll.create_index("country")
    coll.create_index("last_purchase_date")
    coll.create_index("first_purchase_date")
    coll.create_index("total_orders_count")
    logger.info("Indexes created on customer_id, country, last_purchase_date, first_purchase_date, total_orders_count.")
    return True


if __name__ == "__main__":
    apply_schema_validation()
    print("Schema validation successfully applied.")

