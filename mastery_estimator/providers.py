"""LLM provider adapters for Groq, Gemini, and OpenAI mastery evaluators."""

from __future__ import annotations

import json
import logging
import os
import time
from abc import abstractmethod
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from groq import Groq
from openai import OpenAI

from .base import BaseEvaluator, clamp, is_unknown_answer, low_mastery_result
from .models import ConceptEvaluationResult, ConceptRubric, EvaluationEvidence, EvaluationStrategy

logger = logging.getLogger(__name__)


def compute_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate the estimated USD cost of the LLM API call using static rate configurations."""
    model_lower = model.lower()
    provider_lower = provider.lower()
    
    # Defaults: (input_cost_per_million, output_cost_per_million) in USD
    rates = (0.0, 0.0)
    if "groq" in provider_lower:
        rates = (0.59, 0.79)
    elif "gemini" in provider_lower:
        if "flash" in model_lower:
            rates = (0.075, 0.30)
        else:
            rates = (7.00, 21.00)  # gemini-1.5-pro
    elif "openai" in provider_lower:
        if "mini" in model_lower:
            rates = (0.15, 0.60)   # gpt-4o-mini
        else:
            rates = (5.00, 15.00)  # gpt-4o
            
    input_cost = (prompt_tokens / 1_000_000.0) * rates[0]
    output_cost = (completion_tokens / 1_000_000.0) * rates[1]
    return input_cost + output_cost


class BaseLLMEvaluator(BaseEvaluator):
    """Base class for LLM-backed evaluators containing common prompting and parsing logic."""

    strategy = EvaluationStrategy.LLM

    def __init__(self, model_name: str, api_key: Optional[str] = None, temperature: float = 0.0) -> None:
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature

    @abstractmethod
    def _call_api(self, prompt: str) -> tuple[str, int, int, int]:
        """Perform the LLM API call.
        
        Returns:
            tuple of (response_text, prompt_tokens, completion_tokens, total_tokens)
        """
        pass

    def construct_prompt(
        self, concept: str, question: str, answer: str, rubric: ConceptRubric, context: Optional[str] = None
    ) -> str:
        """Construct the prompt for evaluation."""
        req_signals = rubric.required_signals or []
        opt_signals = rubric.optional_signals or []

        req_text = "\n".join([
            f"- {s.signal_id}: {s.description} (keywords: {', '.join(s.keywords)}) (weight: {s.weight})"
            for s in req_signals
        ])
        opt_text = "\n".join([
            f"- {s.signal_id}: {s.description} (keywords: {', '.join(s.keywords)}) (weight: {s.weight})"
            for s in opt_signals
        ])

        context_sec = ""
        if context:
            context_sec = f"\n--- CONTEXT & EXAMPLES ---\n{context}\n"

        prompt = f"""You are a senior AI technical interviewer evaluating a candidate's answer for mastery of the concept '{concept}'.
You must assess the answer against the rubric below and retrieve understanding signals.

--- CONCEPT ---
Concept: {concept}

--- QUESTION ---
{question}

--- CANDIDATE ANSWER ---
{answer}

--- RUBRIC ---
Reference Answer: {rubric.reference_answer}

Required Signals (candidate should demonstrate these):
{req_text}

Optional Signals (candidate might mention these):
{opt_text}
{context_sec}
--- EVALUATION CRITERIA ---
- Calculate a "mastery" score between 0.0 and 1.0. A score of 0.9 or 1.0 represents high mastery. A score below 0.5 represents weak mastery.
- Calculate a "confidence" score between 0.0 and 1.0 representing how clearly the candidate's answer maps to the signals.
- Identify "matched_signals": signals that the candidate successfully demonstrated.
- Identify "missing_signals": required signals that the candidate failed to demonstrate.
- List 1 to 5 sentences of technical "reasoning" for your assessment.

