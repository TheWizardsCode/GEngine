"""Simple chat interface for testing TinyLlama ONNX model.

This script provides an interactive chat interface that uses TinyLlama-1.1B-Chat-v1.0
running locally with ONNX Runtime and NPU acceleration (QNNExecutionProvider).

Usage
-----
Set up the environment variables:
    export TINYLLAMA_MODEL_PATH=/path/to/tinyllama-1.1b-chat-v1.0.onnx
    export TINYLLAMA_TOKENIZER_PATH=/path/to/tokenizer.json
    export TINYLLAMA_USE_NPU=true  # Use NPU acceleration

Then run:
    uv run echoes-tinyllama-chat

Or with Python:
    python -m gengine.echoes.llm.tinyllama_chat
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from .providers import create_provider
from .settings import LLMSettings

console = Console()


async def chat_loop(provider: Any) -> None:
    """Run interactive chat loop with TinyLlama.

    Parameters
    ----------
    provider
        TinyLlama ONNX provider instance
    """
    console.print(
        Panel(
            "[bold cyan]TinyLlama Chat Interface[/bold cyan]\n\n"
            "This is a simple chat interface using TinyLlama-1.1B-Chat-v1.0 "
            "running locally with ONNX Runtime.\n\n"
            "Commands:\n"
            "  /quit or /exit - Exit the chat\n"
            "  /help - Show this help message\n"
            "  /info - Show model information\n\n"
            "Type your message and press Enter to chat.",
            title="Welcome",
            border_style="cyan",
        )
    )

    conversation_history: list[dict[str, str]] = []

    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            # Handle commands
            if user_input.lower() in ("/quit", "/exit"):
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif user_input.lower() == "/help":
                console.print(
                    Panel(
                        "Commands:\n"
                        "  /quit or /exit - Exit the chat\n"
                        "  /help - Show this help message\n"
                        "  /info - Show model information\n"
                        "  /clear - Clear conversation history\n"
                        "  /history - Show conversation history",
                        title="Help",
                        border_style="blue",
                    )
                )
                continue
            elif user_input.lower() == "/info":
                execution_provider = provider.session.get_providers()[0]
                model_path = provider.model_path
                console.print(
                    Panel(
                        f"Model: TinyLlama-1.1B-Chat-v1.0\n"
                        f"Path: {model_path}\n"
                        f"Execution Provider: {execution_provider}\n"
                        f"NPU Acceleration: {provider.use_npu}\n"
                        f"Max Length: {provider.max_length}",
                        title="Model Information",
                        border_style="blue",
                    )
                )
                continue
            elif user_input.lower() == "/clear":
                conversation_history.clear()
                console.print("[yellow]Conversation history cleared.[/yellow]")
                continue
            elif user_input.lower() == "/history":
                if not conversation_history:
                    console.print("[yellow]No conversation history yet.[/yellow]")
                else:
                    history_text = "\n\n".join(
                        f"[bold green]You:[/bold green] {msg['user']}\n"
                        f"[bold blue]TinyLlama:[/bold blue] {msg['assistant']}"
                        for msg in conversation_history
                    )
                    console.print(
                        Panel(
                            history_text,
                            title="Conversation History",
                            border_style="blue",
                        )
                    )
                continue

            if not user_input.strip():
                continue

            # Show thinking indicator
            console.print("[dim]Thinking...[/dim]", end="")

            # Generate response using narrate method
            # (We use narrate here as a simple text generation endpoint)
            events = [{"type": "user_message", "content": user_input}]
            context: dict[str, Any] = {
                "conversation": conversation_history,
            }

            result = await provider.narrate(events, context)

            # Clear thinking indicator
            console.print("\r" + " " * 20 + "\r", end="")

            # Display response
            console.print(f"[bold blue]TinyLlama:[/bold blue] {result.narrative}")

            # Store in conversation history
            conversation_history.append(
                {
                    "user": user_input,
                    "assistant": result.narrative,
                }
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[red]Error: {str(e)}[/red]")
            console.print("[yellow]Continuing...[/yellow]")
            continue


def main() -> None:
    """Main entry point for TinyLlama chat interface."""
    try:
        # Create settings with TinyLlama provider
        settings = LLMSettings(provider="tinyllama")

        # Create provider
        console.print("[cyan]Loading TinyLlama model...[/cyan]")
        provider = create_provider(settings)

        console.print("[green]Model loaded successfully![/green]")

        # Run chat loop
        asyncio.run(chat_loop(provider))

    except ImportError as e:
        console.print(
            Panel(
                f"[red bold]Missing Dependencies[/red bold]\n\n"
                f"{str(e)}\n\n"
                "Install required packages:\n"
                "  uv pip install onnxruntime tokenizers numpy",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)
    except ValueError as e:
        console.print(
            Panel(
                f"[red bold]Configuration Error[/red bold]\n\n"
                f"{str(e)}\n\n"
                "Required environment variables:\n"
                "  TINYLLAMA_MODEL_PATH - Path to ONNX model file\n"
                "  TINYLLAMA_TOKENIZER_PATH - Path to tokenizer.json\n\n"
                "Optional:\n"
                "  TINYLLAMA_USE_NPU - Use NPU acceleration (default: true)\n"
                "  TINYLLAMA_MAX_LENGTH - Max sequence length (default: 512)",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)
    except Exception as e:
        console.print(
            Panel(
                f"[red bold]Unexpected Error[/red bold]\n\n{str(e)}",
                title="Error",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
