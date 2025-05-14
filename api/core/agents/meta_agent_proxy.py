import datetime
from typing import Any, AsyncIterator, Literal, Self

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from core.domain.documentation_section import DocumentationSection
from core.domain.feedback import Feedback
from core.domain.integration.integration_domain import Integration
from core.domain.url_content import URLContent
from core.domain.version_environment import VersionEnvironment

from .extract_company_info_from_domain_task import Product


class WorkflowaiPage(BaseModel):
    title: str
    description: str


class WorkflowaiSection(BaseModel):
    name: str
    pages: list[WorkflowaiPage]


# MVP for the redirection feature, will be replaced by a dynamic feature in the future
STATIC_WORKFLOWAI_PAGES = [
    WorkflowaiSection(  # noqa: F821
        name="Iterate",
        pages=[
            WorkflowaiPage(
                title="Schemas",
                description="Dedicated to the management of agent schemas, allow to see previous schema versions, etc.",
            ),
            WorkflowaiPage(
                title="Playground",
                description="The current page the user is on, allow to run agents, on different models, with different instructions, etc.",
            ),
            WorkflowaiPage(
                title="Versions",
                description="Allows to see an history of all previous instructions versions of the current agent, with changelogs between versions, etc.",
            ),
            WorkflowaiPage(
                title="Settings",
                description="Allow to rename the current agent, delete it, or make it public. Also allows to manage private keys that allow to run the agent via API / SDK.",
            ),
        ],
    ),
    WorkflowaiSection(
        name="Compare",
        pages=[
            WorkflowaiPage(
                title="Reviews",
                description="Allows to visualize the annotated output for this agents (positive, negative, etc.)",
            ),
            WorkflowaiPage(
                title="Benchmarks",
                description="Allows to compare model correctness, cost, latency, based on a set of reviews.",
            ),
        ],
    ),
    WorkflowaiSection(
        name="Integrate",
        pages=[
            WorkflowaiPage(
                title="Code",
                description="Get ready-to-use Python SDK code snippets, TypeScript SDK code snippets, and example REST requests to run the agent via API.",
            ),
            WorkflowaiPage(
                title="Deployments",
                description="Allows to deploy the current agent to fixed environments 'dev', 'staging', 'production'. This allows, for example,to quickly hotfix instructions in production, since the code point to a static 'production' deployment",
            ),
        ],
    ),
    WorkflowaiSection(
        name="Monitor",
        pages=[
            WorkflowaiPage(
                title="User Feedback",
                description="Allows to see an history of all previous user feedbacks for the current agent.",
            ),
            WorkflowaiPage(
                title="Runs",
                description="Allows to see an history of all previous runs of the current agent. 'Run' refers to a single execution of the agent, with a given input, instructions and a given model.",
            ),
            WorkflowaiPage(
                title="Costs",
                description="Allows to visualize the cost incurred by the agent per day, for yesterday, last week, last month, last year, and all time.",
            ),
        ],
    ),
]


class BaseResult(BaseModel):
    tool_name: str = Field(
        description="The name of the tool call",
    )

    status: Literal["assistant_proposed", "user_ignored", "completed", "failed"] = Field(
        description="The status of the tool call",
    )


class BaseToolCallRequest(BaseModel):
    ask_user_confirmation: bool | None = Field(
        default=None,
        description="Whether the tool call should be automatically executed by on the frontend (ask_user_confirmation=false), or if the user should be prompted to run the tool call (ask_user_confirmation=true). Based on the confidence of the meta-agent in the tool call.",
    )


class ImprovePromptToolCallRequest(BaseToolCallRequest):
    agent_run_id: str | None = Field(
        default=None,
        description="The id (agent_runs.id) of the runs among the 'agent_runs' that is the most representative of what we want to improve in the 'agent_instructions'",
    )
    instruction_improvement_request_message: str = Field(
        description="The feedback on the agent run (what is wrong with the output of the run, what is the expected output, etc.).",
    )


class ImprovePromptToolCallResult(BaseResult, ImprovePromptToolCallRequest):
    pass


