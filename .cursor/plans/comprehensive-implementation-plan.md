# Comprehensive Implementation Plan: Tools, Agents, Skills & Online Evaluation

**Status:** For team review  
**Date:** February 2025  
**Related:** 
- [Architecture Document](./conversational-agent-architecture.plan.md)
- [Learnings from Langfuse/Braintrust](./learnings-from-langfuse-braintrust.md)
- [CLI Flow](./cli-flow.md)
- [SDK Flow](./sdk-flow.md)
- [Conversational Flow](./conversational-flow.md)

---

## Overview

This plan implements the complete architecture including tools system, conversational interface, and online evaluation capabilities. Implementation is phased to deliver value incrementally.

---

## Phase 0: Foundation - Tools System (Required)

### Goal

Build tools system foundation that all interfaces (CLI, SDK, API, Conversational) use. This is the foundation for everything else.

### Components

#### 0.1 Tool Base Interface

**Files:**
- `src/aieval/agents/tools/base.py` - Abstract Tool interface

**Tasks:**
- [ ] Define `Tool` base class with:
  - [ ] `name: str` - Tool identifier
  - [ ] `description: str` - Tool description (for LLM)
  - [ ] `parameters_schema: dict[str, Any]` - JSON schema for parameters
  - [ ] `async def execute(self, **kwargs) -> Any` - Execute method
- [ ] Add input validation
- [ ] Add error handling
- [ ] Unit tests

**Estimated Time:** 1 day

#### 0.2 Built-in Tools

**Files:**
- `src/aieval/agents/tools/dataset_tools.py` - Dataset tools
- `src/aieval/agents/tools/scorer_tools.py` - Scorer tools
- `src/aieval/agents/tools/eval_tools.py` - Eval tools
- `src/aieval/agents/tools/comparison_tools.py` - Comparison tools
- `src/aieval/agents/tools/baseline_tools.py` - Baseline tools

**Tasks:**
- [ ] `LoadDatasetTool` - Load dataset from JSONL/index CSV
- [ ] `CreateScorerTool` - Create scorer (DeepDiff, LLM-judge, etc.)
- [ ] `CreateEvalTool` - Create eval definition
- [ ] `EvalTool` - Run eval and get results
- [ ] `CompareEvalResultsTool` - Compare two eval results
- [ ] `SetBaselineTool` - Set baseline eval result for an eval
- [ ] `GetBaselineTool` - Get baseline eval result ID
- [ ] Unit tests for each tool

**Estimated Time:** 3-4 days

#### 0.3 Tool Registry

**Files:**
- `src/aieval/agents/tools/registry.py` - Tool registry

**Tasks:**
- [ ] Create `ToolRegistry` class:
  - [ ] `register(tool: Tool)` - Register a tool
  - [ ] `get(name: str) -> Tool | None` - Get tool by name
  - [ ] `list_all() -> list[Tool]` - List all registered tools
  - [ ] `get_schemas() -> list[dict]` - Get JSON schemas for LLM
- [ ] Singleton pattern (`get_tool_registry()`)
- [ ] Auto-register built-in tools on initialization
- [ ] Unit tests

**Estimated Time:** 1 day

#### 0.4 CLI/SDK Integration

**Files:**
- `src/aieval/cli/main.py` - Update CLI to use tools
- `src/aieval/sdk/__init__.py` - Add tool functions

**Tasks:**
- [ ] Update CLI `eval` command to use `EvalTool`
- [ ] Update CLI `compare` command to use `CompareEvalResultsTool`
- [ ] Add `eval_tool(tool_name, **kwargs)` to SDK
- [ ] Add convenience functions (`load_dataset`, `create_scorer`, `eval_evaluation`)
- [ ] Integration tests

**Estimated Time:** 2 days

### Phase 0 Summary

**Total Estimated Time:** 7-8 days

**Deliverables:**
- ✅ Tools system foundation
- ✅ 6-8 built-in tools
- ✅ Tool registry
- ✅ CLI/SDK use tools directly (no LLM)
- ✅ Fast, predictable performance (<1 second)

---

## Phase 1: Conversational Interface (Optional Enhancement)

### Goal

Add conversational interface for natural language interaction. Optional - CLI/SDK work without it.

### Components

#### 1.1 LLM Infrastructure

