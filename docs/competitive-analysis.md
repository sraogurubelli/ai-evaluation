# Competitive Analysis: AI Evaluation & Observability

**Vendors:** Anthropic, OpenAI, Langfuse, Braintrust  
**Focus:** How each approaches LLM/agent evaluation, observability, and developer tooling.  
**Last updated:** February 2025.

---

## 1. Executive summary

| Vendor      | Primary role        | Evaluation focus                    | Delivery / licensing   |
|------------|----------------------|-------------------------------------|------------------------|
| **Anthropic** | Model provider + safety research | Red-teaming, sabotage evals, Console eval tool | API + Console; no open evals framework |
| **OpenAI**   | Model provider       | Evals registry, benchmarks, dashboard evals | Open-source evals repo; simple-evals deprecation in 2025 |
| **Langfuse** | Observability + evals | Traces first; datasets, experiments, LLM-as-judge | **Open source (MIT)** + cloud |
| **Braintrust** | Eval + observability platform | Eval-first; iterate → eval → ship; CI/CD gates | **Proprietary SaaS** (free tier) |

**Takeaway for ai-evaluation:** Anthropic emphasizes *methodology* (red-teaming, transparency) and in-Console evaluation; OpenAI offers an open evals framework but is deprecating simple-evals; Langfuse and Braintrust are full-stack observability + evaluation, with Langfuse self-hostable and Braintrust managed and eval-centric.

---

## 2. Anthropic

### Role
- **Model provider** (Claude) and **safety/alignment research**.
- Evaluation is framed as **testing and reducing harms**, not only accuracy.

### Evaluation approach
- **Red teaming:** Adversarial testing to elicit harmful or unsafe behavior; results used to improve models and build safer systems.
- **Structured evals:** Clear categories (e.g. sabotage: human decision sabotage, code sabotage, sandbagging, undermining oversight). Research datasets (e.g. SHADE-Arena) decompose agentic behavior into components (suspicion modeling, attack selection, plan synthesis, execution, subtlety).
- **Transparency:** Public papers and summaries on red-teaming methods, scaling behaviors, and lessons learned. Collaboration with third-party evals (e.g. ARC, Stanford HELM).
- **Console Evaluation Tool:** In-product only. Requires variables (`{{variable}}`) in prompts; supports manual test cases, CSV import, and AI-generated test cases. Side-by-side prompt comparison, quality grading (1–5), prompt versioning. No public API or open-source eval framework for developers.

### Observability / tooling
- Claude API (usage, latency); Claude Code Analytics API; no general-purpose tracing product.
- Developer docs: “Test & evaluate” (define success, develop tests, eval tool, guardrails).

### Strengths
- Strong, published methodology; safety and red-teaming as first-class.
- Clear eval categories and reproducible research.
- Console eval tool is simple for prompt iteration.

### Gaps (for third-party use)
- No open-source eval framework; evals are Console-centric or research-only.
- No built-in observability/tracing product; teams use Langfuse/Braintrust/others.

---

## 3. OpenAI

### Role
- **Model provider** (GPT, etc.) and **platform** (API, dashboard, evals).

