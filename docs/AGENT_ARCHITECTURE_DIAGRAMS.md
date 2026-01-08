# Agent Service Architecture Diagrams

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          NEWPORT DEMO SYSTEM                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│    Frontend     │
│  (React + WS)   │
└────────┬────────┘
         │ WebSocket
         │ {type: "query", question: "..."}
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          APP CONTAINER                                   │
│  ┌───────────────┐         ┌──────────────────────────────────────┐    │
│  │   WebSocket   │────────▶│          AgentService                 │    │
│  │    Handler    │         │  ┌────────────────────────────────┐  │    │
│  └───────┬───────┘         │  │   Query Processor              │  │    │
│          │                 │  │   • Classification             │  │    │
│          │                 │  │   • Pattern matching           │  │    │
│  ┌───────▼───────┐         │  └────────────────────────────────┘  │    │
│  │   EventBus    │◀───────▶│  ┌────────────────────────────────┐  │    │
│  │  (pub/sub)    │         │  │   Data Access Layer            │  │    │
│  └───────┬───────┘         │  │   • Alert queries              │  │    │
│          │                 │  │   • Status log queries         │  │    │
│          │                 │  │   • Aggregations               │  │    │
│          │                 │  └────────────────────────────────┘  │    │
│          │                 │  ┌────────────────────────────────┐  │    │
│          │                 │  │   Session Manager              │  │    │
│          │                 │  │   • Context tracking           │  │    │
│          │                 │  │   • Reference resolution       │  │    │
│          │                 │  └────────────────────────────────┘  │    │
│          │                 │  ┌────────────────────────────────┐  │    │
│          │                 │  │   Report Generator             │  │    │
│          │                 │  │   • Weekly summaries           │  │    │
│          │                 │  │   • Trend analysis             │  │    │
│          │                 │  └────────────────────────────────┘  │    │
│          │                 └──────────────────────────────────────┘    │
│          │                                                              │
│  ┌───────▼─────────────────────────────────────────────────────────┐   │
│  │                    Data Access Layer                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │   │
│  │  │ ORM Models   │  │ Connection   │  │ Query Methods│          │   │
│  │  │ (SQLAlchemy) │  │ Pool         │  │ (async)      │          │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
└────────────────────────────────┼──────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐    ┌──────────────────┐
│     Redis       │     │     SQLite      │    │   VLM Container  │
│  (pub/sub)      │     │   (persistent)  │    │ (dustynv/nano)   │
│                 │     │                 │    │                  │
│ • summaries     │     │ • alerts        │    │ • VLM Subscriber │
│ • detections    │     │ • status_log    │    │ • Agent Handler  │
│ • sessions      │     │ • sessions      │    │ • Visual Reason  │
│ • cache         │     │ • query_log     │    │                  │
└─────────────────┘     └─────────────────┘    └──────────────────┘
         ▲                                              ▲
         │                                              │
         └──────────────────────────────────────────────┘
                    Redis Request-Response
                    (visual reasoning queries)
```

## 2. Query Processing Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│                     QUERY PROCESSING FLOW                          │
└────────────────────────────────────────────────────────────────────┘

User Query: "Were there any alerts yesterday?"
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Query Classification                               │
│  Pattern Match: r"(yesterday|last week|past \d+ days)"     │
│  Result: "historical"                                       │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Context Resolution                                 │
│  • Resolve stream_id: from query or session context        │
│  • Resolve time_range: parse "yesterday" → timestamps      │
│  Result: stream_id=None, start=2026-01-07, end=2026-01-08 │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Query Type Routing                                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Current Status│  │ Historical   │  │   Trend      │     │
│  │< 100ms       │  │ Query        │  │ Analysis     │     │
│  │              │  │< 200ms       │  │< 1s          │     │
│  │Redis+SQLite  │  │SQLite alerts │  │Aggregation   │     │
│  └──────────────┘  └──────┬───────┘  └──────────────┘     │
│                           │ ◀─ Selected                     │
│                           │                                  │
│  ┌──────────────┐         │                                 │
│  │Visual        │         │                                 │
│  │Reasoning     │         │                                 │
│  │< 2s          │         │                                 │
│  │VLM via Redis │         │                                 │
│  └──────────────┘         │                                 │
└───────────────────────────┼─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Data Retrieval                                     │
│                                                              │
│  SQL Query:                                                  │
│    SELECT * FROM alerts                                     │
│    WHERE timestamp BETWEEN '2026-01-07' AND '2026-01-08'   │
│    ORDER BY timestamp DESC;                                 │
│                                                              │
│  Result: [Alert1, Alert2, Alert3]                          │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Response Formatting                                │
│                                                              │
│  Template:                                                   │
│    **Alerts from {start} to {end}:**                       │
│                                                              │
│    Total: {count} alerts                                    │
│    - Critical: {critical_count}                             │
│    - Warning: {warning_count}                               │
│    - Info: {info_count}                                     │
│                                                              │
│    **Critical Alerts:**                                     │
│    - {timestamp}: {title}                                   │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: Response Delivery                                  │
│                                                              │
│  WebSocket Message:                                          │
│  {                                                           │
│    "type": "query_response",                                │
│    "request_id": "abc123",                                  │
│    "answer": "**Alerts from 2026-01-07...",                │
│    "metadata": {                                             │
│      "query_type": "historical",                            │
│      "latency_ms": 142                                      │
│    }                                                         │
│  }                                                           │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
                    Frontend Display
```