**Files:**
- `src/aieval/llm/client.py` - Unified LLM client (LiteLLM)
- `src/aieval/llm/config.py` - LLM configuration

**Tasks:**
- [ ] Install LiteLLM dependency (`pyproject.toml`) - Optional dependency
- [ ] Create `LLMClient` class wrapping LiteLLM
- [ ] Support Anthropic (primary) and OpenAI (fallback)
- [ ] Configuration via environment variables
- [ ] Error handling and retries
- [ ] Make LLM optional (graceful degradation)

**Dependencies:**
- `litellm>=1.0.0` (optional dependency)

**Estimated Time:** 1 day

#### 1.2 Conversational Agent

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
- [ ] Unit tests (mocked LLM)

**Estimated Time:** 2-3 days

#### 1.3 CLI Chat Command

**Files:**
- `src/aieval/cli/main.py` - Add `chat` command

**Tasks:**
- [ ] Add `chat` command to CLI
- [ ] Support single message mode: `aieval chat "run eval on dataset X"`
- [ ] Support interactive mode: `aieval chat` (REPL)
- [ ] Add `--model` option for LLM selection
- [ ] Handle exit commands (`exit`, `quit`)
- [ ] Integration tests

**Estimated Time:** 1 day

### Phase 1 Summary

**Total Estimated Time:** 4-5 days

**Deliverables:**
- ✅ Conversational interface via CLI
- ✅ Natural language understanding
- ✅ Tool execution via LLM function calling
- ✅ Natural language responses

**Note:** Optional - tools system works without this.

---

## Phase 2: Skills System & API Integration

### Goal

Add skills system for reusable workflows and API endpoint for conversational interface.

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
- [ ] Integrate skills into CLI/SDK/ConversationalAgent
- [ ] Unit tests

**Estimated Time:** 2-3 days

#### 2.2 Entry Point Discovery

**Files:**
- `src/aieval/agents/loader.py` - Component loader

**Tasks:**
- [ ] Implement entry point discovery for tools
- [ ] Implement entry point discovery for skills
- [ ] Auto-load components on initialization
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

### Phase 2 Summary

**Total Estimated Time:** 4-5 days

**Deliverables:**
- ✅ Skills system for reusable workflows
- ✅ Entry point discovery for custom components
- ✅ API endpoint for conversational interface

---

## Phase 3: Online Evaluation (High Priority)

### Goal

Add online evaluation capabilities - evaluate production traces, continuous monitoring, user feedback integration.

### Components

#### 3.1 Trace Evaluation Infrastructure

**Files:**
- `src/aieval/evaluation/online.py` - Online evaluation agent
- `src/aieval/evaluation/trace_evaluator.py` - Trace evaluator

**Tasks:**
- [ ] Create `OnlineEvaluationAgent` extending `BaseEvaluationAgent`
- [ ] Implement `evaluate_trace(trace_id: str) -> EvalResult`:
  - [ ] Fetch trace from tracing system (Langfuse/OTel)
  - [ ] Extract input/output from trace
  - [ ] Run scorers on trace
  - [ ] Return evaluation results
- [ ] Support multiple tracing systems (Langfuse, OTel)
- [ ] Error handling for missing traces
- [ ] Unit tests

**Estimated Time:** 3-4 days

#### 3.2 Trace → Dataset Conversion

**Files:**
- `src/aieval/datasets/trace_converter.py` - Trace to dataset converter

**Tasks:**
- [ ] Implement `traces_to_dataset(traces: list[Trace]) -> list[DatasetItem]`:
  - [ ] Extract input/output from traces
  - [ ] Handle optional expected values
  - [ ] Preserve trace metadata
- [ ] Support filtering (by date, environment, etc.)
- [ ] Support sampling (random, stratified)
- [ ] Unit tests

**Estimated Time:** 2 days

#### 3.3 Continuous Monitoring

**Files:**
- `src/aieval/monitoring/evaluator.py` - Continuous evaluator
- `src/aieval/monitoring/scheduler.py` - Evaluation scheduler

**Tasks:**
- [ ] Create `ContinuousEvaluator`:
  - [ ] Poll traces from tracing system
  - [ ] Evaluate traces automatically
  - [ ] Store results
  - [ ] Trigger alerts on regressions
- [ ] Support scheduled evaluation (cron-like)
- [ ] Support event-driven evaluation (on trace completion)
- [ ] Integration tests

