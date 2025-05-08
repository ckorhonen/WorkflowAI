from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from core.domain.models import Model, Provider
from core.domain.tenant_data import ProviderSettings
from core.providers.base.abstract_provider import AbstractProvider
from core.providers.base.config import ProviderConfig
from core.providers.base.provider_error import ProviderRateLimitError
from core.providers.factory.abstract_provider_factory import AbstractProviderFactory
from core.providers.factory.local_provider_factory import LocalProviderFactory
from core.runners.workflowai.provider_pipeline import ProviderPipeline, ProviderPipelineBuilder
from core.runners.workflowai.workflowai_options import WorkflowAIRunnerOptions


@pytest.fixture
def provider_builder():
    builder = Mock(spec=ProviderPipelineBuilder)
    # Last argument is the model data
    builder.side_effect = lambda *args: (args[0], Mock(), Mock(), args[1])  # type: ignore
    return builder


def _mock_provider(name: Provider) -> Mock:
    mock = Mock(spec=AbstractProvider)
    mock.name.return_value = name
    return mock


def _provider_settings(provider: Provider) -> ProviderSettings:
    _mock = Mock()
    _mock.provider = provider

    class MockProviderSettings(ProviderSettings):
        def decrypt(self) -> ProviderConfig:
            return _mock

    return MockProviderSettings(
        id="123",
        created_at=datetime.now(),
        provider=provider,
    )


