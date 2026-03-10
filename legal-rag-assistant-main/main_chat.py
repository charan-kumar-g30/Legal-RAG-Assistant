import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent
from tools import retrieve_legal_context

load_dotenv()

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

llm_config = {
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

def is_termination_msg(msg):
    return msg.get("content") and "TERMINATE" in msg["content"]

# Define the assistant agent
legal_assistant = AssistantAgent(
    name="LegalAssistant",
    system_message=(
        "You are a helpful legal assistant that retrieves relevant clauses from legal documents.\n" \
        "Please give summarised responses to user queries based on the legal context retrieved.\n" \
        "After answering the user query, always respond with 'TERMINATE' to end the chat."
    ),
    llm_config = llm_config
)

# Define the user proxy agent
user = UserProxyAgent(
    name="User",
    llm_config=False,
    human_input_mode="NEVER",  # auto-execution
    is_termination_msg = is_termination_msg,
    code_execution_config={"use_docker": False}
)


# Register the tool with both agents
legal_assistant.register_for_llm(
    name="retrieve_legal_context",
    description="Retrieve relevant legal context from the indexed legal documents based on the query."
)(retrieve_legal_context)

user.register_for_execution(
    name="retrieve_legal_context"
)(retrieve_legal_context)

if __name__ == "__main__":# Initiate the conversation
    user.initiate_chat(
        legal_assistant,
        message="Can I have a pet in the apartment?"
    )