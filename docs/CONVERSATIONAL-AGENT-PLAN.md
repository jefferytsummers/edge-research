# AGILE Plan: Conversational Agent Feature

## Overview

This plan synthesizes the UX/UI and Backend agent designs into a unified implementation strategy for adding a Conversational Agent feature to the Newport Demo. The feature enables users to ask natural language questions about monitoring data through a global collapsible sidebar chat interface.

**Goal:** Enable users to query monitoring data, get historical summaries, analyze trends, and receive visual reasoning explanations through a natural conversation interface.

**Builds On:** Core Newport Demo architecture (EventBus, WebSocket, VLM integration, multi-stream pipeline)

---

## Design Alignment Validation

### UX and Backend Compatibility

| Aspect | UX Design | Backend Design | Alignment Status |
|--------|-----------|----------------|------------------|
| Architecture | Collapsible sidebar panel | Extend app container | **COMPATIBLE** - UI sends queries via existing WebSocket |
| Message Types | WSChatQuery, WSChatResponse | query, query_response | **ALIGNED** - Map directly to existing WebSocket types |
| Query Types | Summaries, drill-downs, comparisons | current_status, historical, trend, visual | **COMPATIBLE** - UX flows map to backend query types |
| Streaming | WSChatResponseStream | Optional future enhancement | **GAP** - Backend starts sync, streaming Phase 2 |
| Data Viz | Charts, tables, alert cards | Response includes structured `data` field | **COMPATIBLE** - Backend provides data, frontend renders |
| Conversation Memory | Multi-turn context | Session-based with context resolution | **ALIGNED** - Backend handles reference resolution |

### Identified Gaps and Mitigations

| Gap | Impact | Mitigation |
|-----|--------|------------|
| Streaming responses not in initial backend | User waits for full response | Phase 1: Show typing indicator; Phase 2: Add streaming |
| Global chat vs per-feed chat | UX shows global panel, existing code has per-feed | Build global panel that supports optional stream_id context |
| Chart rendering specification missing | Frontend needs chart data format | Define structured data schema in shared types |
| Keyboard shortcuts (Cmd+K) not implemented | Accessibility feature | Include in UI epic |
| Mobile responsive design details | Sidebar on mobile | Design drawer/modal pattern for mobile |

---

## Epic Summary

| Epic | Description | Container | Size | Critical Path |
|------|-------------|-----------|------|---------------|
| CA1 | Backend Query Infrastructure | app | L | Yes |
| CA2 | Data Storage & Logging | app | M | Yes |
| CA3 | Conversation Context | app | M | Yes |
| CA4 | VLM Visual Reasoning | app + vlm | M | No |
| CA5 | Global Chat UI Components | frontend | L | Yes |
| CA6 | Chat State Management | frontend | M | Yes |
| CA7 | Data Visualization | frontend | M | No |
| CA8 | Demo Milestone & Polish | all | M | Yes |

---

## Epic CA1: Backend Query Infrastructure

**Goal:** Implement core query processing pipeline with classification, routing, and response generation.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA1.1 | Create `agent/` module structure with `__init__.py`, `service.py` | S | Module imports successfully, AgentService class exists |
| CA1.2 | Implement QueryProcessor with rule-based classification | M | Correctly classifies queries into 4 types with >90% accuracy on test set |
| CA1.3 | Create response templates for current_status queries | S | Returns formatted status with severity, icon, description |
| CA1.4 | Create response templates for historical queries | M | Returns alert counts, severity distribution, time-bounded results |
| CA1.5 | Create response templates for trend analysis queries | M | Returns stability assessment, percentage distribution, trend direction |
| CA1.6 | Integrate AgentService with WebSocket handler | M | Query messages processed and responses returned via WebSocket |
| CA1.7 | Add unknown query fallback with helpful suggestions | S | Unrecognized queries get guidance message with example questions |
| CA1.8 | Add input validation and rate limiting | S | Queries limited to 500 chars, 10/minute rate limit enforced |

**Technical Notes:**
- Pattern matching uses pre-compiled regex for <10ms classification
- Response templates use Markdown formatting for rich display
- Integration point: `app/src/websocket.py` lines 125-132

---

## Epic CA2: Data Storage & Logging

