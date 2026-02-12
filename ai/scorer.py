"""Simplified AI highlight scoring using GitHub Models API only."""

import os
import json
import re
import logging
import time
import random
import requests
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

# Score range constants
FINAL_SCORE_MAX = 100.0
COMPONENT_SCORE_MAX = 10.0

# Try importing Azure AI Inference SDK
try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    logger.warning("Azure AI Inference SDK not available, will try OpenAI SDK")

# Fallback to OpenAI SDK
try:
    from openai import OpenAI
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False


def validate_prompt(prompt: str, min_length: int = 10) -> tuple[bool, str | None]:
    """
    Validate a prompt before sending to LLM.
    
    Args:
        prompt: The prompt text to validate
        min_length: Minimum required prompt length
        
    Returns:
        Tuple of (is_valid: bool, error_message: str or None)
    """
    if not prompt:
        return False, "Prompt is empty"
    
    if not isinstance(prompt, str):
        return False, f"Prompt must be a string, got {type(prompt)}"
    
    # Strip whitespace for validation
    stripped = prompt.strip()
    
    if not stripped:
        return False, "Prompt contains only whitespace"
    
    if len(stripped) < min_length:
        return False, f"Prompt too short (min {min_length} chars, got {len(stripped)})"
    
    return True, None


def extract_json_safe(text: str) -> dict:
    """
    Safely extract and parse JSON from model response.
    
    Handles multiple response formats from different LLM providers:
    - Clean JSON: {"hook_score": 7, ...}
    - Markdown wrapped: ```json\n{...}\n```
    - Text with JSON: "Here's the score: {...}"
    - Newline prefixed: \n  {...}
    
    Args:
        text: Raw model response string
        
    Returns:
        Parsed dictionary with scores
        
    Raises:
        ValueError: If no valid JSON found
    """
    if not text or not isinstance(text, str):
        raise ValueError("Empty or invalid response")
    
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Try to find JSON object using brace counting for accuracy
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError(f"No JSON object found in response: {text[:200]}")
    
    # Count braces to find matching closing brace
    brace_count = 0
    end_idx = start_idx
    
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if brace_count != 0:
        # Fallback: try regex for simpler cases
        match = re.search(r'\{[^{}]*\}', text)
        if match:
            json_str = match.group()
        else:
            raise ValueError(f"Unbalanced braces in JSON: {text[start_idx:start_idx+200]}")
    else:
        json_str = text[start_idx:end_idx]
    
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\nExtracted: {json_str[:200]}")


def extract_score_safe(data: dict, field: str, default: float = 0.0) -> float:
    """
    Safely extract and validate a numeric score from AI response.
    
    Args:
        data: Parsed JSON response dictionary
        field: Field name to extract (e.g., 'hook_score')
        default: Default value if field missing or invalid
        
    Returns:
        Float score value, clamped to valid range [0, 10] for component scores
    """
    try:
        value = data.get(field, default)
        
        # Convert to float
        if isinstance(value, (int, float)):
            score = float(value)
        elif isinstance(value, str):
            # Try to parse string numbers
            score = float(value.strip())
        else:
            logger.warning(f"Invalid score type for '{field}': {type(value)}, using default {default}")
            return default
        
        # Clamp to valid range for component scores (0-10)
        # Note: final_score uses 0-100
        if field == 'final_score':
            return max(0.0, min(FINAL_SCORE_MAX, score))
        else:
            return max(0.0, min(COMPONENT_SCORE_MAX, score))
            
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to extract score for '{field}': {e}, using default {default}")
        return default


def load_prompt_template() -> str:
    """Load the scoring prompt template."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = f.read()
        return template
    except FileNotFoundError:
        logger.error(f"Prompt template not found at: {prompt_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to load prompt template: {e}")
        raise


def create_batch_prompt(segments: List[Dict], prompt_template: str) -> str:
    """
    Create a batch scoring prompt for multiple segments.
    
    Args:
        segments: List of segments to score together
        prompt_template: Base prompt template
        
    Returns:
        Formatted batch prompt string
    """
    # Build segment list for batch prompt
    segments_list = []
    for i, seg in enumerate(segments, 1):
        segments_list.append(f"\n\n━━━ SEGMENT {i} ━━━\n")
        segments_list.append(f"Text: {seg['text']}\n")
        segments_list.append(f"Duration: {seg['duration']:.1f}s\n")
    segments_text = ''.join(segments_list)
    
    batch_prompt = f"""Score the following {len(segments)} video segments using the criteria below.

