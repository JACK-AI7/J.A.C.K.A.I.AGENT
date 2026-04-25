import os
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

class MemoryVault:
    """The 'Neural Archive' of JACK: A Vector DB for long-term memory (RAG)."""
    
    def __init__(self, persist_directory="vault/memory"):
        self.persist_directory = persist_directory
        if not os.path.exists(persist_directory):
            os.makedirs(persist_directory)
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use a local embedding function (default is Sentence Transformer)
        # For a high-tech agent, we might want a specific local model
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.client.get_or_create_collection(
            name="jack_longterm_memory",
            embedding_function=self.embedding_fn
        )

    def store_fact(self, fact: str, metadata: dict = None):
        """Store a fact in the neural archive."""
        # Generate a unique ID based on timestamp
        import time
        doc_id = f"fact_{int(time.time() * 1000)}"
        
        self.collection.add(
            documents=[fact],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        print(f"Memory Vault: Fact archived - {fact[:50]}...")

    def retrieve_relevant_facts(self, query: str, limit: int = 5):
        """Retrieve relevant context for a query."""
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        if not results['documents'] or not results['documents'][0]:
            return []
            
        return results['documents'][0]

    def reset_vault(self):
        """Wipe all long-term memory."""
        self.client.delete_collection("jack_longterm_memory")
        self.collection = self.client.get_or_create_collection(
            name="jack_longterm_memory",
            embedding_function=self.embedding_fn
        )

vault = MemoryVault()
