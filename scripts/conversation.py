# A script that simulates a conversation with a model using OpenAI streaming and Rich UI

import os
from typing import Iterator

import typer
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.spinner import Spinner


def _stream_response(client: OpenAI, messages: list[ChatCompletionMessageParam], model: str) -> Iterator[str]:
    """Stream the response from OpenAI and yield chunks of text."""
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


def _chat(model: str = "gpt-4o"):
    console = Console()
    client = OpenAI(api_key=os.getenv("WORKFLOWAI_API_KEY"), base_url=f"{os.getenv('WORKFLOWAI_API_URL')}/v1")

    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": "You are a helpful assistant."},
    ]

    while True:
        # Get user input
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if user_input.lower() in ["exit", "quit", "bye"]:
            console.print("[yellow]Goodbye![/yellow]")
            break

        # Add user message to conversation
        messages.append({"role": "user", "content": user_input})

        # Display AI response with streaming
        console.print("\n[bold blue]Assistant[/bold blue]:")

        full_response = ""

        # Use Live to update the display in real-time
        with Live(console=console, refresh_per_second=10) as live:
            # Show thinking spinner initially
            live.update(Spinner("dots", text="Thinking..."))

            try:
                # Stream the response
                for chunk in _stream_response(client, messages, model):
                    full_response += chunk
                    # Update the live display with the current response
                    live.update(Markdown(full_response))

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                continue

        # Add assistant response to conversation
        messages.append({"role": "assistant", "content": full_response})

        console.print()  # Add some spacing


if __name__ == "__main__":
    load_dotenv(override=True)
    typer.run(_chat)
