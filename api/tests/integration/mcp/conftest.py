import subprocess

import pytest

from tests.utils import root_dir


@pytest.fixture(scope="session", autouse=True)
def install_js_dependencies(workflowai_api_key: str):
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
            "workflowai",
            "http://localhost:8000/mcp/",
            "-H",
            f"Authorization: Bearer {workflowai_api_key}",
            "--transport",
            "http",
        ],
        cwd=root_dir(),
    )
