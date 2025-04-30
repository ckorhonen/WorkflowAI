from typing import Any, NamedTuple

import pytest

from core.domain.llm_completion import LLMCompletion
from core.domain.llm_usage import LLMUsage
from core.domain.message import MessageDeprecated
from core.domain.models import Model, Provider
from core.domain.models.utils import get_model_data
from core.providers.base.abstract_provider import AbstractProvider
from core.providers.base.provider_options import ProviderOptions
from core.providers.factory.local_provider_factory import LocalProviderFactory

_provider_factory = LocalProviderFactory()


class _ModelWithPriceData(NamedTuple):
    model: Model
    provider: AbstractProvider[Any, Any]
    prompt_cost_per_token: float
    completion_cost_per_token: float
    prompt_cached_tokens_discount: float

    def __str__(self):
        return f"{self.model} - {self.provider.name()}"


# For each model, the price per token should be the same for all providers
# Since we should only use the provider for pricing
def active_models_with_price(providers: set[Provider] | None = None):
    if providers is None:
        # TODO: we need to adapt this test, provider for pricing should not be used anymore
        # https://linear.app/workflowai/issue/WOR-3373/sanitize-cost-computations
        providers = {Provider.OPEN_AI}

    for model in Model:
        model_data = get_model_data(model)
        pricing_data = model_data.provider_data_for_pricing()
        if pricing_data.text_price.prompt_cost_per_token == 0:
            continue
        for provider, _ in model_data.providers:
            if provider not in providers:
                continue
            provider_cls = _provider_factory.get_provider(provider)

            m = _ModelWithPriceData(
                model,
                provider_cls,
                pricing_data.text_price.prompt_cost_per_token,
                pricing_data.text_price.completion_cost_per_token,
                pricing_data.text_price.prompt_cached_tokens_discount,
            )
            yield pytest.param(m, id=str(m))


def test_active_models_with_price():
    # Test to check out that the fixture is working
    assert [m for m in active_models_with_price()]


def _llm_completion(messages: list[dict[str, Any]], usage: LLMUsage, response: str | None = None):
    return LLMCompletion(
        messages=messages,
        usage=usage,
        response=response,
        provider=Provider.OPEN_AI,
    )


