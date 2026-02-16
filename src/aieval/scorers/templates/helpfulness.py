"""Helpfulness scorer template."""

from aieval.scorers.templates.base_template import LLMJudgeTemplateScorer


class HelpfulnessScorer(LLMJudgeTemplateScorer):
    """Scorer for evaluating helpfulness of generated text."""
    
    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        rubric = """Rate the generated text on a scale of 1-5 for helpfulness:
- 1: Not helpful - doesn't address the question or provides irrelevant information
- 2: Slightly helpful - partially addresses the question but missing key information
- 3: Moderately helpful - addresses the question but could be more complete or clear
- 4: Very helpful - addresses the question well with good detail and clarity
- 5: Extremely helpful - comprehensive, clear, and directly addresses the question

Return a score from 1-5."""
        
        super().__init__(
            name="helpfulness",
            eval_id="helpfulness.v1",
            rubric=rubric,
            model=model,
            api_key=api_key,
        )
