import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        # Create a clean in-memory Chroma client per instance
        self.client = chromadb.Client(settings=Settings(allow_reset=True))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, ids, texts, embeddings):
        self.collection.add(documents=texts, ids=ids, embeddings=embeddings)

    def query(self, query_embedding, n_results=10):  # feel free to raise default
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents"]
        )

    def delete(self):
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception as e:
            print(f"[Warning] Failed to delete collection '{self.collection_name}': {e}")
