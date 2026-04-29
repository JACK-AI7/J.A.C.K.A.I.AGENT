import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class MemoryStore:
    """Long-term vector memory for JACK (Neural Archive)."""
    def __init__(self, persist_directory="vault/chroma_db"):
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a high-quality local embedding function
        # Default uses SentenceTransformer
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="jack_neural_archive",
            embedding_function=self.embedding_fn
        )

    def add(self, text, metadata=None):
        """Archive a fact or interaction."""
        import time
        doc_id = f"mem_{int(time.time() * 1000)}"
        
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        print(f"Memory Store: Archived interaction - {text[:60]}...")

    def search(self, query, k=3):
        """Retrieve relevant context from the archive."""
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
            
        return results['documents'][0]
