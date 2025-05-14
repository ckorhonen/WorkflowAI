from core.domain.integration_domain.integration_domain import (
    OFFICIAL_INTEGRATIONS,
    PROPOSED_AGENT_NAME_AND_MODEL_PLACEHOLDER,
    WORKFLOWAI_API_KEY_PLACEHOLDER,
    IntegrationKind,
    ProgrammingLanguage,
)


def test_all_integration_slugs_in_official_integrations():
    all_slug_values = {slug.value for slug in IntegrationKind}
    official_integration_slugs = {integration.slug.value for integration in OFFICIAL_INTEGRATIONS}
    assert all_slug_values == official_integration_slugs, (
        f"Mismatch between IntegrationSlug enum and OFFICIAL_INTEGRATIONS. \
Missing in OFFICIAL_INTEGRATIONS: {all_slug_values - official_integration_slugs}. \
Extra in OFFICIAL_INTEGRATIONS: {official_integration_slugs - all_slug_values}"
    )


def test_all_official_integrations_have_valid_slug():
    all_slug_values = {slug.value for slug in IntegrationKind}
    for integration in OFFICIAL_INTEGRATIONS:
        assert integration.slug in all_slug_values, (
            f"Integration '{integration.display_name}' has an invalid slug '{integration.slug}' not found in IntegrationSlug enum."
        )


def test_integration_snippets_contain_required_placeholders():
    for integration in OFFICIAL_INTEGRATIONS:
        # Check that initial snippet contains the API key placeholder
        assert WORKFLOWAI_API_KEY_PLACEHOLDER in integration.integration_chat_initial_snippet, (
            f"Integration '{integration.display_name}' is missing {WORKFLOWAI_API_KEY_PLACEHOLDER} "
            f"in integration_chat_initial_snippet"
        )

        # Check that agent naming snippet contains the agent name placeholder
        assert PROPOSED_AGENT_NAME_AND_MODEL_PLACEHOLDER in integration.integration_chat_agent_naming_snippet, (
            f"Integration '{integration.display_name}' is missing {PROPOSED_AGENT_NAME_AND_MODEL_PLACEHOLDER} "
            f"in integration_chat_agent_naming_snippet"
        )


def test_each_language_has_default_integration():
    default_languages = {
        integration.programming_language
        for integration in OFFICIAL_INTEGRATIONS
        if integration.default_for_language is True
    }
    all_languages = {language for language in ProgrammingLanguage}
    assert all_languages == default_languages, (
        "Each programming language must have exactly one default integration. "
        "Missing default for: {missing}. Extra defaults for: {extra}"
    ).format(
        missing=all_languages - default_languages,
        extra=default_languages - all_languages,
    )
