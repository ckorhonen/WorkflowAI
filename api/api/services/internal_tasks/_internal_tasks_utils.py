from collections.abc import Callable

from workflowai.fields import Image

from core.domain.tool import Tool
from core.runners.workflowai.utils import FileWithKeyPath
from core.runners.workflowai.workflowai_runner import WorkflowAIRunner
from core.tools import ToolKind
from core.utils.tool_utils.tool_utils import get_tools_description

OFFICIALLY_SUGGESTED_TOOLS = {ToolKind.WEB_BROWSER_TEXT, ToolKind.WEB_SEARCH_PERPLEXITY_SONAR_PRO}


# Even though the types almost match, we keep objects separate to make sure we notice changes in the SDK
def file_to_image(file: FileWithKeyPath) -> Image:
    return Image(data=file.data, content_type=file.content_type, url=file.storage_url or file.url)


def internal_tools_description(
    all: bool = False,
    include: set[ToolKind] | None = None,
    formatting_func: Callable[[list[Tool]], str] = get_tools_description,
) -> str:
    if all is True:
        if include is not None:
            raise ValueError("include cannot be used with all=True")

        def take_all(tk: ToolKind) -> bool:
            return True

        predicate: Callable[[ToolKind], bool] = take_all
    else:

        def filter(tk: ToolKind) -> bool:
            if include is None:
                return False
            return tk in include

        predicate: Callable[[ToolKind], bool] = filter

    tools_to_describe = [t.definition for k, t in WorkflowAIRunner.internal_tools.items() if predicate(k)]

    if len(tools_to_describe) == 0:
        return ""

    return formatting_func(tools_to_describe)


def officially_suggested_tools() -> str:
    """A set of tools that are officially suggested by WorkflowAI for user's agents.

    Other tools will work if they are already in the user's instructions, but we won't suggest those anymore (ex: @search-google)
    """

    return internal_tools_description(
        include=OFFICIALLY_SUGGESTED_TOOLS,
    )
