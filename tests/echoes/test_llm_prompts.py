"""Tests for LLM prompt templates."""

from gengine.echoes.llm.prompts import (
    ANTHROPIC_INTENT_SCHEMA,
    INTENT_PARSING_SYSTEM_PROMPT,
    NARRATION_SYSTEM_PROMPT,
    OPENAI_INTENT_FUNCTIONS,
    build_intent_parsing_prompt,
    build_narration_prompt,
)


class TestOpenAIFunctionSchemas:
    """Tests for OpenAI function calling schemas."""

    def test_has_all_intent_functions(self):
        """Test that all intent types have function definitions."""
        function_names = [f["name"] for f in OPENAI_INTENT_FUNCTIONS]
        expected = [
            "inspect_target",
            "negotiate_with_faction",
            "deploy_resource",
            "pass_policy",
            "covert_action",
            "invoke_agent",
            "request_report",
        ]
        for name in expected:
            assert name in function_names

    def test_inspect_function_schema(self):
        """Test inspect function has correct schema."""
        inspect_func = next(
            f for f in OPENAI_INTENT_FUNCTIONS if f["name"] == "inspect_target"
        )
        assert "target_type" in inspect_func["parameters"]["properties"]
        assert "target_id" in inspect_func["parameters"]["properties"]
        required = inspect_func["parameters"]["required"]
        assert "target_type" in required
        assert "target_id" in required

    def test_negotiate_function_schema(self):
        """Test negotiate function has correct schema."""
        negotiate_func = next(
            f
            for f in OPENAI_INTENT_FUNCTIONS
            if f["name"] == "negotiate_with_faction"
        )
        assert "targets" in negotiate_func["parameters"]["properties"]
        assert "levers" in negotiate_func["parameters"]["properties"]
        assert "targets" in negotiate_func["parameters"]["required"]

    def test_deploy_resource_function_schema(self):
        """Test deploy resource function has correct schema."""
        deploy_func = next(
            f for f in OPENAI_INTENT_FUNCTIONS if f["name"] == "deploy_resource"
        )
        props = deploy_func["parameters"]["properties"]
        assert "resource_type" in props
        assert "amount" in props
        assert "target_district" in props
        # Check enum for resource type
        assert props["resource_type"]["enum"] == ["materials", "energy"]

    def test_request_report_function_schema(self):
        """Test request report function has correct schema."""
        report_func = next(
            f for f in OPENAI_INTENT_FUNCTIONS if f["name"] == "request_report"
        )
        props = report_func["parameters"]["properties"]
        assert "report_type" in props
        # Check report type enum
        expected_types = ["summary", "district", "faction", "agent", "environment", "director"]
        assert props["report_type"]["enum"] == expected_types


class TestAnthropicSchema:
    """Tests for Anthropic structured output schema."""

    def test_has_required_fields(self):
        """Test schema has all required fields."""
        props = ANTHROPIC_INTENT_SCHEMA["properties"]
        assert "intent_type" in props
        assert "confidence" in props
        assert "parameters" in props
        assert "narrative_context" in props

    def test_intent_type_enum(self):
        """Test intent type enum is correct."""
        intent_enum = ANTHROPIC_INTENT_SCHEMA["properties"]["intent_type"]["enum"]
        expected = [
            "INSPECT",
            "NEGOTIATE",
            "DEPLOY_RESOURCE",
            "PASS_POLICY",
            "COVERT_ACTION",
            "INVOKE_AGENT",
            "REQUEST_REPORT",
        ]
        assert intent_enum == expected

    def test_confidence_bounds(self):
        """Test confidence has correct bounds."""
        confidence = ANTHROPIC_INTENT_SCHEMA["properties"]["confidence"]
        assert confidence["minimum"] == 0.0
        assert confidence["maximum"] == 1.0

    def test_required_fields(self):
        """Test required fields list is correct."""
        required = ANTHROPIC_INTENT_SCHEMA["required"]
        assert "intent_type" in required
        assert "confidence" in required
        assert "parameters" in required


class TestSystemPrompts:
    """Tests for system prompts."""

    def test_intent_parsing_prompt_content(self):
        """Test intent parsing system prompt has key content."""
        prompt = INTENT_PARSING_SYSTEM_PROMPT
        assert "Echoes of Emergence" in prompt
        assert "INSPECT" in prompt
        assert "NEGOTIATE" in prompt
        assert "DEPLOY" in prompt
        assert "functions" in prompt.lower()

    def test_narration_prompt_content(self):
        """Test narration system prompt has key content."""
        prompt = NARRATION_SYSTEM_PROMPT
        assert "Echoes of Emergence" in prompt
        assert "narrative" in prompt.lower()
        assert "Industrial Tier" in prompt
        assert "Perimeter Hollow" in prompt
        assert "Spire" in prompt
        assert "Union of Flux" in prompt
        assert "Compact Majority" in prompt


