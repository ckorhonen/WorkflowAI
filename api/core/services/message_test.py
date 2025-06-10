from core.domain.fields.file import File
from core.domain.message import MessageDeprecated
from core.services.message import merge_messages


def test_merge_messages_content_only():
    messages = [
        MessageDeprecated(content="Hello", role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="World", role=MessageDeprecated.Role.USER),
    ]
    merged = merge_messages(messages, MessageDeprecated.Role.USER)
    assert merged.content == "Hello\n\nWorld"
    assert merged.files is None
    assert merged.role == MessageDeprecated.Role.USER


def test_merge_messages_with_mixed_files():
    image1 = File(content_type="image/jpeg", data="somedata")
    audio1 = File(content_type="audio/wav", data="someotherdat")
    messages = [
        MessageDeprecated(content="Message 1", files=[image1], role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="Message 2", files=[audio1], role=MessageDeprecated.Role.USER),
    ]
    merged = merge_messages(messages, MessageDeprecated.Role.USER)
    assert merged.content == "Message 1\n\nMessage 2"
    assert merged.files == [image1, audio1]
    assert merged.role == MessageDeprecated.Role.USER


def test_merge_messages_with_images():
    image1 = File(content_type="image/jpeg", data="somedata")
    image2 = File(content_type="image/jpeg", data="someotherdat")
    messages = [
        MessageDeprecated(content="Message 1", files=[image1], role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="Message 2", files=[image2], role=MessageDeprecated.Role.USER),
    ]
    merged = merge_messages(messages, MessageDeprecated.Role.USER)
    assert merged.content == "Message 1\n\nMessage 2"
    assert merged.files == [image1, image2]
    assert merged.role == MessageDeprecated.Role.USER


def test_merge_messages_mixed():
    image = File(content_type="image/jpeg", data="some data")
    audio = File(content_type="audio/wav", data="some data")
    messages = [
        MessageDeprecated(content="Text only", role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="With image", files=[image], role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="With audio", files=[audio], role=MessageDeprecated.Role.USER),
    ]
    merged = merge_messages(messages, MessageDeprecated.Role.USER)
    assert merged.content == "Text only\n\nWith image\n\nWith audio"
    assert merged.files == [image, audio]
    assert merged.role == MessageDeprecated.Role.USER


def test_merge_messages_empty_list():
    merged = merge_messages([], MessageDeprecated.Role.USER)
    assert merged.content == ""
    assert merged.files is None
    assert merged.role == MessageDeprecated.Role.USER


def test_merge_messages_different_roles():
    messages = [
        MessageDeprecated(content="User message", role=MessageDeprecated.Role.USER),
        MessageDeprecated(content="Assistant message", role=MessageDeprecated.Role.ASSISTANT),
    ]
    merged = merge_messages(messages, MessageDeprecated.Role.SYSTEM)
    assert merged.content == "User message\n\nAssistant message"
    assert merged.files is None
    assert merged.role == MessageDeprecated.Role.SYSTEM
