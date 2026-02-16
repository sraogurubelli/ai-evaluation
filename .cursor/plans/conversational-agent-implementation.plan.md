# Implementation Plan: Conversational Agent Interface

**Status:** For team review  
**Date:** February 2025  
**Related:** [Architecture Document](./conversational-agent-architecture.md)

---

## Overview

This plan implements a tools system foundation with CLI/SDK as primary interfaces, and conversational interface as optional enhancement. The implementation is phased, starting with MVP (tools system + CLI/SDK integration) and adding conversational interface incrementally.

---

## Phase 1: MVP - Essential Components

### Goal

Build tools system foundation that CLI/SDK use directly (no LLM required). Optionally add conversational interface for natural language interaction.

### Components

#### 1.1 Tools System (Foundation - Required)

**Files:**
- `src/aieval/agents/tools/base.py` - Abstract Tool interface
- `src/aieval/agents/tools/dataset_tools.py` - Dataset tools
- `src/aieval/agents/tools/scorer_tools.py` - Scorer tools
- `src/aieval/agents/tools/eval_tools.py` - Eval tools
- `src/aieval/agents/tools/comparison_tools.py` - Comparison tools
- `src/aieval/agents/tools/registry.py` - Tool registry

**Tasks:**
- [ ] Define `Tool` base class with `name`, `description`, `parameters_schema`, `execute()`
- [ ] Implement 6 built-in tools:
  - [ ] `LoadDatasetTool` - Load dataset from JSONL/index CSV
  - [ ] `CreateScorerTool` - Create scorer (DeepDiff, LLM-judge, etc.)
  - [ ] `CreateEvalTool` - Create eval definition
  - [ ] `RunEvalTool` - Run eval and get results
  - [ ] `CompareRunsTool` - Compare two runs
  - [ ] `SetBaselineTool` - Set baseline run
- [ ] Create `ToolRegistry` class (register, get, list_all, get_schemas)
- [ ] Generate JSON schemas from tool definitions
- [ ] Unit tests for each tool

**Estimated Time:** 3-4 days

#### 1.2 CLI/SDK Integration with Tools

**Files:**
- `src/aieval/cli/main.py` - Update CLI to use tools directly
- `src/aieval/sdk/__init__.py` - Add `run_tool()` function

**Tasks:**
- [ ] Update CLI commands to use tools directly (no LLM)
- [ ] Add `run_tool(tool_name, **kwargs)` function to SDK
- [ ] Ensure CLI/SDK can call tools without conversational agent
- [ ] Integration tests for CLI/SDK tool usage

**Estimated Time:** 2 days

#### 1.3 LLM Infrastructure (Optional - for Conversational Mode)

**Files:**
- `src/aieval/llm/client.py` - Unified LLM client (LiteLLM)
- `src/aieval/llm/config.py` - LLM configuration

**Tasks:**
- [ ] Install LiteLLM dependency (`pyproject.toml`) - Optional dependency
- [ ] Create `LLMClient` class wrapping LiteLLM
- [ ] Support Anthropic (primary) and OpenAI (fallback)
- [ ] Configuration via environment variables
- [ ] Error handling and retries
- [ ] Make LLM optional (graceful degradation if not configured)

**Dependencies:**
- `litellm>=1.0.0` (optional dependency)

**Estimated Time:** 1 day

#### 1.4 Conversational Agent (Optional Enhancement)

**Files:**
- `src/aieval/agents/conversational.py` - Main conversational agent

**Tasks:**
- [ ] Create `ConversationalAgent` extending `BaseEvaluationAgent`
- [ ] Initialize tool registry and LLM client
- [ ] Implement `chat()` method:
  - [ ] Send user input + tool schemas to LLM
  - [ ] Parse LLM response (tool calls)
  - [ ] Execute tool calls
  - [ ] Generate natural language response
- [ ] Handle errors gracefully (ask clarifying questions)
- [ ] Support conversation context (optional)
- [ ] Unit tests

**Estimated Time:** 2-3 days

**Note:** This is optional - tools system works without conversational agent

#### 1.5 CLI Chat Command (Optional Enhancement)

**Files:**
- `src/aieval/cli/main.py` - Add `chat` command

**Tasks:**
- [ ] Add `chat` command to CLI
- [ ] Support single message mode: `aieval chat "run eval on dataset X"`
- [ ] Support interactive mode: `aieval chat` (REPL)
- [ ] Add `--model` option for LLM selection
- [ ] Add `--no-interactive` flag
- [ ] Handle exit commands (`exit`, `quit`)
- [ ] Integration tests

**Estimated Time:** 1 day

**Note:** This is optional - CLI/SDK work without chat command

#### 1.6 Documentation

