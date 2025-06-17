import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.integration.mcp._mcp_test_utils import ClaudeSteps, Evaluator, EvaluatorDefinition
from tests.utils import root_dir

_MCP_NAME = "workflowai_test"


@pytest.fixture(scope="session", autouse=True)
def install_js_dependencies(workflowai_api_key: str, api_server: str):
    """Install the dependencies for the JS examples.
    We need to have claude code installed to run the tests.
    Also set up the mcp server in claude"""
    subprocess.run(["yarn", "install"], cwd=root_dir())

    # Add the mcp server to claude
    subprocess.run(
        [
            "yarn",
            "run",
            "claude",
            "mcp",
            "add",
            _MCP_NAME,
            f"{api_server}/mcp/",
            "-H",
            f"Authorization: Bearer {workflowai_api_key}",
            "--transport",
            "http",
        ],
        cwd=root_dir(),
    )


def _cur_dir():
    return Path(__file__).parent


def _list_cases():
    """List the test cases in the cases directory"""
    return [f.name for f in (_cur_dir() / "cases").iterdir() if f.is_dir() and not f.name.startswith("_")]


_WAI_TOOLS = [
    "list_available_models",
    "list_agents",
    "fetch_run_details",
    "get_agent_versions",
    "ask_ai_engineer",
    "deploy_agent_version",
]


def base_allowed_tools():
    return ["Read(./*)", "Write(./*)", *[f"mcp__{_MCP_NAME}__{tool}" for tool in _WAI_TOOLS]]


def base_denied_tools():
    return ["Read(../*)"]


# Typing for claude output, does not need to be exhaustive, just here to provide an idea of what is expected
# and potentially check for possible errors


@pytest.mark.parametrize("case", _list_cases())
def test_mcp_cases(case: str):
    case_dir_path = _cur_dir() / "cases" / case
    initial_state_dir = case_dir_path / "initial_state"

    # RM the claude_steps if exists
    # The claude steps file will contain the steps for the actual execution of the agent
    # that is being tested
    claude_steps_file = initial_state_dir / "claude_steps.json"
    if claude_steps_file.exists():
        claude_steps_file.unlink()

    # Make sure there is a .claude_steps directory and that it's empty
    # The claude steps directory will contain other claude steps files
    # for example the logs of evaluations
    claude_steps_dir = case_dir_path / ".claude_steps"
    if claude_steps_dir.exists():
        shutil.rmtree(claude_steps_dir)
    claude_steps_dir.mkdir(parents=True, exist_ok=True)

    # TODO: assert no git changes in the initial_state directory

    allowed_tools = " ".join(f'"{tool}"' for tool in base_allowed_tools())
    denied_tools = " ".join(f'"{tool}"' for tool in base_denied_tools())

    cmd = f'cat "../PROMPT.md" | yarn run claude --verbose --allowedTools {allowed_tools} --disallowedTools {denied_tools} --output-format json -p'

    result = subprocess.run(
        cmd,
        cwd=initial_state_dir,
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0, f"Failed to run claude: {result.stderr}"

    # Write the steps to a claude_steps.json file
    # So that it can be evaluated by claude with the rest of the repo
    with open(claude_steps_file, "w") as f:
        f.write(result.stdout)

    steps = ClaudeSteps.validate_python(json.loads(result.stdout))

    with open(case_dir_path / "evaluator.yaml", "r") as f:
        evaluator = EvaluatorDefinition.model_validate(yaml.safe_load(f))

    evaluator = Evaluator(definition=evaluator, mcp_name=_MCP_NAME, claude_steps_dir=claude_steps_dir)
    failed_assertions = evaluator.evaluate(case_dir_path, steps)
    assert not failed_assertions, f"Failed assertions:{'\n------\n'.join(failed_assertions)}"
