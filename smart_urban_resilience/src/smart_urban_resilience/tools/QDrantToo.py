from crewai_tools import QdrantVectorSearchTool
from qdrant_client import QdrantClient

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)

# Define CrewAI Qdrant Tool
qdrant_tool = QdrantVectorSearchTool(
    name="DecentraSecVectorDB",
    qdrant_url="http://localhost:6333",
    collection_name="metadata_enrichment",
    embedding_model="text-embedding-3-small",  # or any supported model
    api_key=None  # if using cloud, include your API key
)
