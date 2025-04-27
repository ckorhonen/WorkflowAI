import base64

from tests.integration.common import IntegrationTestClient


async def test_imagen_provider(test_client: IntegrationTestClient):
    agent = await test_client.create_agent_v1(
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                },
                "options": {"$ref": "#/$defs/ImageOptions"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "image": {"type": "#/$defs/Image"},
            },
        },
    )

    test_client.httpx_mock.add_response(
        url="https://us-central1-aiplatform.googleapis.com/v1/projects/workflowai-dev/locations/us-central1/publishers/google/models/imagen-3.0-generate-002:predict",
        json={
            "predictions": [
                {
                    "mimeType": "image/png",
                    "bytesBase64Encoded": base64.b64encode(b"hello").decode(),
                },
            ],
        },
    )

    run = await test_client.run_task_v1(
        task=agent,
        task_input={"description": "A wolf", "options": {"shape": "landscape"}},
    )
    assert run

    assert run["task_output"]["image"]["data"] == ""