**Goal:** Implement SQLite schema and data access layer for persistent storage.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA2.1 | Create database schema with all tables | M | alerts, status_log, streams, query_sessions, query_log tables created |
| CA2.2 | Implement DataAccess class with alert queries | M | `query_alerts()`, `get_recent_alerts()`, `insert_alert()` work |
| CA2.3 | Implement status_log queries | M | `get_current_status()`, `query_status_log()`, `insert_status_log()` work |
| CA2.4 | Implement severity distribution aggregation | S | `get_severity_distribution()` returns percentages for time range |
| CA2.5 | Add database indexes for performance | S | Timestamp and stream_id indexes created, queries <100ms |
| CA2.6 | Register EventBus handlers for data logging | S | Status updates and alerts automatically logged to database |
| CA2.7 | Add database initialization to app startup | S | Schema created on first run, migrations handle updates |

**Technical Notes:**
- Database path: `/app/data/newport.db`
- Uses async `aiosqlite` for non-blocking queries
- Indexes: `(timestamp DESC)`, `(stream_id, timestamp DESC)`, `(severity)`

---

## Epic CA3: Conversation Context

**Goal:** Implement session management and context resolution for multi-turn conversations.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA3.1 | Create SessionContext dataclass | S | Tracks session_id, current_stream_id, recent_queries, entities |
| CA3.2 | Implement SessionManager with create/get | M | Sessions created on first query, retrieved by websocket_id |
| CA3.3 | Implement stream reference resolution | M | "Room 2" extracts to stream_2, pronouns resolve from context |
| CA3.4 | Implement time range resolution | M | "yesterday", "last week", "past 24 hours" parse correctly |
| CA3.5 | Add session persistence to database | S | Sessions survive brief disconnects, context JSON stored |
| CA3.6 | Implement session expiration (1 hour) | S | Background task cleans up stale sessions every 15 minutes |
| CA3.7 | Update context after each query | S | current_stream_id and recent_queries updated automatically |

**Technical Notes:**
- Context stored as JSON in `query_sessions.context` column
- Session cleanup uses `asyncio` background task

---

## Epic CA4: VLM Visual Reasoning

**Goal:** Enable visual reasoning queries via VLM container integration.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA4.1 | Create VLM request-response protocol | S | Request/response format defined for `vlm.requests.*` channels |
| CA4.2 | Implement `_request_vlm_analysis()` in AgentService | M | Publishes request, waits for response with 5s timeout |
| CA4.3 | Add AgentHandler to VLM container | M | VLM subscribes to agent requests, processes, publishes response |
| CA4.4 | Handle VLM timeout gracefully | S | Timeout returns user-friendly message, doesn't crash |
| CA4.5 | Add visual reasoning response formatting | S | VLM answer integrated into conversational response |

**Technical Notes:**
- Redis channels: `vlm.requests.{request_id}`, `vlm.responses.{request_id}`
- Frame path: `/shared/frames/{stream_id}/latest.jpg`
- Timeout: 5 seconds (configurable via `AGENT_VLM_TIMEOUT_SECONDS`)

---

## Epic CA5: Global Chat UI Components

**Goal:** Build collapsible sidebar chat panel with message display and input.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA5.1 | Create GlobalChatPanel container component | M | Collapsible sidebar, 320px width, toggles with button |
| CA5.2 | Implement chat toggle button in header | S | Floating button shows/hides panel, shows unread indicator |
| CA5.3 | Create ChatMessage component | M | Renders user/agent messages with timestamp, markdown support |
| CA5.4 | Create ChatInput component with send button | S | Text input, submit on Enter, send button, disabled when disconnected |
| CA5.5 | Create MessageList with scroll behavior | M | Auto-scrolls to bottom, smooth scroll, virtualized for performance |
| CA5.6 | Add SuggestedQuestions component | S | Shows 3-5 clickable starter questions |
| CA5.7 | Add loading state (typing indicator) | S | Animated dots shown while waiting for response |
| CA5.8 | Add error state display | S | Error messages shown with retry option |
| CA5.9 | Implement keyboard shortcut (Cmd+K) | S | Opens/focuses chat panel from anywhere |
| CA5.10 | Add mobile responsive drawer | M | Panel becomes bottom drawer on mobile (<768px) |

**Technical Notes:**
- Component location: `app/frontend/src/components/Chat/`
- Uses existing Tailwind CSS and shadcn/ui patterns
- MessageList uses `react-window` for virtualization if >100 messages

