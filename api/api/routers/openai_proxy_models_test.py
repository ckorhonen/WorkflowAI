from api.routers.openai_proxy_models import OpenAIProxyChatCompletionRequest


class TestOpenAIProxyChatCompletionRequest:
    def test_minimal_payload(self):
        """Check that we have enough defaults to accept minimal payload"""
        payload = OpenAIProxyChatCompletionRequest.model_validate(
            {
                "messages": [{"role": "user", "content": "Hello, world!"}],
                "model": "gpt-4o",
            },
        )
        assert payload
