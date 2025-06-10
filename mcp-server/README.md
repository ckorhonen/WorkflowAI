# WorkflowAI MCP Server

A Model Context Protocol (MCP) server that exposes WorkflowAI agents and tools to MCP-compatible clients like Claude, Cursor, and other AI assistants.

## Overview

This MCP server provides programmatic access to WorkflowAI's functionality, allowing AI assistants to:
- Create and manage WorkflowAI agents
- Get help from WorkflowAI's AI engineer
- List available AI models
- Inspect agent runs and debug issues
- View agent and statistics
- View agent versions

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Access to WorkflowAI API (requires API key)

## Installation

This subproject uses Poetry to manage its dependencies independently from the main WorkflowAI project.

1. **Navigate to the mcp-server directory:**
   ```bash
   cd mcp-server
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

   This will install all required dependencies including:
   - `fastmcp` - FastMCP framework for building MCP servers
   - `httpx` - HTTP client for API calls
   - `pydantic` - Data validation
   - `uvloop` - High-performance event loop
   - Development tools (pytest, ruff, pyright)

## Running the Server

The MCP server can run in two modes:

### 1. SSE Mode (Server-Sent Events)
Run with uvicorn for development and testing:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 2. STDIO Mode (Standard I/O)
Run as a standard MCP server for integration with MCP clients:
```bash
python main.py
```

## Configuration

The server currently uses a fixed API key for authentication. You'll need to update this:

```python
# In main.py
FIXED_WORKFLOWAI_API_KEY = "your-api-key-here"
```

## Available Tools

The MCP server exposes the following tools:

### 1. `get_ai_engineer_response`
Get help from WorkflowAI's AI engineer (meta agent) to improve your agents.

**Parameters:**
- `agent_id` (str): The ID of the agent you want help with
- `agent_schema_id` (int): The schema ID of the agent version
- `message` (str): Your message to the AI engineer

### 2. `fetch_getting_started_docs`
Get example code and best practices for creating WorkflowAI agents from scratch.

**Returns:** Example agent code with comments and best practices

### 3. `list_available_models`
List all available AI models from WorkflowAI.

**Use when:** You need to pick a model for a WorkflowAI agent

### 4. `fetch_run_details`
Get detailed information about a specific agent run for debugging.

**Parameters:**
- `agent_id` (str): The agent ID
- `run_id` (str): The specific run ID

### 5. `list_agents_with_stats`
List all agents with their statistics (run counts and costs).

**Parameters:**
- `from_date` (str): ISO date string to filter stats from (defaults to 7 days ago)

### 6. `list_agent_versions`
List all versions of a specific agent.

**Parameters:**
- `agent_id` (str): The agent ID
- `schema_id` (int, optional): Filter by schema ID

### 7. `get_agent_version`
Get details of a specific agent version.

**Parameters:**
- `agent_id` (str): The agent ID
- `version_id` (str): Version ID (semver like '1.0' or hash)

## Project Structure

```
mcp-server/
├── pyproject.toml      # Poetry dependency management
├── poetry.lock         # Locked dependencies
├── main.py            # Main MCP server implementation
├── example_agent.py   # Example WorkflowAI agent code
├── README.md          # This file
└── .venv/             # Virtual environment (created after setup)
```

## TODOs

Based on the current implementation, here are the pending tasks:

### Authentication & Configuration
- [ ] Replace fixed API key with proper auth

### Tool implementation
- [ ] Directly use code from the service instead of call the API.

### Additional Tools
- [ ] Deploy an agent
- [ ] TBD

### Testing
- [ ] Add unit tests for all tools
- [ ] Add tests that check LLMs call the right tool for the right use case