class EditSchemaStructureToolCallRequest(BaseToolCallRequest):
    edition_request_message: str | None = Field(
        default=None,
        description="The message to edit the agent schema with.",
    )


class EditSchemaDescriptionAndExamplesToolCallRequest(BaseToolCallRequest):
    description_and_examples_edition_request_message: str | None = Field(
        default=None,
        description="The message to edit the agent schema's fields description and examples with.",
    )


class EditSchemaToolCallResult(BaseResult, EditSchemaStructureToolCallRequest):
    pass


class RunCurrentAgentOnModelsToolCallRequest(BaseToolCallRequest):
    class RunConfig(BaseModel):
        run_on_column: Literal["column_1", "column_2", "column_3"] | None = Field(
            default=None,
            description="The column to run the agent on the agent will be run on all columns",
        )
        model: str | None = Field(
            default=None,
            description="The model to run the agent on the agent will be run on all models",
        )

    run_configs: list[RunConfig] | None = Field(
        default=None,
        description="The list of configurations to run the current agent on.",
    )


class RunCurrentAgentOnModelsToolCallResult(BaseResult, RunCurrentAgentOnModelsToolCallRequest):
    pass


class GenerateAgentInputToolCallRequest(BaseToolCallRequest):
    instructions: str | None = Field(
        default=None,
        description="The instructions on how to generate the agent input, this message will be passed to the input generation agent.",
    )


class GenerateAgentInputToolCallResult(BaseResult, GenerateAgentInputToolCallRequest):
    pass


class ProxyMetaAgentChatMessage(BaseModel):
    role: Literal["USER", "PLAYGROUND", "ASSISTANT"] = Field(
        description="The role of the message sender, 'USER' is the actual human user browsing the playground, 'PLAYGROUND' are automated messages sent by the playground to the agent, and 'ASSISTANT' being the assistant generated by the agent",
    )
    content: str = Field(
        description="The content of the message",
        examples=[
            "Thank you for your help!",
            "What is the weather forecast for tomorrow?",
        ],
    )


class PlaygroundState(BaseModel):
    class Agent(BaseModel):
        name: str
        slug: str
        schema_id: int
        description: str | None = None
        input_schema: dict[str, Any]
        output_schema: dict[str, Any]
        used_integration: Integration | None = None

    current_agent: Agent = Field(
        description="The current agent to use for the conversation",
    )

    """
    agent_input: dict[str, Any] | None = Field(
        default=None,
        description="The input for the agent",
    )

    class InputFile(BaseModel):
        key_path: str
        file: File

    agent_input_files: list[InputFile] | None = Field(
        default=None,
        description="The files contained in the 'agent_input' object, if any",
    )

    agent_instructions: str | None = Field(
        default=None,
        description="The instructions for the agent",
    )
    agent_temperature: float | None = Field(
        default=None,
        description="The temperature for the agent",
    )
    """

    class AgentRun(BaseModel):
        id: str = Field(
            description="The id of the agent run",
        )
        model: str | None = Field(
            default=None,
            description="The model that was used to generate the agent output",
        )
        output: str | None = Field(
            default=None,
            description="The output of the agent, if no error occurred.",
        )
        error: dict[str, Any] | None = Field(
            default=None,
            description="The error that occurred during the agent run, if any.",
        )
        raw_run_request: dict[str, Any] | None = Field(
            default=None,
            description="The raw run request that was used to generate the agent output",
        )

        class ToolCall(BaseModel):
            name: str
            input: dict[str, Any]

        tool_calls: list[ToolCall] | None = Field(
            default=None,
            description="The tool calls that were made by the agent to produce the output",
        )
        cost_usd: float | None = Field(
            default=None,
            description="The cost of the agent run in USD",
        )
        duration_seconds: float | None = Field(
            default=None,
            description="The duration of the agent in seconds",
        )
        user_evaluation: Literal["positive", "negative"] | None = Field(
            default=None,
            description="The user evaluation of the agent output",
        )

    class PlaygroundModel(BaseModel):
        id: str = Field(
            description="The id of the model",
        )
        name: str
        is_default: bool = Field(
            default=False,
            description="Whether the model is one of the default models on the WorkflowAI platform",
        )
        is_latest: bool = Field(
            default=False,
            description="Whether the model is the latest model in its family",
        )
        quality_index: int = Field(
            description="The quality index that quantifies the reasoning abilities of the model",
        )
        context_window_tokens: int = Field(
            description="The context window of the model in tokens",
        )
        is_not_supported_reason: str | None = Field(
            default=None,
            description="The reason why the model is not supported for the current agent",
        )
        estimate_cost_per_thousand_runs_usd: float | None = Field(
            default=None,
            description="The estimated cost per thousand runs in USD",
        )

    available_models: list[PlaygroundModel] = Field(
        description="The models currently available in the playground",
    )

    """
    class SelectedModels(BaseModel):
        column_1: str | None = Field(
            default=None,
            description="The id of the model selected in the first column of the playground, if empty, no model is selected in the first column",
        )
        column_2: str | None = Field(
            default=None,
            description="The id of the model selected in the second column of the playground, if empty, no model is selected in the second column",
        )
        column_3: str | None = Field(
            default=None,
            description="The id of the model selected in the third column of the playground, if empty, no model is selected in the third column",
        )

    selected_models: SelectedModels = Field(
        description="The models currently selected in the playground",
    )
    """
    agent_runs: list[AgentRun] | None = Field(
        default=None,
        description="The agent runs",
    )


