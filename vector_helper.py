import chromadb
import chromadb.utils.embedding_functions as embedding_functions
import os
import pandas as pd
import re

class VectorStore:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.ef = None
        
        try:
            # Ensure chroma_db directory exists
            os.makedirs("chroma_db", exist_ok=True)
            
            # Initialize ChromaDB persistent client
            # This saves the database to the 'chroma_db' folder in the project directory
            self.client = chromadb.PersistentClient(path="chroma_db")
            print("✅ ChromaDB: Persistent client initialized at chroma_db/")
        except Exception as e:
            print(f"❌ ChromaDB: Failed to initialize persistent client: {e}")
            print("⚠️ Vector search will be disabled.")
            return
        
        # Setup Google Gemini Embedding Function
        if self.api_key:
            try:
                os.environ["GEMINI_API_KEY"] = self.api_key
                self.ef = embedding_functions.GoogleGeminiEmbeddingFunction(
                    model_name="models/embedding-001"
                )
                print("✅ ChromaDB: Google Gemini Embedding Function initialized.")
            except Exception as e:
                print(f"❌ ChromaDB: Error initializing embedding function: {e}")
                self.ef = None
        else:
            print("⚠️ ChromaDB: GEMINI_API_KEY missing. Vector search will not work.")

    def _sanitize_name(self, name):
        """Sanitize collection name for ChromaDB requirements."""
        # Must be 3-63 chars, alphanumeric/underscore/hyphen, no double dots
        name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        if len(name) < 3: name = name + "_chat"
        if len(name) > 63: name = name[:63]
        return name

    def index_chat(self, df, collection_name="whatsapp_chat"):
        """Index the chat messages into ChromaDB."""
        if not self.ef:
            return False
            
        collection_name = self._sanitize_name(collection_name)
            
        # Clear old collection if it exists to avoid mixing chats or duplicate data
        try:
            self.client.delete_collection(name=collection_name)
            print(f"🗑️ ChromaDB: Deleted existing collection: {collection_name}")
        except:
            pass
            
        collection = self.client.create_collection(
            name=collection_name, 
            embedding_function=self.ef
        )
        
        documents = []
        metadatas = []
        ids = []
        
        # Process each message as a document
        # Embed "user: text" so queries like "what did X say about …" match better
        for i, row in df.iterrows():
            user = str(row['user']).strip()
            if user == "group_notification":
                continue
            msg = str(row['message']).strip()
            if msg and len(msg) > 1 and msg != '<Media omitted>':
                documents.append(f"{user}: {msg}")
                metadatas.append({
                    "user": user,
                    "date": str(row['date'])
                })
                ids.append(f"msg_{i}")
        
        if not documents:
            print("⚠️ ChromaDB: No valid messages found to index.")
            return False

        # Add to collection in batches to avoid API/Memory limits
        batch_size = 100 
        for i in range(0, len(documents), batch_size):
            collection.add(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
        
        print(f"✅ ChromaDB: Indexed {len(documents)} messages into collection: {collection_name}")
        return True

    def search_chat(self, query, collection_name="whatsapp_chat", n_results=18, user_filter=None):
        """Semantic search; optional Chroma metadata filter when a single user is selected."""
        if not self.ef:
            return "Error: Embedding function not initialized."

        collection_name = self._sanitize_name(collection_name)
        where = None
        if user_filter and str(user_filter).strip() and str(user_filter).strip() != "Overall":
            where = {"user": str(user_filter).strip()}

        try:
            collection = self.client.get_collection(name=collection_name, embedding_function=self.ef)
            cnt = collection.count()
            if cnt == 0:
                return "(No messages indexed in Chroma for this upload.)"
            n_q = min(n_results, cnt)
            kwargs = {"query_texts": [query], "n_results": max(1, n_q)}
            if where:
                kwargs["where"] = where
            results = collection.query(**kwargs)

            formatted_context = []
            if results and results.get("documents") and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    doc = results["documents"][0][i]
                    meta = results["metadatas"][0][i]
                    formatted_context.append(f"[{meta['date']}] {doc}")

            if not formatted_context:
                scope = f" for user \"{user_filter}\"" if where else ""
                return f"(No matching chat lines found in semantic search{scope}.)"

            return "\n".join(formatted_context)
        except Exception as e:
            print(f"❌ ChromaDB: Search Error: {e}")
            return ""
