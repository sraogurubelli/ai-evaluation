"""Autoevals-style scorers (inspired by Braintrust's autoevals library).

This module provides pre-built scorers similar to Braintrust's autoevals:
- LLM-as-judge scorers (Factuality, Helpfulness, etc.)
- Heuristic scorers (Levenshtein, etc.)
- Statistical scorers (BLEU, etc.)
- Embedding-based scorers
- RAG-specific scorers

These are designed to be drop-in replacements or alternatives to autoevals.
"""

import os
from typing import Any
from abc import ABC

from aieval.scorers.base import Scorer
from aieval.core.types import Score, DatasetItem


class LLMJudgeScorer(Scorer):
    """
    Base class for LLM-as-judge scorers (autoevals style).

    Similar to autoevals' LLM evaluators like Factuality, Helpfulness, etc.
    """

    def __init__(
        self,
        name: str,
        eval_id: str,
        prompt_template: str,
        model: str = "gpt-4o-mini",
        **kwargs: Any,
    ):
        """
        Initialize LLM judge scorer.

        Args:
            name: Score name
            eval_id: Evaluation ID
            prompt_template: Prompt template for LLM judge
            model: Model to use for judging
            **kwargs: Additional arguments
        """
        super().__init__(name=name, eval_id=eval_id)
        self.prompt_template = prompt_template
        self.model = model
        self.kwargs = kwargs

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt."""
        try:
            from openai import OpenAI

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except ImportError:
            raise ImportError(
                "openai package required for LLM judge scorers. Install with: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"LLM call failed: {e}")

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score using LLM judge.

        Args:
            generated: Generated output
            expected: Expected output
            metadata: Additional metadata (may contain 'input' for context)

        Returns:
            Score object
        """
        import asyncio

        # Build prompt from template
        prompt = self.prompt_template.format(
            output=str(generated),
            expected=str(expected) if expected else "N/A",
            input=metadata.get("input", {}).get("prompt", "")
            if isinstance(metadata.get("input"), dict)
            else str(metadata.get("input", "")),
        )

        # Call LLM (sync wrapper for async)
        try:
            response = asyncio.run(self._call_llm(prompt))
        except Exception as e:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"LLM judge error: {e}",
                metadata={"error": str(e)},
            )

        # Parse response (expects JSON with 'score' and 'reason')
        try:
            import json

            result = json.loads(response)
            score_value = float(result.get("score", 0.0))
            reason = result.get("reason", "No reason provided")
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback: try to extract score from text
            score_value = 0.0
            reason = response
            # Try to find a number between 0 and 1
            import re

            matches = re.findall(r"\b(0\.\d+|1\.0|1)\b", response)
            if matches:
                score_value = float(matches[0])

        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=reason,
            metadata={
                "judge_model": self.model,
                "judge_response": response,
            },
        )


class FactualityScorer(LLMJudgeScorer):
    """
    Factuality scorer (autoevals style).

    Checks if the output is factually correct based on the input/context.
    Similar to autoevals' Factuality evaluator.
    """

    FACTUALITY_PROMPT = """You are evaluating whether an AI assistant's response is factually correct based on the provided context.

Context: {input}

Output: {output}

Expected: {expected}

Evaluate the factuality of the output. Respond with a JSON object:
{{
    "score": <float between 0 and 1, where 1 is completely factual and 0 is completely incorrect>,
    "reason": "<brief explanation>"
}}"""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs: Any):
        """Initialize factuality scorer."""
        super().__init__(
            name="factuality",
            eval_id="factuality.v1",
            prompt_template=self.FACTUALITY_PROMPT,
            model=model,
            **kwargs,
        )


class HelpfulnessScorer(LLMJudgeScorer):
    """
    Helpfulness scorer (autoevals style).

    Evaluates how helpful the output is.
    Similar to autoevals' Helpfulness evaluator.
    """

    HELPFULNESS_PROMPT = """You are evaluating how helpful an AI assistant's response is.

Input: {input}

Output: {output}

Evaluate the helpfulness of the output. Respond with a JSON object:
{{
    "score": <float between 0 and 1, where 1 is extremely helpful and 0 is not helpful>,
    "reason": "<brief explanation>"
}}"""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs: Any):
        """Initialize helpfulness scorer."""
        super().__init__(
            name="helpfulness",
            eval_id="helpfulness.v1",
            prompt_template=self.HELPFULNESS_PROMPT,
            model=model,
            **kwargs,
        )


