from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mistral_api_key: str
    mistral_model: str = "mistral-small-latest"
    mistral_temperature: float = 0.1
    mistral_extraction_temperature: float = 0.0

    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3:latest"

    chroma_dir: str = "./chroma_db"
    chroma_collection: str = "bundestag"

    retrieval_k: int = 5
    retrieval_k_expanded: int = 12
    max_iterations: int = 2

    max_chunk_chars: int = 1500
    chunk_overlap_chars: int = 200

    gradio_port: int = 7860
    gradio_share: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings()