{prompt_template}

{segments_text}

Return JSON with array of scores:
{{
  "segments": [
    {{
      "segment_id": 1,
      "hook_score": <0-10>,
      "retention_score": <0-10>,
      "emotion_score": <0-10>,
      "relatability_score": <0-10>,
      "completion_score": <0-10>,
      "platform_fit_score": <0-10>,
      "final_score": <0-100>,
      "verdict": "viral|maybe|skip",
      "key_strengths": ["strength 1", "strength 2"],
      "key_weaknesses": ["weakness 1"],
      "first_3_seconds": "exact quote from first 3 seconds",
      "primary_emotion": "neutral",
      "optimal_platform": "tiktok"
    }},
    ...
  ]
}}
"""
    return batch_prompt


def pre_filter_candidates(candidates: List[Dict], max_count: int = 20) -> List[Dict]:
    """
    Pre-filter candidates using heuristic scoring before AI analysis.
    
    Simple heuristics based on:
    - Position in video (earlier = better)
    - Duration (30-60s sweet spot for shorts)
    - Word count (substantive content)
    
    Args:
        candidates: List of candidate segments
        max_count: Maximum candidates to keep
        
    Returns:
        Filtered and sorted list of candidates
    """
    if len(candidates) <= max_count:
        return candidates
    
    # Score each candidate
    for candidate in candidates:
        score = 0.0
        
        # Position score (earlier segments often better)
        start_time = candidate.get('start', 0)
        if start_time < 300:  # First 5 minutes
            score += 2.0
        elif start_time < 600:  # First 10 minutes
            score += 1.0
        
        # Duration score (sweet spot: 30-60s)
        duration = candidate.get('duration', 0)
        if 30 <= duration <= 60:
            score += 3.0
        elif 20 <= duration <= 70:
            score += 2.0
        elif 15 <= duration <= 80:
            score += 1.0
        
        # Word count score (substantive content)
        word_count = len(candidate.get('text', '').split())
        if word_count >= 50:
            score += 2.0
        elif word_count >= 30:
            score += 1.0
        
        candidate['heuristic_score'] = score
    
    # Sort by heuristic score and take top candidates
    candidates_sorted = sorted(candidates, key=lambda x: x.get('heuristic_score', 0), reverse=True)
    return candidates_sorted[:max_count]


def process_single_segment_response(segment: Dict, ai_analysis: Dict, idx: int) -> Dict:
    """
    Process a single segment's AI analysis and create scored segment.
    
    Args:
        segment: Original segment data
        ai_analysis: Parsed AI response
        idx: Segment index
        
    Returns:
        Scored segment with all fields
    """
    try:
        # Extract scores with defaults
        hook_score = extract_score_safe(ai_analysis, 'hook_score', 0.0)
        retention_score = extract_score_safe(ai_analysis, 'retention_score', 0.0)
        emotion_score = extract_score_safe(ai_analysis, 'emotion_score', 0.0)
        relatability_score = extract_score_safe(ai_analysis, 'relatability_score', 0.0)
        completion_score = extract_score_safe(ai_analysis, 'completion_score', 0.0)
        platform_fit_score = extract_score_safe(ai_analysis, 'platform_fit_score', 0.0)
        final_score = extract_score_safe(ai_analysis, 'final_score', 0.0)
        
        # Extract other fields
        verdict = ai_analysis.get('verdict', 'skip')
        key_strengths = ai_analysis.get('key_strengths', [])
        key_weaknesses = ai_analysis.get('key_weaknesses', [])
        first_3_seconds = ai_analysis.get('first_3_seconds', '')
        primary_emotion = ai_analysis.get('primary_emotion', 'neutral')
        optimal_platform = ai_analysis.get('optimal_platform', 'none')
        
        # Create scored segment
        scored_segment = {
            **segment,  # Include all original segment data
            'hook_score': hook_score,
            'retention_score': retention_score,
            'emotion_score': emotion_score,
            'relatability_score': relatability_score,
            'completion_score': completion_score,
            'platform_fit_score': platform_fit_score,
            'final_score': final_score,
            'verdict': verdict,
            'key_strengths': key_strengths,
            'key_weaknesses': key_weaknesses,
            'first_3_seconds': first_3_seconds,
            'primary_emotion': primary_emotion,
            'optimal_platform': optimal_platform
        }
        
        logger.info(f"Segment {idx + 1}: score={final_score:.1f}, verdict={verdict}")
        return scored_segment
        
    except Exception as e:
        logger.error(f"Error processing segment {idx + 1} response: {e}")
        return create_fallback_segment(segment)


def create_fallback_segment(segment: Dict) -> Dict:
    """
    Create a fallback scored segment with default values when AI scoring fails.
    
    Args:
        segment: Original segment data
        
    Returns:
        Segment with default/zero scores
    """
    return {
        **segment,
        'hook_score': 0.0,
        'retention_score': 0.0,
        'emotion_score': 0.0,
        'relatability_score': 0.0,
        'completion_score': 0.0,
        'platform_fit_score': 0.0,
        'final_score': 0.0,
        'verdict': 'skip',
        'key_strengths': [],
        'key_weaknesses': ['AI scoring failed'],
        'first_3_seconds': '',
        'primary_emotion': 'neutral',
        'optimal_platform': 'none'
    }


def score_segments(
    candidates: List[Dict],
    model_config: Dict,
    max_segments: int = 50
) -> List[Dict]:
    """
    Score candidate segments using GitHub Models API.
    
    Args:
        candidates: List of candidate segment dictionaries
        model_config: Model configuration (endpoint, model_name, api_key)
        max_segments: Maximum number of segments to score
        
    Returns:
        List of scored segments with AI analysis
    """
    if not candidates:
        logger.warning("No candidate segments to score")
        return []
    
    # Get API credentials
    endpoint = model_config.get("endpoint") or os.getenv("GITHUB_MODELS_ENDPOINT")
    api_key = model_config.get("api_key") or os.getenv("GITHUB_TOKEN")
    model_name = model_config.get("model_name", "gpt-4o")
    temperature = model_config.get("temperature", 0.2)
    
    if not endpoint:
        endpoint = "https://models.inference.ai.azure.com"
    
    if not api_key:
        raise ValueError("GitHub API token not provided. Set GITHUB_TOKEN environment variable.")
    
    logger.info(f"Using GitHub Models API: {model_name}")
    logger.info(f"Scoring {min(len(candidates), max_segments)} segments")
    
    # Load prompt template
    prompt_template = load_prompt_template()
    
    # Pre-filter candidates
    pre_filter_count = model_config.get('pre_filter_count', 20)
    logger.info(f"Pre-filtering {len(candidates)} candidates")
    candidates = pre_filter_candidates(candidates, max_count=pre_filter_count)
    logger.info(f"After pre-filtering: {len(candidates)} candidates")
    
    # Limit to max_segments
    segments_to_score = candidates[:max_segments] if len(candidates) > max_segments else candidates
    
    # Initialize API client
    client = None
    
    if AZURE_SDK_AVAILABLE:
        try:
            client = ChatCompletionsClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            logger.info("Using Azure AI Inference SDK")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure SDK: {e}")
    
    if client is None and OPENAI_SDK_AVAILABLE:
        try:
            client = OpenAI(
                base_url=endpoint,
                api_key=api_key
            )
            logger.info("Using OpenAI SDK")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI SDK: {e}")
    
    if client is None:
        raise RuntimeError("No compatible SDK available. Install azure-ai-inference or openai.")
    
    # System message
    system_message = """You are a video content analyzer. 

