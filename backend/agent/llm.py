from langchain.chat_models import ChatOpenAI

def get_mistral_llm():
    return ChatOpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key="onYcoSEMsQRVRfrt7WfjQrwrMcKJ8HzE",
        model="mistral-large-latest",
        openai_api_base="https://api.mistral.ai/v1",
    )