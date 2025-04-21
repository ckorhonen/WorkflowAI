import datetime

import pytest
from pydantic import BaseModel

from core.domain.errors import ProviderDoesNotSupportModelError
from core.domain.models import Model, Provider
from core.domain.models.model_data_supports import ModelDataSupports
from core.domain.models.model_provider_data import ModelProviderData
from core.domain.models.utils import get_model_provider_data
from core.domain.task_typology import TaskTypology
from core.providers.amazon_bedrock.amazon_bedrock_provider import AmazonBedrockProvider
from core.providers.fireworks.fireworks_provider import FireworksAIProvider
from core.providers.google.google_provider import GoogleProvider
from core.providers.openai.openai_provider import OpenAIProvider

from .model_data import DeprecatedModel, FinalModelData, LatestModel, ModelData
from .model_datas_mapping import MODEL_DATAS
from .model_provider_datas_mapping import MODEL_PROVIDER_DATAS


def test_MODEL_DATAS_is_exhaustive() -> None:
    """
    Test that all provider x model combinations are defined in 'MODEL_DATAS'
    """
    for model in Model:
        assert model in MODEL_DATAS


def assert_model_data_has_all_fields_defined(obj: BaseModel, exclude: set[str] | None = None) -> None:
    fields = [field for field, _ in type(obj).model_fields.items()]
    for field in fields:
        if exclude and field in exclude:
            continue
        assert getattr(obj, field) is not None, f"Field '{field}' is not defined for model {obj}"


def test_assert_model_data_has_all_fields_defined_should_not_raise() -> None:
    class Model(BaseModel):
        display_name: str
        some_other_field: str | None = None

    # Test that 'assert_model_data_has_all_fields_defined' does not raise an error when all fields are defined
    assert_model_data_has_all_fields_defined(
        Model(display_name="test", some_other_field="test"),
    )

    # Test that 'assert_model_data_has_all_fields_defined' raise an error when a field is not defined
    with pytest.raises(AssertionError):
        assert_model_data_has_all_fields_defined(
            Model(display_name="test"),
        )


# Test that all models MODEL_DATAS have all fields defined, even if optional
# TODO: remove, this test is a duplicate of pydantic model validation
def test_MODEL_DATAS_has_all_fields_defined() -> None:
    for model in Model:
        model_data = MODEL_DATAS[model]
        if isinstance(model_data, ModelData):
            assert_model_data_has_all_fields_defined(
                model_data,
                exclude={"latest_model", "quality_index", "reasoning_level"},
            )


@pytest.fixture
def today():
    return datetime.date.today()


class TestDeprecatedModels:
    def test_no_nested_replacement(self):
        # Check all replacement models do not have a replacement model themselves
        for value in MODEL_DATAS.values():
            if not isinstance(value, DeprecatedModel):
                continue

            replacement_data = MODEL_DATAS[value.replacement_model]
            assert isinstance(
                replacement_data,
                ModelData,
            ), f"Replacement model {value.replacement_model} is not a ModelData"

    def test_that_all_models_that_are_fully_sunset_have_a_replacement_model(self, today: datetime.date):
        """Check that if a model is fully sunset on all providers, it is a deprecated model and not a ModelData"""

        def _check(model: Model):
            for provider_data_by_model in MODEL_PROVIDER_DATAS.values():
                if model not in provider_data_by_model:
                    continue

                provider_data = provider_data_by_model[model]
                if provider_data.replacement_model(today) is None:
                    # We have found a model that has no replacement
                    # So the model is not sunset on all providers
                    return
            raise AssertionError(f"Model {model} is fully sunset but has no replacement model")

        for model in Model:
            model_data = MODEL_DATAS[model]
            if not isinstance(model_data, ModelData):
                continue

            _check(model)

    def test_deprecated_models_have_no_provider_data(self):
        # Check that we do not store data for non active models
        for model in Model:
            model_data = MODEL_DATAS[model]
            if isinstance(model_data, ModelData):
                continue

            for provider, provider_data_by_model in MODEL_PROVIDER_DATAS.items():
                assert model not in provider_data_by_model, (
                    f"Model {model} is deprecated but has provider data with provider {provider}"
                )


def _versioned_models():
    for model, model_data in MODEL_DATAS.items():
        if isinstance(model_data, ModelData):
            yield model, model_data


