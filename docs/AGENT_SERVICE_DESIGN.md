# Agent Service Technical Design Document

**Newport Demo - Conversational Query Processing & Report Generation**

**Version:** 1.0
**Date:** 2026-01-08
**Status:** Design Proposal

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Service Architecture](#2-service-architecture)
3. [Query Processing Pipeline](#3-query-processing-pipeline)
4. [Data Access Layer](#4-data-access-layer)
5. [Conversation Memory](#5-conversation-memory)
6. [API Design](#6-api-design)
7. [Report Generation](#7-report-generation)
8. [Integration Points](#8-integration-points)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Code Snippets](#10-code-snippets)

---

## 1. Executive Summary

The Agent Service is a conversational AI component that processes natural language queries about video monitoring data and generates reports. It bridges the gap between the user's questions and the system's historical data (alerts, status logs, stream states).

**Key Capabilities:**
- Natural language query understanding
- Historical data retrieval and analysis
- Aggregate report generation (weekly summaries, trends)
- Conversation context management
- Integration with existing VLM for visual reasoning

**Design Philosophy:**
- **Extend, don't replace**: Build on existing EventBus/Redis patterns
- **Modular**: Separate concerns (query routing, data access, response generation)
- **Performance**: Cache-friendly, async-first
- **Testable**: Mock-friendly interfaces for VLM/DB

---

## 2. Service Architecture

### 2.1 Container Strategy

**Decision: Extend the `app` container**

**Rationale:**
1. **Shared Data Access**: Agent needs direct access to SQLite DB and Redis (already in `app`)
2. **Latency**: No network hop for database queries
3. **Simplicity**: Fewer containers to manage, same deployment lifecycle
4. **Resource Efficiency**: No need for separate container on Jetson

**Alternative Considered:** Separate container for agent service
- **Pros**: Better isolation, independent scaling
- **Cons**: Additional overhead, network latency for DB access, overkill for single-device edge deployment

### 2.2 Component Structure

```
app/
├── src/
│   ├── main.py                    # FastAPI app (existing)
│   ├── event_bus.py               # Event bus (existing)
│   ├── websocket.py               # WebSocket handler (existing)
│   ├── models.py                  # Pydantic models (existing)
│   ├── config.py                  # Settings (existing)
│   │
│   ├── agent/                     # NEW: Agent service module
│   │   ├── __init__.py
│   │   ├── service.py             # AgentService orchestrator
│   │   ├── query_processor.py    # Query classification & routing
│   │   ├── data_access.py         # Database & Redis queries
│   │   ├── conversation.py        # Conversation context manager
│   │   ├── report_generator.py   # Report templates & aggregation
│   │   └── prompts.py             # LLM prompt templates
│   │
│   └── database/                  # NEW: Database layer
│       ├── __init__.py
│       ├── models.py              # SQLAlchemy ORM models
│       └── connection.py          # DB connection management
```

### 2.3 Communication Flow

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │ WebSocket: query message
       ▼
┌─────────────────┐
│  WebSocket      │
│  Handler        │
└──────┬──────────┘
       │ Forward to AgentService
       ▼
┌─────────────────┐
│  AgentService   │◄────┐
└──────┬──────────┘     │
       │                │ Redis pub/sub
       ├───────────────►│ (optional for async)
       │                │
       ├─► Query Processor
       │
       ├─► Data Access ──► SQLite
       │                   (alerts, logs)
       │
       ├─► VLM Client ────► Redis ──► VLM Container
       │                              (visual reasoning)
       │
       └─► Response
           │
           ▼
       WebSocket ──► Frontend
```

---

## 3. Query Processing Pipeline

### 3.1 Query Types & Classification

The agent handles four primary query types:

| Query Type | Example | Data Source | Response Type |
|------------|---------|-------------|---------------|
| **Current Status** | "What's happening in Room 2?" | Redis (live) + SQLite (recent) | Real-time summary |
| **Historical** | "Were there any alerts yesterday?" | SQLite (alerts table) | Aggregate query |
| **Trend Analysis** | "Has Room 1 been stable this week?" | SQLite (status_log) | Statistical summary |
| **Visual Reasoning** | "Why did the alert trigger at 3pm?" | Frame + VLM + Context | VLM inference |

### 3.2 Query Processing Flow

```python
User Query → Query Processor → [Classify] → Route
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ▼                         ▼                         ▼
            [Current Status]          [Historical Query]      [Visual Reasoning]
                    │                         │                         │
                    ▼                         ▼                         ▼
            Redis + SQLite              SQLite Query                VLM Call
                    │                         │                         │
                    └─────────────────────────┴─────────────────────────┘
                                              │
                                              ▼
                                    Template / LLM Response
                                              │
                                              ▼
                                    WebSocket → Frontend
```

### 3.3 Classification Strategy

**Approach: Rule-based + Keyword Matching** (no LLM for classification)

**Rationale:**
- Fast (< 10ms)
- Deterministic
- No model loading overhead
- Good enough for bounded domain

**Patterns:**
```python
QUERY_PATTERNS = {
    "current_status": [
        r"what'?s happening",
        r"current (status|state)",
        r"what is .* doing",
        r"show me (the )?(latest|current)"
    ],
    "historical": [
        r"(yesterday|last week|past \d+ (days|hours))",
        r"how many (alerts|incidents)",
        r"were there any",
        r"show (all|recent) alerts"
    ],
    "trend": [
        r"has .* been (stable|safe|okay)",
        r"(trend|pattern|change)",
        r"compared to",
        r"(improving|getting worse)"
    ],
    "visual": [
        r"why (did|was)",
        r"what caused",
        r"show me (the )?(frame|image)",
        r"describe (the )?scene"
    ]
}
```

**Fallback:** If no pattern matches, use template response asking for clarification.

### 3.4 Response Generation Strategy

**Hybrid Approach:**
- **Simple queries** (current status, counts): Template-based responses
- **Complex queries** (explanations, trends): VLM-generated responses
- **Reports**: Structured templates with data injection

**Why not always use VLM?**
- Latency: Templates are instant, VLM is ~500ms
- Consistency: Templates ensure uniform formatting
- Cost: No need for inference on simple queries

---

## 4. Data Access Layer

### 4.1 Database Schema

**New Tables:**

#### `alerts` Table
```sql
CREATE TABLE alerts (
    id TEXT PRIMARY KEY,              -- UUID
    stream_id TEXT NOT NULL,
    level TEXT NOT NULL,              -- 'info', 'warning', 'critical'
    severity TEXT NOT NULL,           -- 'green', 'yellow', 'red'
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL,      -- ISO 8601
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at DATETIME,
    resolved_at DATETIME,

    -- Optional: Link to frame for visual context
    frame_path TEXT,

    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
);

CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_alerts_stream ON alerts(stream_id, timestamp DESC);
CREATE INDEX idx_alerts_severity ON alerts(severity, timestamp DESC);
```

#### `status_log` Table
```sql
CREATE TABLE status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id TEXT NOT NULL,
    severity TEXT NOT NULL,           -- 'green', 'yellow', 'red'
    icon TEXT,
    description TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    timestamp DATETIME NOT NULL,

    -- Metadata
    duration_seconds INTEGER,         -- How long this status lasted

    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
);

CREATE INDEX idx_status_log_timestamp ON status_log(timestamp DESC);
CREATE INDEX idx_status_log_stream ON status_log(stream_id, timestamp DESC);
CREATE INDEX idx_status_log_severity ON status_log(severity);
```

#### `streams` Table (Configuration)
```sql
CREATE TABLE streams (
    stream_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,               -- e.g., "Room 1", "Living Room"
    source_uri TEXT NOT NULL,
    enabled BOOLEAN DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

#### `protocols` Table
```sql
CREATE TABLE protocols (
    id INTEGER PRIMARY KEY,
    stream_id TEXT,                   -- NULL = global default
    green_rules TEXT NOT NULL,
    yellow_rules TEXT NOT NULL,
    red_rules TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
);
```

#### `query_sessions` Table (Conversation Memory)
```sql
CREATE TABLE query_sessions (
    session_id TEXT PRIMARY KEY,      -- UUID
    websocket_id TEXT NOT NULL,       -- WebSocket connection ID
    created_at DATETIME NOT NULL,
    last_activity DATETIME NOT NULL,
    context TEXT,                     -- JSON: recent queries, entities

    CONSTRAINT expires CHECK (
        last_activity > datetime('now', '-1 hour')
    )
);

CREATE INDEX idx_sessions_activity ON query_sessions(last_activity DESC);
```

#### `query_log` Table (Analytics)
```sql
CREATE TABLE query_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    query_text TEXT NOT NULL,
    query_type TEXT,                  -- classified type
    response_text TEXT,
    latency_ms INTEGER,
    timestamp DATETIME NOT NULL,

    FOREIGN KEY (session_id) REFERENCES query_sessions(session_id)
);
```

### 4.2 Data Access Patterns

**Common Queries:**

```python
# Get alerts for stream in time range
SELECT * FROM alerts
WHERE stream_id = ?
  AND timestamp BETWEEN ? AND ?
ORDER BY timestamp DESC;

# Get severity distribution for period
SELECT severity, COUNT(*) as count
FROM status_log
WHERE stream_id = ?
  AND timestamp >= ?
GROUP BY severity;

# Get recent status changes
SELECT * FROM status_log
WHERE stream_id = ?
ORDER BY timestamp DESC
LIMIT 10;

# Trend analysis: average time in each severity per day
SELECT
    DATE(timestamp) as date,
    severity,
    SUM(duration_seconds) / 3600.0 as hours
FROM status_log
WHERE stream_id = ?
  AND timestamp >= ?
GROUP BY DATE(timestamp), severity
ORDER BY date;
```

### 4.3 Redis Data

**Live Data (Existing):**
- `pipeline:{stream_id}:status` → Pipeline state
- Channel `summaries` → Status updates
- Channel `detections` → Detection events

**Agent-specific Keys:**
- `agent:session:{session_id}:context` → Conversation state (TTL: 1hr)
- `agent:cache:{query_hash}` → Response cache (TTL: 5min)

---

## 5. Conversation Memory

### 5.1 Session Management

**Session Lifecycle:**
1. **Creation**: On first query from WebSocket connection
2. **Maintenance**: Update `last_activity` on each query
3. **Expiration**: Auto-expire after 1 hour of inactivity
4. **Cleanup**: Background task purges expired sessions every 15 minutes

**Session Context Structure:**
```python
@dataclass
class SessionContext:
    session_id: str
    websocket_id: str
    created_at: datetime
    last_activity: datetime

    # Context tracking
    current_stream_id: Optional[str]  # Last stream mentioned
    recent_queries: List[str]         # Last 5 queries
    recent_entities: Dict[str, Any]   # Extracted entities (times, streams)
    conversation_history: List[dict]  # For potential LLM context
```

### 5.2 Reference Resolution

**Problem:** User says "Tell me more about that" or "What happened after?"

**Solution:** Track entities and support pronouns

**Examples:**
```
User: "Were there any alerts in Room 2 yesterday?"
Agent: [Sets context: stream_id="room_2", time_range="yesterday"]
       "Yes, 3 alerts..."

User: "Show me the critical ones"
Agent: [Uses context: stream_id="room_2", time_range="yesterday", filter="critical"]
       "Here are 2 critical alerts from Room 2 yesterday..."

User: "What about today?"
Agent: [Updates context: time_range="today", keeps stream_id]
       "Today Room 2 has 0 critical alerts."
```

**Implementation:**
```python
class ContextResolver:
    """Resolve references using conversation context."""

    def resolve_stream(self, query: str, context: SessionContext) -> Optional[str]:
        """Extract stream ID from query or use context."""
        # Try to extract from query
        match = re.search(r"(room|stream)\s*(\d+|[a-z_]+)", query, re.I)
        if match:
            stream_id = f"stream_{match.group(2)}"
            context.current_stream_id = stream_id
            return stream_id

        # Fall back to context
        return context.current_stream_id

    def resolve_time_range(self, query: str, context: SessionContext) -> Tuple[datetime, datetime]:
        """Extract or infer time range."""
        # Keywords: yesterday, today, last week, past 24 hours
        if "yesterday" in query.lower():
            end = datetime.now().replace(hour=0, minute=0, second=0)
            start = end - timedelta(days=1)
            return start, end

        # ... more patterns

        # Default: last 24 hours
        return datetime.now() - timedelta(days=1), datetime.now()
```

### 5.3 Context Window Management

**Strategy:** Keep last N queries + extracted entities

**Size Limits:**
- Recent queries: 5 (enough for short-term context)
- Conversation history: 10 (for potential LLM prompting)
- Entities: 20 (time ranges, stream IDs, alert IDs)

**Storage:** JSON in `query_sessions.context` column

---

## 6. API Design

### 6.1 WebSocket Messages

**Client → Server: Query Message**
```typescript
{
  type: "query",
  stream_id?: string,        // Optional: context hint
  question: string,
  request_id: string         // Client-generated UUID for tracking
}
```

**Server → Client: Query Acknowledged**
```typescript
{
  type: "query_received",
  request_id: string,
  status: "processing"
}
```

**Server → Client: Query Response**
```typescript
{
  type: "query_response",
  request_id: string,
  answer: string,            // Markdown-formatted response
  data?: {                   // Optional structured data
    alerts?: Alert[],
    status?: StreamStatus,
    chart_data?: any
  },
  timestamp: string,
  metadata?: {
    query_type: string,
    latency_ms: number,
    confidence?: number
  }
}
```

**Server → Client: Streaming Response (Future)**
```typescript
{
  type: "query_response_chunk",
  request_id: string,
  chunk: string,             // Partial response
  done: boolean
}
```

### 6.2 REST Endpoints (Optional)

**For Programmatic Access:**

```
GET  /api/agent/query?q={question}&stream_id={id}
POST /api/agent/query
     Body: {"question": "...", "stream_id": "..."}

GET  /api/agent/reports/weekly?stream_id={id}&date={YYYY-MM-DD}
GET  /api/agent/reports/summary?stream_id={id}&start={ISO}&end={ISO}

GET  /api/agent/sessions/{session_id}
DELETE /api/agent/sessions/{session_id}
```

### 6.3 Redis Channels

**Subscribe (Incoming):**
- `summaries` → Status updates (existing)
- `detections` → Detection events (existing)

**Publish (Outgoing):**
- `agent.queries` → Query log events (analytics)
- `agent.reports` → Generated reports (for archival)

**Optional: Async Processing**
- Client sends query via WebSocket
- AgentService publishes to `agent.queries.pending`
- Worker processes query
- Worker publishes result to `agent.queries.{request_id}`
- WebSocket handler forwards to client

**Why Optional?** Adds complexity; start with sync processing (< 1s latency acceptable).

---

## 7. Report Generation

### 7.1 Report Types

#### 7.1.1 Weekly Incident Summary

**Trigger:** User asks "Summarize last week" or scheduled cron job

**Template:**
```markdown
# Weekly Report: {stream_name}
**Period:** {start_date} - {end_date}

## Summary
- **Total Alerts:** {total_count}
  - Critical: {critical_count}
  - Warning: {warning_count}
  - Info: {info_count}
- **Status Distribution:**
  - Green: {green_hours}h ({green_pct}%)
  - Yellow: {yellow_hours}h ({yellow_pct}%)
  - Red: {red_hours}h ({red_pct}%)

## Critical Incidents
{for alert in critical_alerts}
- **{alert.timestamp}**: {alert.title}
  - {alert.message}
{/for}

## Trend Analysis
{trend_description}
```

**Data Aggregation:**
```python
async def generate_weekly_summary(
    stream_id: str,
    week_start: datetime
) -> WeeklyReport:
    week_end = week_start + timedelta(days=7)

    # Aggregate alerts
    alerts = await db.query_alerts(stream_id, week_start, week_end)
    critical = [a for a in alerts if a.level == "critical"]

    # Aggregate status durations
    status_durations = await db.query_status_durations(
        stream_id, week_start, week_end
    )

    total_hours = 7 * 24
    green_hours = status_durations.get("green", 0) / 3600
    yellow_hours = status_durations.get("yellow", 0) / 3600
    red_hours = status_durations.get("red", 0) / 3600

    # Generate trend description using VLM (optional)
    trend = await generate_trend_analysis(status_durations, alerts)

    return WeeklyReport(
        stream_id=stream_id,
        period=(week_start, week_end),
        alerts=alerts,
        critical=critical,
        status_distribution={
            "green": (green_hours, green_hours / total_hours * 100),
            "yellow": (yellow_hours, yellow_hours / total_hours * 100),
            "red": (red_hours, red_hours / total_hours * 100)
        },
        trend=trend
    )
```

#### 7.1.2 Per-Room Statistics

**Trigger:** User asks "How is Room 2 doing?"

**Output:**
```markdown
# Room 2 Status

**Current Status:** {current_severity} - {current_description}
**Last Updated:** {timestamp}

**Today's Activity:**
- Green: {green_count} periods ({green_total_minutes} min)
- Yellow: {yellow_count} periods ({yellow_total_minutes} min)
- Red: {red_count} periods ({red_total_minutes} min)

**Recent Alerts:** {unresolved_count} unresolved
```

#### 7.1.3 Trend Analysis

**Trigger:** User asks "Is Room 1 stable?"

**Analysis:**
1. Calculate severity distribution over time windows (daily for week, hourly for day)
2. Detect trend: improving (more green), degrading (more red), stable
3. Identify anomalies: unusual spikes in red/yellow

**Output:**
```markdown
Room 1 has been **stable** over the past week.
- Average daily green time: 22.5 hours (94%)
- Yellow incidents: 2-3 per day (normal)
- No critical alerts in past 7 days

Compared to previous week: **+2% improvement** in green time.
```

### 7.2 Report Storage

**Options:**
1. **Generate on-demand**: Query DB each time (simple, always fresh)
2. **Cache in Redis**: TTL-based cache (fast, reduces DB load)
3. **Pre-generate**: Background job creates daily/weekly reports (fast, consistent)

**Recommendation:** Start with on-demand, add caching if latency becomes issue.

**Storage:**
```python
# Redis cache key
report_key = f"report:{report_type}:{stream_id}:{date_key}"
await redis.setex(report_key, ttl=3600, value=json.dumps(report))
```

### 7.3 Report Delivery

**Channels:**
1. **WebSocket**: Immediate response to query
2. **REST API**: Download as JSON/Markdown
3. **Scheduled**: Daily email digest (future)

---

## 8. Integration Points

### 8.1 EventBus Integration

**Existing Pattern:** EventBus manages local handlers + Redis pub/sub

**Agent Integration:**

```python
# In main.py startup
from .agent.service import AgentService

agent_service = AgentService(
    event_bus=event_bus,
    db_path="/app/data/newport.db"
)

# Register agent event handlers
event_bus.on("summary.received", agent_service.on_status_update)
event_bus.on("alert.triggered", agent_service.on_alert_triggered)
```

**Event Handlers:**

```python
# agent/service.py
class AgentService:
    async def on_status_update(self, event: Event):
        """Log status changes to database."""
        status = StreamStatus(**event.data)
        await self.db.insert_status_log(status)

    async def on_alert_triggered(self, event: Event):
        """Log alerts to database."""
        alert = Alert(**event.data)
        await self.db.insert_alert(alert)
```

### 8.2 WebSocket Handler Integration

**Existing Code:**
```python
# websocket.py (lines 125-132)
if msg_type == "query":
    # TODO: Forward to Agent for processing
    await manager.send_to(websocket, {
        "type": "query_received",
        "request_id": message.get("request_id"),
        "status": "processing"
    })
```

**New Code:**
```python
if msg_type == "query":
    request_id = message.get("request_id")
    question = message.get("question")
    stream_id = message.get("stream_id")

    # Acknowledge receipt
    await manager.send_to(websocket, {
        "type": "query_received",
        "request_id": request_id,
        "status": "processing"
    })

    # Get or create session
    session = await agent_service.get_session(websocket)

    # Process query
    try:
        response = await agent_service.process_query(
            question=question,
            stream_id=stream_id,
            session=session
        )

        # Send response
        await manager.send_to(websocket, {
            "type": "query_response",
            "request_id": request_id,
            "answer": response.answer,
            "data": response.data,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "query_type": response.query_type,
                "latency_ms": response.latency_ms
            }
        })
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        await manager.send_to(websocket, {
            "type": "query_response",
            "request_id": request_id,
            "answer": "Sorry, I encountered an error processing your query.",
            "timestamp": datetime.utcnow().isoformat()
        })
```

### 8.3 VLM Container Integration

**Current VLM Usage:** Protocol evaluation (status classification)

**Agent VLM Usage:** Visual reasoning queries

**Integration Method:** Redis Request-Response Pattern

**Flow:**
```
AgentService → Redis Publish
  channel: vlm.requests.{request_id}
  payload: {
    "type": "visual_reasoning",
    "frame_path": "/shared/frames/stream_0/latest.jpg",
    "question": "Why did the status change to red?",
    "context": {...}
  }

VLM Container → Processes → Redis Publish
  channel: vlm.responses.{request_id}
  payload: {
    "request_id": "...",
    "answer": "The person appears to have fallen...",
    "confidence": 0.85
  }

AgentService ← Redis Subscribe
  Receives response, returns to client
```

**Why not HTTP?** Redis is already available, lower latency, handles async naturally.

**VLM Service Extension:**

```python
# vlm/src/agent_handler.py (NEW)
class AgentRequestHandler:
    """Handle agent visual reasoning requests."""

    async def on_agent_request(self, request: dict):
        request_id = request["request_id"]
        frame_path = request["frame_path"]
        question = request["question"]

        # Load frame and run VLM
        answer = self.vlm.describe(
            frame_path,
            prompt=question
        )

        # Publish response
        await self.redis.publish(
            f"vlm.responses.{request_id}",
            json.dumps({
                "request_id": request_id,
                "answer": answer,
                "confidence": 0.85  # Model-specific
            })
        )
```

### 8.4 Database Connection Management

**Pattern:** Connection pool with async SQLAlchemy

**Setup:**
```python
# database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite+aiosqlite:////app/data/newport.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

**Usage in Agent:**
```python
class AgentService:
    def __init__(self, db_path: str, event_bus: EventBus):
        self.db_path = db_path
        self.event_bus = event_bus
        self.data_access = DataAccess(db_path)

    async def initialize(self):
        """Initialize database schema."""
        await self.data_access.create_tables()
```

---

## 9. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Create `agent/` module structure
- [ ] Implement database schema
- [ ] Create DataAccess class with basic queries
- [ ] Add event handlers for status/alert logging
- [ ] Test: Verify data flows into DB

### Phase 2: Query Processing (Week 2)
- [ ] Implement QueryProcessor with classification
- [ ] Build ContextResolver for reference resolution
- [ ] Create SessionManager for conversation tracking
- [ ] Integrate with WebSocket handler
- [ ] Test: End-to-end simple queries

### Phase 3: Response Generation (Week 3)
- [ ] Create response templates
- [ ] Implement report generators
- [ ] Add VLM integration for visual reasoning
- [ ] Test: All query types working

### Phase 4: Polish & Optimization (Week 4)
- [ ] Add response caching (Redis)
- [ ] Implement session cleanup background task
- [ ] Add query analytics logging
- [ ] Performance testing & optimization
- [ ] Documentation & examples

---

## 10. Code Snippets

### 10.1 AgentService Core

```python
# app/src/agent/service.py
import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from ..event_bus import Event, EventBus
from .conversation import SessionManager, SessionContext
from .data_access import DataAccess
from .query_processor import QueryProcessor
from .prompts import PromptBuilder

logger = logging.getLogger(__name__)


class QueryResponse:
    """Agent query response."""
    def __init__(
        self,
        answer: str,
        query_type: str,
        latency_ms: int,
        data: Optional[dict] = None,
        confidence: float = 1.0
    ):
        self.answer = answer
        self.query_type = query_type
        self.latency_ms = latency_ms
        self.data = data or {}
        self.confidence = confidence


class AgentService:
    """
    Agent service for conversational query processing.

    Handles:
    - Natural language queries about monitoring data
    - Conversation context management
    - Report generation
    - VLM integration for visual reasoning
    """

    def __init__(
        self,
        event_bus: EventBus,
        db_path: str = "/app/data/newport.db"
    ):
        self.event_bus = event_bus
        self.db = DataAccess(db_path)
        self.query_processor = QueryProcessor(self.db)
        self.session_manager = SessionManager(self.db)
        self.prompt_builder = PromptBuilder()

    async def initialize(self):
        """Initialize agent service."""
        await self.db.initialize()
        logger.info("AgentService initialized")

    async def get_session(self, websocket_id: str) -> SessionContext:
        """Get or create session for WebSocket connection."""
        return await self.session_manager.get_or_create(websocket_id)

    async def process_query(
        self,
        question: str,
        session: SessionContext,
        stream_id: Optional[str] = None
    ) -> QueryResponse:
        """
        Process a natural language query.

        Args:
            question: User's question
            session: Conversation session
            stream_id: Optional stream context hint

        Returns:
            QueryResponse with answer and metadata
        """
        start_time = datetime.utcnow()

        # Update session activity
        await self.session_manager.update_activity(session)

        # Classify query type
        query_type = self.query_processor.classify(question)

        # Resolve references using context
        resolved_stream = self.session_manager.resolve_stream(
            question, session, stream_id
        )
        time_range = self.session_manager.resolve_time_range(
            question, session
        )

        # Route to appropriate handler
        if query_type == "current_status":
            answer = await self._handle_current_status(
                resolved_stream, session
            )
        elif query_type == "historical":
            answer = await self._handle_historical_query(
                question, resolved_stream, time_range, session
            )
        elif query_type == "trend":
            answer = await self._handle_trend_analysis(
                resolved_stream, time_range, session
            )
        elif query_type == "visual":
            answer = await self._handle_visual_reasoning(
                question, resolved_stream, session
            )
        else:
            answer = self._handle_unknown(question)

        # Calculate latency
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Log query
        await self.db.log_query(
            session_id=session.session_id,
            query_text=question,
            query_type=query_type,
            response_text=answer,
            latency_ms=latency_ms
        )

        # Update session context
        session.recent_queries.append(question)
        session.recent_queries = session.recent_queries[-5:]  # Keep last 5
        if resolved_stream:
            session.current_stream_id = resolved_stream
        await self.session_manager.save_context(session)

        return QueryResponse(
            answer=answer,
            query_type=query_type,
            latency_ms=latency_ms
        )

    async def _handle_current_status(
        self,
        stream_id: Optional[str],
        session: SessionContext
    ) -> str:
        """Handle current status query."""
        if not stream_id:
            # Get all streams
            statuses = await self.db.get_current_statuses()
            return self._format_multi_stream_status(statuses)

        # Get single stream status
        status = await self.db.get_current_status(stream_id)
        if not status:
            return f"No status data available for {stream_id}"

        # Get recent alerts
        alerts = await self.db.get_recent_alerts(stream_id, limit=3)

        return self._format_status_response(status, alerts)

    async def _handle_historical_query(
        self,
        question: str,
        stream_id: Optional[str],
        time_range: tuple,
        session: SessionContext
    ) -> str:
        """Handle historical data query."""
        start, end = time_range

        # Extract what they're asking about
        if "alert" in question.lower():
            alerts = await self.db.query_alerts(stream_id, start, end)
            return self._format_alerts_response(alerts, start, end)

        # General history
        status_log = await self.db.query_status_log(stream_id, start, end)
        return self._format_history_response(status_log, start, end)

    async def _handle_trend_analysis(
        self,
        stream_id: Optional[str],
        time_range: tuple,
        session: SessionContext
    ) -> str:
        """Handle trend analysis query."""
        start, end = time_range

        # Get severity distribution
        distribution = await self.db.get_severity_distribution(
            stream_id, start, end
        )

        # Calculate trend
        trend = self._analyze_trend(distribution)

        return self._format_trend_response(stream_id, distribution, trend)

    async def _handle_visual_reasoning(
        self,
        question: str,
        stream_id: Optional[str],
        session: SessionContext
    ) -> str:
        """Handle visual reasoning query (requires VLM)."""
        if not stream_id:
            return "Please specify which stream you'd like me to analyze."

        # Get latest frame path
        frame_path = f"/shared/frames/{stream_id}/latest.jpg"

        # Request VLM analysis
        request_id = str(uuid4())
        answer = await self._request_vlm_analysis(
            request_id=request_id,
            frame_path=frame_path,
            question=question
        )

        return answer

    def _handle_unknown(self, question: str) -> str:
        """Handle unknown query type."""
        return (
            "I can help you with:\n"
            "- Current status: 'What's happening in Room 2?'\n"
            "- Alert history: 'Were there any critical alerts yesterday?'\n"
            "- Trends: 'Has Room 1 been stable this week?'\n"
            "- Visual analysis: 'Why did the alert trigger?'\n\n"
            "Please rephrase your question."
        )

    async def _request_vlm_analysis(
        self,
        request_id: str,
        frame_path: str,
        question: str,
        timeout: float = 5.0
    ) -> str:
        """Request VLM analysis via Redis."""
        # Publish request
        await self.event_bus.publish(
            f"vlm.requests.{request_id}",
            Event(
                type="visual_reasoning",
                data={
                    "request_id": request_id,
                    "frame_path": frame_path,
                    "question": question
                }
            )
        )

        # Wait for response (with timeout)
        response = await self._wait_for_vlm_response(request_id, timeout)

        if response:
            return response.get("answer", "Unable to analyze image")
        else:
            return "VLM analysis timed out. Please try again."

    async def _wait_for_vlm_response(
        self,
        request_id: str,
        timeout: float
    ) -> Optional[dict]:
        """Wait for VLM response on Redis channel."""
        # Implementation: Subscribe to response channel with timeout
        # This is simplified; actual implementation would use asyncio.wait_for
        # with a subscription to the response channel
        pass

    # Event handlers for data logging

    async def on_status_update(self, event: Event):
        """Log status updates to database."""
        try:
            await self.db.insert_status_log(
                stream_id=event.stream_id,
                severity=event.data["severity"],
                icon=event.data.get("icon"),
                description=event.data["description"],
                confidence=event.data.get("confidence", 1.0),
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to log status update: {e}")

    async def on_alert_triggered(self, event: Event):
        """Log alerts to database."""
        try:
            await self.db.insert_alert(
                alert_id=event.data["id"],
                stream_id=event.data["stream_id"],
                level=event.data["level"],
                severity=event.data["severity"],
                title=event.data["title"],
                message=event.data["message"],
                timestamp=datetime.fromisoformat(event.data["timestamp"])
            )
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")

    # Response formatters

    def _format_status_response(self, status: dict, alerts: list) -> str:
        """Format current status response."""
        severity_emoji = {
            "green": "✅",
            "yellow": "⚠️",
            "red": "🚨"
        }

        emoji = severity_emoji.get(status["severity"], "ℹ️")

        response = f"{emoji} **{status['stream_id']}**: {status['description']}\n"
        response += f"*Last updated: {status['timestamp']}*\n\n"

        if alerts:
            response += f"**Recent Alerts ({len(alerts)}):**\n"
            for alert in alerts[:3]:
                response += f"- {alert['level'].upper()}: {alert['title']}\n"
        else:
            response += "No recent alerts.\n"

        return response

    def _format_alerts_response(
        self,
        alerts: list,
        start: datetime,
        end: datetime
    ) -> str:
        """Format historical alerts response."""
        if not alerts:
            return f"No alerts found between {start.date()} and {end.date()}."

        # Group by severity
        critical = [a for a in alerts if a["level"] == "critical"]
        warning = [a for a in alerts if a["level"] == "warning"]
        info = [a for a in alerts if a["level"] == "info"]

        response = f"**Alerts from {start.date()} to {end.date()}:**\n\n"
        response += f"Total: {len(alerts)} alerts\n"
        response += f"- Critical: {len(critical)}\n"
        response += f"- Warning: {len(warning)}\n"
        response += f"- Info: {len(info)}\n\n"

        if critical:
            response += "**Critical Alerts:**\n"
            for alert in critical[:5]:
                ts = datetime.fromisoformat(alert["timestamp"]).strftime("%m/%d %H:%M")
                response += f"- {ts}: {alert['title']}\n"

        return response

    def _format_history_response(
        self,
        log_entries: list,
        start: datetime,
        end: datetime
    ) -> str:
        """Format status history response."""
        if not log_entries:
            return f"No status data found between {start.date()} and {end.date()}."

        # Calculate severity distribution
        severity_counts = {"green": 0, "yellow": 0, "red": 0}
        for entry in log_entries:
            severity_counts[entry["severity"]] += 1

        total = len(log_entries)

        response = f"**Status History from {start.date()} to {end.date()}:**\n\n"
        response += f"Total status changes: {total}\n"
        response += f"- Green: {severity_counts['green']} ({severity_counts['green']/total*100:.1f}%)\n"
        response += f"- Yellow: {severity_counts['yellow']} ({severity_counts['yellow']/total*100:.1f}%)\n"
        response += f"- Red: {severity_counts['red']} ({severity_counts['red']/total*100:.1f}%)\n"

        return response

    def _format_multi_stream_status(self, statuses: list) -> str:
        """Format status for multiple streams."""
        if not statuses:
            return "No stream status data available."

        response = "**Current Status - All Streams:**\n\n"
        for status in statuses:
            emoji = {"green": "✅", "yellow": "⚠️", "red": "🚨"}[status["severity"]]
            response += f"{emoji} **{status['stream_id']}**: {status['description']}\n"

        return response

    def _analyze_trend(self, distribution: dict) -> str:
        """Analyze trend from severity distribution."""
        # Simple heuristic: compare to expected baseline
        green_pct = distribution.get("green", 0)
        red_pct = distribution.get("red", 0)

        if green_pct > 80:
            return "stable and healthy"
        elif red_pct > 20:
            return "concerning with frequent critical events"
        elif red_pct > 10:
            return "moderately stable with some critical events"
        else:
            return "generally stable with minor fluctuations"

    def _format_trend_response(
        self,
        stream_id: str,
        distribution: dict,
        trend: str
    ) -> str:
        """Format trend analysis response."""
        stream_name = stream_id or "All streams"

        response = f"**Trend Analysis: {stream_name}**\n\n"
        response += f"The status has been **{trend}**.\n\n"
        response += "**Distribution:**\n"
        response += f"- Green: {distribution.get('green', 0):.1f}%\n"
        response += f"- Yellow: {distribution.get('yellow', 0):.1f}%\n"
        response += f"- Red: {distribution.get('red', 0):.1f}%\n"

        return response
```

### 10.2 Query Processor

```python
# app/src/agent/query_processor.py
import re
from typing import Literal

QueryType = Literal["current_status", "historical", "trend", "visual", "unknown"]


class QueryProcessor:
    """
    Classifies and routes queries based on content.

    Uses rule-based pattern matching for speed and determinism.
    """

    PATTERNS = {
        "current_status": [
            r"what'?s happening",
            r"current (status|state)",
            r"what is .* doing",
            r"show me (the )?(latest|current)",
            r"how is .* (doing|now)",
        ],
        "historical": [
            r"(yesterday|last week|past \d+ (days|hours))",
            r"how many (alerts|incidents)",
            r"were there any",
            r"show (all|recent) alerts",
            r"between .* and",
        ],
        "trend": [
            r"has .* been (stable|safe|okay|consistent)",
            r"(trend|pattern|change)",
            r"compared to",
            r"(improving|getting worse|better|worse)",
            r"is .* stable",
        ],
        "visual": [
            r"why (did|was)",
            r"what caused",
            r"show me (the )?(frame|image|picture)",
            r"describe (the )?scene",
            r"what do you see",
        ]
    }

    def __init__(self, db):
        self.db = db
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for performance."""
        self.compiled_patterns = {}
        for query_type, patterns in self.PATTERNS.items():
            self.compiled_patterns[query_type] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in patterns
            ]

    def classify(self, question: str) -> QueryType:
        """
        Classify query into a type.

        Args:
            question: User's question

        Returns:
            Query type classification
        """
        question_lower = question.lower()

        # Check each pattern category
        for query_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(question_lower):
                    return query_type

        return "unknown"
```

### 10.3 Data Access Layer

```python
# app/src/agent/data_access.py
import aiosqlite
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DataAccess:
    """
    Database access layer for agent service.

    Handles all SQLite operations for alerts, status logs, sessions.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create database schema if not exists."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables
            await db.execute("""
                CREATE TABLE IF NOT EXISTS streams (
                    stream_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    source_uri TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    stream_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    acknowledged BOOLEAN DEFAULT 0,
                    acknowledged_at DATETIME,
                    resolved_at DATETIME,
                    frame_path TEXT,
                    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp
                ON alerts(timestamp DESC)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_stream
                ON alerts(stream_id, timestamp DESC)
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS status_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stream_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    icon TEXT,
                    description TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    timestamp DATETIME NOT NULL,
                    duration_seconds INTEGER,
                    FOREIGN KEY (stream_id) REFERENCES streams(stream_id)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_log_timestamp
                ON status_log(timestamp DESC)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_log_stream
                ON status_log(stream_id, timestamp DESC)
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS query_sessions (
                    session_id TEXT PRIMARY KEY,
                    websocket_id TEXT NOT NULL,
                    created_at DATETIME NOT NULL,
                    last_activity DATETIME NOT NULL,
                    context TEXT
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_activity
                ON query_sessions(last_activity DESC)
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS query_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    query_text TEXT NOT NULL,
                    query_type TEXT,
                    response_text TEXT,
                    latency_ms INTEGER,
                    timestamp DATETIME NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES query_sessions(session_id)
                )
            """)

            await db.commit()
            logger.info("Database schema initialized")

    # Alert operations

    async def insert_alert(
        self,
        alert_id: str,
        stream_id: str,
        level: str,
        severity: str,
        title: str,
        message: str,
        timestamp: datetime,
        frame_path: Optional[str] = None
    ):
        """Insert a new alert."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO alerts
                (id, stream_id, level, severity, title, message, timestamp, frame_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, stream_id, level, severity, title, message,
                  timestamp.isoformat(), frame_path))
            await db.commit()

    async def query_alerts(
        self,
        stream_id: Optional[str],
        start: datetime,
        end: datetime,
        level: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query alerts within time range."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = """
                SELECT * FROM alerts
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start.isoformat(), end.isoformat()]

            if stream_id:
                query += " AND stream_id = ?"
                params.append(stream_id)

            if level:
                query += " AND level = ?"
                params.append(level)

            query += " ORDER BY timestamp DESC"

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_recent_alerts(
        self,
        stream_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent alerts for a stream."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("""
                SELECT * FROM alerts
                WHERE stream_id = ?
                  AND resolved_at IS NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """, (stream_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # Status log operations

    async def insert_status_log(
        self,
        stream_id: str,
        severity: str,
        description: str,
        icon: Optional[str] = None,
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None
    ):
        """Insert a status log entry."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO status_log
                (stream_id, severity, icon, description, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (stream_id, severity, icon, description, confidence,
                  timestamp.isoformat()))
            await db.commit()

    async def get_current_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get latest status for a stream."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("""
                SELECT * FROM status_log
                WHERE stream_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (stream_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_current_statuses(self) -> List[Dict[str, Any]]:
        """Get latest status for all streams."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get latest status per stream
            async with db.execute("""
                SELECT s1.* FROM status_log s1
                INNER JOIN (
                    SELECT stream_id, MAX(timestamp) as max_ts
                    FROM status_log
                    GROUP BY stream_id
                ) s2 ON s1.stream_id = s2.stream_id
                    AND s1.timestamp = s2.max_ts
            """) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def query_status_log(
        self,
        stream_id: Optional[str],
        start: datetime,
        end: datetime
    ) -> List[Dict[str, Any]]:
        """Query status log within time range."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = """
                SELECT * FROM status_log
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start.isoformat(), end.isoformat()]

            if stream_id:
                query += " AND stream_id = ?"
                params.append(stream_id)

            query += " ORDER BY timestamp DESC"

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_severity_distribution(
        self,
        stream_id: Optional[str],
        start: datetime,
        end: datetime
    ) -> Dict[str, float]:
        """Calculate severity distribution over time period."""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT severity, COUNT(*) as count
                FROM status_log
                WHERE timestamp BETWEEN ? AND ?
            """
            params = [start.isoformat(), end.isoformat()]

            if stream_id:
                query += " AND stream_id = ?"
                params.append(stream_id)

            query += " GROUP BY severity"

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                # Calculate percentages
                total = sum(row[1] for row in rows)
                if total == 0:
                    return {"green": 0, "yellow": 0, "red": 0}

                distribution = {
                    "green": 0,
                    "yellow": 0,
                    "red": 0
                }

                for severity, count in rows:
                    distribution[severity] = (count / total) * 100

                return distribution

    # Session operations

    async def create_session(
        self,
        session_id: str,
        websocket_id: str,
        context: Optional[str] = None
    ):
        """Create a new query session."""
        now = datetime.utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO query_sessions
                (session_id, websocket_id, created_at, last_activity, context)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, websocket_id, now.isoformat(),
                  now.isoformat(), context))
            await db.commit()

    async def update_session_activity(
        self,
        session_id: str,
        context: Optional[str] = None
    ):
        """Update session last activity timestamp."""
        now = datetime.utcnow()
        async with aiosqlite.connect(self.db_path) as db:
            if context:
                await db.execute("""
                    UPDATE query_sessions
                    SET last_activity = ?, context = ?
                    WHERE session_id = ?
                """, (now.isoformat(), context, session_id))
            else:
                await db.execute("""
                    UPDATE query_sessions
                    SET last_activity = ?
                    WHERE session_id = ?
                """, (now.isoformat(), session_id))
            await db.commit()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("""
                SELECT * FROM query_sessions
                WHERE session_id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def cleanup_expired_sessions(self, hours: int = 1):
        """Delete sessions inactive for specified hours."""
        cutoff = datetime.utcnow().timestamp() - (hours * 3600)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM query_sessions
                WHERE last_activity < datetime(?, 'unixepoch')
            """, (cutoff,))
            await db.commit()

    # Query logging

    async def log_query(
        self,
        session_id: str,
        query_text: str,
        query_type: str,
        response_text: str,
        latency_ms: int
    ):
        """Log a query for analytics."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO query_log
                (session_id, query_text, query_type, response_text,
                 latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, query_text, query_type, response_text,
                  latency_ms, datetime.utcnow().isoformat()))
            await db.commit()
```

### 10.4 Conversation Manager

```python
# app/src/agent/conversation.py
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import uuid4

from .data_access import DataAccess


@dataclass
class SessionContext:
    """Conversation session context."""
    session_id: str
    websocket_id: str
    created_at: datetime
    last_activity: datetime

    # Context tracking
    current_stream_id: Optional[str] = None
    recent_queries: List[str] = None
    recent_entities: Dict[str, Any] = None

    def __post_init__(self):
        if self.recent_queries is None:
            self.recent_queries = []
        if self.recent_entities is None:
            self.recent_entities = {}

    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        data = {
            "current_stream_id": self.current_stream_id,
            "recent_queries": self.recent_queries,
            "recent_entities": self.recent_entities
        }
        return json.dumps(data)

    @classmethod
    def from_json(cls, session_id: str, websocket_id: str,
                  created_at: datetime, last_activity: datetime,
                  context_json: Optional[str]) -> "SessionContext":
        """Deserialize from JSON."""
        context = {}
        if context_json:
            try:
                context = json.loads(context_json)
            except json.JSONDecodeError:
                pass

        return cls(
            session_id=session_id,
            websocket_id=websocket_id,
            created_at=created_at,
            last_activity=last_activity,
            current_stream_id=context.get("current_stream_id"),
            recent_queries=context.get("recent_queries", []),
            recent_entities=context.get("recent_entities", {})
        )


class SessionManager:
    """
    Manages conversation sessions and context.

    Handles:
    - Session creation and lifecycle
    - Context persistence
    - Reference resolution (pronouns, implicit streams)
    """

    def __init__(self, db: DataAccess):
        self.db = db
        self._sessions_cache: Dict[str, SessionContext] = {}

    async def get_or_create(self, websocket_id: str) -> SessionContext:
        """Get existing session or create new one for WebSocket."""
        # Check cache first
        for session in self._sessions_cache.values():
            if session.websocket_id == websocket_id:
                return session

        # Check database
        # For now, create new session each time (could persist by websocket_id)
        session_id = str(uuid4())
        now = datetime.utcnow()

        session = SessionContext(
            session_id=session_id,
            websocket_id=websocket_id,
            created_at=now,
            last_activity=now
        )

        await self.db.create_session(
            session_id=session_id,
            websocket_id=websocket_id,
            context=session.to_json()
        )

        self._sessions_cache[session_id] = session
        return session

    async def update_activity(self, session: SessionContext):
        """Update session activity timestamp."""
        session.last_activity = datetime.utcnow()
        # Don't persist on every update to reduce DB writes
        # Will persist on save_context

    async def save_context(self, session: SessionContext):
        """Persist session context to database."""
        await self.db.update_session_activity(
            session_id=session.session_id,
            context=session.to_json()
        )

    def resolve_stream(
        self,
        query: str,
        session: SessionContext,
        hint: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve stream ID from query or context.

        Args:
            query: User's question
            session: Current session
            hint: Optional explicit stream_id from client

        Returns:
            Resolved stream_id or None
        """
        # Explicit hint takes precedence
        if hint:
            session.current_stream_id = hint
            return hint

        # Try to extract from query
        # Pattern: "room 2", "stream_0", "living room"
        patterns = [
            r"room\s+(\d+)",
            r"stream[_\s](\w+)",
            r"(living room|bedroom|kitchen)"
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Map to stream_id
                identifier = match.group(1).lower().replace(" ", "_")
                stream_id = f"stream_{identifier}" if not identifier.startswith("stream") else identifier
                session.current_stream_id = stream_id
                return stream_id

        # Fall back to session context
        return session.current_stream_id

    def resolve_time_range(
        self,
        query: str,
        session: SessionContext
    ) -> Tuple[datetime, datetime]:
        """
        Extract or infer time range from query.

        Returns:
            (start, end) datetime tuple
        """
        now = datetime.utcnow()
        query_lower = query.lower()

        # Yesterday
        if "yesterday" in query_lower:
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - timedelta(days=1)
            return start, end

        # Today
        if "today" in query_lower:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, now

        # Last week
        if "last week" in query_lower or "past week" in query_lower:
            start = now - timedelta(days=7)
            return start, now

        # Last N hours/days
        match = re.search(r"(?:past|last)\s+(\d+)\s+(hour|day|week)s?", query_lower)
        if match:
            count = int(match.group(1))
            unit = match.group(2)

            if unit == "hour":
                start = now - timedelta(hours=count)
            elif unit == "day":
                start = now - timedelta(days=count)
            elif unit == "week":
                start = now - timedelta(weeks=count)

            return start, now

        # Between X and Y
        # TODO: Parse "between yesterday and today"

        # Default: last 24 hours
        return now - timedelta(days=1), now

    async def cleanup_expired(self, hours: int = 1):
        """Clean up expired sessions."""
        await self.db.cleanup_expired_sessions(hours)

        # Clean cache
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        expired = [
            sid for sid, session in self._sessions_cache.items()
            if session.last_activity < cutoff
        ]
        for sid in expired:
            del self._sessions_cache[sid]
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/test_query_processor.py
import pytest
from app.src.agent.query_processor import QueryProcessor

def test_classify_current_status():
    processor = QueryProcessor(db=None)

    assert processor.classify("What's happening in Room 2?") == "current_status"
    assert processor.classify("Show me the current status") == "current_status"
    assert processor.classify("How is Room 1 doing?") == "current_status"

def test_classify_historical():
    processor = QueryProcessor(db=None)

    assert processor.classify("Were there any alerts yesterday?") == "historical"
    assert processor.classify("How many incidents in the past 24 hours?") == "historical"

def test_classify_trend():
    processor = QueryProcessor(db=None)

    assert processor.classify("Has Room 1 been stable?") == "trend"
    assert processor.classify("Is the status improving?") == "trend"

def test_classify_visual():
    processor = QueryProcessor(db=None)

    assert processor.classify("Why did the alert trigger?") == "visual"
    assert processor.classify("What do you see in the frame?") == "visual"
```

### 11.2 Integration Tests

```python
# tests/test_agent_service.py
import pytest
from datetime import datetime, timedelta
from app.src.agent.service import AgentService
from app.src.event_bus import EventBus

@pytest.mark.asyncio
async def test_current_status_query(agent_service, test_db):
    """Test current status query flow."""
    # Setup: Insert test status
    await test_db.insert_status_log(
        stream_id="stream_0",
        severity="green",
        description="Reading in chair",
        timestamp=datetime.utcnow()
    )

    # Create session
    session = await agent_service.get_session("test_websocket")

    # Query
    response = await agent_service.process_query(
        question="What's happening in stream_0?",
        session=session
    )

    assert response.query_type == "current_status"
    assert "Reading in chair" in response.answer
    assert response.latency_ms < 1000

@pytest.mark.asyncio
async def test_historical_alerts_query(agent_service, test_db):
    """Test historical alert query."""
    # Setup: Insert test alerts
    yesterday = datetime.utcnow() - timedelta(days=1)
    await test_db.insert_alert(
        alert_id="test_1",
        stream_id="stream_0",
        level="critical",
        severity="red",
        title="Fall detected",
        message="Person appears to have fallen",
        timestamp=yesterday
    )

    session = await agent_service.get_session("test_websocket")

    response = await agent_service.process_query(
        question="Were there any critical alerts yesterday?",
        session=session
    )

    assert response.query_type == "historical"
    assert "Fall detected" in response.answer
```

### 11.3 End-to-End Tests

```python
# tests/test_websocket_agent.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_query_via_websocket(test_client):
    """Test complete query flow via WebSocket."""
    with test_client.websocket_connect("/ws/live") as websocket:
        # Send query
        websocket.send_json({
            "type": "query",
            "question": "What's the current status?",
            "request_id": "test_123"
        })

        # Receive acknowledgment
        ack = websocket.receive_json()
        assert ack["type"] == "query_received"
        assert ack["request_id"] == "test_123"

        # Receive response
        response = websocket.receive_json()
        assert response["type"] == "query_response"
        assert response["request_id"] == "test_123"
        assert "answer" in response
```

---

## 12. Performance Considerations

### 12.1 Query Latency Targets

| Query Type | Target Latency | Strategy |
|------------|----------------|----------|
| Current Status | < 100ms | Redis + SQLite indexed query |
| Historical (simple) | < 200ms | Indexed DB query |
| Historical (complex) | < 500ms | Aggregation query + caching |
| Trend Analysis | < 1s | Pre-computed or cached |
| Visual Reasoning | < 2s | VLM inference (unavoidable) |

### 12.2 Caching Strategy

**Redis Cache Keys:**
```python
# Response caching
cache_key = f"agent:response:{hash(query + stream_id + time_window)}"
ttl = 300  # 5 minutes

# Report caching
report_key = f"agent:report:{report_type}:{stream_id}:{date}"
ttl = 3600  # 1 hour
```

**Cache Invalidation:**
- Time-based expiration (TTL)
- Manual invalidation on new critical alerts

### 12.3 Database Optimization

**Indexes:**
- All timestamp columns (for time-range queries)
- stream_id + timestamp (composite for per-stream queries)
- severity (for filtering)

**Query Optimization:**
- Use `LIMIT` on all queries
- Avoid `SELECT *` in production
- Use prepared statements (SQLAlchemy handles this)

**Partitioning (Future):**
- Archive old data (> 30 days) to separate table
- Reduces index size, improves query speed

---

## 13. Security Considerations

### 13.1 Input Validation

**Query Text:**
- Max length: 500 characters
- Sanitize for SQL injection (use parameterized queries)
- Rate limiting: 10 queries/minute per session

### 13.2 Data Access Control

**Stream Access:**
- Future: Add per-user stream permissions
- For now: All authenticated WebSocket connections can query all streams

### 13.3 Sensitive Data

**Redaction:**
- Optionally redact PII from query logs
- Don't store frames in database (only paths)

---

## 14. Monitoring & Observability

### 14.1 Metrics

**Key Metrics to Track:**
- Query volume (queries/minute)
- Query latency by type (p50, p95, p99)
- Cache hit rate
- Session duration
- Error rate

**Implementation:**
```python
# Prometheus metrics (optional)
from prometheus_client import Counter, Histogram

query_counter = Counter('agent_queries_total', 'Total queries', ['type'])
query_latency = Histogram('agent_query_latency_seconds', 'Query latency', ['type'])
```

### 14.2 Logging

**Log Levels:**
- INFO: Query processing start/end
- DEBUG: Query classification, context resolution
- WARNING: Slow queries (> 2s), cache misses
- ERROR: Query failures, VLM timeouts

**Structured Logging:**
```python
logger.info(
    "Query processed",
    extra={
        "session_id": session.session_id,
        "query_type": query_type,
        "latency_ms": latency_ms,
        "stream_id": stream_id
    }
)
```

---

## 15. Future Enhancements

### 15.1 Phase 2 Features

1. **Streaming Responses**: Use Server-Sent Events for progressive answers
2. **Multi-turn Conversations**: Track full dialogue history for context
3. **Scheduled Reports**: Cron job for daily/weekly email digests
4. **Voice Queries**: Integrate speech-to-text for voice commands
5. **Proactive Alerts**: Agent suggests queries based on anomalies

### 15.2 Advanced Analytics

1. **Predictive Alerts**: ML model predicts issues before they occur
2. **Correlation Analysis**: "Room 2 often goes yellow after Room 1 goes red"
3. **Custom Dashboards**: User-defined query templates

### 15.3 LLM Integration (Optional)

**When to Consider:**
- Query classification becomes too complex for rules
- Need more natural, conversational responses
- Want to handle arbitrary follow-up questions

**Model Options:**
- **Local LLM** (e.g., Llama 3.2 3B): Runs on Jetson, no API costs
- **Cloud LLM** (e.g., Claude, GPT-4): Better quality, requires internet

**Hybrid Approach:**
- Use templates for 80% of queries (fast, deterministic)
- Use LLM for complex/ambiguous queries (flexible, slower)

---

## Appendix A: Database Migrations

### Initial Schema Migration

```python
# app/src/database/migrations/001_initial_schema.py
"""
Initial database schema for agent service.

Run with: python -m app.src.database.migrate
"""

async def upgrade(db):
    """Apply migration."""
    # See schema definitions in Section 4.1
    pass

async def downgrade(db):
    """Revert migration."""
    # Drop tables in reverse order
    await db.execute("DROP TABLE IF EXISTS query_log")
    await db.execute("DROP TABLE IF EXISTS query_sessions")
    await db.execute("DROP TABLE IF EXISTS status_log")
    await db.execute("DROP TABLE IF EXISTS alerts")
    await db.execute("DROP TABLE IF EXISTS protocols")
    await db.execute("DROP TABLE IF EXISTS streams")
```

---

## Appendix B: Example Queries & Responses

### Example 1: Current Status

**User:** "What's happening in Room 2?"

**Agent Response:**
```
✅ **stream_2**: Resident reading in rocking chair
*Last updated: 2026-01-08 14:32:15*

**Recent Alerts (0):**
No recent alerts.
```

### Example 2: Historical Alerts

**User:** "Were there any critical alerts yesterday in Room 1?"

**Agent Response:**
```
**Alerts from 2026-01-07 to 2026-01-08:**

Total: 2 alerts
- Critical: 2
- Warning: 0
- Info: 0

**Critical Alerts:**
- 01/07 08:15: Fall Detected - Resident appears to have fallen
- 01/07 14:22: Missing Person - Room is empty, resident not visible
```

### Example 3: Trend Analysis

**User:** "Has Room 1 been stable this week?"

**Agent Response:**
```
**Trend Analysis: stream_1**

The status has been **generally stable with minor fluctuations**.

**Distribution:**
- Green: 82.3%
- Yellow: 14.2%
- Red: 3.5%
```

### Example 4: Visual Reasoning

**User:** "Why did the alert trigger at 3pm?"

**Agent Response:**
```
At 3:00 PM, the system detected a fall. The image shows a person on the ground
in an unusual position, which triggered the critical alert. Emergency protocols
were activated, and the incident was logged.

[Would you like to see the frame image?]
```

---

## Appendix C: Configuration

### Environment Variables

```bash
# .env
AGENT_DB_PATH=/app/data/newport.db
AGENT_SESSION_TIMEOUT_HOURS=1
AGENT_CACHE_TTL_SECONDS=300
AGENT_VLM_TIMEOUT_SECONDS=5
AGENT_MAX_QUERY_LENGTH=500
AGENT_QUERIES_PER_MINUTE=10
```

### Settings Class Extension

```python
# app/src/config.py
class Settings(BaseSettings):
    # ... existing settings ...

    # Agent settings
    agent_db_path: str = Field(
        default="/app/data/newport.db",
        description="Path to SQLite database for agent"
    )
    agent_session_timeout_hours: int = Field(
        default=1,
        description="Session timeout in hours"
    )
    agent_cache_ttl_seconds: int = Field(
        default=300,
        description="Response cache TTL in seconds"
    )
```

---

## Summary

This design provides a comprehensive, production-ready Agent Service architecture for the Newport Demo. Key design decisions:

1. **Extend `app` container** - Simplicity, shared data access, low latency
2. **Hybrid response generation** - Templates for speed, VLM for complex queries
3. **Rule-based classification** - Fast, deterministic, good enough for domain
4. **SQLite for persistence** - Lightweight, sufficient for edge deployment
5. **Redis for caching** - Fast responses, reduced DB load
6. **Session-based memory** - Conversation context, reference resolution

The implementation is modular, testable, and follows existing patterns in the codebase. It integrates cleanly with EventBus, WebSocket handler, and VLM container.

**Next Steps:**
1. Review design with team
2. Begin Phase 1 implementation (foundation)
3. Iterate based on user feedback
4. Scale to advanced features as needed

---

**End of Document**
