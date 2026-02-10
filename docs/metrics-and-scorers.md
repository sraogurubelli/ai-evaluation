# Metrics and Scorers

Scorers evaluate AI outputs and produce scores (e.g. 0.0–1.0).

## Terminology

- **ml-infra/evals:** "metrics" (e.g. `deep_diff_v3`).
- **aieval:** "scorers" (e.g. `DeepDiffScorer(version="v3")`). Same concept.

## Built-in scorers

- **Deterministic:** Exact match, contains, regex (fast, no external calls).
- **DeepDiff** (v1, v2, v3): Compare YAML/JSON; v3 strictest.
- **Schema validation:** Validate output against schema.
- **LLM-as-judge:** Rubric-based evaluation (optional `.[llm]`).
- **Entity-specific:** Dashboard quality, KG quality.

## Usage

```python
from aieval import DeepDiffScorer

scorer = DeepDiffScorer(name="deep_diff", eval_id="deep_diff.v1", version="v3")
score = scorer.score(generated=yaml_out, expected=expected_yaml, metadata={})
# score.value, score.comment, score.metadata
```

Use in `Experiment(scorers=[...])` or SDK runner. Custom scorers: implement `Scorer` interface (see `aieval.scorers.base`).

---

## Deterministic Scorers

Deterministic scorers provide fast, reliable evaluation without external API calls. They return numeric scores (0.0-1.0) and are ideal for simple checks, CI/CD pipelines, and large evaluation runs.

### ExactMatchScorer

Checks for exact string equality after stripping whitespace.

**Returns:** `1.0` if exact match, `0.0` otherwise.

**Configuration:**

```yaml
scorers:
  - type: exact_match
    name: exact_match
    expected_field: "exact"  # Key to look for in expected dict
```

**Expected formats:**
- Dict: `{"exact": "value"}` or `{"value": "value"}`
- String: `"value"`

**Python usage:**

```python
from aieval.scorers import ExactMatchScorer

scorer = ExactMatchScorer(
    name="exact_match",
    eval_id="exact_match.v1",
    expected_field="exact"
)

score = scorer.score(
    generated="hello world",
    expected={"exact": "hello world"},
    metadata={}
)
# score.value = 1.0
```

**Use cases:**
- Validating identifiers, IDs, codes
- Checking exact numeric or boolean outputs
- Ensuring specific command outputs

---

### ContainsScorer

Checks if output contains expected substring(s).

**Returns:** `1.0` if all required substrings found, `0.0` if none found, or ratio (0.0-1.0) if `require_all=False`.

**Configuration:**

```yaml
scorers:
  - type: contains
    name: contains_keywords
    case_sensitive: false  # Default: false
    require_all: true      # Default: true (all must be present)
```

**Expected formats:**
- Dict: `{"contains": "keyword"}` or `{"contains": ["key1", "key2"]}`
- String: `"keyword"`
- List: `["key1", "key2"]`

**Python usage:**

```python
from aieval.scorers import ContainsScorer

scorer = ContainsScorer(
    name="keywords",
    eval_id="contains.v1",
    case_sensitive=False,
    require_all=True
)

score = scorer.score(
    generated="Deploy pipeline to production with CD",
    expected={"contains": ["pipeline", "production", "CD"]},
    metadata={}
)
# score.value = 1.0 (all 3 keywords found)
```

**Use cases:**
- Keyword presence validation
- Multi-term requirement checking
- Partial content verification

**Modes:**
- `require_all=True`: All substrings must be present (binary pass/fail)
- `require_all=False`: Returns ratio of found substrings (partial credit)

---

### RegexMatchScorer

Checks if output matches expected regex pattern(s).

**Returns:** `1.0` if all required patterns match, `0.0` if none match, or ratio (0.0-1.0) if `require_all=False`.

**Configuration:**

```yaml
scorers:
  - type: regex
    name: regex_format
    require_all: true  # Default: true (all patterns must match)
```

**Expected formats:**
- Dict: `{"regex": "pattern"}` or `{"regex": ["p1", "p2"]}`
- String: `"pattern"`
- List: `["p1", "p2"]`

**Python usage:**

```python
from aieval.scorers import RegexMatchScorer

scorer = RegexMatchScorer(
    name="version_check",
    eval_id="regex.v1",
    require_all=True
)

score = scorer.score(
    generated="Release v1.2.3-beta",
    expected={"regex": r"v\d+\.\d+\.\d+(-\w+)?"},
    metadata={}
)
# score.value = 1.0 (pattern matches)
```

**Use cases:**
- Format validation (emails, UUIDs, versions, phone numbers)
- Pattern-based matching (dates, codes)
- Structured output verification

**Modes:**
- `require_all=True`: All patterns must match (binary pass/fail)
- `require_all=False`: Returns ratio of matched patterns (partial credit)

**Sample matches:** Metadata includes up to 3 sample matches for each pattern to help debug.

---

## When to Use Which Scorer

| Scorer | Use When | Performance | Accuracy |
|--------|----------|-------------|----------|
| **ExactMatch** | Need exact equality, validating IDs/codes | < 1ms | Binary (perfect or fail) |
| **Contains** | Need keyword presence, partial matching | < 5ms | Binary or ratio |
| **Regex** | Need format/pattern validation | < 10ms | Binary or ratio |
| **DeepDiff** | Need structural YAML/JSON comparison | ~50ms | Graduated (0.0-1.0) |
| **LLM Judge** | Need semantic/subjective evaluation | ~2s | Graduated (0.0-1.0) |

**Best practices:**
- Start with deterministic scorers for simple checks
- Use DeepDiff for complex structural comparison
- Reserve LLM Judge for semantic/subjective evaluation
- Combine multiple scorers for comprehensive evaluation

---

## Comparison: Deterministic vs DeepDiff

For simple checks, deterministic scorers are faster and clearer:

**Before (using DeepDiff for simple check):**
```yaml
scorers:
  - type: deep_diff
    version: v1  # Overkill for simple equality
```

**After (using ExactMatch):**
```yaml
scorers:
  - type: exact_match  # Clear intent, 50x faster
```

**When to keep using DeepDiff:**
- Comparing complex nested structures
- Need partial match scoring (0.0-1.0 gradient)
- Entity-specific field exclusion (identifiers, optional fields)
- Need deep_distance metric for debugging