class TestProviderCostCalculation:
    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed(
        self,
        model_with_price: _ModelWithPriceData,
    ):
        # Test the case when both the prompt and completion token counts are fed in the original usage

        llm_usage = await model_with_price.provider.compute_llm_completion_usage(
            model=model_with_price.model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    completion_token_count=20,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response="Hello you !",
            ),
        )

        assert llm_usage.prompt_token_count == 10  # from initial usage
        assert llm_usage.prompt_cost_usd == pytest.approx(model_with_price.prompt_cost_per_token * 10, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
        assert llm_usage.completion_token_count == 20  # from initial usage
        assert llm_usage.completion_cost_usd == pytest.approx(  # pyright: ignore [reportUnknownMemberType]
            model_with_price.completion_cost_per_token * 20,
            abs=1e-10,
        )

    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed_no_response(
        self,
        model_with_price: _ModelWithPriceData,
    ):
        # Test the case when both the prompt and completion token counts are fed in the original usage, but no response

        llm_usage = await model_with_price.provider.compute_llm_completion_usage(
            model=model_with_price.model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    completion_token_count=20,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response=None,
            ),
        )
        assert llm_usage.cost_usd != 0

    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed_no_response_no_completion_tokens(
        self,
        model_with_price: _ModelWithPriceData,
    ):
        # Test the case when both the prompt and completion token counts are fed in the original usage, but no response

        llm_usage = await model_with_price.provider.compute_llm_completion_usage(
            model=model_with_price.model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    completion_token_count=0,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response=None,
            ),
        )
        assert llm_usage.cost_usd == 0

    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed_with_cached_tokens(self, model_with_price: _ModelWithPriceData):
        # Test the case when both the prompt and completion token counts are fed in the original usage, with cached tokens

        model, provider, prompt_cost_per_token, completion_cost_per_token, prompt_cached_tokens_discount = (
            model_with_price
        )

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    prompt_token_count_cached=4,
                    completion_token_count=20,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response="Hello you !",
            ),
        )

        assert llm_usage.prompt_token_count == 10  # from initial usage

        assert llm_usage.prompt_cost_usd == pytest.approx(  # pyright: ignore [reportUnknownMemberType]
            (prompt_cost_per_token * 6) + ((1 - prompt_cached_tokens_discount) * 4 * prompt_cost_per_token),
            abs=1e-10,
        )
        assert llm_usage.completion_token_count == 20  # from initial usage
        assert llm_usage.completion_cost_usd == pytest.approx(completion_cost_per_token * 20, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]

    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed_with_cached_tokens_no_response(self, model_with_price: _ModelWithPriceData):
        model, provider, _, _, _ = model_with_price

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    prompt_token_count_cached=4,
                    completion_token_count=20,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response=None,
            ),
        )
        assert llm_usage.cost_usd != 0

    @pytest.mark.parametrize("model_with_price", active_models_with_price())
    async def test_token_count_is_fed_with_cached_tokens_no_response_no_completion_tokens(
        self,
        model_with_price: _ModelWithPriceData,
    ):
        model, provider, _, _, _ = model_with_price

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=_llm_completion(
                messages=[],
                usage=LLMUsage(
                    prompt_token_count=10,
                    prompt_token_count_cached=4,
                    completion_token_count=0,
                    prompt_image_count=0,
                    prompt_audio_token_count=0,
                    prompt_audio_duration_seconds=0,
                ),
                response=None,
            ),
        )
        assert llm_usage.cost_usd == 0

    # TODO: generalize the test to all providers, for now only openai has the "boilerplate" tokens
    @pytest.mark.parametrize("model_with_price", active_models_with_price(providers={Provider.OPEN_AI}))
    async def test_token_count_is_not_fed(self, model_with_price: _ModelWithPriceData):
        # Test the case when the token count is not fed in the original usage

        model, provider, prompt_cost_per_token, completion_cost_per_token, _ = model_with_price
        messages = [MessageDeprecated(content="Hello !", role=MessageDeprecated.Role.USER)]
        _, raw_completion = await provider._prepare_completion(  # pyright: ignore[reportPrivateUsage]
            messages,
            ProviderOptions(model=model),
            stream=False,
        )
        raw_completion.response = "Hello you !"

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=raw_completion,
        )

        assert (
            llm_usage.prompt_token_count == 9
        )  # computed from the messages, 2 tokens + 7 "message boilerplate" tokens
        assert llm_usage.prompt_cost_usd == pytest.approx(prompt_cost_per_token * 9, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
        assert llm_usage.completion_token_count == 3  # computed from the completion
        assert llm_usage.completion_cost_usd == pytest.approx(completion_cost_per_token * 3, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]

    # TODO: generalize the test to all providers, for now only openai has the "boilerplate" tokens
    @pytest.mark.parametrize("model_with_price", active_models_with_price(providers={Provider.OPEN_AI}))
    async def test_token_count_is_not_fed_multiple_messages_and_long_completion(
        self,
        model_with_price: _ModelWithPriceData,
    ):
        # Test the case when the token count is not fed in the original usage

        model, provider, prompt_cost_per_token, completion_cost_per_token, _ = model_with_price
        messages = [
            MessageDeprecated(content="Hello !", role=MessageDeprecated.Role.USER),
            MessageDeprecated(content="How are you !", role=MessageDeprecated.Role.USER),
        ]
        _, raw_completion = await provider._prepare_completion(  # pyright: ignore[reportPrivateUsage]
            messages,
            ProviderOptions(model=model),
            stream=False,
        )
        raw_completion.response = "Hello " * 999 + "."

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=raw_completion,
        )

        assert (
            llm_usage.prompt_token_count == 17
        )  # computed from the messages, 2 tokens + 4 tokens + 7 "boilerplate" tokens + 4 "boilerplate tokens"
        assert llm_usage.prompt_cost_usd == pytest.approx(prompt_cost_per_token * 17, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
        assert llm_usage.completion_token_count == 1000  # computed from the completion, 999 hellos + 1 period
        assert llm_usage.completion_cost_usd == pytest.approx(completion_cost_per_token * 1000, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]

    # TODO: generalize the test to all providers
    @pytest.mark.parametrize("model_with_price", active_models_with_price(providers={Provider.OPEN_AI}))
    async def test_only_prompt_count_is_fed(self, model_with_price: _ModelWithPriceData):
        # Test the case when the prompt token count is fed in the original usage but the completion token count is not

        model, provider, prompt_cost_per_token, completion_cost_per_token, _ = model_with_price
        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=_llm_completion(
                messages=[{"role": "user", "content": "Hello !"}],
                response="Hello you !",
                usage=LLMUsage(prompt_token_count=10),
            ),
        )

        model, provider, prompt_cost_per_token, completion_cost_per_token, _ = model_with_price

        assert llm_usage.prompt_token_count == 10  # from initial usage
        assert llm_usage.prompt_cost_usd == pytest.approx(prompt_cost_per_token * 10, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
        assert llm_usage.completion_token_count == 3  # computed from the completion
        assert llm_usage.completion_cost_usd == pytest.approx(completion_cost_per_token * 3, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]

    # TODO: generalize the test to all providers, for now only openai has the "boilerplate" tokens
    @pytest.mark.parametrize("model_with_price", active_models_with_price(providers={Provider.OPEN_AI}))
    async def test_only_completion_count_is_fed(self, model_with_price: _ModelWithPriceData):
        # Test the case when the completion token count is fed in the original usage but the prompt token count is not

        model, provider, prompt_cost_per_token, completion_cost_per_token, _ = model_with_price

        messages = [MessageDeprecated(content="Hello !", role=MessageDeprecated.Role.USER)]
        _, raw_completion = await provider._prepare_completion(  # pyright: ignore[reportPrivateUsage]
            messages,
            ProviderOptions(model=model),
            stream=False,
        )
        raw_completion.response = "Hello you !"
        raw_completion.usage.completion_token_count = 20

        llm_usage = await provider.compute_llm_completion_usage(
            model=model,
            completion=raw_completion,
        )

        assert (
            llm_usage.prompt_token_count == 9
        )  # computed from the messages, 2 tokens + 7 "message boilerplate" tokens
        assert llm_usage.prompt_cost_usd == pytest.approx(prompt_cost_per_token * 9, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
        assert llm_usage.completion_token_count == 20  # from initial usage
        assert llm_usage.completion_cost_usd == pytest.approx(completion_cost_per_token * 20, abs=1e-10)  # pyright: ignore [reportUnknownMemberType]