CRITICAL: You MUST respond with ONLY valid JSON. 
- Do NOT include markdown code blocks
- Do NOT include any text before or after the JSON
- Start directly with { and end with }"""
    
    # Configuration
    batch_size = model_config.get('batch_size', 6)
    inter_request_delay = model_config.get('inter_request_delay', 1.5)
    max_cooldown_threshold = model_config.get('max_cooldown_threshold', 60)
    
    scored_segments = []
    api_calls_made = 0
    tokens_used = 0
    
    # Process segments in batches
    for batch_start in range(0, len(segments_to_score), batch_size):
        batch_end = min(batch_start + batch_size, len(segments_to_score))
        batch_segments = segments_to_score[batch_start:batch_end]
        
        if len(batch_segments) == 1:
            # Single segment processing
            segment = batch_segments[0]
            idx = batch_start
            
            try:
                # Format prompt
                prompt = (
                    prompt_template
                    .replace("{{SEGMENT_TEXT}}", segment["text"])
                    .replace("{{DURATION}}", f"{segment['duration']:.1f}")
                )
                
                # Validate prompt
                is_valid, error_msg = validate_prompt(prompt)
                if not is_valid:
                    logger.error(f"Invalid prompt for segment {idx + 1}: {error_msg}")
                    scored_segments.append(create_fallback_segment(segment))
                    continue
                
                # Call API with retry
                ai_response = None
                max_retries = 3
                
                for attempt in range(max_retries + 1):
                    try:
                        if AZURE_SDK_AVAILABLE and isinstance(client, ChatCompletionsClient):
                            response = client.complete(
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": prompt}
                                ],
                                model=model_name,
                                temperature=temperature,
                                max_tokens=1024,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                            
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                            
                        else:  # OpenAI SDK
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=temperature,
                                max_tokens=1024,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                            
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                        
                        api_calls_made += 1
                        break
                        
                    except Exception as api_error:
                        if attempt < max_retries:
                            backoff = min(60, (2 ** attempt) + random.uniform(0, 1))
                            logger.warning(f"API call failed, retrying in {backoff:.1f}s... ({api_error})")
                            time.sleep(backoff)
                        else:
                            logger.error(f"API call failed after {max_retries + 1} attempts: {api_error}")
                            raise
                
                if ai_response is None:
                    raise RuntimeError("API call failed")
                
                # Parse response
                ai_analysis = extract_json_safe(ai_response)
                scored_segment = process_single_segment_response(segment, ai_analysis, idx)
                scored_segments.append(scored_segment)
                
                # Delay between requests
                if idx < len(segments_to_score) - 1:
                    time.sleep(inter_request_delay)
                
            except Exception as e:
                logger.error(f"Failed to score segment {idx + 1}: {e}")
                scored_segments.append(create_fallback_segment(segment))
        
        else:
            # Batch processing
            try:
                batch_prompt = create_batch_prompt(batch_segments, prompt_template)
                
                # Validate prompt
                is_valid, error_msg = validate_prompt(batch_prompt)
                if not is_valid:
                    logger.error(f"Invalid batch prompt: {error_msg}")
                    for segment in batch_segments:
                        scored_segments.append(create_fallback_segment(segment))
                    continue
                
                # Call API with retry
                ai_response = None
                max_retries = 1
                
                for attempt in range(max_retries + 1):
                    try:
                        if AZURE_SDK_AVAILABLE and isinstance(client, ChatCompletionsClient):
                            response = client.complete(
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": batch_prompt}
                                ],
                                model=model_name,
                                temperature=temperature,
                                max_tokens=4096,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                            
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                        
                        else:  # OpenAI SDK
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": batch_prompt}
                                ],
                                temperature=temperature,
                                max_tokens=4096,
                                response_format={"type": "json_object"}
                            )
                            ai_response = response.choices[0].message.content
                            
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                        
                        api_calls_made += 1
                        break
                        
                    except Exception as api_error:
                        if attempt < max_retries:
                            backoff = min(60, (2 ** attempt) + random.uniform(0, 1))
                            logger.warning(f"Batch API call failed, retrying in {backoff:.1f}s...")
                            time.sleep(backoff)
                        else:
                            logger.error(f"Batch API call failed: {api_error}")
                            raise
                
                if ai_response is None:
                    raise RuntimeError("Batch API call failed")
                
                # Parse batch response
                batch_data = extract_json_safe(ai_response)
                segments_data = batch_data.get('segments', [])
                
                if len(segments_data) != len(batch_segments):
                    logger.warning(f"Batch response count mismatch: expected {len(batch_segments)}, got {len(segments_data)}")
                
                # Process each segment in batch
                for i, segment in enumerate(batch_segments):
                    idx = batch_start + i
                    if i < len(segments_data):
                        ai_analysis = segments_data[i]
                        scored_segment = process_single_segment_response(segment, ai_analysis, idx)
                        scored_segments.append(scored_segment)
                    else:
                        scored_segments.append(create_fallback_segment(segment))
                
                # Delay between batches
                if batch_end < len(segments_to_score):
                    time.sleep(inter_request_delay)
                
            except Exception as e:
                logger.error(f"Failed to score batch: {e}")
                for segment in batch_segments:
                    scored_segments.append(create_fallback_segment(segment))
    
    logger.info(f"Scoring complete: {len(scored_segments)} segments scored")
    logger.info(f"API calls made: {api_calls_made}")
    logger.info(f"Total tokens used: {tokens_used}")
    
    # Sort by final score
    scored_segments.sort(key=lambda x: x.get('final_score', 0), reverse=True)
    
    return scored_segments
