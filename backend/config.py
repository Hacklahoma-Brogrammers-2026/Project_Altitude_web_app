from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Config(BaseModel):
    mongo_url: str = os.environ["MONGO_URL"]
    db_name: str = os.environ.get("MONGO_DB")
    embed_dim: int = int(os.environ.get("EMBED_DIM")) # type: ignore
    embedding_model: str = "text-embedding-3-small"

config = Config()