**Estimated Time:** 3-4 days

#### 3.4 User Feedback Integration

**Files:**
- `src/aieval/feedback/collector.py` - Feedback collector
- `src/aieval/feedback/integrator.py` - Feedback integrator

**Tasks:**
- [ ] Create `FeedbackCollector`:
  - [ ] Collect user feedback (thumbs up/down, ratings)
  - [ ] Link feedback to traces/eval results
  - [ ] Store feedback
- [ ] Create `FeedbackIntegrator`:
  - [ ] Use feedback to improve evaluation
  - [ ] Weight scores by feedback
  - [ ] Learn from feedback patterns
- [ ] API endpoints for feedback collection
- [ ] Unit tests

**Estimated Time:** 2-3 days

#### 3.5 Online Evaluation Tools

**Files:**
- `src/aieval/agents/tools/online_tools.py` - Online evaluation tools

**Tasks:**
- [ ] `EvaluateTraceTool` - Evaluate a single trace
- [ ] `EvaluateTracesTool` - Evaluate multiple traces
- [ ] `ConvertTracesToDatasetTool` - Convert traces to dataset
- [ ] `MonitorTracesTool` - Set up continuous monitoring
- [ ] `CollectFeedbackTool` - Collect user feedback
- [ ] Unit tests

**Estimated Time:** 2 days

#### 3.6 CLI/SDK Integration

**Files:**
- `src/aieval/cli/main.py` - Add online eval commands
- `src/aieval/sdk/__init__.py` - Add online eval functions

**Tasks:**
- [ ] Add `aieval evaluate-trace --trace-id <id>` command
- [ ] Add `aieval evaluate-traces --filter <filter>` command
- [ ] Add `aieval convert-traces --output <path>` command
- [ ] Add `aieval monitor --eval-id <id>` command
- [ ] Add SDK functions (`evaluate_trace`, `evaluate_traces`, etc.)
- [ ] Integration tests

**Estimated Time:** 2 days

### Phase 3 Summary

**Total Estimated Time:** 14-17 days

**Deliverables:**
- ✅ Online evaluation (production traces)
- ✅ Trace → dataset conversion
- ✅ Continuous monitoring
- ✅ User feedback integration
- ✅ CLI/SDK support for online evaluation

---

## Phase 4: CI/CD Integration & Pre-built Templates

### Goal

Add CI/CD integration (GitHub Actions, deployment gates) and more pre-built scorer templates.

### Components

#### 4.1 GitHub Actions Integration

**Files:**
- `.github/workflows/eval.yml` - GitHub Actions template
- `src/aieval/ci/github_action.py` - GitHub Actions helper

**Tasks:**
- [ ] Create GitHub Actions template:
  - [ ] Run evals on PRs
  - [ ] Compare with baseline
  - [ ] Block merge on regressions
  - [ ] Post results as PR comments
- [ ] Create `GitHubActionHelper`:
  - [ ] Detect PR context
  - [ ] Get baseline eval result
  - [ ] Compare eval results
  - [ ] Post results
- [ ] Documentation and examples
- [ ] Integration tests

**Estimated Time:** 3-4 days

#### 4.2 Deployment Gates

**Files:**
- `src/aieval/ci/gates.py` - Deployment gate logic

**Tasks:**
- [ ] Create `DeploymentGate` class:
  - [ ] Check quality thresholds
  - [ ] Detect regressions
  - [ ] Block deployment on failures
  - [ ] Generate gate reports
- [ ] Support configurable thresholds
- [ ] Support multiple gate types (score threshold, regression count, etc.)
- [ ] Unit tests

**Estimated Time:** 2 days

#### 4.3 Pre-built Scorer Templates

**Files:**
- `src/aieval/scorers/templates/` - Pre-built scorer templates
  - `hallucination.py` - Hallucination scorer
  - `helpfulness.py` - Helpfulness scorer
  - `relevance.py` - Relevance scorer
  - `toxicity.py` - Toxicity scorer
  - `correctness.py` - Correctness scorer

**Tasks:**
- [ ] Implement 5+ pre-built scorer templates
- [ ] Each scorer:
  - [ ] Uses LLM-as-judge
  - [ ] Has configurable rubric
  - [ ] Returns numeric score
- [ ] Documentation and examples
- [ ] Unit tests

**Estimated Time:** 3-4 days

