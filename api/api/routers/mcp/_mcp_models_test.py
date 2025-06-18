# pyright: reportPrivateUsage=false
from datetime import date
from typing import Any
from unittest.mock import Mock

import pytest

from api.routers.mcp._mcp_models import ConciseModelResponse
from core.domain.models import Provider
from core.domain.models.model_provider_data import ModelProviderData, TextPricePerToken


@pytest.fixture
def mock_text_price() -> TextPricePerToken:
    """Create a mock TextPricePerToken for testing"""
    return TextPricePerToken(
        prompt_cost_per_token=0.001,
        completion_cost_per_token=0.002,
        source="test-source",
    )


@pytest.fixture
def mock_provider_data(mock_text_price: TextPricePerToken) -> ModelProviderData:
    """Create a mock ModelProviderData for testing"""
    return ModelProviderData(text_price=mock_text_price)


@pytest.fixture
def mock_final_model_data(mock_provider_data: ModelProviderData) -> Any:
    """Create a mock FinalModelData for testing"""
    model_data = Mock()
    model_data.providers = [(Provider.OPEN_AI, mock_provider_data)]
    model_data.provider_name = "OpenAI"
    model_data.display_name = "GPT-4"
    model_data.release_date = date(2024, 1, 15)
    model_data.quality_index = 100

    # Mock model_dump to return supports fields - only whitelisted ones will be included
    model_data.model_dump.return_value = {
        "supports_tool_calling": True,
        "supports_input_image": True,
        "supports_input_pdf": True,
        "supports_input_audio": True,
        "supports_audio_only": False,  # False value should be ignored
        "supports_json_mode": True,  # Not in whitelist, should be ignored
        "supports_structured_output": True,  # Not in whitelist, should be ignored
        "support_system_messages": True,  # Not in whitelist, should be ignored
        "supports_parallel_tool_calls": True,  # Not in whitelist, should be ignored
        "other_field": "value",  # Should be ignored
    }

    return model_data


