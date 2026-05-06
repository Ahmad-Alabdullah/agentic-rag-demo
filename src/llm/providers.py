from langchain_mistralai import ChatMistralAI

from config import get_settings

_s = get_settings()


def get_llm():
    return ChatMistralAI(
        model=_s.mistral_model,
        api_key=_s.mistral_api_key,
        temperature=_s.mistral_temperature,
    )


def get_llm_for_extraction():
    return ChatMistralAI(
        model=_s.mistral_model,
        api_key=_s.mistral_api_key,
        temperature=_s.mistral_extraction_temperature,
    )
