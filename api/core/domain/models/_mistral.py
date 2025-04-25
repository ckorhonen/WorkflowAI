from datetime import date

from core.domain.models._displayed_provider import DisplayedProvider
from core.domain.models.model_data import DeprecatedModel, LatestModel, MaxTokensData, ModelData
from core.domain.models.models import Model
from core.domain.models.providers import Provider


def mistral_models() -> dict[Model, ModelData | LatestModel | DeprecatedModel]:
    return {
        Model.MIXTRAL_8X7B_32768: DeprecatedModel(
            replacement_model=Model.MISTRAL_SMALL_2503,
        ),
        Model.MISTRAL_LARGE_2_LATEST: LatestModel(
            model=Model.MISTRAL_LARGE_2_2407,
            display_name="Mistral Large 2 (latest)",
        ),
        Model.MISTRAL_LARGE_2_2407: ModelData(
            display_name="Mistral Large 2 (24-07)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://mistral.ai/news/mistral-large-2407/",
            ),
            provider_for_pricing=Provider.AMAZON_BEDROCK,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            latest_model=Model.MISTRAL_LARGE_2_LATEST,
            release_date=date(2024, 7, 24),
            quality_index=549,  # MMLU=84.00, GPQA=46.09
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.MISTRAL_LARGE_LATEST: LatestModel(
            model=Model.MISTRAL_LARGE_2411,
            display_name="Mistral Large (latest)",
        ),
        Model.MISTRAL_LARGE_2411: ModelData(
            display_name="Mistral Large 2 (24-11)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            latest_model=Model.MISTRAL_LARGE_LATEST,
            release_date=date(2024, 11, 24),
            quality_index=702,  # MMLU=84.00, GPQA=59.10
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.PIXTRAL_LARGE_LATEST: LatestModel(
            model=Model.PIXTRAL_LARGE_2411,
            display_name="PixTral Large (latest)",
        ),
        Model.PIXTRAL_LARGE_2411: ModelData(
            display_name="PixTral Large (24-11)",
            supports_json_mode=True,
            supports_input_image=True,
            supports_input_pdf=True,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            latest_model=Model.PIXTRAL_LARGE_LATEST,
            release_date=date(2024, 11, 24),
            quality_index=531,  # MMLU=70.10, GPQA=39.30
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.PIXTRAL_12B_2409: ModelData(
            display_name="PixTral (12B-2409)",
            supports_json_mode=True,
            supports_input_image=True,
            supports_input_pdf=True,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2024, 9, 17),
            quality_index=526,  # MMLU=69.20, GPQA=39.00
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.MINISTRAL_3B_2410: ModelData(
            display_name="MiniStral (3B-2410)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2024, 10, 24),
            quality_index=317,  # MMLU=33.90, GPQA=33.59
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.MINISTRAL_8B_2410: ModelData(
            display_name="MiniStral (8B-2410)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=131072,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2024, 10, 24),
            quality_index=426,  # MMLU=63.40, GPQA=33.80
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.MISTRAL_SMALL_LATEST: LatestModel(
            model=Model.MISTRAL_SMALL_2503,
            display_name="Mistral Small (latest)",
        ),
        Model.MISTRAL_SMALL_2503: ModelData(
            display_name="Mistral Small (25-03)",
            supports_json_mode=True,
            supports_input_image=True,
            supports_input_pdf=True,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=32768,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2025, 3, 17),
            quality_index=377,  # MMLU=52.90, GPQA=33.80
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
            latest_model=Model.MISTRAL_SMALL_LATEST,
        ),
        Model.MISTRAL_SMALL_2501: ModelData(
            display_name="Mistral Small (25-01)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=32768,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2025, 1, 13),
            quality_index=377,  # MMLU=52.90, GPQA=33.80
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
            latest_model=Model.MISTRAL_SMALL_LATEST,
        ),
        Model.MISTRAL_SMALL_2409: ModelData(
            display_name="Mistral Small (24-09)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=32768,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2024, 9, 24),
            quality_index=377,  # MMLU=52.90, GPQA=33.80
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
            latest_model=Model.MISTRAL_SMALL_LATEST,
        ),
        Model.MISTRAL_SABA_2502: ModelData(
            display_name="Mistral Saba (25-02)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=32768,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2025, 2, 17),
            quality_index=377,  # MMLU=52.90, GPQA=33.80
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.CODESTRAL_2501: ModelData(
            display_name="CodeStral Mamba (25-01)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=262144,
                source="https://docs.mistral.ai/getting-started/models/",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2025, 1, 13),
            quality_index=481,  # MMLU=63.47, GPQA=38.35
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
        Model.CODESTRAL_MAMBA_2407: ModelData(
            display_name="CodeStral Mamba (24-07)",
            supports_json_mode=True,
            supports_input_image=False,
            supports_input_pdf=False,
            supports_input_audio=False,
            max_tokens_data=MaxTokensData(
                max_tokens=262144,
                # source="https://docs.mistral.ai/getting-started/models/",
                source="https://api.mistral.ai/v1/models",
            ),
            provider_for_pricing=Provider.MISTRAL_AI,
            icon_url="https://workflowai.blob.core.windows.net/workflowai-public/mistral.svg",
            release_date=date(2024, 7, 24),
            quality_index=481,  # MMLU=63.47, GPQA=38.35
            provider_name=DisplayedProvider.MISTRAL_AI.value,
            supports_tool_calling=True,
        ),
    }