#### 4.4 Agent-Specific Scorers

**Files:**
- `src/aieval/scorers/agent/` - Agent-specific scorers
  - `tool_call_accuracy.py` - Tool call accuracy
  - `parameter_correctness.py` - Parameter correctness
  - `step_selection.py` - Step selection correctness

**Tasks:**
- [ ] Implement agent-specific scorers:
  - [ ] `ToolCallAccuracyScorer` - Did agent choose correct tool?
  - [ ] `ParameterCorrectnessScorer` - Were tool parameters correct?
  - [ ] `StepSelectionScorer` - Did agent select correct next step?
- [ ] Support agent trace format
- [ ] Unit tests

**Estimated Time:** 2-3 days

### Phase 4 Summary

**Total Estimated Time:** 10-13 days

**Deliverables:**
- ✅ GitHub Actions integration
- ✅ Deployment gates
- ✅ Pre-built scorer templates
- ✅ Agent-specific scorers

---

## Phase 5: Enhanced UI & Incremental Evaluation

### Goal

Enhance Gradio UI with playgrounds and add incremental evaluation (step-level, tool-call-level).

### Components

#### 5.1 Enhanced Gradio UI

**Files:**
- `src/aieval/ui/gradio_app.py` - Enhanced UI
- `src/aieval/ui/playground.py` - Playground components

**Tasks:**
- [ ] Add prompt testing playground:
  - [ ] Test prompts with different models
  - [ ] Side-by-side comparison
  - [ ] Score outputs
- [ ] Add scorer testing playground:
  - [ ] Test scorers on sample outputs
  - [ ] Visualize scores
  - [ ] Tune scorer parameters
- [ ] Add agent debugging visualization:
  - [ ] Show agent steps
  - [ ] Show tool calls
  - [ ] Show reasoning
- [ ] Integration tests

**Estimated Time:** 4-5 days

#### 5.2 Incremental Evaluation

**Files:**
- `src/aieval/evaluation/incremental.py` - Incremental evaluator
- `src/aieval/scorers/agent/step_scorer.py` - Step-level scorer

**Tasks:**
- [ ] Create `IncrementalEvaluator`:
  - [ ] Evaluate individual agent steps
  - [ ] Evaluate tool calls
  - [ ] Evaluate parameter correctness
  - [ ] Evaluate reasoning steps
- [ ] Support agent trace format
- [ ] Generate step-level reports
- [ ] Unit tests

**Estimated Time:** 3-4 days

#### 5.3 Agent Trace Support

**Files:**
- `src/aieval/tracing/agent_trace.py` - Agent trace format
- `src/aieval/tracing/parser.py` - Trace parser

**Tasks:**
- [ ] Define agent trace format:
  - [ ] Steps (LLM calls, tool calls, reasoning)
  - [ ] Tool call details (name, parameters, results)
  - [ ] Step metadata (timestamp, cost, tokens)
- [ ] Create trace parser for common formats
- [ ] Support LangGraph, OpenAI Agents SDK, PydanticAI formats
- [ ] Unit tests

**Estimated Time:** 2-3 days

### Phase 5 Summary

**Total Estimated Time:** 9-12 days

**Deliverables:**
- ✅ Enhanced Gradio UI with playgrounds
- ✅ Incremental evaluation (step-level)
- ✅ Agent trace support

---

## Phase 6: Advanced Features (Future)

### Components (Deferred)

1. **Subagents**: Parallel execution with context isolation
2. **Context Compaction**: Automatic conversation summarization
3. **Custom Agents**: Support for user-defined agents
4. **Plugin Directory**: Scan `~/.aieval/plugins/` for components
5. **Session Persistence**: Store conversation history
6. **Manual Evaluation**: Annotation queues, review workflows

**Note:** These features will be added based on user feedback and needs.

---

## Implementation Timeline

### Phase 0: Foundation (Required)
**Timeline:** Weeks 1-2 (7-8 days)
**Priority:** Critical
**Dependencies:** None

### Phase 1: Conversational Interface (Optional)
**Timeline:** Weeks 2-3 (4-5 days)
**Priority:** Medium
**Dependencies:** Phase 0

### Phase 2: Skills & API (Optional)
**Timeline:** Weeks 3-4 (4-5 days)
**Priority:** Medium
**Dependencies:** Phase 0, Phase 1 (optional)

