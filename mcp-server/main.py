#!/usr/bin/env python3
"""
WorkflowAI MCP Server

A Model Context Protocol server that exposes WorkflowAI agents and tools
to MCP-compatible clients like Claude, Cursor, and other AI assistants.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

import httpx
from fastmcp import FastMCP
from pydantic import Field

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

mcp = FastMCP("WorkflowAI MCP Server", transport="sse")  # type: ignore[reportUnknownReturnType]

WORKFLOWAI_API_URL = ""

# TODO: use actual API key / tenant from OAuth
FIXED_WORKFLOWAI_API_KEY = ""
TENANT = ""


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {FIXED_WORKFLOWAI_API_KEY}",
    }


async def _call_ai_engineer_without_agent_id(messages: list[dict[str, Any]]) -> dict[str, Any]:
    headers = _headers()
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "text/event-stream"

    try:
        logger.info(
            "Calling AI Engineer API without agent ID",
            extra={
                "url": f"{WORKFLOWAI_API_URL}/{TENANT}/agents/ai-engineer/messages",
                "messages": messages,
            },
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{WORKFLOWAI_API_URL}/{TENANT}/agents/ai-engineer/messages",
                json={"messages": messages},
                headers=headers,
            )
            response.raise_for_status()

            last_messages: List[Dict[str, Any]] = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break

                        data = json.loads(data_str)
                        if "messages" in data and isinstance(data["messages"], list):
                            last_messages = data["messages"]  # Replace with latest chunk
                    except json.JSONDecodeError:
                        continue

            return {
                "success": True,
                "messages": last_messages,
            }

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error calling meta agent API", extra={"status_code": e.response.status_code})
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error("Error calling meta agent API", extra={"error": str(e)})
        return {
            "success": False,
            "error": "Failed to call AI engineer API",
            "details": str(e),
        }


@mcp.tool
async def get_ai_engineer_response(  # noqa: C901
    agent_schema_id: int | None = Field(
        description="The schema ID of the user's agent version, if known",
        default=None,
    ),
    agent_model_parameter: str | None = Field(
        description="The model parameter of the user's agent, example: 'email-filtering-agent/gemini-2.0-flash-001' (agent id / model name). Pass 'new' when the user wants to create a new agent.",
        default=None,
    ),
    message: str = Field(
        description="Your message to the AI engineer about what help you need",
        default="I need help improving my agent",
    ),
) -> dict[str, Any]:
    """
    <when_to_use>
    Most user request about WorkflowAI must be processed by starting a conversation with the AI engineer agent to get insight about the WorkflowAI platform and the user's agents.
    </when_to_use>

    <returns>
    Returns a response from WorkflowAI's AI engineer (meta agent) to help improve your agent.
    </returns>
    Get a response from WorkflowAI's AI engineer (meta agent) to help improve your agent.
    """

    if not agent_model_parameter or agent_model_parameter == "new":
        # run the "AI Engineer" with no agent ID
        return await _call_ai_engineer_without_agent_id(
            messages=[
                {
                    "role": "USER",
                    "content": message,
                },
            ]
        )

    if not agent_schema_id:
        # TODO: figure out the right schema id to use here
        agent_schema_id = 1

    if "/" in agent_model_parameter:
        agent_id = agent_model_parameter.split("/")[0]
    else:
        agent_id = agent_model_parameter

    body: dict[str, Any] = {
        "schema_id": agent_schema_id,
        "playground_state": {
            "is_proxy": True,
            "version_id": None,
            "version_messages": None,
            "agent_input": None,
            "agent_instructions": None,
            "agent_temperature": None,
            "selected_models": {
                "column_1": None,
                "column_2": None,
                "column_3": None,
            },
            "agent_run_ids": [],
        },
        "messages": [
            {
                "role": "USER",
                "content": message,
            },
        ],
    }

    headers = _headers()
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "text/event-stream"

    try:
        logger.info(
            "Calling meta agent API",
            extra={"url": f"{WORKFLOWAI_API_URL}/{TENANT}/agents/{agent_id}/prompt-engineer-agent/messages"},
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{WORKFLOWAI_API_URL}/{TENANT}/agents/{agent_id}/prompt-engineer-agent/messages",
                json=body,
                headers=headers,
            )
            response.raise_for_status()

            last_messages: List[Dict[str, Any]] = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data_str = line[6:]  # Remove "data: " prefix
                        if data_str.strip() == "[DONE]":
                            break

                        data = json.loads(data_str)
                        if "messages" in data and isinstance(data["messages"], list):
                            last_messages = data["messages"]  # Replace with latest chunk
                    except json.JSONDecodeError:
                        continue

            return {
                "success": True,
                "messages": last_messages,
            }

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error calling meta agent API", extra={"status_code": e.response.status_code})
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error("Error calling meta agent API", extra={"error": str(e)})
        return {
            "success": False,
            "error": "Failed to call AI engineer API",
            "details": str(e),
        }


# Deactivate for now, will probably be deleted
'''
@mcp.tool
async def fetch_getting_started_docs() -> dict[str, Any]:
    """<when_to_use>
    To use when buidling when the user want to create a WorkflowAI agent from scratch.
    </when_to_use>

    <returns>
    Returns an example of a WorkflowAI agent that use the best practices of WorkflowAI.
    </returns>"""
    # Load content from example_agent.py (relative to this script's directory)
    script_dir = Path(__file__).parent
    code_example_content = (script_dir / "example_agent.py").read_text()

    docs = f"""Here is an example of workflow AI agents that use input variables, structured output, and hosted tools (@browser-text) and that act as a very good best practice to get started with workflow AI. You can see the comments, and you can adapt indeed these example agents to the actual user use case.
    The users can get their workflow API keys at 'workflowai.com/keys'. Thank you but when generating a code, you can also try to find WORKFLOWAI_API_KEY in the users code and reuse it.

    Here is an example of a WorkflowAI agent that you can use as a starting point:
    {code_example_content}

    """

    return {
        "success": True,
        "documentation": docs,
    }
'''


@mcp.tool
async def list_available_models() -> dict[str, Any]:
    """
    <when_to_use>
    When you need to pick a model for the user's WorkflowAI agent, or any model-related goal.
    </when_to_use>

    <returns>
    Returns a list of all available AI models from WorkflowAI.
    </returns>
    """

    try:
        logger.info(
            "Calling models API",
            extra={"url": f"{WORKFLOWAI_API_URL}/v1/models"},
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WORKFLOWAI_API_URL}/v1/models",
                headers=_headers(),
            )
            response.raise_for_status()

            models_data = response.json()
            return {
                "success": True,
                "models": models_data,
            }

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error calling models API", extra={"status_code": e.response.status_code})
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error("Error calling models API", extra={"error": str(e)})
        return {
            "success": False,
            "error": "Failed to call models API",
            "details": str(e),
        }


@mcp.tool
async def fetch_run_details(agent_id: str, run_id: str) -> dict[str, Any]:
    """
    <when_to_use>
    When the user wants to investigate a specific run of a WorkflowAI agent, for debugging, improving the agent, fixing a problem on a specific use case, or any other reason.
    </when_to_use>

    <returns>
    Returns the details of a specific run of a WorkflowAI agent.
    </returns>
    """
    try:
        logger.info(
            "Calling run details API",
            extra={
                "url": f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/runs/{run_id}",
                "agent_id": agent_id,
                "run_id": run_id,
            },
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/runs/{run_id}",
                headers=_headers(),
            )
            response.raise_for_status()

            run_data = response.json()
            return {
                "success": True,
                "run_details": run_data,
            }

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error calling run details API",
            extra={
                "status_code": e.response.status_code,
                "agent_id": agent_id,
                "run_id": run_id,
            },
        )
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error(
            "Error calling run details API",
            extra={
                "error": str(e),
                "agent_id": agent_id,
                "run_id": run_id,
            },
        )
        return {
            "success": False,
            "error": "Failed to call run details API",
            "details": str(e),
        }


@mcp.tool
async def list_agents_with_stats(
    from_date: str = Field(
        description="ISO date string to filter stats from (e.g., '2024-01-01T00:00:00Z'). Defaults to 7 days ago if not provided.",
        default="",
    ),
) -> dict[str, Any]:
    """
    <when_to_use>
    When the user wants to see all agents they have created, along with their statistics (run counts and costs on the last 7 days).
    </when_to_use>

    <returns>
    Returns a list of all agents for the user along with their statistics (run counts and costs).
    </returns>
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call both endpoints concurrently
            agents_url = f"{WORKFLOWAI_API_URL}/{TENANT}/agents"
            stats_url = f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/stats"

            params: dict[str, str] = {}
            if from_date:
                params["from_date"] = from_date

            logger.info(
                "Calling agents list and stats APIs",
                extra={
                    "agents_url": agents_url,
                    "stats_url": stats_url,
                    "params": params,
                },
            )

            # Make both requests concurrently
            agents_response, stats_response = await asyncio.gather(
                client.get(agents_url, headers=_headers()),
                client.get(stats_url, params=params, headers=_headers()),
            )

            agents_response.raise_for_status()
            stats_response.raise_for_status()

            agents_data = agents_response.json()
            stats_data = stats_response.json()

            # Create a mapping of agent_uid to stats for easy lookup
            stats_by_uid: dict[int, dict[str, Any]] = {}
            if stats_data.get("items"):
                for stat in stats_data["items"]:
                    stats_by_uid[stat["agent_uid"]] = {
                        "run_count_last_7d": stat.get("run_count", 0),
                        "total_cost_usd_last_7d": stat.get("total_cost_usd", 0.0),
                    }

            # Merge stats into agents based on uid/agent_uid
            enriched_agents: list[dict[str, Any]] = []
            if agents_data.get("items"):
                for agent in agents_data["items"]:
                    agent_uid = agent.get("uid")
                    # Add stats to agent if available
                    if agent_uid and agent_uid in stats_by_uid:
                        agent["stats_last_7d"] = stats_by_uid[agent_uid]
                    else:
                        # Add default stats if no data available
                        agent["stats_last_7d"] = {
                            "run_count_last_7d": 0,
                            "total_cost_usd_last_7d": 0.0,
                        }
                    enriched_agents.append(agent)

            return {
                "success": True,
                "agents": {
                    "items": enriched_agents,
                    "count": agents_data.get("count", len(enriched_agents)),
                },
            }

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error calling agents APIs",
            extra={
                "status_code": e.response.status_code,
                "from_date": from_date,
            },
        )
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error(
            "Error calling agents APIs",
            extra={
                "error": str(e),
                "from_date": from_date,
            },
        )
        return {
            "success": False,
            "error": "Failed to call agents APIs",
            "details": str(e),
        }