class TestProviderForPricing:
    def test_provider_for_pricing_exists(self, today: datetime.date):
        for model, model_data in _versioned_models():
            try:
                get_model_provider_data(model_data.provider_for_pricing, model)
            except ProviderDoesNotSupportModelError:
                raise AssertionError(f"Provider {model_data.provider_for_pricing} does not support model {model}")

    def test_openai_supported_models_use_openai_as_primary(self):
        found = False
        for model in OpenAIProvider.all_supported_models():
            model_data = MODEL_DATAS[model]
            if not isinstance(model_data, FinalModelData):
                continue
            found = True
            assert model_data.providers[0][0] == Provider.OPEN_AI, (
                f"Model {model} should use OpenAI as primary provider"
            )
        assert found

    def test_fireworks_supported_models_use_fireworks_for_pricing(self):
        for model in FireworksAIProvider.all_supported_models():
            model_data = MODEL_DATAS[model]
            if not isinstance(model_data, ModelData):
                continue
            assert model_data.provider_for_pricing == Provider.FIREWORKS, (
                f"Model {model} should use Fireworks for pricing"
            )

    def test_amazon_supported_models_use_amazon_for_pricing(self):
        # Check that we use amazon for pricing for all models that are supported by amazon
        for model in AmazonBedrockProvider.all_supported_models():
            model_data = MODEL_DATAS[model]
            if not isinstance(model_data, ModelData):
                continue
            if model_data.provider_for_pricing == Provider.FIREWORKS:
                # Fireworks has priority
                continue
            assert model_data.provider_for_pricing == Provider.AMAZON_BEDROCK, (
                f"Model {model} should use Amazon Bedrock for pricing"
            )

    def test_google_supported_models_use_google_for_pricing(self):
        # Check that we use google for pricing for all models that are supported by google
        for model in GoogleProvider.all_supported_models():
            model_data = MODEL_DATAS[model]
            if not isinstance(model_data, ModelData):
                continue
            if model_data.provider_for_pricing == Provider.AMAZON_BEDROCK:
                # Bedrock has priority
                continue
            if model_data.provider_for_pricing == Provider.FIREWORKS:
                # Fireworks has priority
                continue
            assert model_data.provider_for_pricing == Provider.GOOGLE, f"Model {model} should use Google for pricing"


class TestProviders:
    def test_providers_is_set(self):
        for model, model_data in _versioned_models():
            assert model_data.providers, f"Providers for model {model} are not set"

    def test_providers_is_accurate(self):
        for model, model_data in _versioned_models():
            found: list[tuple[Provider, ModelProviderData]] = []
            for provider, provider_data_by_model in MODEL_PROVIDER_DATAS.items():
                if model not in provider_data_by_model:
                    continue

                provider_data = provider_data_by_model[model]
                found.append((provider, provider_data))

            for f in found:
                assert f in model_data.providers, f"Provider {f} is not in model {model} providers"


class TestProviderDataForPricing:
    def test_provider_data_for_pricing(self):
        for model, model_data in _versioned_models():
            assert model_data.provider_data_for_pricing() is not None, f"Provider data for model {model} is not set"


class TestImageURL:
    def test_image_url_is_set(self):
        for model, model_data in _versioned_models():
            assert model_data.icon_url, f"Icon url for model {model} is not set"

    def test_all_gemini_models_have_google_icon_url(self):
        for model, model_data in _versioned_models():
            if "gemini" in model_data.display_name.lower():
                assert "google" in model_data.icon_url, f"Icon url for model {model} is not set"

    def test_all_mistral_models_have_mistral_icon_url(self):
        for model, model_data in _versioned_models():
            if "istral" in model_data.display_name.lower():
                assert "mistral" in model_data.icon_url, f"Icon url for model {model} is not set"

    def test_all_claude_models_have_anthropic_icon_url(self):
        for model, model_data in _versioned_models():
            if "claude" in model_data.display_name.lower():
                assert "anthropic" in model_data.icon_url, f"Icon url for model {model} is not set"

    def test_all_groq_models_have_meta_icon_url(self):
        for model, model_data in _versioned_models():
            if "llama" in model_data.display_name.lower():
                assert "meta" in model_data.icon_url, f"Icon url for model {model} is not set"