class LevenshteinScorer(Scorer):
    """
    Levenshtein distance scorer (autoevals style).

    Measures string similarity using Levenshtein distance.
    Similar to autoevals' Levenshtein evaluator.
    """

    def __init__(self, normalize: bool = True, **kwargs: Any):
        """
        Initialize Levenshtein scorer.

        Args:
            normalize: Whether to normalize score to 0-1 range
            **kwargs: Additional arguments
        """
        super().__init__(name="levenshtein", eval_id="levenshtein.v1")
        self.normalize = normalize

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """Score using Levenshtein distance."""
        try:
            from Levenshtein import distance
        except ImportError:
            try:
                from rapidfuzz.distance import Levenshtein

                distance = Levenshtein.distance
            except ImportError:
                raise ImportError(
                    "Levenshtein scorer requires 'python-Levenshtein' or 'rapidfuzz'. "
                    "Install with: pip install python-Levenshtein"
                )

        gen_str = str(generated)
        exp_str = str(expected) if expected else ""

        if not exp_str:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No expected value provided",
            )

        dist = distance(gen_str, exp_str)
        max_len = max(len(gen_str), len(exp_str))

        if self.normalize and max_len > 0:
            score_value = 1.0 - (dist / max_len)
        else:
            score_value = float(dist)

        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=f"Levenshtein distance: {dist} (max length: {max_len})",
            metadata={
                "distance": dist,
                "max_length": max_len,
                "normalized": self.normalize,
            },
        )


class BLUEScorer(Scorer):
    """
    BLEU score scorer (autoevals style).

    Measures n-gram overlap between generated and expected text.
    Similar to autoevals' BLEU evaluator.
    """

    def __init__(self, n: int = 4, **kwargs: Any):
        """
        Initialize BLEU scorer.

        Args:
            n: Maximum n-gram order (default: 4 for BLEU-4)
            **kwargs: Additional arguments
        """
        super().__init__(name="bleu", eval_id="bleu.v1")
        self.n = n

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """Score using BLEU."""
        try:
            from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        except ImportError:
            raise ImportError("BLEU scorer requires 'nltk'. Install with: pip install nltk")

        gen_str = str(generated)
        exp_str = str(expected) if expected else ""

        if not exp_str:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No expected value provided",
            )

        # Tokenize
        gen_tokens = gen_str.split()
        exp_tokens = exp_str.split()

        if not gen_tokens or not exp_tokens:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="Empty tokens",
            )

        # Calculate BLEU with smoothing
        smoothing = SmoothingFunction().method1
        bleu_score = sentence_bleu(
            [exp_tokens],
            gen_tokens,
            smoothing_function=smoothing,
        )

        return Score(
            name=self.name,
            value=float(bleu_score),
            eval_id=self.eval_id,
            comment=f"BLEU-{self.n} score",
            metadata={
                "n": self.n,
                "generated_tokens": len(gen_tokens),
                "expected_tokens": len(exp_tokens),
            },
        )


class EmbeddingSimilarityScorer(Scorer):
    """
    Embedding-based similarity scorer (autoevals style).

    Measures semantic similarity using embeddings.
    Similar to autoevals' embedding-based evaluators.
    """

    def __init__(self, model: str = "text-embedding-3-small", **kwargs: Any):
        """
        Initialize embedding similarity scorer.

        Args:
            model: Embedding model to use
            **kwargs: Additional arguments
        """
        super().__init__(name="embedding_similarity", eval_id="embedding_similarity.v1")
        self.model = model

    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """Score using embedding similarity."""
        try:
            from openai import OpenAI
            import numpy as np
        except ImportError:
            raise ImportError(
                "Embedding scorer requires 'openai' and 'numpy'. Install with: pip install openai numpy"
            )

        gen_str = str(generated)
        exp_str = str(expected) if expected else ""

        if not exp_str:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment="No expected value provided",
            )

        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Get embeddings
            gen_embedding = (
                client.embeddings.create(
                    model=self.model,
                    input=gen_str,
                )
                .data[0]
                .embedding
            )

            exp_embedding = (
                client.embeddings.create(
                    model=self.model,
                    input=exp_str,
                )
                .data[0]
                .embedding
            )

            # Calculate cosine similarity
            gen_vec = np.array(gen_embedding)
            exp_vec = np.array(exp_embedding)

            similarity = np.dot(gen_vec, exp_vec) / (
                np.linalg.norm(gen_vec) * np.linalg.norm(exp_vec)
            )

            return Score(
                name=self.name,
                value=float(similarity),
                eval_id=self.eval_id,
                comment=f"Embedding similarity using {self.model}",
                metadata={
                    "model": self.model,
                    "similarity": float(similarity),
                },
            )
        except Exception as e:
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Embedding error: {e}",
                metadata={"error": str(e)},
            )


class RAGRelevanceScorer(LLMJudgeScorer):
    """
    RAG relevance scorer (autoevals style).

    Evaluates if the output is relevant to the retrieved context.
    Similar to autoevals' RAG evaluators.
    """

    RAG_RELEVANCE_PROMPT = """You are evaluating whether an AI assistant's response is relevant to the retrieved context in a RAG (Retrieval-Augmented Generation) system.

Context: {input}

Output: {output}

Evaluate the relevance of the output to the context. Respond with a JSON object:
{{
    "score": <float between 0 and 1, where 1 is highly relevant and 0 is not relevant>,
    "reason": "<brief explanation>"
}}"""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs: Any):
        """Initialize RAG relevance scorer."""
        super().__init__(
            name="rag_relevance",
            eval_id="rag_relevance.v1",
            prompt_template=self.RAG_RELEVANCE_PROMPT,
            model=model,
            **kwargs,
        )