class ProxyMetaAgentInput(BaseModel):
    current_datetime: datetime.datetime = Field(
        description="The current datetime",
    )

    messages: list[ProxyMetaAgentChatMessage] = Field(
        description="The list of messages in the conversation, the last message being the most recent one",
    )

    latest_messages_url_content: list[URLContent] = Field(
        default_factory=list,
        description="The URL content of the latest 'USER' message, if any URL was found in the message.",
    )

    class CompanyContext(BaseModel):
        company_name: str | None = None
        company_description: str | None = None
        company_locations: list[str] | None = None
        company_industries: list[str] | None = None
        company_products: list[Product] | None = None
        existing_agents_descriptions: list[str] | None = Field(
            default=None,
            description="The list of existing agents for the company",
        )

    company_context: CompanyContext = Field(
        description="The context of the company to which the conversation belongs",
    )

    workflowai_sections: list[WorkflowaiSection] = Field(
        default=STATIC_WORKFLOWAI_PAGES,
        description="Other sections pages of the WorkflowAI platform (outside of the playground page, which this agent is part of). You can use this information to answer questions about the WorkflowAI platform and direct the user to the relevant pages. All those page are clickable on the left panel from the WorkflowAI playground.",
    )

    workflowai_documentation_sections: list[DocumentationSection] = Field(
        description="The relevant documentation sections of the WorkflowAI platform, which this agent is part of",
    )

    integration_documentation: list[DocumentationSection] = Field(
        description="The documentation of the integration that the user is using, if any",
    )

    available_tools_description: str = Field(
        description="The description of the available tools, that can be potientially added to the 'agent_instructions' in order to improve the agent's output",
    )

    playground_state: PlaygroundState

    class AgentLifecycleInfo(BaseModel):
        class DeploymentInfo(BaseModel):
            has_api_or_sdk_runs: bool | None = Field(
                default=None,
                description="Whether the 'current_agent' has already been run via API / SDK",
            )
            latest_api_or_sdk_run_date: datetime.datetime | None = Field(
                default=None,
                description="The date of the latest API / SDK run",
            )

            class Deployment(BaseModel):
                deployed_at: datetime.datetime | None = Field(
                    default=None,
                    description="The date of the deployment",
                )
                deployed_by_email: str | None = Field(
                    default=None,
                    description="The email of the staff member who deployed the 'current_agent' version",
                )
                environment: VersionEnvironment | None = Field(
                    default=None,
                    description="The environment in which the 'current_agent' version is deployed ('dev', 'staging' or 'production')",
                )
                model_used: str | None = Field(
                    default=None,
                    description="The model used to run the 'current_agent' deployment",
                )
                last_active_at: datetime.datetime | None = Field(
                    default=None,
                    description="The date of the last run of the 'current_agent' deployment",
                )
                run_count: int | None = Field(
                    default=None,
                    description="The number of runs of the 'current_agent' deployment",
                )
                notes: str | None = Field(
                    default=None,
                    description="The notes of the 'current_agent' deployment, added by the staff member who created the deployed version",
                )

            deployments: list[Deployment] | None = Field(
                default=None,
                description="The list of deployments of the 'current_agent'",
            )

        deployment_info: DeploymentInfo | None = Field(
            default=None,
            description="The deployment info of the agent",
        )

        class FeedbackInfo(BaseModel):
            user_feedback_count: int | None = Field(
                default=None,
                description="The number of user feedbacks",
            )

            class AgentFeedback(BaseModel):
                created_at: datetime.datetime | None = None
                outcome: Literal["positive", "negative"] | None = None
                comment: str | None = None

                @classmethod
                def from_domain(cls, feedback: Feedback) -> Self:
                    return cls(
                        created_at=feedback.created_at,
                        outcome=feedback.outcome,
                        comment=feedback.comment,
                    )

            latest_user_feedbacks: list[AgentFeedback] | None = Field(
                default=None,
                description="The 10 latest user feedbacks",
            )

        feedback_info: FeedbackInfo | None = Field(
            default=None,
            description="The info related to the user feedbacks of the agent.",
        )

        class InternalReviewInfo(BaseModel):
            reviewed_input_count: int | None = Field(
                default=None,
                description="The number of reviewed inputs",
            )

        internal_review_info: InternalReviewInfo | None = Field(
            default=None,
            description="The info related to the internal reviews of the agent.",
        )

    agent_lifecycle_info: AgentLifecycleInfo | None = Field(
        default=None,
        description="The lifecycle info of the agent",
    )

    suggested_instructions_with_input_variables: str | None = Field(
        default=None,
        description="The suggested instructions with input variables, if any",
    )
    suggested_input_variables_example: dict[str, Any] | None = Field(
        default=None,
        description="The suggested input variables example, if any",
    )

    suggested_output_class_code: str | None = Field(
        default=None,
        description="The suggested output class code to migrate to structured generation, if any",
    )
    suggested_instructions_parts_to_remove: list[str] | None = Field(
        default=None,
        description="The suggested instructions parts to remove from the original instructions when migrating to structured generation, if any",
    )


