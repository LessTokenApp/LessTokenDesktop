# Sprint 2: Clipboard Pipeline — Complete ✅

## Overview
Built the complete clipboard processing pipeline with content detection, prompt management, history persistence, and orchestration.

## Architecture: Monitor → Detect → Prompt → AI → Format → History

```
┌─────────────────────────────────────────────────────────────┐
│  User copies text to clipboard                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  1️⃣  MONITOR                 │
        │  ClipboardService            │
        │  (polling + change detection)│
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  2️⃣  DETECT                  │
        │  ContentDetector             │
        │  (text/code/email/json/etc.) │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  3️⃣  SUGGEST PROMPTS         │
        │  PromptService               │
        │  (match content type)        │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  4️⃣  PROCESS                 │
        │  ProcessorService            │
        │  (call AI provider)          │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  5️⃣  PERSIST                 │
        │  HistoryService              │
        │  (save to SQLite)            │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  6️⃣  OUTPUT                  │
        │  Copy to clipboard           │
        │  (optional)                  │
        └──────────────────────────────┘
```

## What Was Built

### 1. **Content Detector** (`services/content.py`)

Intelligent content type detection with confidence scoring.

**Supported Types:**
- `TEXT` — Plain text
- `CODE` — Code (with language detection: Python, JS, Go, Rust, Java, SQL, Bash)
- `EMAIL` — Email addresses
- `URL` — HTTP/HTTPS URLs
- `JSON` — JSON data (validated)
- `YAML` — YAML configuration
- `MARKDOWN` — Markdown documents
- `IMAGE` — Image files
- `FILE` — Other file types
- `UNKNOWN` — Unrecognized

**Smart Detection:**
```python
detector = ContentDetector()
content_info = detector.detect("def hello():\n    print('hi')")

# Returns:
# ContentInfo(
#     content_type=ContentType.CODE,
#     language="python",
#     confidence=0.85
# )
```

**Language Detection** for code:
- Analyzes first 10 lines for keywords
- Supports: Python, JavaScript, Go, Rust, Java, SQL, Bash
- Confidence scoring (≥2 keyword matches)

### 2. **Prompt Service** (`services/prompt.py`)

Built-in + custom prompt management with content-type awareness.

**Built-in Prompts:**
- `fix-grammar` — Fix spelling/grammar
- `summarize` — Create concise summary
- `expand` — Add details
- `code-review` — Review code
- `explain-code` — Explain code logic
- `json-format` — Format JSON
- `markdown-format` — Clean up Markdown

**Key Features:**
```python
prompt_service = PromptService(prompts_dir)

# Get prompt
prompt = prompt_service.get_prompt("fix-grammar")

# Get prompts for content type
prompts = prompt_service.get_prompts_for_content_type(ContentType.CODE)

# Create custom prompt
custom = Prompt(
    id="my-seo",
    name="SEO Optimize",
    content="Optimize for SEO: {text}",
    category="seo",
    content_types=[ContentType.TEXT],
)
prompt_service.create_prompt(custom)

# Track usage
prompt_service.increment_usage("fix-grammar")
popular = prompt_service.get_popular_prompts(limit=5)
```

**Persistence:**
- Built-in prompts (7 included)
- Custom prompts saved to `~/.config/prompts.json`
- Automatic serialization/deserialization

### 3. **History Service** (`services/history.py`)

SQLite-backed persistent history with search + analytics.

**Database Schema:**
- `id` (UUID)
- `timestamp` (ISO format)
- `original_content` (text)
- `processed_content` (text)
- `content_type` (enum)
- `prompt_id` + `prompt_name`
- `provider`, `model`, `tokens`, `cost`
- `metadata` (JSON)

**Indexes for Performance:**
- `timestamp DESC` — Fast recent queries
- `content_type` — Filter by type
- `prompt_id` — Filter by prompt

**Key Methods:**
```python
history = HistoryService()

# Add entry
entry_id = history.add_entry(
    original_content="hello world",
    processed_content="Hello World",
    content_type=ContentType.TEXT,
    prompt_id="fix-grammar",
    prompt_name="Fix Grammar",
    provider="claude",
    model="claude-3-5-haiku",
    input_tokens=10,
    output_tokens=12,
    cost_usd=0.00123,
)

# Query
recent = history.get_recent(limit=50)
by_type = history.get_by_content_type(ContentType.CODE)
by_prompt = history.get_by_prompt("fix-grammar")

# Search
results = history.search("hello")

# Analytics
stats = history.get_statistics()
# Returns: total_entries, total_cost_usd, total_tokens, 
#          content_type_distribution, top_prompts
```

**Auto-Cleanup:**
```python
# Delete entries older than 30 days
deleted = history.clear_history(days_old=30)
```

### 4. **Pipeline Service** (`services/pipeline.py`)

Orchestrator that ties together the entire flow.

