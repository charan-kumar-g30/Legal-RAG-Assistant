import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from autogen import AssistantAgent, register_function

load_dotenv()

# Load Azure OpenAI credentials and config from environment variables
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

# Define the assistant agent
legal_assistant = AssistantAgent(
    name="LegalAssistant",
    llm_config={
        "config_list": [
            {
                "api_key": AZURE_OPENAI_API_KEY,
                "base_url": AZURE_OPENAI_ENDPOINT,
                "api_type": "azure",
                "api_version": AZURE_OPENAI_API_VERSION,
                "model": "gpt-4o",  # Replace with your Azure deployment model name
            }
        ],
        "temperature": 0
    }
)

def retrieve_legal_context(query: str) -> str:
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_deployment=AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )

    db = FAISS.load_local("rag_faiss_store", embeddings, allow_dangerous_deserialization=True)
    docs = db.similarity_search(query, k=3)
    print(docs)
    return "\n\n".join([doc.page_content for doc in docs])

# ✅ Register it manually using function call style
register_function(
    retrieve_legal_context,
    caller=legal_assistant,
    executor=legal_assistant,
    description="Retrieve relevant legal context from the indexed legal documents based on the query."
)

# Test the function
if __name__ == "__main__":
    query = "Are the pets allowed in the property?"
    context = retrieve_legal_context(query)
    print("Retrieved Context:\n", context)
