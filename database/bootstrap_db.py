import os
import time
import sys
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.operations import SearchIndexModel

# Add backend to path to import config if not installed as package
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from config import config

load_dotenv()

MONGO_URI = config.mongo_url
DB_NAME = config.db_name
EMBED_DIM = config.embed_dim

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Create User collection
users = db["users"]
users.create_index("user_id", unique=True)
users.create_index([("username", ASCENDING)], unique=True)
users.create_index([("email", ASCENDING)], unique=True)

# create Contact collection
contacts = db["contacts"]
contacts.create_index([("contact_id", ASCENDING)], unique=True)
contacts.create_index([("owner_user_id", ASCENDING)])

# Create Contact Note collection
contact_notes = db["contact_notes"]
contact_notes.create_index([("note_id", ASCENDING)], unique=True)
contact_notes.create_index([("user_id", ASCENDING)])
contact_notes.create_index([("contact_id", ASCENDING)])
contact_notes.create_index([("user_id", ASCENDING), ("label", ASCENDING)], name="by_user_label")

# Create Contact Note Vector Embedding vector search index
index_name = "contact_note_vector_index"
model = SearchIndexModel(
    name=index_name,
    type="vectorSearch",
    definition={
        "fields":
            [
                {
                   "type": "vector",
                   "path":  "embedding",
                   "numDimensions": EMBED_DIM,
                   "similarity": "dotProduct",
                   "quantization": "scalar"
                },
                {
                    "type": "filter",
                    "path": "user_id"
                },
                {
                    "type": "filter",
                    "path": "contact_id"
                }
            ]
    }
)

result = contact_notes.create_search_index(model=model)
print("Polling...")
predicate = None
if predicate is None:
    predicate = lambda index: index.get("queryable") is True

while True:
    indices = list(contact_notes.list_search_indexes(result))
    if len(indices) and predicate(indices[0]):
        break
print(f"{result} is ready")
client.close()