class TestBuildIntentParsingPrompt:
    """Tests for build_intent_parsing_prompt function."""

    def test_basic_prompt(self):
        """Test building a basic intent parsing prompt."""
        prompt = build_intent_parsing_prompt("inspect the industrial tier")
        assert "inspect the industrial tier" in prompt
        assert "Player command:" in prompt

    def test_prompt_with_available_actions(self):
        """Test prompt includes available actions."""
        actions = ["inspect", "negotiate", "deploy"]
        prompt = build_intent_parsing_prompt(
            "what can I do?", available_actions=actions
        )
        assert "Currently available actions:" in prompt
        assert "inspect" in prompt
        assert "negotiate" in prompt

    def test_prompt_with_context(self):
        """Test prompt includes context information."""
        context = {
            "district": "industrial-tier",
            "tick": 42,
            "recent_events": ["Pollution increased", "Agent recruited"],
        }
        prompt = build_intent_parsing_prompt(
            "stabilize the district", context=context
        )
        assert "Current district: industrial-tier" in prompt
        assert "Current tick: 42" in prompt
        assert "Recent events:" in prompt
        assert "Pollution increased" in prompt

    def test_prompt_with_partial_context(self):
        """Test prompt handles partial context."""
        context = {"district": "perimeter-hollow"}
        prompt = build_intent_parsing_prompt("check status", context=context)
        assert "perimeter-hollow" in prompt
        assert "tick" not in prompt.lower() or "Current tick" not in prompt

    def test_prompt_limits_recent_events(self):
        """Test prompt only includes first 3 recent events."""
        context = {
            "recent_events": [
                "Event 1",
                "Event 2",
                "Event 3",
                "Event 4",
                "Event 5",
            ]
        }
        prompt = build_intent_parsing_prompt("check events", context=context)
        assert "Event 1" in prompt
        assert "Event 2" in prompt
        assert "Event 3" in prompt
        # Events 4 and 5 should not be included
        assert "Event 4" not in prompt
        assert "Event 5" not in prompt


class TestBuildNarrationPrompt:
    """Tests for build_narration_prompt function."""

    def test_empty_events(self):
        """Test prompt handles empty events list."""
        prompt = build_narration_prompt([])
        assert "nothing significant" in prompt.lower()

    def test_single_event(self):
        """Test prompt with single event."""
        events = ["Pollution increased by 15%"]
        prompt = build_narration_prompt(events)
        assert "Pollution increased by 15%" in prompt
        assert "1." in prompt

    def test_multiple_events(self):
        """Test prompt with multiple events."""
        events = [
            "Agent recruited",
            "Faction legitimacy increased",
            "Resource shortage detected",
        ]
        prompt = build_narration_prompt(events)
        assert "Agent recruited" in prompt
        assert "Faction legitimacy increased" in prompt
        assert "Resource shortage detected" in prompt
        assert "1." in prompt
        assert "2." in prompt
        assert "3." in prompt

    def test_narration_with_context(self):
        """Test narration prompt includes context."""
        events = ["Pollution spike detected"]
        context = {
            "district": "industrial-tier",
            "faction": "union-of-flux",
            "sentiment": "tense",
            "tick": 100,
        }
        prompt = build_narration_prompt(events, context)
        assert "Location: industrial-tier" in prompt
        assert "Involved faction: union-of-flux" in prompt
        assert "Sentiment: tense" in prompt
        assert "Tick: 100" in prompt

    def test_narration_with_partial_context(self):
        """Test narration prompt handles partial context."""
        events = ["Event occurred"]
        context = {"district": "spire"}
        prompt = build_narration_prompt(events, context)
        assert "Location: spire" in prompt
        assert "faction" not in prompt.lower() or "Involved faction" not in prompt

    def test_narration_instructions(self):
        """Test prompt includes narrative generation instructions."""
        events = ["Something happened"]
        prompt = build_narration_prompt(events)
        assert "cohesive" in prompt.lower()
        assert "narrative" in prompt.lower()
        assert "2-4 sentence" in prompt
