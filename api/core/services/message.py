from core.domain.fields.file import File
from core.domain.message import MessageDeprecated


def merge_messages(messages: list[MessageDeprecated], role: MessageDeprecated.Role):
    """
    Merges message content and images from a list of messages

    """

    contents: list[str] = []
    files: list[File] = []

    for message in messages:
        contents.append(message.content)
        if message.files:
            files.extend(message.files)

    return MessageDeprecated(
        content="\n\n".join(contents),
        files=files if files else None,
        role=role,
    )