--- RESPONSE FORMAT ---
You MUST respond in valid JSON format matching this schema exactly:
{{
  "mastery": float,
  "confidence": float,
  "matched_signals": ["signal_id1", ...],
  "missing_signals": ["signal_id2", ...],
  "reasoning": ["Sentence 1", "Sentence 2", ...]
}}
Return ONLY valid JSON. Do not include markdown wraps or anything outside the JSON object."""
        return prompt

    def evaluate(
        self,
        concept: str,
        question: str,
        answer: str,
        rubric: ConceptRubric,
        context: Optional[str] = None,
    ) -> ConceptEvaluationResult:
        """Run LLM evaluation on candidate's response."""
        if is_unknown_answer(answer):
            return low_mastery_result(concept, self.strategy, rubric)

        prompt = self.construct_prompt(concept, question, answer, rubric, context)
        
        start_time = time.time()
        response_text, prompt_tokens, completion_tokens, total_tokens = self._call_api(prompt)
        latency = time.time() - start_time

        # Parse JSON output
        try:
            # Strip potential code fence outputs that LLMs sometimes generate
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse JSON response from provider: {response_text}. Error: {e}")
            raise ValueError(f"Invalid JSON returned from evaluator: {e}") from e

        mastery = clamp(float(parsed.get("mastery", 0.0)))
        confidence = clamp(float(parsed.get("confidence", 0.0)))
        
        # Ensure reasoning is a list of strings
        reasoning_raw = parsed.get("reasoning", ["Evaluator completed successfully."])
        if isinstance(reasoning_raw, str):
            reasoning = [reasoning_raw]
        elif isinstance(reasoning_raw, list):
            reasoning = [str(r) for r in reasoning_raw]
        else:
            reasoning = ["Evaluator completed successfully."]

        matched = parsed.get("matched_signals", [])
        missing = parsed.get("missing_signals", [])

        # Clean lists
        matched = [str(x) for x in matched] if isinstance(matched, list) else []
        missing = [str(x) for x in missing] if isinstance(missing, list) else []

        evidence = EvaluationEvidence(matched_signals=matched, missing_signals=missing)
        
        metadata = {
            "model": self.model_name,
            "latency_seconds": round(latency, 3),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(compute_cost(self.__class__.__name__, self.model_name, prompt_tokens, completion_tokens), 6),
            "raw_request": prompt,
            "raw_response": response_text
        }

        return ConceptEvaluationResult(
            concept=concept,
            mastery=mastery,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            strategy=self.strategy,
            metadata=metadata
        )


class GroqEvaluator(BaseLLMEvaluator):
    """Groq API evaluator implementation."""

    def __init__(self, model_name: str = "llama3-70b-8192", api_key: Optional[str] = None, temperature: float = 0.0) -> None:
        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY environment variable is missing.")
        super().__init__(model_name, key, temperature)
        self.client = Groq(api_key=self.api_key)

    def _call_api(self, prompt: str) -> tuple[str, int, int, int]:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a professional, objective technical interviewer and evaluator. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        return content, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens


class GeminiEvaluator(BaseLLMEvaluator):
    """Gemini API evaluator implementation."""

    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: Optional[str] = None, temperature: float = 0.0) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY environment variable is missing.")
        super().__init__(model_name, key, temperature)
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _call_api(self, prompt: str) -> tuple[str, int, int, int]:
        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=self.temperature
            )
        )
        content = response.text or ""
        
        # Access token counts from usage metadata
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", 0)
            completion_tokens = getattr(response.usage_metadata, "candidates_token_count", 0)
            total_tokens = getattr(response.usage_metadata, "total_token_count", 0)
            
        # If usage data is missing, estimate as fallback
        if total_tokens == 0:
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(content) // 4
            total_tokens = prompt_tokens + completion_tokens

        return content, prompt_tokens, completion_tokens, total_tokens


class OpenAIEvaluator(BaseLLMEvaluator):
    """OpenAI API evaluator implementation."""

    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None, temperature: float = 0.0) -> None:
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable is missing.")
        super().__init__(model_name, key, temperature)
        self.client = OpenAI(api_key=self.api_key)

    def _call_api(self, prompt: str) -> tuple[str, int, int, int]:
        completion = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a professional, objective technical interviewer and evaluator. Return only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        return content, usage.prompt_tokens, usage.completion_tokens, usage.total_tokens