class TestConciseModelResponseFromModelData:
    def test_basic_functionality(self, mock_final_model_data: Any, mock_provider_data: ModelProviderData):
        """Test basic functionality with typical model data"""
        result = ConciseModelResponse.from_model_data("test-model-id", mock_final_model_data)

        assert result.id == "test-model-id"
        assert result.maker == "OpenAI"
        assert result.display_name == "GPT-4"
        assert result.cost_per_input_token_usd == 0.001
        assert result.cost_per_output_token_usd == 0.002
        assert result.release_date == "2024-01-15"

        # Check supports filtering - only whitelisted fields that are True should be included
        expected_supports = ["tool_calling", "input_image", "input_pdf", "input_audio"]
        assert sorted(result.supports) == sorted(expected_supports)

    def test_only_whitelisted_supports_included(self, mock_final_model_data: Any):
        """Test that only whitelisted supports are included"""
        result = ConciseModelResponse.from_model_data("test-id", mock_final_model_data)

        # These should NOT be in the result because they're not in the whitelist
        assert "json_mode" not in result.supports
        assert "structured_output" not in result.supports
        assert "system_messages" not in result.supports
        assert "parallel_tool_calls" not in result.supports

        # Only whitelisted ones should be included
        for support in result.supports:
            assert support in ["tool_calling", "input_image", "input_pdf", "input_audio", "audio_only"]

    def test_empty_supports_when_none_whitelisted(self, mock_provider_data: ModelProviderData):
        """Test when model has no whitelisted supports"""
        model_data = Mock()
        model_data.providers = [(Provider.ANTHROPIC, mock_provider_data)]
        model_data.provider_name = "Anthropic"
        model_data.display_name = "Claude"
        model_data.release_date = date(2023, 5, 10)
        model_data.quality_index = 95

        # Only non-whitelisted supports
        model_data.model_dump.return_value = {
            "supports_json_mode": True,  # Not in whitelist
            "supports_structured_output": True,  # Not in whitelist
            "supports_parallel_tool_calls": True,  # Not in whitelist
            "other_field": True,  # Doesn't match whitelist pattern
        }

        result = ConciseModelResponse.from_model_data("claude-id", model_data)

        # Should be empty since no whitelisted supports are present
        assert result.supports == []

    def test_all_whitelisted_supports(self, mock_provider_data: ModelProviderData):
        """Test model with all whitelisted supports enabled"""
        model_data = Mock()
        model_data.providers = [(Provider.FIREWORKS, mock_provider_data)]
        model_data.provider_name = "Fireworks"
        model_data.display_name = "Llama 3.1"
        model_data.release_date = date(2024, 7, 23)
        model_data.quality_index = 85

        # All whitelisted supports set to True
        model_data.model_dump.return_value = {
            "supports_tool_calling": True,
            "supports_input_image": True,
            "supports_input_audio": True,
            "supports_input_pdf": True,
            "supports_audio_only": True,
            # Add some non-whitelisted ones to ensure they're ignored
            "supports_output_image": True,
            "supports_json_mode": True,
        }

        result = ConciseModelResponse.from_model_data("llama-id", model_data)

        expected_supports = [
            "tool_calling",
            "input_image",
            "input_audio",
            "input_pdf",
            "audio_only",
        ]
        assert sorted(result.supports) == sorted(expected_supports)

    def test_false_values_ignored(self, mock_provider_data: ModelProviderData):
        """Test that False values are ignored even if whitelisted"""
        model_data = Mock()
        model_data.providers = [(Provider.OPEN_AI, mock_provider_data)]
        model_data.provider_name = "Test Provider"
        model_data.display_name = "Test Model"
        model_data.release_date = date(2024, 1, 1)
        model_data.quality_index = 90

        model_data.model_dump.return_value = {
            "supports_tool_calling": True,  # Should be included
            "supports_input_image": False,  # Should be ignored (False)
            "supports_input_audio": True,  # Should be included
            "supports_input_pdf": False,  # Should be ignored (False)
            "supports_audio_only": True,  # Should be included
        }

        result = ConciseModelResponse.from_model_data("test", model_data)

        expected_supports = ["tool_calling", "input_audio", "audio_only"]
        assert sorted(result.supports) == sorted(expected_supports)

    def test_different_provider_costs(self, mock_final_model_data: Any):
        """Test with different provider cost structure"""
        # Create provider data with different costs
        expensive_price = TextPricePerToken(
            prompt_cost_per_token=0.05,
            completion_cost_per_token=0.15,
            source="expensive-provider",
        )
        expensive_provider_data = ModelProviderData(text_price=expensive_price)

        # Update the first provider data
        mock_final_model_data.providers = [(Provider.AZURE_OPEN_AI, expensive_provider_data)]

        result = ConciseModelResponse.from_model_data("expensive-model", mock_final_model_data)

        assert result.cost_per_input_token_usd == 0.05
        assert result.cost_per_output_token_usd == 0.15

    @pytest.mark.parametrize(
        "test_date,expected_iso",
        [
            (date(2024, 1, 1), "2024-01-01"),
            (date(2023, 12, 31), "2023-12-31"),
            (date(2025, 6, 15), "2025-06-15"),
        ],
    )
    def test_date_formatting(self, mock_final_model_data: Any, test_date: date, expected_iso: str):
        """Test that dates are properly formatted to ISO format"""
        mock_final_model_data.release_date = test_date

        result = ConciseModelResponse.from_model_data("date-test", mock_final_model_data)

        assert result.release_date == expected_iso

    def test_uses_first_provider_for_pricing(self, mock_final_model_data: Any):
        """Test that it uses the first provider in the list for pricing"""
        # Create a second provider with different pricing
        second_price = TextPricePerToken(
            prompt_cost_per_token=0.999,
            completion_cost_per_token=0.888,
            source="second-provider",
        )
        second_provider_data = ModelProviderData(text_price=second_price)

        # Add second provider to the list
        first_provider_data: ModelProviderData = mock_final_model_data.providers[0][1]
        mock_final_model_data.providers = [
            (Provider.OPEN_AI, first_provider_data),
            (Provider.ANTHROPIC, second_provider_data),
        ]

        result = ConciseModelResponse.from_model_data("multi-provider", mock_final_model_data)

        # Should use first provider's pricing
        assert result.cost_per_input_token_usd == 0.001  # From first provider
        assert result.cost_per_output_token_usd == 0.002  # From first provider

    def test_supports_prefix_removal(self, mock_provider_data: ModelProviderData):
        """Test that 'supports_' prefix is properly removed from whitelisted field names"""
        model_data = Mock()
        model_data.providers = [(Provider.OPEN_AI, mock_provider_data)]
        model_data.provider_name = "Test Provider"
        model_data.display_name = "Test Model"
        model_data.release_date = date(2024, 1, 1)
        model_data.quality_index = 90

        model_data.model_dump.return_value = {
            "supports_tool_calling": True,  # Whitelisted - should be included as "tool_calling"
            "supports_input_image": True,  # Whitelisted - should be included as "input_image"
            "supports_custom_feature": True,  # Not whitelisted - should be ignored
        }

        result = ConciseModelResponse.from_model_data("test", model_data)

        expected_supports = ["tool_calling", "input_image"]
        assert sorted(result.supports) == sorted(expected_supports)

    def test_whitelist_exact_matching(self, mock_provider_data: ModelProviderData):
        """Test that whitelist matching is exact (no partial matches)"""
        model_data = Mock()
        model_data.providers = [(Provider.OPEN_AI, mock_provider_data)]
        model_data.provider_name = "Test Provider"
        model_data.display_name = "Test Model"
        model_data.release_date = date(2024, 1, 1)
        model_data.quality_index = 75

        model_data.model_dump.return_value = {
            "supports_tool": True,  # Similar but not exact match to "supports_tool_calling"
            "supports_tool_calling_advanced": True,  # Similar but not exact match
            "supports_tool_calling": True,  # Exact match - should be included
            "tool_calling": True,  # Missing prefix - should be ignored
        }

        result = ConciseModelResponse.from_model_data("test", model_data)

        # Only the exact whitelist match should be included
        assert result.supports == ["tool_calling"]
