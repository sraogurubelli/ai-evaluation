# Learnings from Langfuse and Braintrust

**Status:** For team review  
**Date:** February 2025  
**Focus:** What we can learn from Langfuse and Braintrust's architectures, especially around agents, tools, skills, and evaluation patterns.

---

## Executive Summary

Langfuse and Braintrust are leading evaluation and observability platforms. This document extracts actionable learnings for `ai-evaluation`, focusing on:

1. **Architecture patterns** (agents, tools, skills)
2. **Evaluation methodologies**
3. **Integration approaches**
4. **User experience patterns**
5. **What to avoid** (based on their gaps)

---

## Langfuse Learnings

### Architecture: Observability-First

**Key Insight:** Langfuse uses **observability as the foundation**, with evaluation built on top.

**Architecture Pattern:**
```
Traces (Observability Foundation)
    ↓
Datasets (Built from Traces)
    ↓
Experiments (Run Evals on Datasets)
    ↓
Scores (Evaluation Results)
```

**What We Can Learn:**

1. **Traces as Foundation**
   - All LLM calls, tool calls, and agent steps are traced
   - Traces become the source of truth for evaluation
   - Evaluation can be run on production traces (online evaluation)

2. **Agent Representation**
   - Agents represented as graphs (multi-step workflows)
   - Each agent step is a trace span
   - Tool calls are traced as child spans
   - Enables visualization and debugging

3. **Three-Phase Evaluation**
   - **Phase 1**: Manual tracing (visual inspection during development)
   - **Phase 2**: Online evaluation (user feedback on production traces)
   - **Phase 3**: Offline evaluation (systematic dataset-based testing)

**Application to ai-evaluation:**

- **BYOT (Bring Your Own Tracing)**: We already do this! ✅
- **Trace → Dataset**: Could add ability to convert traces to datasets
- **Online Evaluation**: Could support evaluating production traces
- **Agent Visualization**: Could add agent step visualization

### Evaluation Framework

**Key Components:**
1. **Task**: The function being tested
2. **Data**: Test cases from managed datasets
3. **Evaluators**: Score output quality (LLM-as-judge, custom)

**What We Can Learn:**

