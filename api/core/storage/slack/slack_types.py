from typing import Any, Literal, NamedTuple, NotRequired, TypedDict


class SlackTextBlock(TypedDict):
    type: Literal["mrkdwn"]
    text: str


class SlackPlainTextBlock(TypedDict):
    type: Literal["plain_text"]
    text: str
    emoji: NotRequired[bool]


class SlackImageAccessory(TypedDict):
    type: Literal["image"]
    image_url: str
    alt_text: NotRequired[str]


class SlackHeaderBlock(TypedDict):
    type: Literal["header"]
    text: SlackPlainTextBlock


class SlackButtonElement(TypedDict):
    type: Literal["button"]
    text: SlackPlainTextBlock
    style: NotRequired[Literal["primary", "danger"]]
    value: str
    url: NotRequired[str]


class SlackActionsBlock(TypedDict):
    type: Literal["actions"]
    elements: list[SlackButtonElement]


class SlackSectionBlock(TypedDict, total=False):
    type: Literal["section"]
    text: NotRequired[SlackTextBlock]
    block_id: NotRequired[str]
    accessory: NotRequired[SlackImageAccessory]
    fields: NotRequired[list[SlackTextBlock]]


SlackBlock = SlackSectionBlock | SlackHeaderBlock | SlackActionsBlock


class OutboundSlackMessage(TypedDict):
    text: NotRequired[str]
    blocks: NotRequired[list[SlackBlock]]


class SlackMessage(OutboundSlackMessage):
    type: str
    user: str
    ts: str
    bot_id: NotRequired[str]


# Data structures for the webhooks events. Most field are ununsed for now.
class SlackBotProfile(NamedTuple):
    id: str
    deleted: bool
    name: str
    updated: int
    app_id: str
    user_id: str
    icons: dict[str, str]
    team_id: str


class SlackEventData(NamedTuple):
    user: str
    type: str
    ts: str
    team: str
    channel: str
    event_ts: str
    channel_type: str
    bot_id: str | None = None
    app_id: str | None = None
    text: str | None = None
    client_msg_id: str | None = None
    bot_profile: SlackBotProfile | None = None
    blocks: list[dict[str, Any]] | None = None


class SlackAuthorization(NamedTuple):
    enterprise_id: str | None
    team_id: str
    user_id: str
    is_bot: bool
    is_enterprise_install: bool


class SlackWebhookEvent(NamedTuple):
    token: str
    team_id: str
    context_team_id: str
    context_enterprise_id: str | None
    api_app_id: str
    event: SlackEventData
    type: str
    event_id: str
    event_time: int
    authorizations: list[SlackAuthorization]
    is_ext_shared_channel: bool
    event_context: str

    def is_bot_triggered(self) -> bool:
        return self.event.bot_profile is not None
