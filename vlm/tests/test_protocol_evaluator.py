"""
Tests for ProtocolEvaluator and StatusStateMachine.

Tests protocol classification, state machine debouncing, and VLM integration.
"""
import pytest

# Import from src package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.protocol_evaluator import (
    ProtocolConfig,
    ProtocolEvaluator,
    StreamStatus,
    StatusStateMachine,
    Severity,
    ICON_MAP,
)


class TestStatusStateMachine:
    """Tests for StatusStateMachine debouncing logic."""

    def test_initial_state_is_green(self):
        """Test state machine starts in green state."""
        sm = StatusStateMachine()
        assert sm.current == "green"

    def test_no_change_on_same_status(self):
        """Test no state change when same status received."""
        sm = StatusStateMachine()

        result = sm.update("green")
        assert result is None
        assert sm.current == "green"

    def test_debounce_requires_multiple_updates(self):
        """Test state change requires debounce_count updates."""
        sm = StatusStateMachine(debounce_count=2)

        # First yellow update - pending
        result = sm.update("yellow")
        assert result is None
        assert sm.current == "green"

        # Second yellow update - confirmed
        result = sm.update("yellow")
        assert result == "yellow"
        assert sm.current == "yellow"

    def test_debounce_count_customization(self):
        """Test custom debounce count."""
        sm = StatusStateMachine(debounce_count=3)

        # Need 3 consecutive updates to change state
        sm.update("red")
        assert sm.current == "green"

        sm.update("red")
        assert sm.current == "green"

        result = sm.update("red")
        assert result == "red"
        assert sm.current == "red"

    def test_pending_reset_on_different_status(self):
        """Test pending state resets when different status received."""
        sm = StatusStateMachine(debounce_count=2)

        # Start pending yellow
        sm.update("yellow")
        assert sm.pending == "yellow"
        assert sm.pending_count == 1

        # Send different status - resets pending
        sm.update("red")
        assert sm.pending == "red"
        assert sm.pending_count == 1

    def test_pending_reset_on_current_status(self):
        """Test pending state resets when current status received."""
        sm = StatusStateMachine(debounce_count=2)

        # Start pending yellow
        sm.update("yellow")
        assert sm.pending == "yellow"

        # Send current status (green) - resets pending
        sm.update("green")
        assert sm.pending is None
        assert sm.pending_count == 0

    def test_full_state_transition_cycle(self):
        """Test complete green -> yellow -> red -> green cycle."""
        sm = StatusStateMachine(debounce_count=2)

        # green -> yellow
        sm.update("yellow")
        sm.update("yellow")
        assert sm.current == "yellow"

        # yellow -> red
        sm.update("red")
        sm.update("red")
        assert sm.current == "red"

        # red -> green
        sm.update("green")
        sm.update("green")
        assert sm.current == "green"


class TestProtocolConfig:
    """Tests for ProtocolConfig dataclass."""

    def test_protocol_config_creation(self):
        """Test creating a protocol configuration."""
        config = ProtocolConfig(
            green_rules="Reading, watching TV, sleeping",
            yellow_rules="Pacing, minor injuries",
            red_rules="Unconscious, severe injury"
        )

        assert "Reading" in config.green_rules
        assert "Pacing" in config.yellow_rules
        assert "Unconscious" in config.red_rules


class TestStreamStatus:
    """Tests for StreamStatus dataclass."""

    def test_stream_status_creation(self):
        """Test creating a stream status."""
        status = StreamStatus(
            stream_id="stream_1",
            severity="green",
            icon="reading",
            description="Resident reading quietly"
        )

        assert status.stream_id == "stream_1"
        assert status.severity == "green"
        assert status.confidence == 1.0  # Default

    def test_stream_status_with_confidence(self):
        """Test stream status with custom confidence."""
        status = StreamStatus(
            stream_id="stream_1",
            severity="yellow",
            icon="unclear",
            description="Unable to determine",
            confidence=0.5
        )

        assert status.confidence == 0.5


class TestIconMap:
    """Tests for the ICON_MAP constant."""

    def test_green_icons_exist(self):
        """Test green category icons exist."""
        assert "reading" in ICON_MAP
        assert "tv" in ICON_MAP
        assert "sleeping" in ICON_MAP
        assert "calm" in ICON_MAP

    def test_yellow_icons_exist(self):
        """Test yellow category icons exist."""
        assert "unclear" in ICON_MAP
        assert "injury" in ICON_MAP
        assert "distress" in ICON_MAP

    def test_red_icons_exist(self):
        """Test red category icons exist."""
        assert "emergency" in ICON_MAP
        assert "missing" in ICON_MAP
        assert "danger" in ICON_MAP