### Evaluation approach
- **Open-source evals repo** ([openai/evals](https://github.com/openai/evals)): Framework and registry of benchmarks; run via CLI or Dashboard. Python 3.9+, OpenAI API key, Git-LFS for data.
- **Benchmarks:** e.g. SimpleQA (short-form factuality, 4K+ questions). Dashboard supports pre-built and private evals.
- **Positioning:** Evals as a core practice for understanding how model versions affect use cases.
- **simple-evals:** Lightweight reference implementations; deprecation notice for new model updates (July 2025).

### Observability / tooling
- API usage and dashboard; no standalone tracing product. Ecosystem relies on Langfuse, Braintrust, LangSmith, etc.

### Strengths
- Widely used, community-driven evals registry.
- Integrated with OpenAI Dashboard and API.

### Gaps
- simple-evals deprecation creates migration need.
- Evals are benchmark/registry-oriented; less emphasis on safety/red-team methodology than Anthropic.
- No first-party observability.

---

## 4. Langfuse

### Role
- **LLM engineering platform:** observability first, then evaluation and experiments.

### Evaluation approach
- **Datasets & experiments:** Structured data model (datasets → experiment runs → scores). Offline eval workflows; model-based (LLM-as-judge) and custom evaluators.
- **Pre-built templates:** Hallucination, helpfulness, relevance, toxicity, correctness, context relevance, conciseness.
- **Scoring:** Numeric, boolean, categorical; custom prompts and variables.
- **User feedback & annotation:** Manual annotation queues and feedback collection.
- **Integration:** Evals sit on top of traces; same platform for production observability and evaluation.

### Observability
- Tracing (including RAG, agents), sessions, environments, token/cost tracking, multi-modality, metrics API, custom dashboards.

### Business model
- **Open source (MIT):** Self-hosted, full feature set (datasets, experiments, evals, prompts, observability).
- **Cloud:** Hobby (free), Core ($29/mo), Pro ($199/mo), Enterprise ($2,499/mo). Units-based pricing; self-host avoids per-unit cost.

### Strengths
- Single stack for trace + eval; good for teams that already use Langfuse for observability.
- Self-hosting and cost control; no vendor lock-in for core logic.

### Gaps
- Evaluation is “building blocks”; more setup and custom engineering than Braintrust’s turnkey evals.
- CI/CD and “production → eval” automation less emphasized than Braintrust.

---

## 5. Braintrust

### Role
- **Eval-centric platform:** “Iterate, eval, ship” with observability and deployment.

### Evaluation approach
- **Three pillars:** Dataset, task, scorers. Shared framework for systematic testing.
- **Autoevals:** LLM-as-judge, heuristics (e.g. Levenshtein), statistical (e.g. BLEU), RAG, embeddings, custom prompts.
- **Workflow:** Playgrounds for prompt tuning; batch testing; run evals on changes; compare models; deploy and monitor with quality alerts.
- **CI/CD:** GitHub Actions and deployment gates when quality metrics fail.
- **Collaboration:** Engineers (code), PMs (UI), shared review and debugging; Loop agent for prompt/scorer optimization.

### Observability
- Production trace collection; conversion of traces to eval cases; quality monitoring and alerts.

### Business model
- **Proprietary SaaS only.** Free tier (1M spans, 10K scores, 14-day retention); Pro ($249/mo); Enterprise (custom). Usage-based (traces, scores, retention).

### Strengths
- End-to-end: evals, production monitoring, and deployment gates in one product.
- Low-friction for teams that want managed infra and turnkey CI/CD.
- Strong positioning for “production teams” and “gold standard” evals.

### Gaps
- No open-source option; vendor lock-in.
- Self-hosting only at Enterprise level.

---

## 6. Comparison matrix

| Dimension            | Anthropic     | OpenAI        | Langfuse           | Braintrust        |
|---------------------|---------------|---------------|--------------------|-------------------|
| **Primary product** | Claude API + Console | API + evals   | Observability + evals | Eval + observability |
| **Eval methodology** | Red-team, safety, transparency | Benchmarks, registry | Datasets, experiments, LLM-judge | Dataset + task + scorers |
| **Open evals framework** | No (Console only) | Yes (evals repo) | N/A (platform) | No (SaaS) |
| **Open source**     | No            | Evals only    | **Yes (MIT)**     | No                |
| **Self-hostable**   | N/A           | Evals only    | **Yes**           | Enterprise only   |
| **Observability**   | Limited (API) | Limited       | **Full**          | **Full**          |
| **CI/CD / gates**   | No            | No            | Manual            | **Turnkey**       |
| **Safety/red-team** | **Strong**    | Moderate      | Templates         | Custom            |
| **Best for**        | Safety-focused evals, prompt iteration in Console | Benchmark-driven evals, OpenAI ecosystem | Cost control, self-host, trace+eval in one | Managed eval pipeline, deployment gates |

---

## 7. Implications for ai-evaluation (this project)

- **Anthropic-style methodology:** Adopt structured eval categories (e.g. capability, safety, robustness), document what is measured and limitations, and optionally add “eval philosophy” and red-team-inspired templates. No need to copy Console; align *principles* (transparency, categories, reproducibility).
- **OpenAI-style:** Our registry, datasets, and scorers are compatible with a benchmark/registry mindset. We could document compatibility with OpenAI evals format or add a thin adapter if useful.
- **Langfuse:** We already integrate (LangfuseSink, LangfuseAdapter, LangfuseTracingAdapter). We complement Langfuse: we run evals and experiments; Langfuse provides traces and optional cloud. BYOT (bring your own tracing) keeps us backend-agnostic.
- **Braintrust:** Different model (SaaS, no self-host). We can position ai-evaluation as the **open, self-hostable** alternative: same “dataset + task + scorers” idea, with optional observability via Langfuse/OTel and no vendor lock-in.

**Suggested positioning:** Open-source, self-hostable evaluation and experimentation platform that supports Anthropic-style methodology (structured evals, transparency), works with any model and adapter, and integrates with observability (e.g. Langfuse) via BYOT rather than replacing it.

---

## 8. References

- Anthropic: [Red teaming and model evaluations](https://www.anthropic.com/uk-government-internal-ai-safety-policy-response/red-teaming-and-model-evaluations), [Sabotage evaluations](https://www.anthropic.com/research/sabotage-evaluations), [Evaluation Tool](https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool).
- OpenAI: [Evals guide](https://platform.openai.com/docs/guides/evals), [openai/evals](https://github.com/openai/evals).
- Langfuse: [Evaluation overview](https://langfuse.com/docs/evaluation/overview), [Pricing](https://langfuse.com/pricing), [Self-host](https://langfuse.com/pricing-self-host).
- Braintrust: [Experiments](https://www.braintrust.dev/docs/core/experiments), [Scorers](https://www.braintrust.dev/docs/best-practices/scorers), [Pricing](https://braintrust.dev/pricing).
- Comparisons: [Langfuse alternatives (Braintrust)](https://www.braintrust.dev/articles/langfuse-alternatives-2026), [Braintrust vs Langfuse](https://www.braintrust.dev/articles/langfuse-vs-braintrust).
