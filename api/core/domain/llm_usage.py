from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LLMPromptUsage(BaseModel):
    # Tokens are floats because it is possible for some providers to have fractional tokens.
    # For example, for google we count 4 characters as 1 token, so the number of tokens is 1/4 the number of characters.

    prompt_token_count: Optional[float] = None
    prompt_token_count_cached: Optional[float] = Field(
        default=None,
        description="The part of the prompt_token_count that were cached from a previous request.",
    )
    prompt_cost_usd: Optional[float] = None
    prompt_audio_token_count: Optional[float] = None
    prompt_audio_duration_seconds: Optional[float] = None
    prompt_image_count: Optional[int] = None
    prompt_image_token_count: Optional[float] = None


class LLMCompletionUsage(BaseModel):
    completion_token_count: Optional[float] = None
    completion_cost_usd: Optional[float] = None
    reasoning_token_count: Optional[float] = None
    completion_image_token_count: Optional[float] = None
    completion_image_count: Optional[int] = None


class LLMUsage(LLMPromptUsage, LLMCompletionUsage):
    model_context_window_size: Optional[int] = None

    @property
    def cost_usd(self) -> Optional[float]:
        if self.prompt_cost_usd is not None and self.completion_cost_usd is not None:
            return self.prompt_cost_usd + self.completion_cost_usd
        # If either 'prompt_cost_usd' or 'completion_cost_usd' is missing, we consider there is a problem and prefer
        # to return nothing rather than a False value.
        return None

    model_config = ConfigDict(
        protected_namespaces=(),
    )
