"""
ProtocolEvaluator - Maps VLM descriptions to protocol severity levels.

Evaluates scenes against user-defined behavioral protocols.
"""
import logging
from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

Severity = Literal["green", "yellow", "red"]


@dataclass
class ProtocolConfig:
    """User-defined monitoring protocols."""
    green_rules: str  # Natural language description of safe behaviors
    yellow_rules: str  # Behaviors needing attention
    red_rules: str  # Critical situations


@dataclass
class StreamStatus:
    """Current status for one stream."""
    stream_id: str
    severity: Severity
    icon: str
    description: str
    confidence: float = 1.0


# Icon mappings by category and severity
ICON_MAP = {
    # Green icons
    "reading": "📗",
    "tv": "📺",
    "sleeping": "😴",
    "eating": "🍽️",
    "calm": "🧘",
    "exercise": "🏃‍♂️",
    # Yellow icons
    "unclear": "🔍",
    "injury": "🩹",
    "distress": "😰",
    "pacing": "🚶",
    # Red icons
    "emergency": "🚨",
    "missing": "🏃",
    "danger": "⚠️",
    "unconscious": "🚨",
}


class StatusStateMachine:
    """
    Tracks status transitions with debouncing.

    Requires N consecutive classifications before changing state
    to prevent flapping on transient misclassifications.
    """

    def __init__(self, debounce_count: int = 2):
        self.current: Severity = "green"
        self.pending: Optional[Severity] = None
        self.pending_count: int = 0
        self.debounce_count = debounce_count

    def update(self, new_status: Severity) -> Optional[Severity]:
        """
        Update with new status.

        Returns the new status only when confirmed (after debounce).
        Returns None if status unchanged or still pending.
        """
        if new_status != self.current:
            if new_status == self.pending:
                self.pending_count += 1
                if self.pending_count >= self.debounce_count:
                    self.current = new_status
                    self.pending = None
                    self.pending_count = 0
                    return new_status
            else:
                self.pending = new_status
                self.pending_count = 1
        else:
            # Reset pending if we got the current status again
            self.pending = None
            self.pending_count = 0
        return None


class ProtocolEvaluator:
    """
    Maps VLM descriptions to protocol severity levels.

    Uses VLM to classify scenes against user-defined behavioral rules.
    """

    def __init__(self, protocols: ProtocolConfig, vlm_client=None):
        self.protocols = protocols
        self.vlm = vlm_client
        self._state_machines: Dict[str, StatusStateMachine] = {}

    def _get_state_machine(self, stream_id: str) -> StatusStateMachine:
        """Get or create state machine for stream."""
        if stream_id not in self._state_machines:
            self._state_machines[stream_id] = StatusStateMachine()
        return self._state_machines[stream_id]

    def _check_critical_detections(
        self, detections: List[Dict]
    ) -> Optional[StreamStatus]:
        """
        Fast path for critical detection-based conditions.

        Returns RED status immediately if:
        - No person detected in frame (missing)
        - Person detected on ground (fall)
        """
        # TODO: Implement detection-based fast path
        # Check for person class in detections
        # Check for fall/ground-level detection
        return None

    def _build_classification_prompt(self, description: str) -> str:
        """Build VLM prompt for protocol classification."""
        return f"""Based on the following scene description, classify the situation.

Scene: {description}

User's protocols:
- GREEN (safe): {self.protocols.green_rules}
- YELLOW (attention): {self.protocols.yellow_rules}
- RED (critical): {self.protocols.red_rules}

Respond with EXACTLY this format (one line):
SEVERITY|ICON|MESSAGE

Where:
- SEVERITY is one of: GREEN, YELLOW, RED
- ICON is one word describing the activity: reading, tv, sleeping, eating, calm, exercise, unclear, injury, distress, pacing, emergency, missing, danger, unconscious
- MESSAGE is a brief one-sentence status description

Example: GREEN|reading|Resident reading in rocking chair."""

    def _parse_response(
        self, stream_id: str, response: str
    ) -> StreamStatus:
        """Parse VLM response into StreamStatus."""
        try:
            parts = response.strip().split("|")
            if len(parts) >= 3:
                severity = parts[0].lower()
                icon_key = parts[1].lower()
                message = parts[2]

                if severity not in ("green", "yellow", "red"):
                    severity = "yellow"  # Default to attention needed

                icon = ICON_MAP.get(icon_key, "🔍")

                return StreamStatus(
                    stream_id=stream_id,
                    severity=severity,
                    icon=icon,
                    description=message,
                    confidence=0.9
                )
        except Exception as e:
            logger.warning(f"Failed to parse VLM response: {e}")

        # Fallback
        return StreamStatus(
            stream_id=stream_id,
            severity="yellow",
            icon="🔍",
            description="Unable to determine status clearly",
            confidence=0.5
        )

    async def evaluate(
        self,
        stream_id: str,
        description: str,
        detections: List[Dict]
    ) -> Optional[StreamStatus]:
        """
        Evaluate current scene against user protocols.

        Args:
            stream_id: Camera/stream identifier
            description: VLM-generated scene description
            detections: YOLO detection results

        Returns:
            StreamStatus if status changed, None otherwise
        """
        # Fast path: Check for critical detection conditions
        critical = self._check_critical_detections(detections)
        if critical:
            sm = self._get_state_machine(stream_id)
            if sm.update(critical.severity):
                return critical

        # VLM classification
        if self.vlm:
            prompt = self._build_classification_prompt(description)
            # TODO: Call VLM
            # response = await self.vlm.query(prompt)
            response = "GREEN|calm|Resident sitting calmly"  # Placeholder

            status = self._parse_response(stream_id, response)

            # Apply state machine debouncing
            sm = self._get_state_machine(stream_id)
            if sm.update(status.severity):
                return status

        return None