@mcp.tool
async def list_agent_versions(
    agent_id: str = Field(description="The ID of the agent to list versions for"),
    schema_id: int | None = Field(
        description="Optional schema ID to filter versions by",
        default=None,
    ),
) -> dict[str, Any]:
    """
    <when_to_use>
    When the user wants to see all versions of a specific agent, or when they want to compare different versions of an agent.
    </when_to_use>

    <returns>
    Returns a list of all versions of a specific agent.
    </returns>
    """
    try:
        params: dict[str, str] = {}
        if schema_id is not None:
            params["schema_id"] = str(schema_id)

        logger.info(
            "Calling list versions API",
            extra={
                "url": f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/versions",
                "agent_id": agent_id,
                "schema_id": schema_id,
            },
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/versions",
                params=params,
                headers=_headers(),
            )
            response.raise_for_status()

            versions_data = response.json()
            return {
                "success": True,
                "versions": versions_data,
            }

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error calling list versions API",
            extra={
                "status_code": e.response.status_code,
                "agent_id": agent_id,
                "schema_id": schema_id,
            },
        )
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error(
            "Error calling list versions API",
            extra={
                "error": str(e),
                "agent_id": agent_id,
                "schema_id": schema_id,
            },
        )
        return {
            "success": False,
            "error": "Failed to call list versions API",
            "details": str(e),
        }


