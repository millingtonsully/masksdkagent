# Secure, Multi-language Email Agent Integration with Mask SDK

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

#### Generating the MASK_ENCRYPTION_KEY
The Mask SDK requires a 256-bit encryption key to perform JIT encryption/decryption. You can generate a secure key using Python's `secrets` module:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Open your `.env` file and supply the following:
- `LLM_API_KEY`: Your OpenAI or Anthropic API key.
- `MASK_ENCRYPTION_KEY`: The 64-character hex string generated above.
- `MASK_LANGUAGES`: Set to `es,en` for Spanish support.

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
> The `mask-privacy[spacy]` package includes the spaCy local ML engine for fast, local PII scanning. After installation, you must download a model.
> 
> **Standard Users (pip):**
> `python -m spacy download en_core_web_sm`
> 
> **Fast Users (uv):**
> `uv add "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl"`

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

## Demonstration: Multilingual Spanish PII Protection

The following interaction demonstrates the Mask SDK successfully protecting complex Spanish-language identifiers in a real-world tool execution flow.

### 1. The Tokenized Prompt (Sent to LLM)
When the user provides a prompt in Spanish containing a **DNI** and a **phone number**, the LLM only ever receives the following secure payload:

> **Human:** Envía un correo a **tkn-91546cda@email.com** con el asunto 'Seguimiento de la reunión'. En el cuerpo, menciona que mi número de DNI es **[TKN-b5fb1a86]** y mi teléfono es **[TKN-f4aa24d5]**.

### 2. Transparent Detokenization (Local Tool Execution)
Despite only seeing tokens, the LLM correctly triggers the `send_email` tool because it LOOKS like the real info. The Mask SDK intercepts this call locally and restores the data just-in-time for the API call:

```text
[Mask SDK] Intercepting tool call... Decrypting parameters transparently...
[Agent Tool] Executing send_email with decrypted data:
To:      info@ejemplo.es
Subject: Seguimiento de la reunión
Body:    Menciona que mi número de DNI es 54362718X y mi teléfono es +34 612 345 678.
```

### 3. The "Zero-Knowledge" Guarantee
*   **Semantic Shape Preservation**: One of the Mask SDK's most powerful features is that it generates tokens that **match the semantic pattern** of the real data (e.g., an email token like `tkn-91546cda@email.com` or a DNI token like `[TKN-b5fb1a86]`). This ensures that the LLM's background knowledge and system instructions—which often expect specific string formats—remain 100% functional, preventing "halucination" or tool-call rejection.
*   **The "Double-Blind" Win**: 
    1.  **OpenAI** performed the reasoning (understanding the Spanish command) but **never saw** the real email or DNI.
    2.  **Gmail** performed the action (sending the email) but **never saw** the LLM's internal "thought process" about the tokens.
    3.  **The Bridge**: Only your **local machine** held the `MASK_ENCRYPTION_KEY` required to link the tokens back to the real PII.
*   **Realistic Localization**: The demonstration uses a valid Spanish DNI (`54362718X`) and a standard mobile format (`+34 612 345 678`) to show that the SDK handles locale-specific validation and checksums, not just basic pattern matching.

---

## Strategic Multilingual Support

The Mask SDK provides enterprise-class support for **8 major languages** by utilizing a language-aware 3-tier waterfall pipeline (Regex → Local NLP → Transformer).

### Configuration Matrix
To enable the multilingual resolver, you must configure the `MASK_LANGUAGES` environment variable. The following code in `agent.py` demonstrates the default for Spanish/English workflows:

```python
# Enable Spanish and English language support
os.environ["MASK_LANGUAGES"] = "es,en"
```

| Language | ISO Code | Script / Support Level |
| :--- | :--- | :--- |
| English | `en` | Full (Regex + NLP + Checksums) |
| Spanish | `es` | Full (Enhanced with `ñ` / `¿` / `¡` character sets) |
| French | `fr` | Full (Insee / Mod-97 validation) |
| German | `de` | Full (Post-Match Address Rules) |
| Turkish | `tr` | Full (TCID Kimlik validation + Plate rules) |
| Arabic | `ar` | Full (Unicode `\u0600-\u06ff` script heuristics) |
| Japanese | `ja` | Partial (Romanized surnames/place detection) |
| Chinese | `zh` | Partial (Romanized Pinyin surname detection) |

### Advanced: Tier 2 NLP Models (spaCy)

The SDK utilizes **spaCy** for context-aware detection. You can scale the performance vs. accuracy trade-off by selecting different model families.

| Family | Suffix | Accuracy | Speed | Memory |
| :--- | :--- | :--- | :--- | :--- |
| Small | `sm` | Standard | High | ~50MB |
| Medium | `md` | Enhanced | Medium | ~200MB |
| Large | `lg` | Professional| Low | ~500MB |
| Transformer| `trf` | State-of-the-art | Low | ~1GB+ |

**Installation Commands:**
- **Spanish:** `python -m spacy download es_core_news_sm`
- **French:** `python -m spacy download fr_core_news_sm`
- **German:** `python -m spacy download de_core_news_sm`

### Technical Core: Unicode Script-Heuristics
The internal `LanguageContextResolver` uses script-heuristics to detect locale-specific characters and automatically routes them to the correct regex and NLP registries. For instance, when it detects characters in the `\u0600-\u06ff` block, it automatically triggers the Arabic name and address handlers, even if `MASK_LANGUAGES="en"` is the only primary locale set.

---

## License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Mask AI Solutions