class ProxyMetaAgentOutput(BaseModel):
    assistant_answer: str | None = Field(
        default=None,
        description="The content of the answer message from the meta-agent",
    )


_PROXY_META_AGENT_COMMON_INSTRUCTIONS = """Your WorkflowAI proxy playground agent's role is to make the user succeed in the WorkflowAI platform, having performant and reliable agents.


The discussion you are having with the user happens in the "Playground" section of the WorkflowAI platform, which is the main interface to build agents.

It's very important that you check the 'playground_state.agent_runs' to see the latest agent runs that the user has made.
Pay attention to the temporality of those runs, with newer runs being at the beginning of the agent runs array.

If the first run in the array use Claude models, and the second one is GPT, that means the user has switched to Claude. If there are back and forth between models, consider that the user has tried cloud but went back to GPT.

When returning code blocks, always make sure the code block is customized to the user's specific context—for example, the model it uses or the name of its agent ('current_agent.slug').
When returning code blocks, always make sure to just return the part that is to be updated and do not return a full working code block that is too lengthy.
When returning code blocks, do not use diff formate (+, -, etc.) because the user will not be able to copy paste the code block effectively.
Inside returning code blocks do not forget to escape double quotes: \" , same for triple quotes: \"\"\"
Always refer to the 'integration_documentation' that matchers 'playground_state.current_agent.used_integration' for code block language and syntax.
"""

_PROPOSE_NON_OPENAI_MODELS_INSTRUCTIONS = """
Your promise goal here is to make the user migrate to non-OpenAI models. You can check the documentation to see why it's a good idea to use non-OpenAI models.

The reason to use different models than OpenAI is having better performing models, cheaper models, faster models.

You must pick a relevant model for the use case of the client and show him some code blocks that show how to update the model."""