**Files:**
- `README.md` - Update with conversational interface as primary UX
- `CHANGELOG.md` - Document breaking changes
- `docs/conversational-agent.md` - New guide
- `docs/tools.md` - Document tools system
- `docs/migration.md` - Migration guide for breaking changes

**Tasks:**
- [ ] Update README with conversational interface as primary UX
- [ ] Create conversational agent guide with examples
- [ ] Document tools system and custom tools
- [ ] Document any breaking changes in CHANGELOG
- [ ] Create migration guide if breaking changes introduced
- [ ] Add examples to documentation

**Estimated Time:** 1-2 days

### Phase 1 Summary

**Total Estimated Time:** 8-10 days (6-7 days for tools + CLI/SDK, 2-3 days for optional conversational)

**Required Deliverables (Tools Foundation):**
- ✅ Tools system works independently
- ✅ CLI can use tools directly (no LLM required)
- ✅ SDK can use tools directly (no LLM required)
- ✅ Fast, predictable performance (<1 second)

**Optional Deliverables (Conversational Enhancement):**
- ✅ Users can chat with agent via CLI (if LLM configured)
- ✅ Agent understands basic commands (if conversational used)
- ✅ Agent executes via tools (if conversational used)
- ✅ Agent responds in natural language (if conversational used)

---

## Phase 2: Enhanced Features (Optional)

### Goal

Add skills system, entry point discovery, and API endpoint.

### Components

#### 2.1 Skills System

**Files:**
- `src/aieval/agents/skills/base.py` - Base Skill class
- `src/aieval/agents/skills/evaluation_skill.py` - Evaluation workflow
- `src/aieval/agents/skills/baseline_comparison_skill.py` - Baseline comparison
- `src/aieval/agents/skills/multi_model_evaluation_skill.py` - Multi-model eval
- `src/aieval/agents/skills/registry.py` - Skill registry

**Tasks:**
- [ ] Define `Skill` base class with `name`, `description`, `execute()`
- [ ] Implement 3 built-in skills:
  - [ ] `EvaluationSkill` - Complete evaluation workflow
  - [ ] `BaselineComparisonSkill` - Compare against baseline
  - [ ] `MultiModelEvaluationSkill` - Parallel model evaluation
- [ ] Create `SkillRegistry` class
- [ ] Integrate skills into `ConversationalAgent`
- [ ] Unit tests

**Estimated Time:** 2-3 days

#### 2.2 Entry Point Discovery

**Files:**
- `src/aieval/agents/loader.py` - Component loader

**Tasks:**
- [ ] Implement entry point discovery for tools
- [ ] Implement entry point discovery for skills
- [ ] Auto-load components on agent initialization
- [ ] Log loaded components for debugging
- [ ] Unit tests

**Estimated Time:** 1 day

#### 2.3 API Integration

**Files:**
- `src/aieval/api/app.py` - Add `/chat` endpoint
- `src/aieval/api/models.py` - Add chat models

**Tasks:**
- [ ] Add `ChatRequest` model (message, context, config)
- [ ] Add `ChatResponse` model (message, session_id)
- [ ] Add `POST /chat` endpoint
- [ ] Support session management (optional)
- [ ] Integration tests

**Estimated Time:** 1 day

#### 2.4 Documentation Updates

**Files:**
- `docs/skills.md` - Document skills system
- `docs/extensibility.md` - Comprehensive extensibility guide
- `examples/custom-tool.py` - Example custom tool
- `examples/custom-skill.py` - Example custom skill

**Tasks:**
- [ ] Document skills system
- [ ] Create extensibility guide
- [ ] Add example implementations
- [ ] Update architecture docs

**Estimated Time:** 1 day

### Phase 2 Summary

**Total Estimated Time:** 5-6 days  
**Deliverables:**
- ✅ Skills system for reusable workflows
- ✅ Entry point discovery for custom components
- ✅ API endpoint for conversational interface
- ✅ Comprehensive documentation

---

## Phase 3: Advanced Features (Future)

### Components (Deferred)

1. **Subagents**: Parallel execution with context isolation
2. **Context Compaction**: Automatic conversation summarization
3. **Custom Agents**: Support for user-defined agents
4. **Plugin Directory**: Scan `~/.aieval/plugins/` for components
5. **Session Persistence**: Store conversation history

**Note:** These features will be added based on user feedback and needs.

---

## File Structure

