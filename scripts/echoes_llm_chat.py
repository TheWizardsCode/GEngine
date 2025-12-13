#!/usr/bin/env python3
"""Interactive chat interface for Echoes LLM service.

This script provides a developer-facing REPL for testing the LLM service
endpoints (/parse_intent and /narrate) with multi-turn history support.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

# Add src to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gengine.echoes.llm.chat_client import LLMChatClient


def detect_service_url() -> str | None:
    """Auto-detect the LLM service URL.
    
    Tries the following in order:
    1. Windows host IP (when running in WSL)
    2. localhost
    
    Returns
    -------
    str | None
        The detected service URL, or None if not found
    """
    urls_to_try = []
    
    # Check if running in WSL and try Windows host IP
    if os.path.exists("/proc/version"):
        try:
            with open("/proc/version", "r") as f:
                version_content = f.read().lower()
                if "microsoft" in version_content or "wsl" in version_content:
                    # Running in WSL, try to get Windows host IP
                    try:
                        result = subprocess.run(
                            ["cat", "/etc/resolv.conf"],
                            capture_output=True,
                            text=True,
                            timeout=2,
                        )
                        # Look for nameserver line which points to Windows host
                        for line in result.stdout.split("\n"):
                            if line.strip().startswith("nameserver"):
                                match = re.search(r"nameserver\s+(\S+)", line)
                                if match:
                                    host_ip = match.group(1)
                                    urls_to_try.append(f"http://{host_ip}:8001")
                                    break
                    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
                        pass
        except (FileNotFoundError, PermissionError):
            pass
    
    # Always try localhost as fallback
    urls_to_try.append("http://localhost:8001")
    
    # Try each URL with a quick health check
    for url in urls_to_try:
        try:
            response = httpx.get(f"{url}/healthz", timeout=2.0)
            if response.status_code == 200:
                return url
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPError):
            continue
    
    return None


class ChatSession:
    """Manages an interactive chat session with the LLM service."""

    def __init__(
        self,
        service_url: str,
        mode: str = "parse",
        history_limit: int = 10,
        context_file: str | None = None,
    ) -> None:
        """Initialize chat session.
        
        Parameters
        ----------
        service_url
            Base URL of the LLM service
        mode
            Chat mode: "parse" or "narrate"
        history_limit
            Maximum number of history entries to keep
        context_file
            Optional JSON file with initial context
        """
        self.service_url = service_url
        self.mode = mode
        self.history_limit = history_limit
        self.history: list[dict[str, str]] = []
        self.additional_context: dict[str, Any] = {}
        
        # Load context file if provided
        if context_file:
            try:
                with open(context_file, "r") as f:
                    self.additional_context = json.load(f)
                print(f"✓ Loaded context from {context_file}")
            except Exception as e:
                print(f"⚠ Failed to load context file: {e}")

    def add_to_history(self, role: str, content: str) -> None:
        """Add an entry to the conversation history."""
        self.history.append({"role": role, "content": content})
        # Trim history to limit
        if len(self.history) > self.history_limit * 2:  # *2 for user + assistant pairs
            self.history = self.history[-self.history_limit * 2:]

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.history.clear()
        print("✓ History cleared")

    def save_transcript(self, path: str) -> None:
        """Save conversation transcript to JSON file."""
        try:
            transcript = {
                "mode": self.mode,
                "service_url": self.service_url,
                "history": self.history,
                "context": self.additional_context,
            }
            with open(path, "w") as f:
                json.dump(transcript, f, indent=2)
            print(f"✓ Transcript saved to {path}")
        except Exception as e:
            print(f"✗ Failed to save transcript: {e}")

    def build_context(self) -> dict[str, Any]:
        """Build context payload including history."""
        context = dict(self.additional_context)
        if self.history:
            context["history"] = self.history
        return context

    async def handle_parse_mode(
        self,
        client: LLMChatClient,
        user_input: str,
    ) -> None:
        """Handle parse intent mode."""
        start_time = time.perf_counter()
        try:
            response = await client.parse_intent(
                user_input,
                self.build_context(),
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Display intents
            print("\n📋 Intents:")
            print(json.dumps(response.get("intents", []), indent=2))
            
            # Display metadata
            print(f"\n⏱  Latency: {latency_ms:.0f}ms")
            if "confidence" in response and response["confidence"] is not None:
                print(f"🎯 Confidence: {response['confidence']:.2f}")
            
            # Add to history
            self.add_to_history("user", user_input)
            self.add_to_history("assistant", json.dumps(response.get("intents", [])))
            
        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"\n✗ Error: {e}")

    async def handle_narrate_mode(
        self,
        client: LLMChatClient,
        user_input: str,
    ) -> None:
        """Handle narrate mode.
        
        In narrate mode, user input is interpreted as JSON events array.
        """
        start_time = time.perf_counter()
        try:
            # Try to parse user input as JSON events
            try:
                events = json.loads(user_input)
                if not isinstance(events, list):
                    events = [events]
            except json.JSONDecodeError:
                # If not JSON, create a simple event
                events = [{"type": "user_input", "content": user_input}]
            
            response = await client.narrate(
                events,
                self.build_context(),
            )
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Display narrative
            print(f"\n📖 Narrative:")
            print(response.get("narrative", ""))
            
            # Display metadata
            print(f"\n⏱  Latency: {latency_ms:.0f}ms")
            if "metadata" in response and response["metadata"]:
                metadata = response["metadata"]
                if "input_tokens" in metadata:
                    print(f"📊 Tokens: {metadata.get('input_tokens', 0)} in / {metadata.get('output_tokens', 0)} out")
            
            # Add to history
            self.add_to_history("user", json.dumps(events))
            self.add_to_history("assistant", response.get("narrative", ""))
            
        except httpx.HTTPStatusError as e:
            print(f"\n✗ HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"\n✗ Error: {e}")

    async def run(self) -> None:
        """Run the interactive chat session."""
        print(f"Echoes LLM Chat Interface")
        print(f"Service: {self.service_url}")
        print(f"Mode: {self.mode}")
        print(f"History limit: {self.history_limit}")
        print(f"\nCommands: /clear, /save <path>, /quit, /exit")
        print(f"{'=' * 60}\n")
        
        async with LLMChatClient(self.service_url) as client:
            # Health check
            try:
                health = await client.health_check()
                print(f"✓ Connected to {health.get('provider', 'unknown')} provider")
                if health.get("model"):
                    print(f"  Model: {health['model']}")
                print()
            except Exception as e:
                print(f"⚠ Warning: Health check failed: {e}\n")
            
            # Main REPL loop
            while True:
                try:
                    # Read user input
                    if self.mode == "parse":
                        prompt = "You: "
                    else:
                        prompt = "Events (JSON or text): "
                    
                    user_input = input(prompt).strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle slash commands
                    if user_input.startswith("/"):
                        if user_input in ("/quit", "/exit"):
                            print("Goodbye!")
                            break
                        elif user_input == "/clear":
                            self.clear_history()
                        elif user_input.startswith("/save "):
                            path = user_input[6:].strip()
                            self.save_transcript(path)
                        else:
                            print(f"Unknown command: {user_input}")
                        continue
                    
                    # Route to appropriate handler
                    if self.mode == "parse":
                        await self.handle_parse_mode(client, user_input)
                    else:
                        await self.handle_narrate_mode(client, user_input)
                    
                    print()  # Blank line for readability
                    
                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    break
                except EOFError:
                    print("\n\nGoodbye!")
                    break


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive chat interface for Echoes LLM service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect service (tries WSL Windows host, then localhost)
  python scripts/echoes_llm_chat.py
  
  # Connect to local service in parse mode
  python scripts/echoes_llm_chat.py --service-url http://localhost:8001
  
  # Connect in narrate mode
  python scripts/echoes_llm_chat.py --service-url http://localhost:8001 --mode narrate
  
  # Use custom context and history limit
  python scripts/echoes_llm_chat.py --service-url http://localhost:8001 \\
    --context-file context.json --history-limit 20

Environment variables:
  ECHOES_LLM_PROVIDER, ECHOES_LLM_API_KEY, ECHOES_LLM_MODEL
  (configure the service, not this client)
        """,
    )
    
    parser.add_argument(
        "--service-url",
        default=None,
        help="Base URL of the LLM service (default: auto-detect)",
    )
    parser.add_argument(
        "--mode",
        choices=["parse", "narrate"],
        default="parse",
        help="Chat mode: parse (intent JSON) or narrate (story text)",
    )
    parser.add_argument(
        "--context-file",
        help="JSON file with initial context",
    )
    parser.add_argument(
        "--history-limit",
        type=int,
        default=10,
        help="Maximum number of history entries to keep (default: 10)",
    )
    parser.add_argument(
        "--export",
        help="Export transcript to this file on exit (deprecated: use /save command)",
    )
    
    args = parser.parse_args()
    
    # Auto-detect service URL if not provided
    service_url = args.service_url
    if service_url is None:
        print("Auto-detecting LLM service...")
        service_url = detect_service_url()
        if service_url is None:
            print("\n✗ Error: Could not detect LLM service.", file=sys.stderr)
            print("  Tried:", file=sys.stderr)
            print("    - Windows host (if running in WSL)", file=sys.stderr)
            print("    - http://localhost:8001", file=sys.stderr)
            print("\n  Please ensure the service is running or specify --service-url", file=sys.stderr)
            return 1
        print(f"✓ Detected service at {service_url}\n")
    
    # Create and run session
    session = ChatSession(
        service_url=service_url,
        mode=args.mode,
        history_limit=args.history_limit,
        context_file=args.context_file,
    )
    
    try:
        asyncio.run(session.run())
        
        # Export transcript if requested
        if args.export:
            session.save_transcript(args.export)
        
        return 0
    except Exception as e:
        print(f"\n✗ Fatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