PROPOSE_NON_OPENAI_MODELS_INSTRUCTIONS = f"""
{_PROXY_META_AGENT_COMMON_INSTRUCTIONS}
{_PROPOSE_NON_OPENAI_MODELS_INSTRUCTIONS}
"""

_PROPOSE_INPUT_VARIABLES_INSTRUCTIONS = """Your promise goal here is to make the user migrate to input variables. You can check the documentation to see why it's a good idea to use input variables.
Use the 'suggested_instructions_with_input_variables' and 'suggested_input_variables_example' in order to provide code snippet that are valid in the context of the WorkflowAI integrations documented in the 'workflowai_documentation_sections' section of the input.`

Start by 1. Explaining to the user why it's a good idea to use input variables. Start with a simple phrase like "I have something to propose to make your to unlock a lot of WorkflowAI's capabilities: ..."
Then 2. ALWAYS return the WHOLE 'suggested_instructions_with_input_variables' in a code code block in order for the user to easily copy paste it.
ALWAYS provide a block that shows how to pass the input variables in the completion request (with extra_body=...)
When instructions are spread over several messages, make sure to display a code block that showed several messages with the right instructions at the right place.
"""

PROPOSE_INPUT_VARIABLES_INSTRUCTIONS = f"""
{_PROPOSE_INPUT_VARIABLES_INSTRUCTIONS}
"""

_PROPOSE_STRUCTURED_OUTPUT_INSTRUCTIONS = """
Your precise goal here is to make the user migrate to structured output. You can check the documentation to see why it's a good idea to use structured output.
Use the 'suggested_output_class_code' and 'suggested_instructions_parts_to_remove' in order to provide code snippet that are valid in the context of the WorkflowAI integrations documented in the 'workflowai_documentation_sections' section of the input.`
If 'suggested_instructions_parts_to_remove' are fed, you can mention to the user that they can remove those parts in their existing instructions that talk about generating a valid JSON, because this is not needed anymore when you use structure generation.

Start by 1. Explaining to the user why it's a good idea to use structured output. Start with a simple phrase like "Next step is to migrate to structured output...."
Then 2. Provide the code snippets to the user that will allow them to use structured output. Based on 'suggested_output_class_code' and how to plug the right respons format in the code.
Also add the imports in the code block.

If you mention a SDK or package, etc., make sure you are mentioning the right one, for example "Instructor". You do not need to rebuild the full code snippets, just higlight the main changes to do and a few lines of code around it.

Be aware that the user can just update his code and has nothing to do in the interface. Just updating the code is enough, and a new schema and the agent will be automatically updated in WorkflowAI.com."""

PROPOSE_STRUCTURED_OUTPUT_INSTRUCTIONS = f"""
{_PROXY_META_AGENT_COMMON_INSTRUCTIONS}
{_PROPOSE_STRUCTURED_OUTPUT_INSTRUCTIONS}
"""

GENERIC_INSTRUCTIONS = f"""
{_PROXY_META_AGENT_COMMON_INSTRUCTIONS}

# In case the user enquires a about testing new models:
{_PROPOSE_NON_OPENAI_MODELS_INSTRUCTIONS}

# In case the user enquires a about input variables:
{_PROPOSE_INPUT_VARIABLES_INSTRUCTIONS}

# In case the user enquires a about structured output:
{_PROPOSE_STRUCTURED_OUTPUT_INSTRUCTIONS}
"""


async def proxy_meta_agent(input: ProxyMetaAgentInput, instructions: str) -> AsyncIterator[ProxyMetaAgentOutput]:
    client = AsyncOpenAI(
        api_key="wai-4hcqxDO3eZLytkIsLdSHGLbviAP0P16bRoX6AVGLTFM",
        base_url="https://run.workflowai.dev/v1",
    )
    response = await client.chat.completions.create(
        model="proxy_meta_agent/claude-3-7-sonnet-20250219",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": "{% raw %}" + input.model_dump_json() + "{% endraw %}"},
        ],
        stream=True,
    )
    async for chunk in response:
        yield ProxyMetaAgentOutput(assistant_answer=chunk.choices[0].delta.content)
