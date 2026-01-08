# Agent Service Design - Executive Summary

## Overview

This document summarizes the complete technical design for the **Agent Service** component of the Newport Demo video monitoring system. The Agent Service processes natural language queries about monitoring data and generates analytical reports.

## Deliverables

Three comprehensive documents have been created:

### 1. AGENT_SERVICE_DESIGN.md (Main Technical Design)
**Complete technical specification including:**

- **Service Architecture**: Extend the `app` container rather than create a new one
  - Rationale: Shared data access, lower latency, simpler deployment
  - Component structure with clear module organization

- **Query Processing Pipeline**:
  - Rule-based classification (current_status, historical, trend, visual)
  - Hybrid response generation (templates + VLM)
  - Target latencies: 100ms-2s depending on query type

- **Data Access Layer**:
  - Complete SQLite schema (alerts, status_log, sessions, query_log)
  - Optimized indexes for time-range queries
  - Async connection pooling

- **Conversation Memory**:
  - Session-based context tracking
  - Reference resolution ("tell me more about that")
  - 1-hour session timeout with cleanup

- **API Design**:
  - WebSocket message types (query, query_response)
  - Optional REST endpoints
  - Redis channels for async VLM integration

- **Report Generation**:
  - Weekly summaries
  - Per-room statistics
  - Trend analysis

- **Integration Points**:
  - EventBus for data logging
  - WebSocket handler for user queries
  - VLM container for visual reasoning

### 2. AGENT_ARCHITECTURE_DIAGRAMS.md (Visual Reference)
**ASCII diagrams covering:**

- System architecture overview
- Query processing pipeline flow
- Conversation context management
- Database schema relationships
- VLM integration pattern
- Report generation flow
- Session lifecycle
- Performance benchmarks

### 3. AGENT_IMPLEMENTATION_GUIDE.md (Developer Guide)
**Practical implementation guide with:**

- Step-by-step setup instructions
- Code integration examples
- Database initialization scripts
- Testing strategies (unit, integration, manual)
- Debugging tips
- Common issues and solutions
- Deployment checklist

## Key Design Decisions

### 1. Container Strategy: Extend App Container ✅
**Why:**
- Direct SQLite access (no network hop)
- Share Redis connection
- Simpler deployment on Jetson
- Same lifecycle as FastAPI app

**Alternative Rejected:** Separate agent container (added complexity, latency)

### 2. Query Classification: Rule-Based ✅
**Why:**
- Fast (< 10ms classification)
- Deterministic behavior
- No model loading overhead
- Sufficient for bounded domain

**Alternative Rejected:** LLM-based classification (slower, less predictable)

### 3. Response Generation: Hybrid ✅
**Why:**
- Templates for speed (< 100ms)
- VLM for complex queries (visual reasoning)
- Best of both worlds

**Pattern:**
```
Simple queries (status, counts) → Templates (instant)
Complex queries (explanations)  → VLM (~500ms)
Reports                         → Structured templates
```

### 4. Data Storage: SQLite + Redis ✅
**Why:**
- SQLite: Persistent storage, SQL queries, good for edge
- Redis: Caching, pub/sub, live data
- Complementary strengths

**Schema:**
- `alerts` - Historical alerts with metadata
- `status_log` - Status change timeline
- `query_sessions` - Conversation context
- `query_log` - Analytics

### 5. VLM Integration: Redis Request-Response ✅
**Why:**
- Redis already available
- Async-friendly
- Lower latency than HTTP

**Pattern:**
```
Agent → Publish vlm.requests.{id}
VLM   → Subscribe, process, publish vlm.responses.{id}
Agent → Subscribe, receive, return to user
```

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
- ✅ Module structure created
- ✅ Database schema designed
- ⏳ DataAccess class implementation
- ⏳ Event handlers for logging

### Phase 2: Query Processing (Week 2)
- ⏳ QueryProcessor with classification
- ⏳ SessionManager for context
- ⏳ WebSocket integration
- ⏳ End-to-end query flow

### Phase 3: Response Generation (Week 3)
- ⏳ Response templates
- ⏳ Report generators
- ⏳ VLM integration
- ⏳ All query types working

### Phase 4: Polish (Week 4)
- ⏳ Redis caching
- ⏳ Session cleanup task
- ⏳ Performance optimization
- ⏳ Documentation

## Performance Targets

| Query Type | Target Latency | Strategy |
|------------|----------------|----------|
| Current Status | < 100ms | Redis + indexed query |
| Historical (simple) | < 200ms | Indexed DB query |
| Historical (complex) | < 500ms | Aggregation + cache |
| Trend Analysis | < 1s | Pre-computed/cached |
| Visual Reasoning | < 2s | VLM inference |

## Example Usage

### Query 1: Current Status
```
User: "What's happening in Room 2?"

Agent Response:
✅ stream_2: Resident reading in rocking chair
Last updated: 2026-01-08 14:32:15

Recent Alerts (0):
No recent alerts.
```

### Query 2: Historical
```
User: "Were there any critical alerts yesterday?"

Agent Response:
**Alerts from 2026-01-07 to 2026-01-08:**

Total: 2 alerts
- Critical: 2
- Warning: 0
- Info: 0

**Critical Alerts:**
- 01/07 08:15: Fall Detected
- 01/07 14:22: Missing Person
```

### Query 3: Trend
```
User: "Has Room 1 been stable this week?"

Agent Response:
**Trend Analysis: stream_1**

The status has been stable and healthy.

**Distribution:**
- Green: 82.3%
- Yellow: 14.2%
- Red: 3.5%
```