## 3. Conversation Context Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                  CONVERSATION MEMORY EXAMPLE                       │
└────────────────────────────────────────────────────────────────────┘

Query 1: "Were there any alerts in Room 2 yesterday?"
┌──────────────────────────────────────────────────────────────┐
│ Session Context Update:                                      │
│   current_stream_id: "stream_2"                              │
│   recent_queries: ["Were there any alerts in Room 2..."]    │
│   recent_entities: {                                         │
│     "stream": "stream_2",                                    │
│     "time_range": "yesterday"                                │
│   }                                                           │
└──────────────────────────────────────────────────────────────┘
Response: "Yes, 3 alerts in Room 2 yesterday..."

     │
     ▼

Query 2: "Show me the critical ones"
┌──────────────────────────────────────────────────────────────┐
│ Context Resolution:                                           │
│   • No stream mentioned → use session.current_stream_id      │
│   • "the" → refers to previous query context                │
│   • "critical" → filter parameter                            │
│                                                               │
│ Resolved Query:                                               │
│   stream_id: "stream_2" (from context)                       │
│   time_range: "yesterday" (from context)                     │
│   filter: "level = 'critical'"                               │
└──────────────────────────────────────────────────────────────┘
Response: "Here are 2 critical alerts from Room 2 yesterday..."

     │
     ▼

Query 3: "What about today?"
┌──────────────────────────────────────────────────────────────┐
│ Context Resolution:                                           │
│   • stream_id: "stream_2" (from context, still talking       │
│     about Room 2)                                             │
│   • time_range: "today" (override previous "yesterday")     │
│   • filter: "level = 'critical'" (carry forward)            │
└──────────────────────────────────────────────────────────────┘
Response: "Today Room 2 has 0 critical alerts."
```

## 4. Data Schema Relationships

```
┌────────────────────────────────────────────────────────────────────┐
│                      DATABASE SCHEMA                               │
└────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│    streams       │
├──────────────────┤           ┌──────────────────────┐
│ stream_id (PK)   │───────────│ alerts               │
│ name             │           ├──────────────────────┤
│ source_uri       │           │ id (PK)              │
│ enabled          │           │ stream_id (FK)       │
│ created_at       │           │ level                │
│ updated_at       │           │ severity             │
└──────────────────┘           │ title                │
         │                     │ message              │
         │                     │ timestamp            │
         │                     │ acknowledged         │
         │                     │ resolved_at          │
         │                     │ frame_path           │
         │                     └──────────────────────┘
         │
         │                     ┌──────────────────────┐
         └─────────────────────│ status_log           │
                               ├──────────────────────┤
                               │ id (PK)              │
                               │ stream_id (FK)       │
                               │ severity             │
                               │ icon                 │
                               │ description          │
                               │ confidence           │
                               │ timestamp            │
                               │ duration_seconds     │
                               └──────────────────────┘

┌──────────────────────┐
│ query_sessions       │
├──────────────────────┤       ┌──────────────────────┐
│ session_id (PK)      │───────│ query_log            │
│ websocket_id         │       ├──────────────────────┤
│ created_at           │       │ id (PK)              │
│ last_activity        │       │ session_id (FK)      │
│ context (JSON)       │       │ query_text           │
└──────────────────────┘       │ query_type           │
                               │ response_text        │
                               │ latency_ms           │
                               │ timestamp            │
                               └──────────────────────┘