**Core Method:**
```python
pipeline = Pipeline(
    clipboard_service,
    content_detector,
    prompt_service,
    processor_service,
    history_service,
    event_bus,
)

# Process text
result = pipeline.process(
    content="Fix this: teh quick brow fox",
    prompt_id="fix-grammar",
    auto_copy=True  # Copy result to clipboard
)
# Returns processed text

# Process with auto-detected prompt
result = pipeline.process_with_prompt(
    content=code_text,
    prompt_id="code-review",
)

# Get suggested prompts
suggestions = pipeline.get_quick_actions(text)
# Returns: [{"prompt_id": "...", "prompt_name": "...", "category": "..."}]

# Start background monitoring
pipeline.start_monitoring()
# Watches clipboard for changes in background thread

# Get stats
stats = pipeline.get_pipeline_stats()
# Returns full analytics from history service
```

**Pipeline Flow in Code:**
1. **Detect** content type
2. **Auto-select** prompt (or use provided prompt_id)
3. **Format** prompt with `{text}` placeholder
4. **Process** through AI (gets ProviderResponse)
5. **Save** to SQLite history
6. **Copy** result to clipboard (optional)
7. **Track** tokens and cost

### 5. **Updated Application Class**

Complete service orchestration:

```python
# Initialize everything
app = Application(config)

# Startup all services
app.startup()

# Use services
result = app.process_text("teh quick fox", prompt_id="fix-grammar")
suggestions = app.get_quick_actions("def hello(): ...")
stats = app.get_stats()

# Shutdown
app.shutdown()
```

## Pipeline Data Flow Example

**Input:** User copies "def hello() pass"

```
1. ClipboardService detects change
   ↓
2. ContentDetector identifies: CODE (python)
   ↓
3. PromptService finds: [code-review, explain-code]
   ↓
4. User selects: "explain-code"
   ↓
5. ProcessorService calls AI:
   Prompt: "Explain what the following code does in simple terms:
            def hello() pass"
   Response: "This defines a function named hello that does nothing..."
   Tokens: 15 → 28
   Cost: $0.00045
   ↓
6. HistoryService saves entry
   ↓
7. Result copied to clipboard
   ↓
8. Stats updated
```

## Service Integration

### Event Flow
Services communicate via EventBus:
- `ClipboardChangedEvent` — When clipboard monitored
- `ProcessingStartedEvent` — Before AI call
- `ProcessingCompletedEvent` — After AI call
- `HistorySavedEvent` — History persisted

```python
event_bus.subscribe("processing:completed", on_processing_done)
```

### Database Location
```
~/.ai-clipboard-optimizer/
├── history.db           (SQLite history)
└── prompts.json         (Custom prompts)
```

### Configuration
All services respect `AppConfig`:
- `poll_interval_seconds` — Clipboard check frequency
- `ai_provider` — Default provider
- `log_level` — Logging verbosity
- `output_dir` — Data storage location

## Testing Examples

```python
# Test content detection
def test_code_detection():
    detector = ContentDetector()
    result = detector.detect("def foo(): pass")
    assert result.content_type == ContentType.CODE
    assert result.language == "python"

# Test prompt service
def test_prompt_service():
    prompts = PromptService()
    assert len(prompts.get_all_prompts()) >= 7  # Built-in
    
    suitable = prompts.get_prompts_for_content_type(ContentType.CODE)
    assert "code-review" in [p.id for p in suitable]

# Test history service
def test_history():
    history = HistoryService(":memory:")  # In-memory DB
    
    entry_id = history.add_entry(
        original_content="test",
        processed_content="TEST",
        content_type=ContentType.TEXT,
        prompt_id="test",
        prompt_name="Test",
        provider="mock",
        model="mock",
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
    )
    
    entry = history.get_entry(entry_id)
    assert entry is not None
    assert entry.processed_content == "TEST"

# Test pipeline
def test_pipeline_flow():
    # Create mocks
    clipboard = ClipboardService(EventBus())
    detector = ContentDetector()
    prompts = PromptService()
    processor = ProcessorService(EventBus(), ProviderFactory())
    history = HistoryService()
    
    pipeline = Pipeline(
        clipboard, detector, prompts, processor, history, EventBus()
    )
    
    # Mock processor response
    processor.set_provider(MockProvider())
    
    result = pipeline.process("hello world", "fix-grammar")
    assert result is not None
```

## Files Created

### New Services
- `services/content.py` — ContentDetector
- `services/prompt.py` — PromptService
- `services/history.py` — HistoryService
- `services/pipeline.py` — Pipeline orchestrator

### Modified Files
- `services/__init__.py` — Exports all new services
- `application.py` — Full service setup + convenience methods

## Next Steps (Sprint 3)

### UI/UX
- [ ] PySide6 desktop application with tray icon
- [ ] Hotkeys for quick processing (Ctrl+Shift+P)
- [ ] History viewer UI
- [ ] Prompt management UI
- [ ] Settings/configuration UI
- [ ] Dark mode support

### Enhancements
- [ ] Clipboard history search with AI
- [ ] Batch processing
- [ ] Prompt chains (Fix → Summarize → SEO → Tweet)
- [ ] Real-time token cost preview
- [ ] Provider auto-selection based on cost/speed

## Summary

Sprint 2 delivers a **production-ready pipeline** that:

✅ Detects content type intelligently (code, email, JSON, etc.)
✅ Manages built-in + custom prompts
✅ Persists all transformations to SQLite
✅ Provides search + analytics
✅ Orchestrates complete workflow
✅ Fully testable with mock providers
✅ Event-driven for decoupled integration

The pipeline is now ready for UI integration in Sprint 3.