### Query 4: Visual (with VLM)
```
User: "Why did the alert trigger at 3pm?"

Agent Response:
At 3:00 PM, the system detected a fall. The image shows
a person on the ground in an unusual position, which
triggered the critical alert. Emergency protocols were
activated, and the incident was logged.
```

## File Structure

```
app/src/agent/
├── __init__.py
├── service.py              # Main AgentService orchestrator
├── query_processor.py      # Query classification
├── data_access.py          # Database operations
├── conversation.py         # Session management
├── report_generator.py     # Report templates
└── prompts.py             # VLM prompts

app/src/database/
├── __init__.py
├── models.py              # SQLAlchemy ORM
└── connection.py          # Connection pool

Documentation:
├── AGENT_SERVICE_DESIGN.md           # Main technical design (11,000+ lines)
├── AGENT_ARCHITECTURE_DIAGRAMS.md    # Visual diagrams
├── AGENT_IMPLEMENTATION_GUIDE.md     # Developer guide
└── AGENT_SERVICE_SUMMARY.md          # This file
```

## Integration Points

### 1. EventBus (app/src/event_bus.py)
```python
# Register agent handlers
event_bus.on("summary.received", agent_service.on_status_update)
event_bus.on("alert.triggered", agent_service.on_alert_triggered)
```

### 2. WebSocket (app/src/websocket.py)
```python
# Process user queries
if msg_type == "query":
    session = await agent_service.get_session(websocket_id)
    response = await agent_service.process_query(question, session)
    await websocket.send(response)
```

### 3. VLM Container (vlm/src/)
```python
# New: Agent request handler
class AgentHandler:
    async def on_visual_query(self, request):
        answer = vlm.describe(frame_path, question)
        await redis.publish(f"vlm.responses.{request_id}", answer)
```

## Database Schema Overview

```
streams (configuration)
  ├── alerts (incidents)
  └── status_log (timeline)

query_sessions (conversation state)
  └── query_log (analytics)
```

**Key Indexes:**
- `alerts(timestamp DESC)`
- `alerts(stream_id, timestamp DESC)`
- `status_log(timestamp DESC)`
- `status_log(stream_id, timestamp DESC)`

## Testing Strategy

### Unit Tests
- Query classification patterns
- Context resolution logic
- Response formatting

### Integration Tests
- End-to-end query flow
- Database operations
- Session management

### Manual Testing
- WebSocket client script
- Query examples
- Performance profiling

## Security Considerations

1. **Input Validation**: Max 500 chars, SQL injection protection
2. **Rate Limiting**: 10 queries/minute per session
3. **Data Access**: Stream-level permissions (future)
4. **Sensitive Data**: No PII in logs, frame paths only (not frames)

## Monitoring & Observability

**Metrics to Track:**
- Query volume (queries/minute)
- Query latency by type (p50, p95, p99)
- Cache hit rate
- Session duration
- Error rate

**Logging:**
- INFO: Query processing start/end
- DEBUG: Classification, context resolution
- WARNING: Slow queries, cache misses
- ERROR: Query failures, VLM timeouts

## Next Steps

1. **Review**: Team review of design documents
2. **Prototype**: Implement Phase 1 (foundation)
3. **Iterate**: Gather feedback, refine design
4. **Deploy**: Gradual rollout with monitoring
5. **Enhance**: Add advanced features based on usage

## Questions to Address

Before starting implementation, clarify:

1. **VLM Availability**: Can we modify the VLM container to add agent handler?
2. **Database Location**: Confirm `/app/data/` is the right path
3. **Session Expiry**: Is 1 hour the right timeout?
4. **Query Limits**: Is 10 queries/minute appropriate?
5. **Caching**: Should we cache reports? For how long?

## Resources

- **Technical Design**: `AGENT_SERVICE_DESIGN.md` (complete spec)
- **Architecture Diagrams**: `AGENT_ARCHITECTURE_DIAGRAMS.md` (visual reference)
- **Implementation Guide**: `AGENT_IMPLEMENTATION_GUIDE.md` (developer guide)
- **Existing Codebase**:
  - `app/src/event_bus.py` - Event handling pattern
  - `app/src/websocket.py` - WebSocket integration
  - `app/src/models.py` - Data models
  - `vlm/src/vlm_subscriber.py` - VLM service pattern

## Success Criteria

The Agent Service will be considered successful when:

1. ✅ Users can ask natural language queries via WebSocket
2. ✅ 90%+ of queries classified correctly
3. ✅ Responses meet latency targets (< 2s for all types)
4. ✅ Conversation context works for follow-up questions
5. ✅ Reports generate accurate summaries
6. ✅ Integration with VLM for visual reasoning works
7. ✅ No data loss (all alerts/status logged to DB)
8. ✅ System stable under load (10+ concurrent sessions)

## Conclusion

This design provides a **production-ready** architecture for the Agent Service that:

- **Integrates cleanly** with existing Newport Demo components
- **Scales efficiently** for edge deployment on Jetson
- **Performs well** with latencies under 2 seconds
- **Maintains context** for natural conversation
- **Provides value** through reports and analytics

The modular design allows for **incremental implementation** and **future enhancements** (LLM integration, proactive alerts, predictive analytics).

---

**Ready for implementation!** 🚀

Contact: Backend Engineer Team
Date: 2026-01-08
Version: 1.0
