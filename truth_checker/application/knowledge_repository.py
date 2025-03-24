"""Implementation of the knowledge repository using ChromaDB."""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

from truth_checker.domain.ports import KnowledgeRepository

logger = logging.getLogger(__name__)


class ChromaKnowledgeRepository(KnowledgeRepository):
    """Implementation of KnowledgeRepository using ChromaDB."""

    def __init__(
        self,
        collection_name: str = "truth_checker_kb",
        embedding_model_name: str = "BAAI/bge-base-en-v1.5",
        persist_directory: Optional[str] = None,
    ):
        """Initialize the knowledge repository.
        
        Args:
            collection_name: Name of the ChromaDB collection
            embedding_model_name: Name of the embedding model to use
            persist_directory: Directory to persist the database
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        self.persist_directory = persist_directory
        
        # Initialize embedding model
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=embedding_model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        # Initialize ChromaDB
        self.client = self._initialize_chroma_client()
        
        # Initialize Langchain's Chroma wrapper
        self.vector_store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embedding_model,
        )
        
        logger.info(f"Initialized ChromaKnowledgeRepository with collection: {collection_name}")
    
    def _initialize_chroma_client(self) -> chromadb.Client:
        """Initialize and return a ChromaDB client."""
        chroma_settings = Settings()
        
        if self.persist_directory:
            os.makedirs(self.persist_directory, exist_ok=True)
            return chromadb.PersistentClient(
                path=self.persist_directory,
                settings=chroma_settings
            )
        else:
            return chromadb.Client(settings=chroma_settings)
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search the knowledge repository.

        Args:
            query: The search query
            limit: Maximum number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        logger.info(f"Searching knowledge repository for: {query}")
        
        try:
            # Use similarity search from LangChain's Chroma implementation
            documents = await self.vector_store.asimilarity_search_with_relevance_scores(
                query, k=limit
            )
            
            # Format the results
            results = []
            for doc, score in documents:
                results.append({
                    "content": doc.page_content,
                    "relevance_score": score,
                    "metadata": doc.metadata,
                })
            
            logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge repository: {e}")
            return []
    
    async def add_document(self, document: Dict[str, Any]) -> str:
        """Add a document to the knowledge repository.

        Args:
            document: The document to add, should contain 'content' and 'metadata' keys

        Returns:
            ID of the added document
        """
        logger.info(f"Adding document to knowledge repository")
        
        try:
            content = document.get("content", "")
            metadata = document.get("metadata", {})
            
            # Generate a document ID if not provided
            doc_id = document.get("id") or f"doc_{len(metadata.get('source', ''))}"
            
            # Add the document to the vector store
            self.vector_store.add_texts(
                texts=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            logger.info(f"Added document with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document to knowledge repository: {e}")
            return ""
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add multiple documents to the knowledge repository.

        Args:
            documents: List of documents to add, each should contain 'content' and 'metadata' keys

        Returns:
            List of IDs of the added documents
        """
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_id = doc.get("id") or f"doc_{i}"
            
            texts.append(content)
            metadatas.append(metadata)
            ids.append(doc_id)
        
        try:
            self.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
            return ids
        except Exception as e:
            logger.error(f"Error adding multiple documents: {e}")
            return [] 