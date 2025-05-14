from ._run_previews import _messages_preview  # pyright: ignore [reportPrivateUsage]


class TestMessagesPreview:
    def test_messages_preview(self):
        assert (
            _messages_preview({"messages": [{"role": "user", "content": [{"text": "Hello, world!"}]}]})
            == "Hello, world!"
        )

    def test_messages_preview_with_file(self):
        assert (
            _messages_preview(
                {"messages": [{"role": "user", "content": [{"file": {"url": "https://example.com/file.png"}}]}]},
            )
            == "[[img:https://example.com/file.png]]"
        )
