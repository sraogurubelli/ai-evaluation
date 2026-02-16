"""Relevance scorer template."""

from aieval.scorers.templates.base_template import LLMJudgeTemplateScorer


class RelevanceScorer(LLMJudgeTemplateScorer):
    """Scorer for evaluating relevance of generated text."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        rubric = """Rate the generated text on a scale of 1-5 for relevance:
- 1: Not relevant - completely off-topic or unrelated to the query
- 2: Slightly relevant - tangentially related but mostly off-topic
- 3: Moderately relevant - related but includes significant irrelevant content
- 4: Very relevant - mostly on-topic with minor irrelevant content
- 5: Highly relevant - directly and completely addresses the query

Return a score from 1-5."""

        super().__init__(
            name="relevance",
            eval_id="relevance.v1",
            rubric=rubric,
            model=model,
            api_key=api_key,
        )
