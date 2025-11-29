### Project Name: User_Assistant_Agent

### Problem Statement  
Most personal AI assistants (ChatGPT, Claude, Gemini, etc.) can answer questions and write emails, but they are "blind" to our real digital life. They can't read our Gmail, search our Google Drive files, check our calendar, or search google for user specific information because they have zero access to our personal data and tools.
As a result, when you ask “List down today's mail” or “Create a doc and share it with the team”, the assistant either hallucinates, gives generic advice, or tells you to do it manually.
This creates a huge gap between what an AI could do for us and what it actually does today. We want a single, trustworthy agent that can securely act across all our personal productivity tools with the same ease as a human assistant.

The goal: a single, secure, always-on agent that can actually act across Local Directory, Gmail, Google Drive, Docs, Calendar, and web search using nothing more than natural language.

### Why agents?  
Traditional “one-shot” LLMs are stateless and tool-less by design.  
Agents fix this by adding three critical capabilities:  

1. Tool use – they can call real APIs (Gmail, Drive, Calendar, web search, Google Drive, MCP, etc.)  

2. Memory & planning – they can reason step-by-step, loop, and remember context across multiple turns  

3. Secure delegated authentication – they can act on your behalf without ever seeing your passwords (using OAuth2 refresh tokens)

Only an agent architecture can safely and reliably turn natural language requests into real actions across multiple services.

### What I created – Overall architecture (2025 version)

![Architecture diagram](<AI_Architecture diagram.png>)
- Core model: Gemini-2.0-flash 
- Framework: Google ADK, Google Cloud Platform  
- Authentication: OAuth2 by Google Cloud Platform 
- One main agent that first detects which services are needed uses a multi-agent structure 
- Five specialised sub-routers (Gmail, Drive, Docs, Calendar, Search)  
- Full tool suite (same as in the diagram you posted):  
  → Gmail: search threads, send, read, delete  
  → Drive: list/search  
  → Docs: create, find, update title/content, share 
  → Calendar: free-busy, create events, list, remove
  → Search Agent: Google Custom Search 
  → MCP server fetches the user's local environment files/folders, reads, and  writes them 
  → General LLM fallback for reasoning/summarisation  


## Run locally

### Shared setup (all Google agents)

For all four agents, keep the flow and wording identical:

1) Google Cloud configuration  
- In the same GCP project, enable these APIs: Gmail API, Google Drive API, Google Docs API, and Google Calendar API.
- Under Google Auth Platform → Clients, create one OAuth 2.0 Web client (or one per agent if you prefer strict separation)
- Set Authorized JavaScript origins to:  
  - http://localhost:8000 (ADK Web UI)  
- Set Authorized redirect URIs to:  
  - http://localhost:8080/ (ADK local OAuth callback, matching your screenshot).

2) Download credentials  
- Download the client secret JSON and rename it appropriately per agent, for example:  
  - gmail/credentials/oauth.keys.json  
  - gdrive/credentialsoauth.keys.json  
  - gdoc/credentials/oauth.keys.json  
  - gcalendar/credentials/oauth.keys.json

3) Token storage convention  
- Each agent will create and reuse its own token.json in the same credentials folder, generated using google-auth-oauthlib’s InstalledAppFlow, exactly like the official Python quickstarts.

Start the agent with the built-in web UI (default http://127.0.0.1:8000):

```bash
adk web
```

For full visibility during development/debugging:

```bash
adk web --log_level DEBUG
```

Other useful local flags I use all the time:
```bash

adk web --reload --log_level DEBUG

```

That’s it — after the first `adk web`, it will automatically open the beautiful built-in ADK chat interface with Nova al-Din ready to go.

### The Build – Tech stack

- Languages: Python
- LLM: gemini-2.0-flash-exp (Google AI Studio API)  
- Agent framework: Google ADK + Google Cloud Platform  
- Google Workspace: official google-api-python-client (Gmail, Drive, Docs, Calendar)  
- Search: Google search tools  
- OAuth2 flow: Google Cloud Oauth  
- Token storage: local folder
- Memory: Google Adk InMemorySession


### If I had more time

1. **Long-Term Vector Memory**
   Enable persistent memory for preferences, past conversations, recurring tasks, and user-specific behavior.

2. **n8n Automation Pipelines**
   Integrate with **n8n** to support fully automated background workflows:

   * Auto-organize emails
   * Generate Docs from Gmail content
   * Scheduled summaries and reminders
   * Multi-step workflow execution where the agent is the “brain” and n8n is the “automation engine”

3. **Google Location Sharing Integration**

   * Connect to Google Maps Location Sharing API
   * If the user provides a live share link, the agent can fetch and describe the real-time location (address, area, distance, etc.)
   * Add automated polling: **every 5 minutes**, n8n fetches updated location → agent interprets → returns latest status

4. **Voice Mode (Hands-Free Agent)**
   Add Whisper + Gemini streaming for:

   * Real-time voice commands
   * Spoken summaries
   * Dictation for emails and documents

5. **Secure Token Vault**
   Move from local JSON token storage to an encrypted system, such as:

   * Google Cloud Secret Manager
   * HashiCorp Vault
   * Local encrypted Vault mode for offline usage

6. **Expanded Multi-Agent Hierarchy**
   Support temporary, task-specialized sub-agents:

   * Research Agent
   * Finance Agent
   * Travel Planner Agent
   * Inbox Automation Agent
     Each runs with an isolated context and dedicated tool permissions.

7. **Enhanced Google Drive Control**
   Add full file operations:

   * Upload
   * Delete
   * Move/rename
   * Duplicate
   * Generate & manage share links

8. **Smarter Calendar Tools**

   * Read past events
   * Suggest optimal meeting times
   * Weekly schedule summaries
   * Conflict detection & resolution

9. **Advanced Web Search Layer**
   Combine multiple engines and tools:

   * Tavily API
   * Twitter API v2
   * Playwright for full-page retrieval
     The agent will automatically choose the best search strategy for each query.

10. **Mobile App (React Native)**

* Background sync with n8n
* Push notifications (emails, events, alerts, location updates)
* Voice activation for commands on the go



— KPorus / User_Assistant_Agent – November 2025  
(gemini-2.0-flash + Google ADK + Google Cloud Platform )
