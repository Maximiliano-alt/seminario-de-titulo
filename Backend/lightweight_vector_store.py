"""
Lightweight Vector Store for production deployment with memory constraints.
This version is optimized for platforms like Render with limited memory.
"""

import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

class LightweightVectorStore:
    """
    A lightweight vector store that doesn't require heavy ML models.
    Falls back to simple text matching when memory is limited.
    """
    
    def __init__(self, use_embeddings=None):
        load_dotenv()
        
        # Check if we should use embeddings based on environment
        self.use_embeddings = use_embeddings
        if self.use_embeddings is None:
            # Default to False in production to save memory
            self.use_embeddings = os.getenv("USE_EMBEDDINGS", "false").lower() == "true"
        
        self.documents = []
        self.vector_store = None
        self.embeddings = None
        
        # Only initialize embeddings if explicitly enabled and we have enough memory
        if self.use_embeddings:
            try:
                self._initialize_embeddings()
            except Exception as e:
                print(f"Failed to initialize embeddings, falling back to text search: {e}")
                self.use_embeddings = False
    
    def _initialize_embeddings(self):
        """Initialize embeddings only when needed and memory allows."""
        try:
            # Try to use the lightest possible embedding model
            from langchain_huggingface import HuggingFaceEmbeddings
            
            # Use a very lightweight model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("Initialized lightweight HuggingFace embeddings")
            
        except ImportError:
            print("HuggingFace embeddings not available, using text search")
            raise
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
            raise
    
    def create_embeddings_from_dataset(self, dataset_path: str):
        """Load dataset and create searchable index."""
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            print(f"Loaded dataset with {len(dataset)} projects")
            
            # Prepare documents for search
            self.documents = []
            
            for project in dataset:
                project_name = project.get('project_name', 'Unknown')
                
                if 'stories' in project:
                    for story in project['stories']:
                        doc = {
                            'content': f"Project: {project_name}\nStory: {story['description']}\n" +
                                     "Acceptance Criteria:\n" + 
                                     "\n".join(f"- {criteria}" for criteria in story['acceptance_criteria']),
                            'metadata': {
                                'project_name': project_name,
                                'story_id': story.get('story_id', 'Unknown'),
                                'type': 'user_story'
                            }
                        }
                        self.documents.append(doc)
            
            print(f"Prepared {len(self.documents)} documents for search")
            
            # Only create vector embeddings if enabled and possible
            if self.use_embeddings and self.embeddings:
                try:
                    self._create_vector_index()
                except Exception as e:
                    print(f"Vector index creation failed, using text search: {e}")
                    self.use_embeddings = False
                    
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Create minimal fallback dataset
            self.documents = [
                {
                    'content': "Sample eCommerce user story: As a customer, I want to browse products so that I can find items to purchase.",
                    'metadata': {'type': 'user_story', 'project_name': 'Sample'}
                }
            ]
    
    def _create_vector_index(self):
        """Create vector index only if memory allows."""
        if not self.use_embeddings or not self.embeddings:
            return
            
        try:
            from langchain_community.vectorstores import FAISS
            
            texts = [doc['content'] for doc in self.documents]
            metadatas = [doc['metadata'] for doc in self.documents]
            
            self.vector_store = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            print("Created FAISS vector index")
            
        except Exception as e:
            print(f"Vector index creation failed: {e}")
            raise
    
    def search_similar(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents using vector search or text matching."""
        if not self.documents:
            return []
        
        # If vector search is available, use it
        if self.use_embeddings and self.vector_store:
            try:
                results = self.vector_store.similarity_search(query, k=k)
                return [{'page_content': doc.page_content, 'metadata': doc.metadata} for doc in results]
            except Exception as e:
                print(f"Vector search failed, falling back to text search: {e}")
        
        # Fallback to simple text matching
        return self._text_search(query, k)
    
    def _text_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Simple text-based search as fallback."""
        query_lower = query.lower()
        scored_docs = []
        
        for doc in self.documents:
            content_lower = doc['content'].lower()
            
            # Simple scoring based on word matches
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            
            # Calculate similarity score
            intersection = query_words.intersection(content_words)
            if query_words:
                score = len(intersection) / len(query_words)
            else:
                score = 0
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top k
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [
            {'page_content': doc['content'], 'metadata': doc['metadata']}
            for _, doc in scored_docs[:k]
        ]
    
    def load_vector_store(self, collection_name: str = "ecommerce_examples") -> bool:
        """Load existing vector store (not implemented for lightweight version)."""
        return False  # Always return False to force recreation 