### Phase 3: Online Evaluation (High Priority)
**Timeline:** Weeks 4-6 (14-17 days)
**Priority:** High
**Dependencies:** Phase 0

### Phase 4: CI/CD & Templates (High Priority)
**Timeline:** Weeks 6-8 (10-13 days)
**Priority:** High
**Dependencies:** Phase 0, Phase 3

### Phase 5: Enhanced UI & Incremental (Medium Priority)
**Timeline:** Weeks 8-10 (9-12 days)
**Priority:** Medium
**Dependencies:** Phase 0, Phase 3

### Phase 6: Advanced Features (Future)
**Timeline:** TBD
**Priority:** Low
**Dependencies:** User feedback

---

## Total Estimated Timeline

**Minimum (Phase 0 only):** 7-8 days  
**Recommended (Phases 0-3):** 29-35 days (~6-7 weeks)  
**Full (Phases 0-5):** 48-60 days (~10-12 weeks)

---

## Success Criteria

### Phase 0 (Foundation)
- [ ] CLI can run evaluations using tools directly
- [ ] SDK can run evaluations using tools directly
- [ ] Response time <1 second for CLI/SDK (no LLM overhead)
- [ ] Tools system is extensible (users can add custom tools)

### Phase 1 (Conversational)
- [ ] Users can run evaluations via natural language
- [ ] Intent understanding accuracy >90%
- [ ] Response time <5 seconds for simple queries

### Phase 2 (Skills & API)
- [ ] Users can create custom skills
- [ ] Auto-discovery works via entry points
- [ ] API endpoint functional

### Phase 3 (Online Evaluation)
- [ ] Users can evaluate production traces
- [ ] Trace → dataset conversion works
- [ ] Continuous monitoring functional
- [ ] User feedback integration works

### Phase 4 (CI/CD & Templates)
- [ ] GitHub Actions integration works
- [ ] Deployment gates block on regressions
- [ ] 5+ pre-built scorer templates available
- [ ] Agent-specific scorers functional

### Phase 5 (Enhanced UI & Incremental)
- [ ] Playgrounds functional in Gradio UI
- [ ] Incremental evaluation works (step-level)
- [ ] Agent trace support functional

---

## Dependencies

### New Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    # ... existing dependencies ...
]

[project.optional-dependencies]
conversational = [
    "litellm>=1.0.0",  # For conversational interface
]
```

### Existing Dependencies Used

- `langfuse>=2.57` - Already have (for tracing)
- `fastapi>=0.104.0` - Already have (for API)
- `gradio>=4.0` - Already have (for UI)

---

## File Structure

```
src/aieval/
├── agents/
│   ├── base.py                    # Update: add tool/skill registration
│   ├── conversational.py          # NEW: Conversational agent (Phase 1)
│   ├── tools/                     # NEW: Tools system (Phase 0)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── dataset_tools.py
│   │   ├── scorer_tools.py
│   │   ├── eval_tools.py
│   │   ├── comparison_tools.py
│   │   ├── baseline_tools.py
│   │   ├── online_tools.py        # NEW: Online eval tools (Phase 3)
│   │   └── registry.py
│   ├── skills/                     # NEW: Skills system (Phase 2)
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── evaluation_skill.py
│   │   ├── baseline_comparison_skill.py
│   │   ├── multi_model_evaluation_skill.py
│   │   └── registry.py
│   └── loader.py                   # NEW: Component loader (Phase 2)
├── llm/                            # NEW: LLM infrastructure (Phase 1)
│   ├── __init__.py
│   ├── client.py
│   └── config.py
├── evaluation/                     # NEW: Evaluation infrastructure
│   ├── __init__.py
│   ├── online.py                   # NEW: Online evaluation (Phase 3)
│   ├── trace_evaluator.py          # NEW: Trace evaluator (Phase 3)
│   └── incremental.py             # NEW: Incremental eval (Phase 5)
├── monitoring/                     # NEW: Continuous monitoring (Phase 3)
│   ├── __init__.py
│   ├── evaluator.py
│   └── scheduler.py
├── feedback/                       # NEW: User feedback (Phase 3)
│   ├── __init__.py
│   ├── collector.py
│   └── integrator.py
├── ci/                             # NEW: CI/CD integration (Phase 4)
│   ├── __init__.py
│   ├── github_action.py
│   └── gates.py
├── datasets/
│   └── trace_converter.py          # NEW: Trace converter (Phase 3)
├── scorers/
│   ├── templates/                   # NEW: Pre-built templates (Phase 4)
│   │   ├── __init__.py
│   │   ├── hallucination.py
│   │   ├── helpfulness.py
│   │   ├── relevance.py
│   │   ├── toxicity.py
│   │   └── correctness.py
│   └── agent/                      # NEW: Agent-specific (Phase 4)
│       ├── __init__.py
│       ├── tool_call_accuracy.py
│       ├── parameter_correctness.py
│       └── step_selection.py
├── tracing/
│   └── agent_trace.py               # NEW: Agent trace format (Phase 5)
├── cli/
│   └── main.py                     # Update: add chat, online eval commands
├── api/
│   ├── app.py                      # Update: add /chat, /feedback endpoints
│   └── models.py                   # Update: add chat, feedback models
└── ui/
    ├── gradio_app.py               # Update: enhance with playgrounds
    └── playground.py               # NEW: Playground components (Phase 5)

