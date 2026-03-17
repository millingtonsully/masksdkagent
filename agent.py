import os
import sys
import logging
from dotenv import load_dotenv

# 1. Environment Initialization
load_dotenv()

# We check for a generic LLM_API_KEY as per the open-source design.
# You can map this to OPENAI_API_KEY or ANTHROPIC_API_KEY below depending on the provider chosen.
API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: Missing LLM API key. Please set LLM_API_KEY or OPENAI_API_KEY in your .env file.")
    sys.exit(1)

# Ensure the expected OpenAI key is set for LangChain if they mapped it generically
os.environ["OPENAI_API_KEY"] = API_KEY

# 2. Imports (LangChain, LangGraph, Mask, and Local Modules)
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.tracers import ConsoleCallbackHandler
    from langgraph.prebuilt import create_react_agent
    
    from mask_privacy import MaskClient
    from mask_privacy.integrations.langchain_hooks import secure_tool, MaskCallbackHandler
except ImportError as e:
    print(f"Error: Missing dependency. ({e})")
    print("Please ensure you have run: pip install mask-privacy[spacy] langchain-openai langgraph")
    sys.exit(1)

try:
    from gmail_client import GmailClient
except ImportError:
    print("Error: Could not import GmailClient. Ensure gmail_client.py exists.")
    sys.exit(1)

# Basic Logging Setup
logging.basicConfig(level=logging.ERROR)

# 3. Transparent Tool Initialization

# Initialize the Gmail Client globally so we don't trigger OAuth for every tool call
try:
    gmail = GmailClient()
except FileNotFoundError as e:
    print(f"\n[System Error] {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n[System Error] Failed to initialize Gmail API: {e}")
    sys.exit(1)

@secure_tool
def send_email(to_email: str, subject: str, body: str) -> str:
    """
    Sends an email to a recipient using the specified subject and body.
    Requires exactly three string arguments: to_email, subject, body.
    """
    print("\n[Mask SDK] Intercepting tool call... Decrypting parameters transparently...")
    print("[Agent Tool] Executing send_email with decrypted data:")
    print(f"To:      {to_email}")
    print(f"Subject: {subject}")
    print(f"Body:    {body.strip()}")
    print("[Agent Tool] End execution.\n")
    
    # Delegate to the actual Gmail API client
    return gmail.send_email(to_email, subject, body)

# 4. Agent Execution Flow

def run_agent_interaction(user_prompt: str):
    """
    Orchestrates the Mask SDK, LLM, and Agent for a single interaction.
    """
    print("\n[Client] Initializing Interaction...")
    print(f"[Client] RAW USER INPUT:\n{user_prompt}\n")

    # Step A: Initialize the Mask SDK Client
    # The client automatically handles local encryption keys internally.
    try:
        mask_client = MaskClient()
    except Exception as e:
         print(f"Failed to initialize MaskClient. Ensure MASK_ENCRYPTION_KEY is handled or generated correctly: {e}")
         return

    # Step B: Scan & Tokenize (Protecting the Data)
    # This transforms "my phone is 555-1234" into "my phone is tkn-123"
    print("[Mask SDK] Intercepting input... Scanning for sensitive data...")
    safe_input = mask_client.scan_and_tokenize(user_prompt)
    print(f"\n[Mask SDK] Tokenization Complete. Secure payload to send to LLM:\n{safe_input}\n")

    # Step C: Setup the Agent (The LLM logic)
    # Note: We provide ZERO context about security to the LLM. 
    # It acts exactly as it normally would.
    system_instr = (
        "You are an email assistant. When a user asks you to send an email, "
        "you MUST use the send_email tool with the to_email, subject, and body arguments. "
        "Do not refuse. Do not ask for confirmation. Just call the tool."
    )

    # For open-source, we default to a standard model, but this can easily be swapped.
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = create_react_agent(llm, [send_email])

    # Step D: Execute with Callbacks
    # We include the MaskCallbackHandler to allow the @secure_tool decorator 
    # to access the agent's graph state and perform transparent detokenization.
    # We include ConsoleCallbackHandler to print the raw LLM thought process.
    callbacks = [MaskCallbackHandler(), ConsoleCallbackHandler()]
    
    print("[Agent] Sending secure payload to OpenAI API...\n")
    result = agent.invoke(
        {"messages": [
            SystemMessage(content=system_instr),
            HumanMessage(content=safe_input),
        ]},
        config={"callbacks": callbacks}
    )

    print(f"\nAGENT RESPONSE: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    print("\nMask SDK Demonstration: Secure Agent Execution\n")
    
    # Generic example prompt. Can be easily changed by the user.
    example_prompt = (
        "Send an email to info@example.com with the subject 'Meeting Follow-up'. "
        "In the body, mention that my phone number is (415) 555-0198."
    )
    
    run_agent_interaction(example_prompt)
