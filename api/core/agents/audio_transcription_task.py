# Install the SDK

import workflowai
from pydantic import BaseModel
from workflowai.fields import Audio

from core.domain.deprecated.task import Task
from core.domain.errors import InternalError
from core.domain.fields.file import File
from core.domain.models.models import Model


class AudioTranscriptionTaskInput(BaseModel):
    audio_file: Audio


class AudioTranscriptionTaskOutput(BaseModel):
    transcription: str


# This is a task that transcribes an audio file, It could not yet be built by WorkflowAI
# as the format is not yet supported by the frontend/SDK
# https://linear.app/workflowai/issue/WOR-1774/ux-audio-file-inputs
class AudioTranscriptionTask(Task[AudioTranscriptionTaskInput, AudioTranscriptionTaskOutput]):
    input_class: type[AudioTranscriptionTaskInput] = AudioTranscriptionTaskInput
    output_class: type[AudioTranscriptionTaskOutput] = AudioTranscriptionTaskOutput
    instructions: str = ""


@workflowai.agent(id="audio-transcription", model=Model.GEMINI_2_0_FLASH_LATEST)
async def audio_transcription_agent(input: AudioTranscriptionTaskInput) -> AudioTranscriptionTaskOutput:
    """Transcribe the audio file. If the audio is not clear, do your best effort to transcribe it.
    Transcribe in the original language of speech if possible. If the language cannot be determined or transcribed accurately,
    default to transcribing in English. Pauses in speech should be transcribed as '...'.
    Capture the speaker's tone, intent and emotions e.x. exclamations and other intonations that convey emotion.
    """
    ...


# Wrapper to use domain file object
async def transcribe_audio(file: File, model: str | None = None) -> str:
    if not file.is_audio:
        raise InternalError(
            "File is not an audio file",
            extras={"file": file.model_dump(mode="json", exclude={"data"})},
        )
    converted = Audio(
        url=file.url,
        data=file.data,
        content_type=file.content_type,
    )

    return (
        await audio_transcription_agent(
            AudioTranscriptionTaskInput(
                audio_file=converted,
            ),
            model=model,
        )
    ).transcription
