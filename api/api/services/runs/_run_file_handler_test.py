from core.runners.workflowai.utils import (
    FileWithKeyPath,
)

from ._run_file_handler import FileHandler


class TestFileHandlerApplyFiles:
    async def test_apply_files_with_include(self):
        payload = {"image": {"data": "1234"}}
        files = [
            FileWithKeyPath(
                key_path=["image"],
                storage_url="https://test-url.com/bla",
                data="1234",
                content_type="image",
            ),
        ]
        FileHandler._apply_files(  # pyright: ignore [reportPrivateUsage]
            payload,
            files,
            include={"content_type", "url", "storage_url"},
        )
        assert payload == {
            "image": {
                "url": "https://test-url.com/bla",
                "content_type": "image",
                "storage_url": "https://test-url.com/bla",
            },
        }