.github/workflows/
└── eval.yml                        # NEW: GitHub Actions template (Phase 4)

docs/
├── online-evaluation.md            # NEW: Online eval guide (Phase 3)
├── ci-cd-integration.md            # NEW: CI/CD guide (Phase 4)
└── incremental-evaluation.md       # NEW: Incremental eval guide (Phase 5)
```

---

## Testing Strategy

### Unit Tests

- [ ] Tool execution tests
- [ ] Tool registry tests
- [ ] ConversationalAgent tests (mocked LLM)
- [ ] Skill execution tests
- [ ] Online evaluation tests (mocked traces)
- [ ] Trace converter tests
- [ ] CI/CD gate tests
- [ ] Scorer template tests

### Integration Tests

- [ ] End-to-end CLI flow
- [ ] End-to-end SDK flow
- [ ] End-to-end conversational flow
- [ ] Online evaluation with real traces
- [ ] CI/CD integration (GitHub Actions)
- [ ] Custom tool/skill registration

### E2E Tests

- [ ] Complete evaluation via CLI
- [ ] Complete evaluation via SDK
- [ ] Complete evaluation via conversational interface
- [ ] Online evaluation workflow
- [ ] CI/CD deployment gate workflow

---

## Migration Path

### Breaking Changes Allowed

We can refactor existing interfaces to use tools system internally.

### For Users

1. **Phase 0**: No breaking changes (tools are additive)
2. **Phase 1-5**: May introduce breaking changes (documented in CHANGELOG)
3. **Migration guide**: Provided for any breaking changes
4. **Version bump**: Breaking changes reflected in version number

### For Developers

1. **Refactoring allowed**: Can simplify existing interfaces
2. **New APIs**: Tools system is foundation
3. **Extensibility**: Follow existing patterns

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scope Creep** | High | Phased approach, clear priorities |
| **LLM Costs** | Medium | Optional conversational, track usage |
| **LLM Latency** | Medium | Fast models, async execution |
| **Complexity** | Medium | Start minimal, add incrementally |
| **Online Eval Complexity** | Medium | Start with simple trace evaluation |
| **CI/CD Integration** | Low | Use existing GitHub Actions patterns |

---

## Open Questions

1. **Online Evaluation Scope**: How much trace data to evaluate?
   - **Decision**: Start with single trace evaluation, add batch later

2. **Feedback Integration**: How to weight feedback in scores?
   - **Decision**: Start with simple weighting, enhance later

3. **CI/CD Gates**: What thresholds to use?
   - **Decision**: Configurable thresholds, sensible defaults

---

## Next Steps

1. **Team Review**: Review this comprehensive plan
2. **Prioritization**: Decide which phases to implement first
3. **Approval**: Get team approval for Phase 0
4. **Implementation**: Start with Phase 0 (Foundation)
5. **Iteration**: Gather feedback and adjust plan

---

## References

- [Architecture Document](./conversational-agent-architecture.plan.md)
- [Learnings from Langfuse/Braintrust](./learnings-from-langfuse-braintrust.md)
- [CLI Flow](./cli-flow.md)
- [SDK Flow](./sdk-flow.md)
- [Conversational Flow](./conversational-flow.md)
- [Competitive Analysis](../docs/competitive-analysis.md)