KEY INDEXES:
  alerts: (timestamp DESC), (stream_id, timestamp DESC), (severity)
  status_log: (timestamp DESC), (stream_id, timestamp DESC)
  query_sessions: (last_activity DESC)
```

## 5. VLM Integration Pattern

```
┌────────────────────────────────────────────────────────────────────┐
│               VLM VISUAL REASONING REQUEST FLOW                    │
└────────────────────────────────────────────────────────────────────┘

User Query: "Why did the alert trigger at 3pm?"

AgentService
     │
     │ 1. Classify as "visual" query
     ▼
┌─────────────────────────────────────────────────┐
│ Generate request_id: "req_abc123"               │
│ Locate frame: /shared/frames/stream_0/latest.jpg│
└──────────────────────┬──────────────────────────┘
                       │
                       │ 2. Publish to Redis
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Redis Channel: vlm.requests.req_abc123                   │
│                                                           │
│ Payload:                                                  │
│ {                                                         │
│   "request_id": "req_abc123",                            │
│   "type": "visual_reasoning",                            │
│   "frame_path": "/shared/frames/stream_0/latest.jpg",   │
│   "question": "Why did the alert trigger at 3pm?"       │
│ }                                                         │
└───────────────────────┬──────────────────────────────────┘
                        │
                        │ 3. VLM Container subscribes
                        ▼
┌──────────────────────────────────────────────────────────┐
│ VLM Container - Agent Handler                            │
│                                                           │
│ 1. Load image from frame_path                           │
│ 2. Run VILA model inference                              │
│ 3. Generate natural language explanation                │
└───────────────────────┬──────────────────────────────────┘
                        │
                        │ 4. Publish response
                        ▼
┌──────────────────────────────────────────────────────────┐
│ Redis Channel: vlm.responses.req_abc123                  │
│                                                           │
│ Payload:                                                  │
│ {                                                         │
│   "request_id": "req_abc123",                            │
│   "answer": "At 3:00 PM, the system detected a fall.    │
│              The image shows a person on the ground in   │
│              an unusual position, which triggered the    │
│              critical alert.",                            │
│   "confidence": 0.85                                     │
│ }                                                         │
└───────────────────────┬──────────────────────────────────┘
                        │
                        │ 5. AgentService receives (timeout: 5s)
                        ▼
                  Format Response
                        │
                        ▼
                  WebSocket → Frontend
```

## 6. Report Generation Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                  WEEKLY REPORT GENERATION                          │
└────────────────────────────────────────────────────────────────────┘

Trigger: User asks "Summarize last week for Room 2"
         OR: Scheduled cron job

     │
     ▼
┌─────────────────────────────────────────────────────┐
│  STEP 1: Time Range Calculation                     │
│  week_start = now - 7 days                          │
│  week_end = now                                      │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  STEP 2: Data Aggregation (Parallel Queries)        │
│                                                      │
│  Query 1: Get all alerts in time range              │
│    SELECT * FROM alerts                             │
│    WHERE stream_id = 'stream_2'                     │
│      AND timestamp BETWEEN ? AND ?                  │
│                                                      │
│  Query 2: Get severity distribution                 │
│    SELECT severity,                                 │
│           SUM(duration_seconds) as total_time       │
│    FROM status_log                                  │
│    WHERE stream_id = 'stream_2'                     │
│      AND timestamp BETWEEN ? AND ?                  │
│    GROUP BY severity                                │
│                                                      │
│  Query 3: Get critical incidents                    │
│    SELECT * FROM alerts                             │
│    WHERE stream_id = 'stream_2'                     │
│      AND level = 'critical'                         │
│      AND timestamp BETWEEN ? AND ?                  │
│    ORDER BY timestamp DESC                          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  STEP 3: Calculate Metrics                          │
│                                                      │
│  total_alerts = 15                                  │
│  critical_count = 2                                 │
│  warning_count = 8                                  │
│  info_count = 5                                     │
│                                                      │
│  green_hours = 142.5 (84.5%)                       │
│  yellow_hours = 22.0 (13.1%)                       │
│  red_hours = 3.5 (2.4%)                            │
│                                                      │
│  trend = "stable and healthy" (> 80% green)        │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  STEP 4: Apply Template                             │
│                                                      │
│  # Weekly Report: Room 2                            │
│  **Period:** 2026-01-01 - 2026-01-08              │
│                                                      │
│  ## Summary                                          │
│  - **Total Alerts:** 15                             │
│    - Critical: 2                                    │
│    - Warning: 8                                     │
│    - Info: 5                                        │
│  - **Status Distribution:**                         │
│    - Green: 142.5h (84.5%)                         │
│    - Yellow: 22.0h (13.1%)                         │
│    - Red: 3.5h (2.4%)                              │
│                                                      │
│  ## Critical Incidents                              │
│  - **2026-01-03 08:15**: Fall Detected              │
│    - Resident appears to have fallen                │
│  - **2026-01-05 14:22**: Missing Person             │
│    - Room is empty, resident not visible            │
│                                                      │
│  ## Trend Analysis                                  │
│  Room 2 has been stable and healthy this week.     │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  STEP 5: Cache (Optional)                           │
│                                                      │
│  Redis Key: report:weekly:stream_2:2026-01-08      │
│  TTL: 3600 seconds (1 hour)                         │
│  Value: {report JSON}                               │
└──────────────────────┬──────────────────────────────┘
                       ▼
                 Return to User
```

