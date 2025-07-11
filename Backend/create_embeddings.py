from vector_store import VectorStore
import os

def main():
    # Get the absolute path to the dataset
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    dataset_path = os.path.join(project_root, "data", "datasetLLM.json")

    print("Creating embeddings from dataset...")
    
    # Create vector store
    vector_store = VectorStore()
    vector_store.create_embeddings_from_dataset(dataset_path)
    
    print("Embeddings created successfully!")
    
    # Test the vector store
    query = "How to implement user authentication?"
    print(f"\nTesting with query: {query}\n")
    
    results = vector_store.search_similar(query, k=3)
    print("Similar results:\n")
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(result.page_content)
        print()

if __name__ == "__main__":
    main() 