1. **Managed Execution Framework**
   - Automatic tracing during evaluation
   - Error isolation (one failure doesn't stop entire eval)
   - Concurrent execution
   - Built-in retry logic

2. **Pre-built Templates**
   - Hallucination, helpfulness, relevance, toxicity, correctness
   - Users can customize but start with templates
   - Reduces setup time

3. **Scoring Flexibility**
   - Numeric, boolean, categorical scores
   - Custom prompts and variables
   - LLM-as-judge with configurable rubrics

**Application to ai-evaluation:**

- **Error Isolation**: Already have this in our runner ✅
- **Pre-built Scorers**: We have some (DeepDiff, LLM-judge), could add more templates
- **Scoring Types**: Support numeric, boolean, categorical (could enhance)

### Integration Approach

**Key Insight:** Langfuse integrates with multiple agent frameworks (LangGraph, OpenAI Agents SDK, PydanticAI) without requiring framework-specific code.

**What We Can Learn:**

1. **Framework Agnostic**
   - Works with any agent framework
   - Traces agent behavior, not framework internals
   - Unified evaluation across frameworks

2. **API-First Architecture**
   - Everything accessible via API
   - Easy to integrate into existing workflows
   - Programmatic control

**Application to ai-evaluation:**

- **Framework Agnostic**: We already position this way ✅
- **API-First**: We have FastAPI, could enhance API coverage
- **Integration**: Could add more framework-specific adapters

### Gaps (What to Avoid)

1. **Evaluation as "Building Blocks"**
   - More setup and custom engineering required
   - Less turnkey than Braintrust
   - **Learning**: Provide both building blocks AND turnkey solutions

2. **CI/CD Less Emphasized**
   - Manual CI/CD integration
   - Less automation than Braintrust
   - **Learning**: Make CI/CD integration easy (GitHub Actions, etc.)

---

## Braintrust Learnings

### Architecture: Eval-First

**Key Insight:** Braintrust uses **evaluation as the foundation**, with observability supporting evaluation.

**Architecture Pattern:**
```
Dataset + Task + Scorers (Eval Foundation)
    ↓
Experiments (Run Evals)
    ↓
Production Monitoring (Observability)
    ↓
CI/CD Gates (Deployment)
```

**What We Can Learn:**

1. **Three Pillars**
   - **Dataset**: Test cases with ground truth
   - **Task**: The function/agent being evaluated
   - **Scorers**: How to score outputs
   - Simple, clear mental model

2. **Eval-Centric Workflow**
   - "Iterate, eval, ship" philosophy
   - Evaluation drives development decisions
   - Production monitoring feeds back into evaluation

**Application to ai-evaluation:**

- **Three Pillars**: We already have this! (Dataset, Eval, Scorers) ✅
- **Eval-First**: Our architecture aligns with this
- **Workflow**: Could emphasize "eval-driven development" more

### Agent Architecture: Simple While Loop

**Key Insight:** Braintrust uses a **canonical agent pattern** - simple while loop that's debuggable and scalable.

**Pattern:**
```python
while not done:
    # 1. Call LLM
    response = llm.chat(messages)
    
    # 2. Collect tool calls
    tool_calls = response.tool_calls
    
    # 3. Execute tools
    tool_results = []
    for tool_call in tool_calls:
        result = execute_tool(tool_call)
        tool_results.append(result)
    
    # 4. Feed results back
    messages.append({"role": "tool", "content": tool_results})
    
    # 5. Check if done
    if response.finish_reason == "stop":
        done = True
```

**What We Can Learn:**

1. **Simple Pattern**
   - Easy to understand and debug
   - Scales to complex workflows
   - Clear hooks for logging and evaluation

2. **Tool Interface**
   - Tools defined with: name, description, parameters (schema), execute function
   - Standardized interface
   - Easy to extend

3. **Agent Options**
   - Model selection
   - System prompt
   - Max iterations
   - Available tools
   - Clear configuration

**Application to ai-evaluation:**

- **Simple Pattern**: Our tools system aligns with this ✅
- **Tool Interface**: We're implementing similar pattern
- **Agent Options**: Could add agent configuration to our tools

### Evaluation Methodology

**Key Insight:** Braintrust uses **two complementary approaches** - offline and online evaluation.

**Offline Evaluation:**
- Proactive testing before deployment
- Datasets with ground truth
- Assess incremental behavior (individual steps, tool calls)
- Isolate specific actions with deterministic scenarios
- Stub external dependencies

**Online Evaluation:**
- Continuous monitoring of real-time performance
- LLM-as-judge scorers (no ground truth needed)
- Feedback integration
- Adaptive sampling
- Real-time scoring for hallucinations and tool accuracy

**What We Can Learn:**

1. **Incremental Evaluation**
   - Evaluate individual agent steps
   - Evaluate tool call accuracy
   - Evaluate parameter correctness
   - Evaluate next step selection
   - Evaluate reasoning steps

2. **Critical Questions**
   - Did agent choose correct tools?
   - Were tool arguments built properly?
   - Did it select correct next step?
   - Were intermediate reasoning steps expected?
   - Does action plan make sense?

3. **Stubbing External Dependencies**
   - Mock external APIs during evaluation
   - Deterministic scenarios
   - Faster, cheaper evaluation

**Application to ai-evaluation:**

- **Incremental Evaluation**: Could add step-level evaluation
- **Critical Questions**: Could add agent-specific scorers
- **Stubbing**: Could add adapter mocking/stubbing

### Development Tools

**Key Insight:** Braintrust provides **playgrounds** for rapid prototyping.

**What We Can Learn:**

1. **Playgrounds**
   - No-code workspace for prompt/scorer testing
   - Side-by-side result comparison
   - Rapid iteration
   - Good for non-engineers (PMs, etc.)

2. **Collaboration**
   - Engineers write code
   - PMs use UI
   - Shared review and debugging
   - Loop agent for optimization

**Application to ai-evaluation:**

- **Playgrounds**: Could add Gradio UI for prompt/scorer testing
- **Collaboration**: Our Gradio UI could be enhanced for this

### CI/CD Integration

**Key Insight:** Braintrust provides **turnkey CI/CD** with deployment gates.

**What We Can Learn:**

1. **GitHub Actions Integration**
   - Pre-built GitHub Actions
   - Run evals on PRs
   - Block merge on regressions
   - Easy to adopt

2. **Deployment Gates**
   - Quality metrics thresholds
   - Automatic blocking on failures
   - Clear feedback to developers

**Application to ai-evaluation:**

- **CI/CD**: Could add GitHub Actions templates
- **Gates**: Could add regression detection and gating

### Gaps (What to Avoid)

1. **No Open Source**
   - Proprietary SaaS only
   - Vendor lock-in
   - **Learning**: Stay open source ✅

2. **No Self-Hosting**
   - Self-hosting only at Enterprise level
   - **Learning**: Keep self-hosting as primary ✅

---

## Comparative Analysis

### Langfuse vs Braintrust

| Aspect | Langfuse | Braintrust | Our Approach |
|--------|----------|------------|--------------|
| **Foundation** | Observability-first | Eval-first | Eval-first ✅ |
| **Open Source** | Yes (MIT) | No | Yes ✅ |
| **Self-Hostable** | Yes | Enterprise only | Yes ✅ |
| **Agent Pattern** | Graph representation | Simple while loop | Tools-based ✅ |
| **Evaluation** | Three-phase (manual → online → offline) | Two-phase (offline → online) | Offline (could add online) |
| **CI/CD** | Manual | Turnkey | Could improve |
| **Templates** | Pre-built evaluators | Autoevals library | Some scorers |
| **Collaboration** | API-first | Playgrounds + API | API + Gradio UI |

### What We're Already Doing Right

1. **Eval-First Architecture** ✅ (like Braintrust)
2. **Open Source** ✅ (like Langfuse)
3. **Self-Hostable** ✅ (like Langfuse)
4. **Framework Agnostic** ✅ (like both)
5. **BYOT (Bring Your Own Tracing)** ✅ (complements Langfuse)
6. **Three Pillars (Dataset + Task + Scorers)** ✅ (like Braintrust)

### What We Can Improve

1. **Online Evaluation** (evaluating production traces)
2. **CI/CD Integration** (GitHub Actions, deployment gates)
3. **Pre-built Templates** (more scorer templates)
4. **Playgrounds** (enhanced Gradio UI)
5. **Incremental Evaluation** (step-level, tool-call-level)
6. **Trace → Dataset Conversion** (from Langfuse)

---

## Specific Learnings for Our Architecture

### 1. Agent Evaluation Patterns

**From Braintrust:**
- Evaluate individual agent steps
- Evaluate tool call accuracy
- Evaluate parameter correctness
- Evaluate reasoning steps

**Application:**
```python
# Could add agent-specific scorers
class ToolCallAccuracyScorer(Scorer):
    """Score if agent chose correct tool."""
    def score(self, generated, expected, metadata):
        # Check if tool calls match expected
        ...

class ParameterCorrectnessScorer(Scorer):
    """Score if tool parameters are correct."""
    def score(self, generated, expected, metadata):
        # Check parameter values
        ...
```

### 2. Online Evaluation

**From Langfuse:**
- Evaluate production traces
- User feedback integration
- Continuous monitoring

**Application:**
```python
# Could add online evaluation support
class OnlineEvaluationAgent(BaseEvaluationAgent):
    """Evaluate production traces."""
    async def evaluate_trace(self, trace_id: str) -> Run:
        # Fetch trace from tracing system
        # Run scorers on trace
        # Return evaluation results
        ...
```

### 3. Trace → Dataset Conversion

**From Langfuse:**
- Convert production traces to evaluation datasets
- Use real production data for evaluation

**Application:**
```python
# Could add trace conversion
def traces_to_dataset(traces: list[Trace]) -> list[DatasetItem]:
    """Convert traces to dataset items."""
    items = []
    for trace in traces:
        items.append(DatasetItem(
            input=trace.input,
            expected=trace.output,  # or None for online eval
            metadata={"trace_id": trace.id}
        ))
    return items
```

### 4. CI/CD Integration

**From Braintrust:**
- GitHub Actions templates
- Deployment gates
- Regression detection

**Application:**
```yaml
# .github/workflows/eval.yml
name: Run Evaluations
on: [pull_request]
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: aieval/action@v1
        with:
          eval_name: my_eval
          baseline_run_id: ${{ github.base_ref }}
          fail_on_regression: true
```

### 5. Pre-built Templates

**From Langfuse:**
- Pre-built evaluator templates
- Customizable but start with templates

**Application:**
```python
# Could add more pre-built scorers
from aieval.scorers.templates import (
    HallucinationScorer,
    HelpfulnessScorer,
    RelevanceScorer,
    ToxicityScorer,
    CorrectnessScorer
)
```

### 6. Playgrounds / Enhanced UI

**From Braintrust:**
- No-code workspace
- Side-by-side comparison
- Rapid iteration

**Application:**
- Enhance Gradio UI with:
  - Prompt testing playground
  - Scorer testing playground
  - Side-by-side result comparison
  - Visual agent step debugging

---

## Architecture Patterns We Can Adopt

### 1. Agent Representation

**Langfuse:** Agents as graphs (multi-step workflows)
- Each step is a trace span
- Tool calls are child spans
- Enables visualization

**Braintrust:** Agents as simple while loops
- Canonical pattern
- Easy to debug
- Clear hooks for evaluation

**Our Approach:**
- Tools system provides clear hooks ✅
- Could add agent step visualization
- Could add trace span representation

### 2. Tool Interface

**Both:** Standardized tool interface
- Name, description, parameters (schema), execute function

**Our Approach:**
- We're implementing this ✅
- Aligns with both platforms

### 3. Evaluation Phases

**Langfuse:** Three-phase (manual → online → offline)
**Braintrust:** Two-phase (offline → online)

**Our Approach:**
- Currently: Offline evaluation ✅
- Could add: Online evaluation (production traces)
- Could add: Manual evaluation (annotation queues)

### 4. Integration Patterns

**Langfuse:** API-first, framework-agnostic
**Braintrust:** API + Playgrounds, framework-agnostic

**Our Approach:**
- API-first ✅
- Framework-agnostic ✅
- Could enhance: Gradio UI (playgrounds)

---

## Recommendations

### High Priority

1. **Add Online Evaluation**
   - Evaluate production traces
   - User feedback integration
   - Continuous monitoring

2. **Enhance CI/CD Integration**
   - GitHub Actions templates
   - Deployment gates
   - Regression detection

3. **Add More Pre-built Scorers**
   - Hallucination, helpfulness, relevance, toxicity
   - Agent-specific scorers (tool call accuracy, etc.)

### Medium Priority

4. **Trace → Dataset Conversion**
   - Convert production traces to datasets
   - Use real production data

5. **Enhance Gradio UI**
   - Playground for prompt/scorer testing
   - Side-by-side comparison
   - Visual agent debugging

6. **Incremental Evaluation**
   - Step-level evaluation
   - Tool-call-level evaluation
   - Parameter correctness

### Low Priority

7. **Manual Evaluation**
   - Annotation queues
   - User feedback collection
   - Review workflows

---

## What NOT to Do (Based on Their Gaps)

### Langfuse Gaps

1. **Don't make evaluation too "building blocks"**
   - Provide both building blocks AND turnkey solutions
   - Make common workflows easy

2. **Don't ignore CI/CD**
   - Make CI/CD integration easy
   - Provide templates and examples

### Braintrust Gaps

1. **Don't go proprietary**
   - Stay open source ✅
   - Keep self-hosting as primary ✅

2. **Don't require cloud**
   - Keep local-first ✅
   - Make cloud optional ✅

---

## Summary

### Key Learnings

1. **Architecture Patterns**
   - Simple agent patterns (while loop) are effective
   - Tools should have standardized interfaces ✅
   - Evaluation can be built on observability OR be the foundation ✅

2. **Evaluation Methodology**
   - Offline + Online evaluation complement each other
   - Incremental evaluation (step-level) is valuable
   - Pre-built templates reduce setup time

3. **Integration**
   - API-first enables programmatic control ✅
   - CI/CD integration is important
   - Framework-agnostic is key ✅

4. **User Experience**
   - Playgrounds help non-engineers
   - Side-by-side comparison aids debugging
   - Turnkey solutions reduce friction

### What We're Doing Right

- Eval-first architecture ✅
- Open source ✅
- Self-hostable ✅
- Framework agnostic ✅
- BYOT (bring your own tracing) ✅
- Tools system ✅

### What We Should Add

- Online evaluation (production traces)
- CI/CD integration (GitHub Actions)
- More pre-built scorers
- Enhanced UI (playgrounds)
- Incremental evaluation (step-level)
- Trace → dataset conversion

---

## References

- Langfuse: [Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
- Langfuse: [Evaluating Agents](https://langfuse.com/guides/cookbook/example_pydantic_ai_mcp_agent_evaluation)
- Braintrust: [Architecture](https://www.braintrust.dev/docs/reference/architecture)
- Braintrust: [Evaluating Agents](https://www.braintrust.dev/docs/best-practices/agents)
- Braintrust: [Agent While Loop](https://braintrust.dev/docs/cookbook/recipes/AgentWhileLoop)
- [Competitive Analysis](./competitive-analysis.md) - Our existing analysis