## 7. Session Lifecycle

```
┌────────────────────────────────────────────────────────────────────┐
│                      SESSION LIFECYCLE                             │
└────────────────────────────────────────────────────────────────────┘

WebSocket Connection Established
     │
     ▼
┌─────────────────────────────────────────────────┐
│ Session Creation                                 │
│   session_id = uuid4()                          │
│   websocket_id = connection.id                  │
│   created_at = now()                            │
│   last_activity = now()                         │
│   context = {}                                  │
└──────────────────────┬──────────────────────────┘
                       │
                       │ Insert to DB
                       ▼
┌──────────────────────────────────────────────────┐
│ INSERT INTO query_sessions                       │
│ (session_id, websocket_id, created_at,          │
│  last_activity, context)                         │
│ VALUES (?, ?, ?, ?, ?)                          │
└──────────────────────┬──────────────────────────┘
                       │
                       │ User sends queries...
                       ▼
┌──────────────────────────────────────────────────┐
│ Query Processing (multiple queries)              │
│   • Update last_activity = now()                │
│   • Update context with stream_id, entities     │
│   • Log query to query_log table                │
└──────────────────────┬──────────────────────────┘
                       │
                       │ Periodic check...
                       ▼
┌──────────────────────────────────────────────────┐
│ Session Expiry Check (every 15 minutes)         │
│                                                   │
│ IF (now() - last_activity) > 1 hour THEN        │
│   DELETE FROM query_sessions                     │
│   WHERE session_id = ?                          │
│                                                   │
│   Remove from cache                              │
│ END IF                                           │
└──────────────────────┬──────────────────────────┘
                       │
                       │ WebSocket disconnects OR expires
                       ▼
                  Session Cleanup
```

## Performance Benchmarks (Target)

```
┌────────────────────────────────────────────────────────────┐
│                   PERFORMANCE TARGETS                      │
├─────────────────────────────┬──────────────┬───────────────┤
│ Query Type                  │ Target       │ Strategy      │
├─────────────────────────────┼──────────────┼───────────────┤
│ Current Status              │ < 100ms      │ Redis + Index │
│ Historical (simple)         │ < 200ms      │ DB Index      │
│ Historical (complex)        │ < 500ms      │ Aggregation   │
│ Trend Analysis              │ < 1s         │ Cache         │
│ Visual Reasoning            │ < 2s         │ VLM Inference │
└─────────────────────────────┴──────────────┴───────────────┘

Cache Hit Rates:
  • Response cache: > 30% (5-minute TTL)
  • Report cache: > 60% (1-hour TTL)

Database Query Optimization:
  • All queries use prepared statements
  • Indexes on: timestamp, stream_id, severity
  • LIMIT clauses on all SELECT statements
  • Async connection pooling

Concurrency:
  • Multiple concurrent queries supported
  • WebSocket per-connection sessions
  • No blocking on VLM calls (async with timeout)
```
