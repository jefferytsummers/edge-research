# Agent Service Implementation Guide

Quick reference for implementing the Agent Service based on the technical design.

## Quick Start Checklist

### Phase 1: Foundation (Week 1)

- [ ] Create module structure
- [ ] Set up database schema
- [ ] Implement DataAccess class
- [ ] Add event handlers for logging
- [ ] Write unit tests

### Phase 2: Query Processing (Week 2)

- [ ] Implement QueryProcessor
- [ ] Build SessionManager
- [ ] Integrate with WebSocket
- [ ] Add context resolution
- [ ] Test end-to-end queries

### Phase 3: Response Generation (Week 3)

- [ ] Create response templates
- [ ] Implement report generators
- [ ] Add VLM integration
- [ ] Test all query types

### Phase 4: Polish (Week 4)

- [ ] Add Redis caching
- [ ] Background session cleanup
- [ ] Performance optimization
- [ ] Documentation

---

## File Structure

```bash
app/src/agent/
├── __init__.py
├── service.py              # Main AgentService class
├── query_processor.py      # Query classification
├── data_access.py          # Database operations
├── conversation.py         # Session management
├── report_generator.py     # Report templates
└── prompts.py             # VLM prompt templates

app/src/database/
├── __init__.py
├── models.py              # SQLAlchemy ORM models
└── connection.py          # DB connection pool
```

---

## Step-by-Step Implementation

### Step 1: Create Database Schema

```bash
# Create database directory
mkdir -p app/src/database

# Create migration script
cat > app/src/database/init_schema.py << 'EOF'
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

async def initialize_schema(db_path: str):
    """Initialize agent database schema."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        # Streams table
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

        # Alerts table
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

        # Indexes for alerts
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_stream ON alerts(stream_id, timestamp DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity, timestamp DESC)")

        # Status log table
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

        # Indexes for status_log
        await db.execute("CREATE INDEX IF NOT EXISTS idx_status_log_timestamp ON status_log(timestamp DESC)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_status_log_stream ON status_log(stream_id, timestamp DESC)")

        # Query sessions table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS query_sessions (
                session_id TEXT PRIMARY KEY,
                websocket_id TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                last_activity DATETIME NOT NULL,
                context TEXT
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_activity ON query_sessions(last_activity DESC)")

        # Query log table
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
        logger.info("Agent database schema initialized")

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(initialize_schema("/app/data/newport.db"))
EOF
```

### Step 2: Integrate with Main App

```python
# app/src/main.py

# Add to imports
from .agent.service import AgentService

# Add global instance
agent_service: Optional[AgentService] = None

# In lifespan startup (after EventBus initialization):
async def lifespan(app: FastAPI):
    global event_bus, redis_subscriber_task, startup_time, agent_service

    # ... existing code ...

    if event_bus.is_connected:
        # ... existing code ...

        # Initialize Agent Service
        agent_service = AgentService(
            event_bus=event_bus,
            db_path=settings.agent_db_path
        )
        await agent_service.initialize()
        logger.info("Agent service initialized")

        # Register event handlers for data logging
        event_bus.on("summary.received", agent_service.on_status_update)
        event_bus.on("alert.triggered", agent_service.on_alert_triggered)

    # ... rest of startup ...
```

### Step 3: Update WebSocket Handler

```python
# app/src/websocket.py

# Add to imports
from .agent.service import AgentService
from datetime import datetime

# Modify the query handler
@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for live updates."""
    await manager.connect(websocket)

    # Get agent service from app state
    from .main import agent_service

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

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

                    if agent_service:
                        # Get or create session
                        session = await agent_service.get_session(str(id(websocket)))

                        try:
                            # Process query
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
                    else:
                        # Agent service not available
                        await manager.send_to(websocket, {
                            "type": "query_response",
                            "request_id": request_id,
                            "answer": "Agent service is not available.",
                            "timestamp": datetime.utcnow().isoformat()
                        })

                elif msg_type == "ping":
                    await manager.send_to(websocket, {"type": "pong"})

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from client: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
```

### Step 4: Add Configuration

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
    agent_vlm_timeout_seconds: float = Field(
        default=5.0,
        description="VLM request timeout in seconds"
    )
    agent_max_query_length: int = Field(
        default=500,
        description="Maximum query text length"
    )
```

### Step 5: Create Test Stream Data

```python
# scripts/seed_test_data.py
"""Seed test data for agent development."""