class TestProtocolEvaluator:
    """Tests for ProtocolEvaluator class."""

    @pytest.fixture
    def protocols(self):
        """Create default protocol configuration."""
        return ProtocolConfig(
            green_rules="Reading, watching TV, sleeping normally, eating meals",
            yellow_rules="Out of view, minor injuries, pacing erratically",
            red_rules="Unconscious on ground, severe injury, room empty"
        )

    @pytest.fixture
    def evaluator(self, protocols):
        """Create evaluator with protocols."""
        return ProtocolEvaluator(protocols, vlm_client=None)

    def test_evaluator_initialization(self, protocols):
        """Test evaluator initialization."""
        evaluator = ProtocolEvaluator(protocols)

        assert evaluator.protocols == protocols
        assert evaluator.vlm is None
        assert len(evaluator._state_machines) == 0

    def test_state_machine_created_per_stream(self, evaluator):
        """Test state machines are created per stream."""
        sm1 = evaluator._get_state_machine("stream_1")
        sm2 = evaluator._get_state_machine("stream_2")

        assert sm1 is not sm2
        assert "stream_1" in evaluator._state_machines
        assert "stream_2" in evaluator._state_machines

    def test_state_machine_reused_for_same_stream(self, evaluator):
        """Test same state machine is returned for same stream."""
        sm1 = evaluator._get_state_machine("stream_1")
        sm2 = evaluator._get_state_machine("stream_1")

        assert sm1 is sm2

    def test_build_classification_prompt(self, evaluator):
        """Test classification prompt generation."""
        prompt = evaluator._build_classification_prompt(
            "Person sitting in rocking chair with book"
        )

        assert "Person sitting in rocking chair with book" in prompt
        assert "GREEN" in prompt
        assert "YELLOW" in prompt
        assert "RED" in prompt
        assert evaluator.protocols.green_rules in prompt

    def test_parse_response_valid(self, evaluator):
        """Test parsing valid VLM response."""
        response = "GREEN|reading|Resident reading in rocking chair"

        status = evaluator._parse_response("stream_1", response)

        assert status.stream_id == "stream_1"
        assert status.severity == "green"
        assert status.icon == ICON_MAP["reading"]
        assert "reading" in status.description.lower()

    def test_parse_response_yellow(self, evaluator):
        """Test parsing yellow severity response."""
        response = "YELLOW|unclear|Unable to see resident clearly"

        status = evaluator._parse_response("stream_1", response)

        assert status.severity == "yellow"
        assert status.icon == ICON_MAP["unclear"]

    def test_parse_response_red(self, evaluator):
        """Test parsing red severity response."""
        response = "RED|emergency|Person appears unconscious on floor"

        status = evaluator._parse_response("stream_1", response)

        assert status.severity == "red"
        assert status.icon == ICON_MAP["emergency"]

    def test_parse_response_invalid_severity(self, evaluator):
        """Test parsing response with invalid severity defaults to yellow."""
        response = "INVALID|calm|Some description"

        status = evaluator._parse_response("stream_1", response)

        assert status.severity == "yellow"

    def test_parse_response_unknown_icon(self, evaluator):
        """Test parsing response with unknown icon uses fallback."""
        response = "GREEN|unknown_icon|Some description"

        status = evaluator._parse_response("stream_1", response)

        assert status.icon == ICON_MAP.get("unknown_icon", "?")

    def test_parse_response_malformed(self, evaluator):
        """Test parsing malformed response returns fallback."""
        response = "This is not a valid response format"

        status = evaluator._parse_response("stream_1", response)

        assert status.severity == "yellow"
        assert status.confidence == 0.5

    @pytest.mark.asyncio
    async def test_evaluate_without_vlm(self, evaluator):
        """Test evaluate returns None without VLM client."""
        # With no VLM client, evaluate uses placeholder response
        result = await evaluator.evaluate(
            stream_id="stream_1",
            description="Person sitting calmly",
            detections=[]
        )

        # First evaluation should trigger state change from initial
        # but placeholder response is "GREEN|calm|Resident sitting calmly"
        # which matches initial state, so no change
        # Actually, it depends on debounce logic
        # Let's call twice to confirm state
        result = await evaluator.evaluate(
            stream_id="stream_1",
            description="Person sitting calmly",
            detections=[]
        )

        # Since placeholder is green and initial is green, no change
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_with_state_change(self, evaluator):
        """Test evaluate returns status when state changes."""
        # Manually trigger state change by modifying state machine
        sm = evaluator._get_state_machine("stream_1")
        sm.current = "yellow"  # Start in yellow

        # Now placeholder green response should trigger change
        # after debounce
        await evaluator.evaluate("stream_1", "test", [])
        result = await evaluator.evaluate("stream_1", "test", [])

        assert result is not None
        assert result.severity == "green"


class TestProtocolEvaluatorDetectionFastPath:
    """Tests for detection-based fast path in ProtocolEvaluator."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator for detection tests."""
        protocols = ProtocolConfig(
            green_rules="Normal activity",
            yellow_rules="Attention needed",
            red_rules="Emergency"
        )
        return ProtocolEvaluator(protocols)

    def test_check_critical_detections_placeholder(self, evaluator):
        """Test critical detection check (currently placeholder)."""
        # The _check_critical_detections is a TODO stub
        result = evaluator._check_critical_detections([])
        assert result is None

        result = evaluator._check_critical_detections([
            {"class_id": 0, "class_name": "person", "confidence": 0.9}
        ])
        assert result is None  # Currently returns None (TODO)
