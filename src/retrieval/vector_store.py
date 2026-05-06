from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import get_settings

_s = get_settings()


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=_s.embedding_model,
        base_url=_s.ollama_base_url,
    )


def get_vector_store() -> Chroma:
    return Chroma(
        collection_name=_s.chroma_collection,
        embedding_function=get_embeddings(),
        persist_directory=_s.chroma_dir,
    )