import asyncio
import aiosqlite
from datetime import datetime, timedelta
from uuid import uuid4

async def seed_test_data(db_path="/app/data/newport.db"):
    async with aiosqlite.connect(db_path) as db:
        # Create test streams
        streams = [
            ("stream_0", "Room 1", "rtsp://test/stream0"),
            ("stream_1", "Room 2", "rtsp://test/stream1"),
        ]

        for stream_id, name, uri in streams:
            await db.execute("""
                INSERT OR IGNORE INTO streams
                (stream_id, name, source_uri, enabled, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (stream_id, name, uri, datetime.utcnow().isoformat(),
                  datetime.utcnow().isoformat()))

        # Create test alerts
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)

        test_alerts = [
            ("stream_0", "critical", "red", "Fall Detected",
             "Resident appears to have fallen", yesterday + timedelta(hours=8)),
            ("stream_0", "warning", "yellow", "Out of View",
             "Resident not visible in camera", yesterday + timedelta(hours=14)),
            ("stream_1", "info", "green", "Activity Detected",
             "Normal activity resumed", yesterday + timedelta(hours=10)),
        ]

        for stream_id, level, severity, title, message, timestamp in test_alerts:
            alert_id = str(uuid4())
            await db.execute("""
                INSERT INTO alerts
                (id, stream_id, level, severity, title, message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (alert_id, stream_id, level, severity, title, message,
                  timestamp.isoformat()))

        # Create test status log entries
        test_statuses = [
            ("stream_0", "green", "📗", "Reading in chair", 0.95),
            ("stream_0", "red", "🚨", "Fall detected", 0.90),
            ("stream_0", "green", "🧘", "Sitting calmly", 0.92),
            ("stream_1", "green", "📺", "Watching TV", 0.88),
        ]

        for i, (stream_id, severity, icon, description, confidence) in enumerate(test_statuses):
            timestamp = now - timedelta(hours=(len(test_statuses) - i))
            await db.execute("""
                INSERT INTO status_log
                (stream_id, severity, icon, description, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (stream_id, severity, icon, description, confidence,
                  timestamp.isoformat()))

        await db.commit()
        print("Test data seeded successfully")

if __name__ == "__main__":
    asyncio.run(seed_test_data())
```

---

## Testing

### Unit Tests

```python
# tests/test_query_processor.py

import pytest
from app.src.agent.query_processor import QueryProcessor

def test_classify_queries():
    processor = QueryProcessor(db=None)

    # Current status
    assert processor.classify("What's happening?") == "current_status"
    assert processor.classify("Show me current status") == "current_status"

    # Historical
    assert processor.classify("Were there alerts yesterday?") == "historical"
    assert processor.classify("Show me last week's incidents") == "historical"

    # Trend
    assert processor.classify("Has it been stable?") == "trend"
    assert processor.classify("Is it improving?") == "trend"

    # Visual
    assert processor.classify("Why did the alert trigger?") == "visual"
    assert processor.classify("What do you see?") == "visual"
```

### Integration Tests

```python
# tests/test_agent_integration.py

import pytest
from datetime import datetime, timedelta
from app.src.agent.service import AgentService
from app.src.event_bus import EventBus

@pytest.mark.asyncio
async def test_query_processing_end_to_end(tmp_path):
    """Test complete query processing flow."""
    db_path = tmp_path / "test.db"

    # Initialize agent
    event_bus = EventBus("redis://localhost:6379")
    agent = AgentService(event_bus, str(db_path))
    await agent.initialize()

    # Seed test data
    await agent.db.insert_alert(
        alert_id="test_1",
        stream_id="stream_0",
        level="critical",
        severity="red",
        title="Test Alert",
        message="Test message",
        timestamp=datetime.utcnow() - timedelta(days=1)
    )

    # Create session
    session = await agent.get_session("test_websocket")

    # Process query
    response = await agent.process_query(
        question="Were there any alerts yesterday?",
        session=session
    )

    # Verify
    assert response.query_type == "historical"
    assert "Test Alert" in response.answer
    assert response.latency_ms < 1000
```

### Manual Testing with WebSocket Client

```python
# scripts/test_websocket_client.py
"""Manual WebSocket testing client."""

import asyncio
import json
import websockets
from uuid import uuid4

async def test_agent_queries():
    uri = "ws://localhost:8080/ws/live"

    async with websockets.connect(uri) as websocket:
        # Test query 1: Current status
        request_id = str(uuid4())
        await websocket.send(json.dumps({
            "type": "query",
            "question": "What's happening in Room 1?",
            "request_id": request_id
        }))

        # Receive acknowledgment
        ack = await websocket.recv()
        print("ACK:", ack)

        # Receive response
        response = await websocket.recv()
        print("RESPONSE:", response)

        # Test query 2: Historical
        request_id = str(uuid4())
        await websocket.send(json.dumps({
            "type": "query",
            "question": "Were there any alerts yesterday?",
            "request_id": request_id
        }))

        ack = await websocket.recv()
        response = await websocket.recv()
        print("RESPONSE 2:", response)

if __name__ == "__main__":
    asyncio.run(test_agent_queries())
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In config.py or .env
LOG_LEVEL=DEBUG
```

### Check Database State

```bash
sqlite3 /app/data/newport.db

# Verify schema
.schema alerts
.schema status_log
.schema query_sessions

# Check data
SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 5;
SELECT * FROM status_log ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM query_sessions;

# Check indexes
.indexes alerts
```

### Monitor Redis

```bash
# Monitor Redis pub/sub
redis-cli MONITOR

# Check specific keys
redis-cli KEYS "agent:*"
redis-cli GET "agent:session:abc123:context"
```

### Test Query Classification

```python
python -c "
from app.src.agent.query_processor import QueryProcessor
qp = QueryProcessor(None)
print(qp.classify('Were there any alerts yesterday?'))
"
```

---

## Common Issues & Solutions

### Issue: Agent service not initializing

**Solution:**
- Check Redis connection: `redis-cli ping`
- Verify database path exists: `ls -la /app/data/`
- Check logs: `docker logs newport-demo-app-1`

### Issue: Queries timing out

**Solution:**
- Check database indexes: See "Check Database State" above
- Verify VLM container is running: `docker ps | grep vlm`
- Increase timeout in config: `AGENT_VLM_TIMEOUT_SECONDS=10`

### Issue: Session context not persisting

**Solution:**
- Check session cleanup job isn't too aggressive
- Verify WebSocket ID mapping: Add debug logging
- Check database writes: `SELECT * FROM query_sessions`

### Issue: VLM not responding

**Solution:**
- Verify Redis channels: `redis-cli PUBSUB CHANNELS vlm.*`
- Check VLM container logs: `docker logs newport-demo-vlm-1`
- Test Redis pub/sub manually:
  ```bash
  # Terminal 1
  redis-cli SUBSCRIBE vlm.responses.test123

  # Terminal 2
  redis-cli PUBLISH vlm.requests.test123 '{"request_id":"test123"}'
  ```

---

## Deployment Checklist

- [ ] Database schema initialized
- [ ] Indexes created for performance
- [ ] Agent service starts without errors
- [ ] WebSocket integration working
- [ ] Test queries execute successfully
- [ ] Session cleanup background task running
- [ ] Redis connection stable
- [ ] VLM integration tested
- [ ] Error handling covers edge cases
- [ ] Logging configured appropriately
- [ ] Performance meets targets

---

## Next Steps After Implementation

1. **User Testing**: Get feedback on query understanding and responses
2. **Performance Tuning**: Profile slow queries, optimize indexes
3. **Feature Expansion**: Add scheduled reports, proactive alerts
4. **Documentation**: Create user guide with example queries
5. **Monitoring**: Set up metrics collection (Prometheus/Grafana)

---

## Quick Reference: Key Files

| File | Purpose |
|------|---------|
| `app/src/agent/service.py` | Main orchestrator, query processing |
| `app/src/agent/query_processor.py` | Query classification logic |
| `app/src/agent/data_access.py` | Database operations |
| `app/src/agent/conversation.py` | Session and context management |
| `app/src/websocket.py` | WebSocket integration point |
| `app/src/main.py` | Initialization and lifecycle |
| `app/src/config.py` | Configuration settings |

---

## Useful Commands

```bash
# Initialize database
python -m app.src.database.init_schema

# Seed test data
python scripts/seed_test_data.py

# Run tests
pytest tests/test_agent_*.py -v

# Test WebSocket manually
python scripts/test_websocket_client.py

# Check database
sqlite3 /app/data/newport.db ".dump"

# Monitor Redis
redis-cli MONITOR

# View logs
docker logs -f newport-demo-app-1
```
