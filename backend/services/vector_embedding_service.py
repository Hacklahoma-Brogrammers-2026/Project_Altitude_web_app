from langchain_openai import OpenAIEmbeddings
from backend.config import config

embeddings = OpenAIEmbeddings(
   model=config.embedding_model 
)

def get_vector_embedding(query: str) -> list[float]:
    vector = embeddings.embed_query(query)
    return vector