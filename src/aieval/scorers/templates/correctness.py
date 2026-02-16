"""Correctness scorer template."""

from aieval.scorers.templates.base_template import LLMJudgeTemplateScorer


class CorrectnessScorer(LLMJudgeTemplateScorer):
    """Scorer for evaluating correctness of generated text."""

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        rubric = """Rate the generated text on a scale of 1-5 for correctness:
- 1: Completely incorrect - major factual errors or wrong information
- 2: Mostly incorrect - significant errors or inaccuracies
- 3: Partially correct - some correct information but with errors
- 4: Mostly correct - minor errors or inaccuracies
- 5: Completely correct - all information is accurate and correct

Return a score from 1-5."""

        super().__init__(
            name="correctness",
            eval_id="correctness.v1",
            rubric=rubric,
            model=model,
            api_key=api_key,
        )