```
src/aieval/
├── agents/
│   ├── base.py                    # Update: add tool/skill registration
│   ├── conversational.py          # NEW: Main conversational agent
│   ├── tools/                     # NEW: Tools system
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dataset_tools.py
│   │   ├── scorer_tools.py
│   │   ├── eval_tools.py
│   │   ├── comparison_tools.py
│   │   └── registry.py
│   ├── skills/                     # NEW: Skills system (Phase 2)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── evaluation_skill.py
│   │   ├── baseline_comparison_skill.py
│   │   ├── multi_model_evaluation_skill.py
│   │   └── registry.py
│   └── loader.py                   # NEW: Component loader (Phase 2)
├── llm/                            # NEW: LLM infrastructure
│   ├── __init__.py
│   ├── client.py
│   └── config.py
├── cli/
│   └── main.py                     # Update: add chat command
└── api/
    ├── app.py                      # Update: add /chat endpoint (Phase 2)
    └── models.py                   # Update: add chat models (Phase 2)

docs/
├── conversational-agent.md         # NEW: Conversational agent guide
├── tools.md                        # NEW: Tools system guide
├── skills.md                       # NEW: Skills system guide (Phase 2)
└── extensibility.md                # NEW: Extensibility guide (Phase 2)

examples/
├── custom-tool.py                  # NEW: Custom tool example (Phase 2)
└── custom-skill.py                 # NEW: Custom skill example (Phase 2)
```

---

## Testing Strategy

### Unit Tests

- [ ] Tool execution tests
- [ ] Tool registry tests
- [ ] ConversationalAgent tests (mocked LLM)
- [ ] Skill execution tests (Phase 2)
- [ ] Component loader tests (Phase 2)

### Integration Tests

- [ ] End-to-end conversational flow
- [ ] CLI chat command
- [ ] API chat endpoint (Phase 2)
- [ ] Custom tool registration and usage
- [ ] Custom skill registration and usage (Phase 2)

### E2E Tests

- [ ] Complete evaluation via conversational interface
- [ ] Run comparison via conversational interface
- [ ] Baseline management via conversational interface

---

## Dependencies

### New Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    # ... existing dependencies ...
    "litellm>=1.0.0",  # NEW: Unified LLM client
]
```

### Optional Dependencies

No new optional dependencies required.

---

## Migration Path

### Breaking Changes Allowed

We can refactor existing interfaces to use the conversational agent internally, which may introduce breaking changes.

### For Users

1. **Breaking changes possible**: CLI/API/SDK interfaces may change
2. **Migration guide**: Will be provided for any breaking changes
3. **Version bump**: Breaking changes will be reflected in version number

### For Developers

1. **Refactoring allowed**: Can simplify existing interfaces by using conversational agent
2. **New APIs**: Conversational agent APIs are the foundation
3. **Extensibility**: Follow existing patterns (like custom Scorers/Adapters)

### Potential Refactorings

**CLI:**
- Refactor CLI commands to use `ConversationalAgent` internally
- Simplifies CLI code
- Ensures consistency

**API:**
- Refactor API endpoints to use `ConversationalAgent` internally
- Unified interface layer
- May change request/response formats

**SDK:**
- Refactor SDK methods to wrap conversational agent
- Consistent behavior
- May change method signatures

---

## Success Criteria

### Phase 1 (MVP)

**Required (Tools Foundation):**
- [ ] CLI can run evaluations using tools directly
- [ ] SDK can run evaluations using tools directly
- [ ] Response time <1 second for CLI/SDK (no LLM overhead)
- [ ] Tools system is extensible (users can add custom tools)

**Optional (Conversational Enhancement):**
- [ ] Users can run evaluations via natural language (if conversational used)
- [ ] Users can compare runs via natural language (if conversational used)
- [ ] Users can set baselines via natural language (if conversational used)
- [ ] Response time <5 seconds for simple queries (if conversational used)
- [ ] Intent understanding accuracy >90% (if conversational used)

### Phase 2 (Enhanced)

- [ ] Users can create custom tools
- [ ] Users can create custom skills
- [ ] Auto-discovery works via entry points
- [ ] API endpoint functional

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM costs | Medium | Track usage, use efficient models, cache responses |
| LLM latency | Medium | Use fast models, async execution, timeout handling |
| Complexity | Low | Phased approach, start minimal |
| User confusion | Medium | Clear documentation, migration guide, examples |

---

## Open Questions

1. **Session Management**: Should conversations persist?
   - **Decision**: Start without persistence, add if needed

2. **Error Handling**: How to handle ambiguous requests?
   - **Decision**: Ask clarifying questions via LLM

3. **Tool Execution**: Sync or async?
   - **Decision**: Async for better performance

---

## Next Steps

1. **Team Review**: Review architecture document and implementation plan
2. **Approval**: Get team approval for Phase 1
3. **Implementation**: Start with Phase 1 (MVP)
4. **Iteration**: Gather feedback and iterate
5. **Phase 2**: Proceed to Phase 2 if needed

---

## References

- [Architecture Document](./conversational-agent-architecture.md)
- [AGENTS.md](../AGENTS.md)
- [Architecture Docs](../docs/architecture.md)
- [Key Learnings Plan](./key_learnings_from_claude_cursor_and_openai_b1384647.plan.md)
