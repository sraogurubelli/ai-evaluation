# Deterministic Scorers Example

This example demonstrates how to use the three deterministic scorers in the ai-evolution framework:

- **ExactMatchScorer** - Checks for exact string equality
- **ContainsScorer** - Checks for substring presence
- **RegexMatchScorer** - Checks for regex pattern matches

## Quick Start

Run the example evaluation:

```bash
aieval run examples/deterministic/config.yaml
```

## Dataset Format

The dataset (`dataset.jsonl`) shows how to structure expected values for each scorer:

```json
{
  "id": "001",
  "input": {"query": "What is 2+2?"},
  "expected": {
    "exact": "4",
    "contains": ["two", "plus"],
    "regex": "\\d+"
  }
}
```

## Scorer Configuration

### Exact Match

```yaml
scorers:
  - type: exact_match
    name: exact_match
    expected_field: "exact"  # Key in expected dict to look for
```

Checks if the output exactly equals the expected value. Comparison is done after stripping whitespace.

### Contains

```yaml
scorers:
  - type: contains
    name: contains_keywords
    case_sensitive: false
    require_all: true  # All substrings must be present
```

Checks if the output contains all (or any) expected substrings.

- `case_sensitive`: Whether matching is case-sensitive (default: false)
- `require_all`: If true, all substrings must be present. If false, returns ratio of found/total (default: true)

### Regex

```yaml
scorers:
  - type: regex
    name: regex_format
    require_all: true  # All patterns must match
```

Checks if the output matches regex pattern(s).

- `require_all`: If true, all patterns must match. If false, returns ratio of matched/total (default: true)

## Expected Value Formats

Each scorer supports multiple input formats for flexibility:

### Exact Match
- Dict: `{"exact": "value"}` or `{"value": "value"}`
- String: `"value"`

### Contains
- Dict: `{"contains": "keyword"}` or `{"contains": ["key1", "key2"]}`
- String: `"keyword"`
- List: `["key1", "key2"]`

### Regex
- Dict: `{"regex": "pattern"}` or `{"regex": ["p1", "p2"]}`
- String: `"pattern"`
- List: `["p1", "p2"]`

## Use Cases

### Exact Match
- Validating identifiers, IDs, or codes
- Checking specific numeric or boolean outputs
- Ensuring exact command outputs

### Contains
- Keyword presence validation
- Multi-term requirement checking
- Partial content verification

### Regex
- Format validation (emails, UUIDs, versions)
- Pattern-based matching (phone numbers, dates)
- Structured output verification

## Performance

Deterministic scorers are fast (< 10ms per score) and require no external API calls, making them ideal for:
- Large evaluation runs
- CI/CD pipeline integration
- Quick feedback loops
- Regression testing