@mcp.tool
async def get_agent_version(
    agent_id: str = Field(description="The ID of the agent"),
    version_id: str = Field(
        description="The version ID (either a semver like '1.0' or a hash)",
    ),
) -> dict[str, Any]:
    """
    <when_to_use>
    When the user wants to see the details of a specific version of a WorkflowAI agent, or when they want to compare a specific version of an agent.
    </when_to_use>

    <returns>
    Returns the details of a specific version of a WorkflowAI agent.
    </returns>
    """
    try:
        logger.info(
            "Calling get version API",
            extra={
                "url": f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/versions/{version_id}",
                "agent_id": agent_id,
                "version_id": version_id,
            },
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{WORKFLOWAI_API_URL}/v1/{TENANT}/agents/{agent_id}/versions/{version_id}",
                headers=_headers(),
            )
            response.raise_for_status()

            version_data = response.json()
            return {
                "success": True,
                "version": version_data,
            }

    except httpx.HTTPStatusError as e:
        logger.error(
            "HTTP error calling get version API",
            extra={
                "status_code": e.response.status_code,
                "agent_id": agent_id,
                "version_id": version_id,
            },
        )
        return {
            "success": False,
            "error": f"API returned status {e.response.status_code}",
            "details": str(e),
        }
    except Exception as e:
        logger.error(
            "Error calling get version API",
            extra={
                "error": str(e),
                "agent_id": agent_id,
                "version_id": version_id,
            },
        )
        return {
            "success": False,
            "error": "Failed to call get version API",
            "details": str(e),
        }


if __name__ == "__main__":
    logger.info("Starting WorkflowAI MCP Server...")

    # Check if we should run in SSE mode (for uvicorn) or STDIO mode (for MCP clients)
    if any("uvicorn" in arg for arg in sys.argv):
        # Running via uvicorn - don't call mcp.run()
        logger.info("Running in SSE mode (uvicorn)")
        pass
    else:
        # Run in STDIO mode (standard MCP transport)
        logger.info("Running in STDIO mode (standard MCP transport)")
        mcp.run(transport="sse", host="127.0.0.1", port=8001)

# SSE app for uvicorn
app = mcp.sse_app()
