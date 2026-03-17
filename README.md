# Secure Email Agent Integration with Mask SDK

Contact: millingtonsully@gmail.com

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This repository provides a production-ready, open-source reference implementation demonstrating how to build a highly secure, privacy-first artificial intelligence agent. It showcases the integration of the [Mask SDK](https://github.com/maskaisolutions/mask) to protect Personally Identifiable Information (PII) before it is transmitted to cloud-based Large Language Models (LLMs), while simultaneously maintaining the agent's ability to execute external tools, such as the Gmail API, relying on that very same data.

The project demonstrates:
- **Zero-Config PII Detection:** Automatic identification of sensitive data using the Mask engine.
- **Transparent Detokenization:** Secure tool execution where the agent's logic remains unaware of the underlying encryption.
- **Privacy-Preserving Reasoning:** Enabling cloud-hosted LLMs to reason over tasks without access to raw PII.
- **Actual Tool Integration:** A real-world bridge to the Gmail API for sending secure emails.

---

## The Problem Space: LLM Data Leakage

When building agentic AI systems that interact with real-world tools, developers face a critical security paradox. Complex agents require LLMs to reason about task data, but transmitting unredacted PII (e.g., email addresses, phone numbers, social security numbers) to third-party model providers violates strict data privacy regulations like GDPR and HIPAA. 

The core vulnerability in standard agentic architectures is that sensitive data retrieved by users or tools is injected as plain-text directly into the LLM's context window.

Traditional redaction systems fail in agentic workflows because they permanently destroy the data. If an agent's objective is to send an email, redacting the target email address mathematically prevents the agent from completing its task.

## The Solution: Privacy by Design

This repository uses the Mask SDK to implement **Transparent Detokenization**.

Instead of trusting the LLM to safeguard plain-text data, the system strictly enforces cryptographic boundaries using **Just-In-Time (JIT) Encryption and Decryption Middleware**. 

1.  **Scanning and Tokenization:** User input is intercepted before reaching the LLM. The Mask SDK scans the text locally using its engine and replaces sensitive data with cryptographic tokens (e.g., replacing "info@example.com" with "tkn-12345"). The LLM only ever "sees" and reasons over scrambled, encrypted cyphertext.
2.  **LLM Processing:** The cloud provider (e.g., OpenAI, Anthropic) receives only the tokenized prompt. The LLM reasons over the query without ever seeing the raw PII.
3.  **Tool Execution:** When the LLM decides to call a specific authorized tool (e.g., `send_email`), a **Pre-Tool Decryption Hook** (`@secure_tool`) intercepts the call. It decrypts the specific parameters required by the tool, allowing the backend Gmail function to execute securely with real data.

This architecture guarantees that the cloud provider maintains zero knowledge of the sensitive data, while the agent retains 100% functional capability.

---

## Architectural Overview

### 1. The Core Agent (`agent.py`)
The primary orchestration script. It handles environment loading, Mask SDK initialization, LangGraph agent construction, and the secure tool definition.

### 2. The Email Client (`gmail_client.py`)
A wrapper class around the `google-api-python-client`. It manages the OAuth 2.0 flow and constructs the MIME messages required by the Gmail API.

### 3. The Configuration Templates
- `credentials.json.example`: A structural template indicating the expected format of the Google Cloud configuration file.
- `.env.example`: A template for configuring API keys and environment variables.

---

## Installation and Setup

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python package management. 

### 1. Install `uv`

If you haven't already, install `uv` by following the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Environment Configuration

Copy the provided configuration template:
```bash
cp .env.example .env
```
Open the newly created `.env` file and supply your API key. The application is designed to be model-agnostic. You may define `LLM_API_KEY` or `OPENAI_API_KEY`. 

### 3. Google Cloud Platform (Gmail API) Configuration

The `GmailClient` requires a valid OAuth 2.0 client configuration to authenticate and send emails on your behalf.

1.  Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Enable the "Gmail API".
3.  Navigate to **APIs & Services > OAuth consent screen**. Configure it as "Internal" or "External" and add the scope `https://www.googleapis.com/auth/gmail.send`.
4.  Navigate to **APIs & Services > Credentials**. Create an **OAuth client ID** (Desktop app).
5.  Download the resulting JSON file. Rename this file to exactly `credentials.json` and place it in the root directory.

### 4. Dependency Installation (with uv)

Ensure you have the Mask SDK and all other dependencies installed. Using `uv`, this is a single command that ensures environment consistency:

```bash
uv sync
```

This will create a virtual environment (if it doesn't exist) and install the exact versions specified in `uv.lock`, including:
- **`langchain-openai` / `langgraph`**: For agent orchestration.
- **`mask-privacy[spacy]`**: The core Mask SDK for PII detection and tokenization.
- **`google-api-python-client`**: For Gmail integration.

> [!NOTE]
> The `mask-privacy[spacy]` package includes the spaCy local ML engine for fast, local PII scanning. After installation, you must download a model: `uv run spacy download en_core_web_sm`.

---

## Quick Start: From Zero to Secure Agent

Follow these steps to see the Mask SDK in action:

1.  **Initialize Environment:** Run `uv sync` to install dependencies.
2.  **Configure API Keys:** Set up your `.env` and `credentials.json` as described above.
3.  **Run the Agent:**
    ```bash
    uv run agent.py
    ```
4.  **Authorize Gmail:** On the first run, a browser window will open. Sign in to your Google account and grant permission.
5.  **Observe the Magic:**
    - The agent receives a prompt containing PII (e.g., an email address and phone number).
    - **Step 1:** The Mask SDK scans the input locally and replaces PII with cryptographic tokens.
    - **Step 2:** The tokenized (secure) prompt is sent to the LLM.
    - **Step 3:** The LLM decides to send an email.
    - **Step 4:** The `@secure_tool` hook intercepts the call, decrypts the tokens, and passes real data to the Gmail API.
    - **Result:** An email is sent, but the LLM provider never saw the actual PII.

---

## Agent Execution

With `.env` and `credentials.json` in place, you may execute the agent:

```bash
python agent.py
```

1.  **First Run Authentication:** Upon initial execution, the script will halt and open a web browser. You must log in with your Google account and grant the application permission to send emails on your behalf.
2.  **Token Generation:** After authorization, the script will generate a `token.json` file in the root directory. Subsequent runs will not require browser authentication.
3.  **Audit Logs:** During execution, you will observe the standard output printing the exact, tokenized schema being sent to the LLM, followed by the decrypted fields being passed securely to the local Gmail client.

---

## Appendix: Advanced Architecture & Security Guarantees

### Substituting the LLM Provider

The agent is constructed utilizing LangChain and LangGraph, which abstracts the underlying language model. To migrate from OpenAI to an alternative provider (e.g., Anthropic or a local instance of Llama 3), you only need to modify the instantiation within `agent.py`.

**Example: Migrating to Anthropic**

1. Install the required package:
   ```bash
   pip install langchain-anthropic
   ```
2. Modify `agent.py`:
   ```python
   from langchain_anthropic import ChatAnthropic
   llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
   ```

### Security Considerations for Production

While this repository demonstrates a secure architectural pattern, deploying this software to a production environment requires additional hardening:

1.  **Credential Scope:** The provided `token.json` holds power over the authenticated Gmail account. In a server environment, rely on Google Cloud Service Accounts with Domain-Wide Delegation rather than user-level OAuth flows.
2.  **Key Rotation:** The `MASK_ENCRYPTION_KEY` should be managed via a secure vault (e.g., AWS KMS, HashiCorp Vault) and rotated periodically.
3.  **Audit Persistence:** The current implementation prints security audits to the standard output. For production, the `MaskCallbackHandler` should be configured to write to a secure, append-only centralized logging system for compliance verification.

---

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Mask AI Solutions
