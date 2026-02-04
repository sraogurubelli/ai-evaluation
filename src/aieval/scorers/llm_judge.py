"""LLM-as-judge scorer."""

import os
import json
import re
import asyncio
import logging
from typing import Any

from aieval.scorers.base import Scorer
from aieval.core.types import Score

logger = logging.getLogger(__name__)


class LLMJudgeScorer(Scorer):
    """Scorer that uses LLM to evaluate outputs."""
    
    def __init__(
        self,
        name: str = "llm_judge",
        eval_id: str = "llm_judge.v1",
        model: str = "gpt-4o-mini",
        rubric: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize LLM judge scorer.
        
        Args:
            name: Score name
            eval_id: Evaluation ID
            model: LLM model to use for judging (supports OpenAI and Anthropic models)
            rubric: Rubric/prompt for evaluation
            api_key: API key (if None, uses OPENAI_API_KEY or ANTHROPIC_API_KEY env var)
        """
        super().__init__(name, eval_id)
        self.model = model
        self.rubric = rubric or "Evaluate the quality of the response."
        self.api_key = api_key
        self.provider = self._determine_provider(model)
    
    def _determine_provider(self, model: str) -> str:
        """Determine provider from model name."""
        model_lower = model.lower()
        if "claude" in model_lower:
            return "anthropic"
        elif any(x in model_lower for x in ["gpt", "o1", "o3"]):
            return "openai"
        else:
            # Default to OpenAI
            return "openai"
    
    def _build_prompt(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> str:
        """Build evaluation prompt from rubric."""
        # Extract input context if available
        input_context = ""
        if "input" in metadata:
            if isinstance(metadata["input"], dict):
                input_context = metadata["input"].get("prompt", str(metadata["input"]))
            else:
                input_context = str(metadata["input"])
        
        # Format the prompt
        prompt = f"""You are an expert evaluator. {self.rubric}

"""
        
        if input_context:
            prompt += f"""Input/Context:
{input_context}

"""
        
        prompt += f"""Generated Output:
{str(generated)}

"""
        
        if expected:
            prompt += f"""Expected Output (for reference):
{str(expected)}

"""
        
        prompt += """Evaluate the generated output based on the rubric above. Respond with a JSON object in the following format:
{
    "score": <float between 0 and 1, where 1 is excellent and 0 is poor>,
    "reason": "<brief explanation of your evaluation>"
}"""
        
        return prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package required for LLM judge scorer. "
                "Install with: pip install openai"
            )
        
        api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set and no api_key provided")
        
        client = OpenAI(api_key=api_key)
        
        try:
            # Use structured output for better reliability
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that evaluates AI outputs. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},  # Force JSON output
                temperature=0.0,  # Deterministic scoring
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            return content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise RuntimeError(f"OpenAI API call failed: {e}") from e
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package required for Anthropic models. "
                "Install with: pip install anthropic"
            )
        
        api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set and no api_key provided")
        
        client = Anthropic(api_key=api_key)
        
        try:
            # Anthropic doesn't support JSON mode directly, but we can request it in the prompt
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.0,  # Deterministic scoring
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            
            # Extract text from response
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                if not content:
                    raise ValueError("Empty response from Anthropic")
                return content
            else:
                raise ValueError("No content in Anthropic response")
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise RuntimeError(f"Anthropic API call failed: {e}") from e
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API based on provider."""
        if self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _parse_response(self, response: str) -> tuple[float, str]:
        """
        Parse LLM response to extract score and reason.
        
        Returns:
            Tuple of (score, reason)
        """
        # Try to parse as JSON first
        try:
            # Clean up response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            result = json.loads(cleaned)
            score = float(result.get("score", 0.0))
            reason = result.get("reason", "No reason provided")
            
            # Clamp score to [0, 1]
            score = max(0.0, min(1.0, score))
            
            return score, reason
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse JSON response: {e}. Response: {response[:200]}")
            
            # Fallback: try to extract score from text
            # Look for numbers between 0 and 1
            score_patterns = [
                r'"score"\s*:\s*([0-9]*\.?[0-9]+)',  # JSON-like: "score": 0.85
                r'score["\']?\s*[:=]\s*([0-9]*\.?[0-9]+)',  # score: 0.85 or score=0.85
                r'\b(0\.\d+|1\.0|1)\b',  # Any float between 0 and 1
            ]
            
            score = 0.0
            reason = response[:200]  # Use first 200 chars as reason
            
            for pattern in score_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                if matches:
                    try:
                        score = float(matches[0])
                        score = max(0.0, min(1.0, score))
                        break
                    except ValueError:
                        continue
            
            return score, reason
    
    def score(
        self,
        generated: Any,
        expected: Any,
        metadata: dict[str, Any],
    ) -> Score:
        """
        Score using LLM-as-judge.
        
        Args:
            generated: Generated output to evaluate
            expected: Expected output (for reference, optional)
            metadata: Additional metadata (may contain 'input' for context)
        
        Returns:
            Score object with evaluation result
        """
        # Build prompt
        prompt = self._build_prompt(generated, expected, metadata)
        
        # Call LLM (sync wrapper for async)
        try:
            response = asyncio.run(self._call_llm(prompt))
        except ImportError as e:
            # Missing dependencies
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"LLM judge error: {e}. Install required package.",
                metadata={"error": str(e), "provider": self.provider},
            )
        except ValueError as e:
            # Missing API key
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"LLM judge error: {e}",
                metadata={"error": str(e), "provider": self.provider},
            )
        except Exception as e:
            # Other errors
            logger.error(f"LLM judge scoring failed: {e}", exc_info=True)
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"LLM judge error: {e}",
                metadata={"error": str(e), "provider": self.provider},
            )
        
        # Parse response
        try:
            score_value, reason = self._parse_response(response)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return Score(
                name=self.name,
                value=0.0,
                eval_id=self.eval_id,
                comment=f"Failed to parse LLM response: {e}",
                metadata={
                    "error": str(e),
                    "raw_response": response[:500],
                    "provider": self.provider,
                },
            )
        
        return Score(
            name=self.name,
            value=score_value,
            eval_id=self.eval_id,
            comment=reason,
            metadata={
                "judge_model": self.model,
                "judge_provider": self.provider,
                "rubric": self.rubric,
            },
        )
