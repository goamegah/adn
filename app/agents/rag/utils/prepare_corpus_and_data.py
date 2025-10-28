from google.auth import default
from google.api_core.exceptions import ResourceExhausted
from google.cloud import storage
import vertexai
from vertexai.preview import rag
import os
from dotenv import load_dotenv, set_key
import tempfile

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable not set. Please set it in your .env file."
    )

LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")
if not LOCATION:
    raise ValueError(
        "GOOGLE_CLOUD_LOCATION environment variable not set. Please set it in your .env file."
    )

BUCKET_NAME = "adn-chn-cicd-adn-agent-corpus-data"
CORPUS_DISPLAY_NAME = "adn-agent-corpus-regulation"
CORPUS_DESCRIPTION = "Corpus for the aide à la régulation project"
ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env"))

# Extensions de fichiers supportés par Vertex AI RAG
SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.html', '.json', '.csv']


# --- Functions ---
def initialize_vertex_ai():
    """Initialize Vertex AI with credentials."""
    credentials, _ = default()
    vertexai.init(
        project=PROJECT_ID, location=LOCATION, credentials=credentials
    )


def get_or_create_corpus():
    """Creates a new corpus or retrieves an existing one."""
    embedding_model_config = rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    )
    
    existing_corpora = rag.list_corpora()
    corpus = None
    
    for existing_corpus in existing_corpora:
        if existing_corpus.display_name == CORPUS_DISPLAY_NAME:
            corpus = existing_corpus
            print(f"Found existing corpus with display name '{CORPUS_DISPLAY_NAME}'")
            break
    
    if corpus is None:
        corpus = rag.create_corpus(
            display_name=CORPUS_DISPLAY_NAME,
            description=CORPUS_DESCRIPTION,
            embedding_model_config=embedding_model_config,
        )
        print(f"Created new corpus with display name '{CORPUS_DISPLAY_NAME}'")
    
    return corpus


def list_gcs_files(bucket_name, prefix=""):
    """List all files in a GCS bucket with optional prefix filter."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)
    
    files = []
    for blob in blobs:
        # Skip directories (blobs ending with /)
        if not blob.name.endswith('/'):
            # Filter by supported extensions
            _, ext = os.path.splitext(blob.name)
            if ext.lower() in SUPPORTED_EXTENSIONS:
                files.append(blob)
            else:
                print(f"Skipping unsupported file type: {blob.name}")
    
    return files


def download_gcs_file(bucket_name, blob_name, local_path):
    """Download a file from GCS to local path."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    blob.download_to_filename(local_path)
    print(f"Downloaded {blob_name} to {local_path}")


def upload_file_to_corpus(corpus_name, file_path, display_name, description):
    """Uploads a file to the specified corpus."""
    print(f"Uploading {display_name} to corpus...")
    try:
        rag_file = rag.upload_file(
            corpus_name=corpus_name,
            path=file_path,
            display_name=display_name,
            description=description,
        )
        print(f"✓ Successfully uploaded {display_name} to corpus")
        return rag_file
    except ResourceExhausted as e:
        print(f"✗ Error uploading file {display_name}: {e}")
        print("\nThis error suggests that you have exceeded the API quota for the embedding model.")
        print("Please see the 'Troubleshooting' section in the README.md for instructions on how to request a quota increase.")
        return None
    except Exception as e:
        print(f"✗ Error uploading file {display_name}: {e}")
        return None


def import_gcs_files_to_corpus(corpus_name, bucket_name, prefix=""):
    """Import all supported files from GCS bucket to RAG corpus."""
    print(f"\n=== Importing files from GCS bucket: {bucket_name} ===\n")
    
    # List files in GCS bucket
    gcs_files = list_gcs_files(bucket_name, prefix)
    
    if not gcs_files:
        print(f"No supported files found in bucket '{bucket_name}' with prefix '{prefix}'")
        return
    
    print(f"Found {len(gcs_files)} supported file(s) in GCS bucket\n")
    
    # Create temporary directory for downloads
    with tempfile.TemporaryDirectory() as temp_dir:
        successful_uploads = 0
        failed_uploads = 0
        
        for blob in gcs_files:
            try:
                # Create local file path
                local_filename = os.path.basename(blob.name)
                local_path = os.path.join(temp_dir, local_filename)
                
                # Download from GCS
                download_gcs_file(bucket_name, blob.name, local_path)
                
                # Upload to corpus
                result = upload_file_to_corpus(
                    corpus_name=corpus_name,
                    file_path=local_path,
                    display_name=local_filename,
                    description=f"Document imported from GCS: gs://{bucket_name}/{blob.name}"
                )
                
                if result:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                
                print()  # Add blank line between files
                
            except Exception as e:
                print(f"✗ Error processing {blob.name}: {e}\n")
                failed_uploads += 1
        
        print(f"\n=== Import Summary ===")
        print(f"Total files processed: {len(gcs_files)}")
        print(f"Successful uploads: {successful_uploads}")
        print(f"Failed uploads: {failed_uploads}")


def list_corpus_files(corpus_name):
    """Lists files in the specified corpus."""
    print(f"\n=== Files in corpus ===")
    files = list(rag.list_files(corpus_name=corpus_name))
    print(f"Total files: {len(files)}")
    for file in files:
        print(f"  - {file.display_name}")


def update_env_file(corpus_name, env_file_path):
    """Updates the .env file with the corpus name."""
    try:
        set_key(env_file_path, "RAG_CORPUS", corpus_name)
        print(f"\n✓ Updated RAG_CORPUS in {env_file_path}")
    except Exception as e:
        print(f"✗ Error updating .env file: {e}")


def main():
    """Main execution function."""
    print("=== Vertex AI RAG Corpus Setup ===\n")
    
    # Initialize Vertex AI
    initialize_vertex_ai()
    
    # Get or create corpus
    corpus = get_or_create_corpus()
    
    # Update .env file with corpus name
    update_env_file(corpus.name, ENV_FILE_PATH)
    
    # Import files from GCS bucket
    import_gcs_files_to_corpus(
        corpus_name=corpus.name,
        bucket_name=BUCKET_NAME,
        prefix=""  # Optional: specify a prefix to filter files, e.g., "documents/"
    )
    
    # List all files in corpus
    list_corpus_files(corpus_name=corpus.name)
    
    print("\n=== Setup Complete ===")


if __name__ == "__main__":
    main()