# Memory configuration placeholder
# CrewAI automatically uses ChromaDB when memory=True is set.
# This module can be expanded in the future for custom vector stores (e.g., Supabase pgvector)

def get_memory_config():
    """Returns memory configuration for the Crew."""
    return {
        "enabled": True,
        "provider": "chromadb",
        "persist_directory": "./.chroma_db"
    }