# TODO: The tests are based on the real model data, we should patch
class TestProviderIterator:
    def test_claude_ordering_and_support(self, provider_builder: Mock):
        pipeline = ProviderPipeline(
            options=WorkflowAIRunnerOptions(
                model=Model.CLAUDE_3_5_SONNET_20241022,
                provider=None,
                is_structured_generation_enabled=None,
                instructions="",
            ),
            custom_configs=None,
            builder=provider_builder,
            factory=LocalProviderFactory(),
        )

        # List all providers
        providers = list(pipeline.provider_iterator())
        assert len(providers) == 2

        assert provider_builder.call_count == 2

        provider_1 = provider_builder.call_args_list[0].args[0]
        assert provider_1.name() == Provider.ANTHROPIC
        # Testing the override
        assert providers[0][-1].supports_input_pdf

        provider_2 = provider_builder.call_args_list[1].args[0]
        assert provider_2.name() == Provider.AMAZON_BEDROCK
        assert not providers[1][-1].supports_input_pdf

    def test_multiple_providers_forced_provider(self, provider_builder: Mock):
        mock_provider_factory = Mock(spec=AbstractProviderFactory)
        # Mock multiple providers of the same type
        mock_provider1 = _mock_provider(Provider.OPEN_AI)
        mock_provider2 = _mock_provider(Provider.OPEN_AI)
        mock_provider_factory.get_providers.return_value = [mock_provider1, mock_provider2]

        """Check that the providers are iterated correctly when a forced provider is set"""
        # Create a model that has multiple providers of the same type
        pipeline = ProviderPipeline(
            options=WorkflowAIRunnerOptions(
                model=Model.GPT_4O_MINI_2024_07_18,
                provider=Provider.OPEN_AI,
                is_structured_generation_enabled=None,
                instructions="",
            ),
            custom_configs=None,
            builder=provider_builder,
            factory=mock_provider_factory,
        )

        # List all providers
        # By setting the errors we force the pipeline to try all providers
        pipeline.errors = [ProviderRateLimitError()]
        providers = list(pipeline.provider_iterator())
        mock_provider_factory.get_providers.assert_called_once_with(Provider.OPEN_AI)
        assert len(providers) == 2

        assert provider_builder.call_count == 2

        # First provider should be tried first (non-round-robin behavior)
        provider_1 = provider_builder.call_args_list[0].args[0]
        assert provider_1 == mock_provider1

        provider_2 = provider_builder.call_args_list[1].args[0]
        assert provider_2 == mock_provider2

    @patch("random.shuffle")
    def test_round_robin_providers(self, mock_shuffle: Mock, provider_builder: Mock):
        """Test that providers with a full round robin are shuffled"""
        # Mock multiple providers of the same type
        mock_provider_factory = Mock(spec=AbstractProviderFactory)
        mock_provider1 = _mock_provider(Provider.FIREWORKS)
        mock_provider2 = _mock_provider(Provider.FIREWORKS)
        mock_provider3 = _mock_provider(Provider.FIREWORKS)
        mock_provider_factory.get_providers.return_value = [mock_provider1, mock_provider2, mock_provider3]

        mock_shuffle.side_effect = lambda providers: providers.reverse()  # type: ignore

        # Create a model that has multiple providers of the same type
        pipeline = ProviderPipeline(
            options=WorkflowAIRunnerOptions(
                model=Model.DEEPSEEK_R1_2501,
                provider=None,
                is_structured_generation_enabled=None,
                instructions="",
            ),
            custom_configs=None,
            builder=provider_builder,
            factory=mock_provider_factory,
        )

        # List all providers
        # By setting the errors we force the pipeline to try all providers
        pipeline.errors = [ProviderRateLimitError()]
        providers = list(pipeline.provider_iterator())
        assert len(providers) == 3
        mock_provider_factory.get_providers.assert_called_once_with(Provider.FIREWORKS)
        mock_shuffle.assert_called_once()

        assert provider_builder.call_count == 3

        # For round-robin providers, all providers should be shuffled
        assert [p[0] for p in providers] == [mock_provider3, mock_provider2, mock_provider1]

    def test_mixed_provider_types(self, provider_builder: Mock, mock_provider_factory: Mock):
        # Create a model that has multiple providers of different types
        pipeline = ProviderPipeline(
            options=WorkflowAIRunnerOptions(
                model=Model.GPT_4O_MINI_2024_07_18,
                provider=None,  # So we will be using Azure and OpenAI
                is_structured_generation_enabled=None,
                instructions="",
            ),
            custom_configs=None,
            builder=provider_builder,
            factory=mock_provider_factory,
        )

        # Mock multiple providers of different types
        mock_provider1 = _mock_provider(Provider.OPEN_AI)
        mock_provider2 = _mock_provider(Provider.OPEN_AI)
        mock_provider3 = _mock_provider(Provider.AZURE_OPEN_AI)
        mock_provider4 = _mock_provider(Provider.AZURE_OPEN_AI)

        # Mock the factory to return different providers based on type
        def get_providers(provider_type: Provider) -> list[Mock]:
            if provider_type == Provider.OPEN_AI:
                return [mock_provider1, mock_provider2]
            if provider_type == Provider.AZURE_OPEN_AI:
                return [mock_provider3, mock_provider4]
            return []

        mock_provider_factory.get_providers.side_effect = get_providers

        # List all providers
        # By setting the errors we force the pipeline to try all providers
        pipeline.errors = [ProviderRateLimitError()]
        providers = list(pipeline.provider_iterator())
        assert len(providers) == 4

        assert provider_builder.call_count == 4

        # First OpenAI provider should be tried first (non-round-robin)
        provider_1 = provider_builder.call_args_list[0].args[0]
        assert provider_1 == mock_provider1

        # Second OpenAI provider should be tried second
        provider_2 = provider_builder.call_args_list[1].args[0]
        assert provider_2 == mock_provider2

        # Fireworks providers should be shuffled
        provider_3 = provider_builder.call_args_list[2].args[0]
        provider_4 = provider_builder.call_args_list[3].args[0]
        assert {provider_3, provider_4} == {mock_provider3, mock_provider4}

    def test_custom_configs_with_unsupported_provider(self, provider_builder: Mock, mock_provider_factory: Mock):
        """Check that a custom config is not returned if the provider is not supported"""
        mock_provider_factory.build_provider.side_effect = lambda *args, **kwargs: _mock_provider(args[0].provider)  # type: ignore
        mock_provider_factory.get_providers.side_effect = lambda provider: [_mock_provider(provider)]  # type: ignore

        pipeline = ProviderPipeline(
            options=WorkflowAIRunnerOptions(
                model=Model.GPT_4O_MINI_2024_07_18,
                provider=None,
                is_structured_generation_enabled=None,
                instructions="",
            ),
            custom_configs=[
                _provider_settings(Provider.GROQ),
                _provider_settings(Provider.OPEN_AI),
            ],
            builder=provider_builder,
            factory=mock_provider_factory,
        )

        providers = list(pipeline.provider_iterator())
        assert len(providers) == 3
        names = [p[0].name() for p in providers]
        assert names == [Provider.OPEN_AI, Provider.OPEN_AI, Provider.AZURE_OPEN_AI]