---

## Epic CA6: Chat State Management

**Goal:** Implement Zustand store for chat state and WebSocket integration.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA6.1 | Create chatStore with messages array | S | Store tracks messages, loading state, error state |
| CA6.2 | Add sendMessage action | S | Creates user message, sends via WebSocket, tracks request_id |
| CA6.3 | Handle query_received acknowledgment | S | Shows "processing" state in UI |
| CA6.4 | Handle query_response messages | M | Adds agent response to messages, clears loading state |
| CA6.5 | Update useWebSocket hook for chat messages | M | handleMessage processes chat-related WebSocket messages |
| CA6.6 | Add message persistence (localStorage) | S | Last 50 messages persist across page reloads |
| CA6.7 | Track current conversation context | S | Stores current_stream_id for contextual queries |

**Technical Notes:**
- Store location: `app/frontend/src/store/chatStore.ts`
- Extends existing WebSocket hook pattern from `useWebSocket.ts`
- Message format includes request_id for request-response correlation

---

## Epic CA7: Data Visualization

**Goal:** Render structured data (tables, charts, alert cards) in chat responses.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA7.1 | Define structured response data schema | S | TypeScript interfaces for table/chart/alert data |
| CA7.2 | Create ChatDataTable component | M | Renders tabular alert/status data with sorting |
| CA7.3 | Create ChatAlertCard component | S | Shows alert details inline in chat |
| CA7.4 | Create ChatChart component (severity pie chart) | M | Renders severity distribution as pie/donut chart |
| CA7.5 | Create ChatTrendChart component | M | Renders time-series trend data as line chart |
| CA7.6 | Auto-detect and render data type | S | Response renderer chooses component based on data shape |

**Technical Notes:**
- Chart library: recharts (add to package.json)
- Components location: `app/frontend/src/components/Chat/DataVisualization/`
- Backend sends structured data in `response.data` field

---

## Epic CA8: Demo Milestone & Polish

**Goal:** Create a compelling demo experience with polish and documentation.

| ID | Story | Size | Acceptance Criteria |
|----|-------|------|---------------------|
| CA8.1 | Create demo conversation script | S | 5-minute scripted demo showing all query types |
| CA8.2 | Seed realistic demo data | M | 7 days of alerts and status history for demo |
| CA8.3 | Add conversation starter on first visit | S | Panel shows welcome message with suggested questions |
| CA8.4 | Implement response caching (Redis) | M | Repeated queries within 5 min return cached response |
| CA8.5 | Add query analytics logging | S | All queries logged with type, latency, session |
| CA8.6 | Performance optimization pass | M | All queries meet latency targets (<2s) |
| CA8.7 | Add ARIA labels for accessibility | S | Screen reader support for chat panel |
| CA8.8 | Write user documentation | S | README section with example queries |
| CA8.9 | Add feature flag for gradual rollout | S | Chat feature can be enabled/disabled via config |

**Technical Notes:**
- Demo script covers: current status, historical alerts, trend analysis, visual reasoning
- Analytics stored in `query_log` table
- Feature flag: `AGENT_CHAT_ENABLED` environment variable

---

## Sprint Structure

### Sprint CA1: Backend Foundation (Week 1)
- **Epic CA1** (Query Infrastructure) - All stories
- **Epic CA2** (Data Storage) - CA2.1 through CA2.5

**Demo:** Run `make test-agent` to show query classification working, database logging status updates.

### Sprint CA2: Context & Storage (Week 2)
- **Epic CA2** (Data Storage) - CA2.6, CA2.7
- **Epic CA3** (Conversation Context) - All stories

**Demo:** Multi-turn conversation in terminal: "Room 2 alerts" -> "Show critical ones" -> "What about today?"

### Sprint CA3: Chat UI (Week 3)
- **Epic CA5** (Global Chat UI) - All stories
- **Epic CA6** (Chat State) - All stories

**Demo:** Full chat sidebar visible, send/receive messages, mobile responsive.

### Sprint CA4: Polish & Viz (Week 4)
- **Epic CA4** (VLM Visual Reasoning) - All stories
- **Epic CA7** (Data Visualization) - All stories
- **Epic CA8** (Demo & Polish) - All stories