class TestLatestModels:
    def test_all_latest_models_are_mapped(self):
        for model, model_data in MODEL_DATAS.items():
            if not isinstance(model_data, LatestModel):
                continue
            assert "latest" in model.value

            mapped_model = MODEL_DATAS[model_data.model]
            assert isinstance(mapped_model, ModelData), f"Mapped model {model_data.model} is not a ModelData"
            assert mapped_model.latest_model == model, f"Mapped model {model_data.model} is not the latest model"

    def test_latel_models_all_have_an_icon_url(self):
        for model, model_data in MODEL_DATAS.items():
            if not isinstance(model_data, LatestModel):
                continue
            assert model_data.icon_url, f"Icon url for model {model} is not set"

    def test_latest_model_field(self):
        # Check that all latest_model fields map to a LatestModel object
        for model, model_data in MODEL_DATAS.items():
            if not isinstance(model_data, ModelData):
                continue
            if model_data.latest_model is None:
                continue
            assert isinstance(
                MODEL_DATAS[model_data.latest_model],
                LatestModel,
            ), f"Latest model {model_data.latest_model} is not a LatestModel for model {model}"

    def test_latest_model_is_more_permissive(self):
        # Check that all latest models are more permissive than the model they replace
        # This is a sanity check because we do not want to replace a model by one that supports less to avoid breaking
        # existing tasks
        for model, model_data in MODEL_DATAS.items():
            if not isinstance(model_data, ModelData) or not model_data.latest_model:
                continue

            latest_model_data = MODEL_DATAS[model_data.latest_model]
            assert isinstance(latest_model_data, LatestModel), "sanity"

            actual_model_data = MODEL_DATAS[latest_model_data.model]

            # Extracting model_data_supports from both objects
            model_data_supports = ModelDataSupports.model_validate(model_data.model_dump()).model_dump()
            latest_model_data_supports = ModelDataSupports.model_validate(actual_model_data.model_dump()).model_dump()

            # Keys for which being more tolerant is reversed
            negative_keys = {"supports_audio_only"}

            for k, latest_model_value in latest_model_data_supports.items():
                assert isinstance(latest_model_value, bool), "sanity"
                current_model_value = model_data_supports[k]
                assert isinstance(current_model_value, bool), "sanity"

                if latest_model_value == current_model_value:
                    continue

                # If the 2 are not the same we expect the latest model to be more permissive, i-e:
                # - "true" when the property is not negative
                # - "false" when the property is negative
                is_negative = k in negative_keys

                assert latest_model_value is not is_negative, (
                    f"Latest model {model_data.latest_model} is not more permissive than model {model} for key {k}"
                )


class TestModelAvailability:
    @pytest.mark.parametrize(
        "typology",
        [
            pytest.param(
                TaskTypology(
                    has_image_in_input=False,
                    has_multiple_images_in_input=False,
                    has_audio_in_input=False,
                ),
                id="text",
            ),
            pytest.param(
                TaskTypology(
                    has_image_in_input=True,
                    has_multiple_images_in_input=False,
                    has_audio_in_input=False,
                ),
                id="image",
            ),
            pytest.param(
                TaskTypology(
                    has_image_in_input=True,
                    has_multiple_images_in_input=True,
                    has_audio_in_input=False,
                ),
                id="multiple_images",
            ),
            pytest.param(
                TaskTypology(
                    has_image_in_input=False,
                    has_multiple_images_in_input=False,
                    has_audio_in_input=True,
                ),
                id="audio",
            ),
        ],
    )
    def test_minimum_models_per_typology(self, typology: TaskTypology):
        # Count models that support this typology
        supported_models: list[ModelData | LatestModel] = []
        for model_data in MODEL_DATAS.values():
            if isinstance(model_data, DeprecatedModel):
                continue

            if isinstance(model_data, LatestModel):
                model_data_for_check = MODEL_DATAS[model_data.model]
                assert isinstance(model_data_for_check, ModelData), "sanity"
            else:
                model_data_for_check = model_data

            if model_data_for_check.is_not_supported_reason(typology) is not None:
                continue
            supported_models.append(model_data)

        # Build description of typology for error message
        default_models = [model for model in supported_models if model.is_default]
        # Assert we have at least 3 models supporting this typology
        assert len(default_models) >= 3


class TestUniqueness:
    def test_all_models_have_unique_display_names(self):
        display_names: set[str] = set()
        for model, model_data in MODEL_DATAS.items():
            if isinstance(model_data, ModelData):
                assert model_data.display_name is not None, f"Display name for model {model} is not set"
                display_names.add(model_data.display_name)

        # Check that all display names are unique
        assert len(display_names) == len(
            [m for m in MODEL_DATAS.values() if isinstance(m, ModelData)],
        ), "Some models have duplicate display names"


class TestMaxTokens:
    def test_max_tokens_is_set(self):
        for model, model_data in MODEL_DATAS.items():
            if not isinstance(model_data, ModelData):
                continue

            assert model_data.max_tokens_data.max_tokens > 0, f"Model {model} has no max tokens"
