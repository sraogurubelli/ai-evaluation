"""Hallucination scorer template."""

from aieval.scorers.templates.base_template import LLMJudgeTemplateScorer


class HallucinationScorer(LLMJudgeTemplateScorer):
    """Scorer for detecting hallucinations in generated text."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        rubric = """Rate the generated text on a scale of 1-5 for hallucination:
- 1: Severe hallucination - contains false facts, made-up information, or contradicts source material
- 2: Major hallucination - significant false claims or unsupported assertions
- 3: Minor hallucination - some inaccuracies or unsupported details
- 4: Mostly accurate - minor issues or unclear sourcing
- 5: No hallucination - all claims are accurate and well-supported

Return a score from 1-5."""

        super().__init__(
            name="hallucination",
            eval_id="hallucination.v1",
            rubric=rubric,
            model=model,
            api_key=api_key,
        )