**Demo:** Complete conversational agent with charts, visual reasoning, and demo script.

---

## Dependencies

### On Existing Code

| Component | File | Usage |
|-----------|------|-------|
| EventBus | `app/src/event_bus.py` | Register agent handlers, publish to Redis |
| WebSocket Handler | `app/src/websocket.py` | Process query messages, send responses |
| Models | `app/src/models.py` | Extend WSQuery, WSQueryResponse types |
| Frontend Store | `app/frontend/src/store/` | Add chatStore following existing patterns |
| useWebSocket Hook | `app/frontend/src/hooks/useWebSocket.ts` | Extend sendQuery, handle chat messages |
| Types | `app/frontend/src/types/index.ts` | Add ChatMessage, ChatResponse types |

### Between Epics

```
CA1 (Query Infrastructure)
   |
   +-- CA2 (Data Storage) --> CA3 (Context)
   |          |
   |          +--------------> CA4 (VLM) -----+
   |                                          |
   +----------------------------------------> CA8 (Demo)
                                              |
CA5 (Chat UI) -> CA6 (Chat State) -> CA7 (Viz) +
```

### External Dependencies

| Dependency | Purpose | Status |
|------------|---------|--------|
| aiosqlite | Async SQLite | Add to requirements.txt |
| recharts | Chart rendering | Add to package.json |
| react-window | List virtualization | Add to package.json |

---

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Query classification accuracy < 90% | Medium | High | Test with 100+ real queries, add fallback patterns |
| VLM response latency > 5s | Medium | Medium | Timeout with retry suggestion, cache frequent questions |
| Session context lost on WebSocket reconnect | Medium | Medium | Persist session in Redis, reconnect with session_id |
| SQLite performance with large history | Low | Medium | Add data retention policy (30 days), archive old data |
| Mobile chat UX feels cramped | Medium | Low | Test early on mobile, consider full-screen mode |
| Chart rendering performance | Low | Low | Virtualize large datasets, limit visible data points |
| Redis memory pressure with caching | Low | Medium | Set TTL on all cache keys, monitor memory usage |
| Context resolution ambiguity | Medium | Medium | Ask clarifying question when confidence < 0.7 |

---

## Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Query classification accuracy | Test suite with labeled queries | > 90% |
| Current status query latency | End-to-end timing | < 100ms |
| Historical query latency | End-to-end timing | < 500ms |
| Trend analysis latency | End-to-end timing | < 1s |
| Visual reasoning latency | End-to-end timing | < 5s |
| Chat panel open time | Time from click to render | < 200ms |
| Multi-turn context works | "Room 2" -> "critical ones" -> "today" | All resolve correctly |
| Mobile responsive | Works on 375px width | No horizontal scroll, usable |
| Accessibility score | Lighthouse accessibility audit | > 90 |
| Demo runs 15 minutes stable | No crashes, errors, or freezes | Pass |

---

## Backlog Summary

| Epic | Stories | S | M | L |
|------|---------|---|---|---|
| CA1. Query Infrastructure | 8 | 4 | 4 | 0 |
| CA2. Data Storage | 7 | 4 | 3 | 0 |
| CA3. Conversation Context | 7 | 4 | 3 | 0 |
| CA4. VLM Visual Reasoning | 5 | 3 | 2 | 0 |
| CA5. Global Chat UI | 10 | 6 | 4 | 0 |
| CA6. Chat State Management | 7 | 5 | 2 | 0 |
| CA7. Data Visualization | 6 | 2 | 4 | 0 |
| CA8. Demo & Polish | 9 | 6 | 3 | 0 |
| **Total** | **59** | **34** | **25** | **0** |

---

## Critical Path

```
Week 1: CA1 + CA2 (Backend foundation)
           |
           v
Week 2: CA3 (Context) -----> enables multi-turn queries
           |
           v
Week 3: CA5 + CA6 (UI) -----> user can see and interact
           |
           v
Week 4: CA4 + CA7 + CA8 ----> full feature complete
```

**Minimum Viable Feature (Week 2):** Backend handles queries with context resolution
**Minimum Visible Feature (Week 3):** Users can chat via sidebar
**Full Feature (Week 4):** Visual reasoning, charts, and polished demo

---

*Conversational Agent Feature Plan - January 2026*
*Synthesized from UX/UI and Backend Agent Designs*
