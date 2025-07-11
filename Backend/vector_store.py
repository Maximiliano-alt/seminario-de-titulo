from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
import json
from dotenv import load_dotenv
import os
import chromadb
import tempfile

class VectorStore:
    def __init__(self, use_faiss=False, embedding_provider="sentence-transformers"):
        # Load environment variables
        load_dotenv()
        
        # Choose embedding provider
        if embedding_provider == "openai" and os.getenv("OPENAI_API_KEY"):
            try:
                self.embeddings = OpenAIEmbeddings()
                print("Using OpenAI embeddings")
            except Exception as e:
                print(f"Failed to initialize OpenAI embeddings: {e}")
                print("Falling back to SentenceTransformers")
                self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        else:
            # Use sentence transformers by default (no API key required)
            self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            print("Using SentenceTransformers embeddings (local, no API key required)")
            
        self.vector_store = None
        self.use_faiss = use_faiss
        
        # Create a persistent directory for vector store
        self.persist_directory = os.path.join(os.path.dirname(__file__), "vector_store")
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)

    def create_vector_store(self, texts, collection_name="code_examples"):
        # Split texts into chunks using RecursiveCharacterTextSplitter for better context handling
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ". ", " ", ""],
            chunk_size=1000,
            chunk_overlap=200
        )
        
        all_documents = []
        if isinstance(texts, list):
            for text in texts:
                if isinstance(text, str) and text.strip():  # Only process non-empty strings
                    chunks = text_splitter.split_text(text)
                    all_documents.extend(chunks)
        else:
            # Handle single text input
            if isinstance(texts, str) and texts.strip():
                all_documents = text_splitter.split_text(texts)
        
        if not all_documents:
            raise ValueError("No valid text chunks were generated")

        # Create vector store based on selected backend
        if self.use_faiss:
            self.vector_store = FAISS.from_texts(
                texts=all_documents,
                embedding=self.embeddings
            )
            # Save FAISS index
            self.vector_store.save_local(self.persist_directory)
        else:
            # Initialize ChromaDB client
            client = chromadb.PersistentClient(path=self.persist_directory)

            # Create vector store from all chunks
            self.vector_store = Chroma.from_texts(
                texts=all_documents,
                embedding=self.embeddings,
                client=client,
                collection_name=collection_name
            )

    def load_vector_store(self, collection_name="code_examples"):
        """Load an existing vector store"""
        if self.use_faiss:
            if os.path.exists(os.path.join(self.persist_directory, "index.faiss")):
                self.vector_store = FAISS.load_local(
                    self.persist_directory,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return True
        else:
            try:
                client = chromadb.PersistentClient(path=self.persist_directory)
                self.vector_store = Chroma(
                    client=client,
                    embedding_function=self.embeddings,
                    collection_name=collection_name
                )
                return True
            except Exception as e:
                print(f"Error loading vector store: {str(e)}")
        return False

    def create_embeddings_from_dataset(self, dataset_path):
        # Check if file exists
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")
            
        print(f"Reading dataset from: {dataset_path}")
        print(f"File size: {os.path.getsize(dataset_path)} bytes")
        
        try:
            # Try different approaches to read the file
            try:
                # First try: binary mode with explicit encoding
                with open(dataset_path, 'rb') as f:
                    content = f.read().decode('utf-8')
                    print(f"Successfully read file in binary mode")
            except UnicodeDecodeError:
                print("Binary read with UTF-8 failed, trying text mode...")
                # Second try: text mode with explicit encoding
                with open(dataset_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                print("Successfully read file in text mode")
            
            if not content.strip():
                raise ValueError("Dataset file is empty")
                
            dataset = json.loads(content)
            print(f"Successfully loaded JSON with {len(dataset)} projects")
            
            # Print project names for verification
            print("\nProjects found:")
            for project in dataset:
                print(f"- {project.get('project_name', 'Unknown')} ({len(project.get('stories', []))} stories)")
        
            # Prepare texts for embedding with enhanced metadata for eCommerce context
            texts = []
            metadatas = []
            
            for project in dataset:
                project_id = project.get('project_id', 'Unknown')
                project_name = project.get('project_name', 'Unknown')
                
                # Add project information
                project_text = f"Project: {project_name}\n"
                
                # Add stories with detailed eCommerce metadata
                if 'stories' in project:
                    for story in project['stories']:
                        story_id = story.get('story_id', 'Unknown')
                        
                        # Combine project info with story
                        story_text = project_text + f"Story: {story['description']}\n"
                        story_text += "Acceptance Criteria:\n"
                        for criteria in story['acceptance_criteria']:
                            story_text += f"- {criteria}\n"
                            
                        if 'related_classes' in story:
                            story_text += "Related Classes:\n"
                            for class_name in story['related_classes']:
                                story_text += f"- {class_name}\n"
                                
                        texts.append(story_text)
                        
                        # Add enhanced metadata for eCommerce context
                        metadata = {
                            "project_id": project_id,
                            "project_name": project_name,
                            "story_id": story_id,
                            "type": "user_story",
                            "domain": "eCommerce",
                            "content_type": "requirement"
                        }
                        metadatas.append(metadata)
                
                # Add UML diagrams if they exist
                if 'uml' in project:
                    try:
                        for uml in project['uml']:
                            story_id = uml.get('story_id', 'Unknown')
                            uml_text = project_text + f"UML Diagram for story {story_id}:\n{uml.get('plantuml_code', '')}\n"
                            texts.append(uml_text)
                            
                            # Add UML-specific metadata
                            metadata = {
                                "project_id": project_id,
                                "project_name": project_name,
                                "story_id": story_id,
                                "type": "uml",
                                "domain": "eCommerce",
                                "content_type": "design"
                            }
                            metadatas.append(metadata)
                    except Exception as e:
                        print(f"Warning: Error processing UML for project {project_id}: {str(e)}")
                
                # Add class implementations if they exist
                if 'classes' in project:
                    try:
                        for class_info in project['classes']:
                            file_name = class_info.get('file_name', 'Unknown')
                            class_text = project_text + f"Class {file_name}:\n{class_info.get('content', '')}\n"
                            texts.append(class_text)
                            
                            # Add class implementation metadata
                            metadata = {
                                "project_id": project_id,
                                "project_name": project_name,
                                "file_name": file_name,
                                "type": "class_implementation",
                                "domain": "eCommerce",
                                "content_type": "code",
                                "language": "java" if file_name.endswith(".java") else "javascript" if file_name.endswith(".js") else "unknown"
                            }
                            metadatas.append(metadata)
                    except Exception as e:
                        print(f"Warning: Error processing classes for project {project_id}: {str(e)}")
            
            print(f"\nProcessed {len(texts)} text chunks from dataset")
            
            # Create vector store from the prepared texts
            if not texts:
                raise ValueError("No text chunks were generated from the dataset")
                
            print("Creating vector store...")
            
            # Choose the vector store implementation based on configuration
            if self.use_faiss:
                self.vector_store = FAISS.from_texts(
                    texts=texts,
                    embedding=self.embeddings,
                    metadatas=metadatas
                )
                # Save FAISS index
                self.vector_store.save_local(self.persist_directory)
            else:
                # Initialize ChromaDB client
                client = chromadb.PersistentClient(path=self.persist_directory)
                # Create vector store from all chunks with metadata
                self.vector_store = Chroma.from_texts(
                    texts=texts,
                    embedding=self.embeddings,
                    metadatas=metadatas,
                    client=client,
                    collection_name="ecommerce_examples"
                )
                
            print("Vector store created successfully")
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {str(e)}")
            if 'content' in locals():
                print(f"First 100 characters of file: {content[:100]}")
            raise
        except Exception as e:
            print(f"Error processing dataset: {str(e)}")
            raise

    def search_similar(self, query, k=3, filter_criteria=None):
        """Search for similar documents with optional filtering"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        if filter_criteria:
            return self.vector_store.similarity_search(query, k=k, filter=filter_criteria)
        else:
            return self.vector_store.similarity_search(query, k=k)
            
    def search_similar_by_type(self, query, doc_type, k=3):
        """Search for similar documents by type (user_story, uml, class_implementation)"""
        filter_criteria = {"type": doc_type}
        return self.search_similar(query, k, filter_criteria)
    
    def search_similar_by_domain(self, query, domain, k=3):
        """Search for similar documents by domain"""
        filter_criteria = {"domain": domain}
        return self.search_similar(query, k, filter_criteria)
        
    def search_similar_code(self, query, language="java", k=3):
        """Search specifically for code examples in a given language"""
        filter_criteria = {"content_type": "code", "language": language}
        return self.search_similar(query, k, filter_criteria)
