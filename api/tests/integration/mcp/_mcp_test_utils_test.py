import json
from pathlib import Path

from tests.integration.mcp._mcp_test_utils import ClaudeSteps


def test_claude_step_deser():
    """Check that we can deserialize the claude outputs from the json file"""
    fixture_path = Path(__file__).parent / "fixtures" / "claude_steps.json"
    with open(fixture_path, "r") as f:
        ClaudeSteps.validate_python(json.load(f))
