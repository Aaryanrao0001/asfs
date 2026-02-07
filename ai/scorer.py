"""AI highlight scoring using GitHub Models API."""

import os
import json
import re
import logging
import time
import random
from typing import List, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

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

# Try importing Ollama SDK
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logger.info("Ollama SDK not available - will use remote APIs only")


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
    # This ensures we get complete nested objects
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
    Safely extract a numeric score from parsed JSON.
    
    Handles multiple schema variations:
    - Direct key: {"hook_score": 7}
    - Nested: {"scores": {"hook_score": 7}}
    - String numbers: {"hook_score": "7"}
    
    Individual scores are expected to be on a 0-10 scale.
    The final_score field is expected to be on a 0-100 scale.
    
    Args:
        data: Parsed JSON dictionary
        field: Field name to extract (e.g., "hook_score")
        default: Default value if field not found (can be None for optional fields)
        
    Returns:
        Numeric score as float, or default if not found/invalid
    """
    try:
        # Try direct access
        if field in data:
            value = data[field]
            # Return None explicitly if the value is None and default is None
            if value is None and default is None:
                return None
            return float(value)
        
        # Try nested in "scores"
        if "scores" in data and isinstance(data["scores"], dict):
            if field in data["scores"]:
                return float(data["scores"][field])
        
        # Try without underscore (e.g., "hookscore")
        alt_field = field.replace("_", "")
        if alt_field in data:
            return float(data[alt_field])
        
        # Not found - return default
        return default
        
    except (ValueError, TypeError):
        return default if default is not None else 0.0



def load_prompt_template() -> str:
    """Load the scoring prompt template."""
    prompt_path = Path(__file__).parent / "prompt.txt"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def check_ollama_availability(model_name: str = "qwen3:latest", timeout: float = 1.0, endpoint: str = "http://localhost:11434") -> bool:
    """
    Check if Ollama is running and model is available.
    
    Args:
        model_name: Name of the Ollama model to check (e.g., "qwen3:8b")
        timeout: Connection timeout in seconds
        endpoint: Ollama endpoint URL
        
    Returns:
        True if Ollama is running and model exists, False otherwise
    """
    if not OLLAMA_AVAILABLE:
        logger.debug("Ollama SDK not installed")
        return False
    
    try:
        # Quick health check with timeout
        client = ollama.Client(host=endpoint, timeout=timeout)
        
        # List available models
        response = client.list()
        
        # Extract model names - handle both 'name' and 'model' fields
        available_models = []
        for m in response.get('models', []):
            # Try both common field names
            model_id = m.get('name') if m.get('name') is not None else m.get('model')
            if model_id:
                available_models.append(model_id)
        
        # Log all discovered models at DEBUG level
        logger.debug(f"Ollama detected models: {available_models}")
        
        if not available_models:
            logger.warning("Ollama is running but no models found")
            return False
        
        # Normalize model names for comparison (case-insensitive)
        model_name_normalized = model_name.lower().strip()
        available_normalized = [m.lower().strip() for m in available_models]
        
        # Strategy 1: Exact match (preferred)
        for i, available in enumerate(available_normalized):
            if available == model_name_normalized:
                matched_model = available_models[i]
                logger.info(f"Ollama is running with model: {matched_model} (exact match)")
                return True
        
        # Strategy 2: Base name match (e.g., "qwen3:8b" matches "qwen3:*")
        model_base = model_name_normalized.split(':')[0]
        for i, available in enumerate(available_normalized):
            available_base = available.split(':')[0]
            if available_base == model_base:
                matched_model = available_models[i]
                logger.info(f"Ollama is running with model: {matched_model} (base name match for '{model_name}')")
                return True
        
        # No match found - log available models at INFO level for debugging
        logger.warning(f"Ollama is running but model '{model_name}' not found.")
        logger.info(f"Available models: {', '.join(available_models)}")
        logger.info(f"Tip: Check your config/model.yaml - local_model_name should match one of the above")
        return False
        
    except ConnectionError as e:
        logger.debug(f"Ollama connection failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"Ollama availability check failed: {e}")
        logger.debug("Full error details:", exc_info=True)
        return False


def score_with_ollama(
    segment: Dict,
    prompt: str,
    model_name: str = "qwen3:latest",
    temperature: float = 0.2,
    endpoint: str = "http://localhost:11434"
) -> Dict:
    """
    Score a segment using local Ollama model.
    
    Args:
        segment: Segment data
        prompt: Formatted prompt
        model_name: Ollama model name
        temperature: Temperature for generation
        endpoint: Ollama endpoint URL
        
    Returns:
        Parsed AI analysis dictionary
        
    Raises:
        Exception: If Ollama call fails
    """
    client = ollama.Client(host=endpoint)
    
    # Call Ollama API
    response = client.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": """You are a video content analyzer.

CRITICAL: You MUST respond with ONLY valid JSON.
- Do NOT include markdown code blocks
- Do NOT include any text before or after the JSON
- Start directly with { and end with }"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": temperature,
            "num_predict": 1024  # Max tokens
        },
        format="json"  # Force JSON output
    )
    
    # Extract response
    ai_response = response['message']['content']
    
    # Parse JSON
    ai_analysis = extract_json_safe(ai_response)
    
    return ai_analysis


def create_batch_prompt(segments: List[Dict], prompt_template: str) -> str:
    """
    Create a batch scoring prompt for multiple segments.
    
    Args:
        segments: List of segments to score together (batch size is configurable)
        prompt_template: Base template
        
    Returns:
        Formatted batch prompt
    """
    batch_data = []
    for i, seg in enumerate(segments):
        batch_data.append({
            "id": i + 1,
            "text": seg["text"],
            "duration": seg["duration"]
        })
    
    batch_prompt = f"""
Score the following {len(segments)} video segments. Return a JSON array with results for each.

Segments:
{json.dumps(batch_data, indent=2)}

{prompt_template}

Return format:
{{
  "results": [
    {{
      "id": 1,
      "hook_score": 7,
      "retention_score": 6,
      "emotion_score": 5,
      "relatability_score": 4,
      "completion_score": 6,
      "platform_fit_score": 5,
      "final_score": 60,
      "verdict": "maybe",
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
    Pre-filter candidates using heuristics before AI scoring.
    
    Criteria:
    - Duration: 20-60 seconds
    - High pause density (natural breaks)
    - Emotional keywords
    - Sentence density (engagement)
    
    Args:
        candidates: All candidate segments
        max_count: Maximum to return
        
    Returns:
        Filtered candidates most likely to be viral
    """
    EMOTIONAL_KEYWORDS = [
        'never', 'always', 'nobody', 'everyone', 'shocked', 'crazy', 
        'insane', 'ruined', 'destroyed', 'unbelievable', 'secret', 
        'truth', 'lie', 'wrong', 'right', 'mistake', 'regret'
    ]
    
    scored_candidates = []
    
    for candidate in candidates:
        heuristic_score = 0.0
        text = candidate.get('text', '').lower()
        duration = candidate.get('duration', 0)
        
        # Duration check (20-60s ideal)
        if 20 <= duration <= 60:
            heuristic_score += 3.0
        elif 15 <= duration <= 75:
            heuristic_score += 1.5
        
        # Emotional keywords
        keyword_count = sum(1 for kw in EMOTIONAL_KEYWORDS if kw in text)
        heuristic_score += min(keyword_count * 0.5, 3.0)
        
        # Sentence density (engagement indicator)
        sentences = text.count('.') + text.count('!') + text.count('?')
        if duration > 0:
            sentence_density = sentences / (duration / 10)  # Sentences per 10s
            heuristic_score += min(sentence_density * 0.8, 2.0)
        
        # Pause density (from metadata if available)
        pause_density = candidate.get('pause_density', 0)
        heuristic_score += min(pause_density * 2.0, 2.0)
        
        scored_candidates.append({
            **candidate,
            'heuristic_score': heuristic_score
        })
    
    # Sort by heuristic score and return top N
    scored_candidates.sort(key=lambda x: x['heuristic_score'], reverse=True)
    return scored_candidates[:max_count]


def save_pipeline_state(scored_segments: List[Dict], remaining_segments: List[Dict], output_path: str = "state/pipeline_state.json"):
    """Save pipeline state when rate limited."""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    state = {
        'timestamp': time.time(),
        'scored_segments': scored_segments,
        'remaining_segments': remaining_segments,
        'reason': 'rate_limit_exceeded'
    }
    
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    logger.info(f"Pipeline state saved to {output_path}")


def extract_retry_after(api_error) -> int:
    """
    Extract retry-after value from API error response.
    
    Args:
        api_error: Exception from API call
        
    Returns:
        Retry-after value in seconds, or None if not found
    """
    retry_after = None
    
    # Try to get from response headers (standard HTTP header)
    if hasattr(api_error, 'response') and hasattr(api_error.response, 'headers'):
        retry_after_header = api_error.response.headers.get('retry-after') or \
                           api_error.response.headers.get('Retry-After')
        if retry_after_header:
            try:
                retry_after = int(retry_after_header)
            except (ValueError, TypeError):
                pass
    
    # Fallback: try direct attribute (some SDKs may expose it directly)
    if retry_after is None:
        retry_after = getattr(api_error, 'retry_after', None)
    
    return retry_after


def process_single_segment_response(segment: Dict, ai_analysis: Dict, idx: int) -> Dict:
    """
    Process AI analysis for a single segment and create scored segment.
    
    Args:
        segment: Original segment data
        ai_analysis: Parsed AI response
        idx: Segment index for logging
        
    Returns:
        Scored segment dictionary
    """
    try:
        # Extract scores safely with fallbacks
        hook_score = extract_score_safe(ai_analysis, "hook_score", 0.0)
        retention_score = extract_score_safe(ai_analysis, "retention_score", 0.0)
        emotion_score = extract_score_safe(ai_analysis, "emotion_score", 0.0)
        relatability_score = extract_score_safe(ai_analysis, "relatability_score", 0.0)
        completion_score = extract_score_safe(ai_analysis, "completion_score", 0.0)
        platform_fit_score = extract_score_safe(ai_analysis, "platform_fit_score", 0.0)
        
        # Extract final score with fallback calculation
        final_score = extract_score_safe(ai_analysis, "final_score", None)
        
        # If final_score not provided, calculate weighted average
        if final_score is None:
            final_score = (
                hook_score * 0.35 +
                retention_score * 0.25 +
                emotion_score * 0.20 +
                completion_score * 0.10 +
                platform_fit_score * 0.05 +
                relatability_score * 0.05
            ) * 10.0  # Scale from 0-10 to 0-100
        
        # Convert final_score (0-100) to overall_score (0-10)
        overall_score = final_score / 10.0
        verdict = ai_analysis.get("verdict", "skip")
        
        scored_segment = {
            **segment,
            "ai_analysis": ai_analysis,
            "overall_score": overall_score,
            "hook_score": hook_score,
            "retention_score": retention_score,
            "emotion_score": emotion_score,
            "relatability_score": relatability_score,
            "completion_score": completion_score,
            "platform_fit_score": platform_fit_score,
            "final_score": final_score,
            "verdict": verdict,
            "key_strengths": ai_analysis.get("key_strengths", []),
            "key_weaknesses": ai_analysis.get("key_weaknesses", []),
            "first_3_seconds": ai_analysis.get("first_3_seconds", ""),
            "primary_emotion": ai_analysis.get("primary_emotion", "neutral"),
            "optimal_platform": ai_analysis.get("optimal_platform", "none")
        }
        
        logger.info(f"[OK] Segment {idx + 1}: final_score={final_score:.1f}/100, verdict={verdict}")
        return scored_segment
        
    except Exception as e:
        logger.error(f"Failed to process segment {idx + 1} response: {e}")
        return create_fallback_segment(segment)


def create_fallback_segment(segment: Dict) -> Dict:
    """
    Create a fallback segment with zero scores when AI analysis fails.
    
    Args:
        segment: Original segment data
        
    Returns:
        Segment with default scores
    """
    return {
        **segment,
        "ai_analysis": {
            "error": "AI analysis failed",
            "final_score": 0
        },
        "overall_score": 0.0,
        "final_score": 0,
        "verdict": "skip",
        "hook_score": 0,
        "retention_score": 0,
        "emotion_score": 0,
        "relatability_score": 0,
        "completion_score": 0,
        "platform_fit_score": 0,
        "key_strengths": [],
        "key_weaknesses": ["AI analysis failed"],
        "first_3_seconds": "",
        "primary_emotion": "neutral",
        "optimal_platform": "none"
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
        max_segments: Maximum number of segments to score (top candidates first)
        
    Returns:
        List of scored segments with AI analysis
    """
    if not candidates:
        logger.warning("No candidate segments to score")
        return []
    
    # Get API credentials from config or environment
    endpoint = model_config.get("endpoint") or os.getenv("GITHUB_MODELS_ENDPOINT")
    api_key = model_config.get("api_key") or os.getenv("GITHUB_TOKEN")
    model_name = model_config.get("model_name", "gpt-4o")
    
    if not endpoint:
        endpoint = "https://models.inference.ai.azure.com"
    
    if not api_key:
        raise ValueError("GitHub API token not provided. Set GITHUB_TOKEN environment variable.")
    
    logger.info(f"Scoring {min(len(candidates), max_segments)} segments using {model_name}")
    
    # Load prompt template
    prompt_template = load_prompt_template()
    
    # Backend selection configuration
    llm_backend = model_config.get("llm_backend", "auto")  # auto | local | api
    local_model_name = model_config.get("local_model_name", "qwen3:latest")
    local_endpoint = model_config.get("local_endpoint", "http://localhost:11434")
    temperature = model_config.get("temperature", 0.2)  # Use from config
    
    # Determine if we should try local model
    ollama_available = False
    
    if llm_backend == "api":
        logger.info("Backend: API only (local disabled by config)")
    elif llm_backend in ["auto", "local"]:
        # Check Ollama availability
        ollama_available = check_ollama_availability(local_model_name, endpoint=local_endpoint)
        
        if ollama_available:
            logger.info(f"Backend: Local LLM (Ollama) - model: {local_model_name}")
        else:
            if llm_backend == "local":
                logger.warning("Backend: LOCAL required but Ollama unavailable - falling back to API")
            else:  # auto
                logger.info("Backend: AUTO - Ollama unavailable, using API")
    else:
        logger.warning(f"Unknown llm_backend '{llm_backend}', defaulting to 'auto'")
        ollama_available = check_ollama_availability(local_model_name, endpoint=local_endpoint)
        if ollama_available:
            logger.info(f"Backend: Local LLM (Ollama) - model: {local_model_name}")
        else:
            logger.info("Backend: AUTO - Ollama unavailable, using API")
    
    # Pre-filter candidates using heuristics
    pre_filter_count = model_config.get('pre_filter_count', 20)
    logger.info(f"Pre-filtering {len(candidates)} candidates using heuristics")
    candidates = pre_filter_candidates(candidates, max_count=pre_filter_count)
    logger.info(f"After pre-filtering: {len(candidates)} candidates remain")
    
    # Limit to max_segments (score best candidates based on duration and position)
    segments_to_score = candidates[:max_segments] if len(candidates) > max_segments else candidates
    
    scored_segments = []
    
    # Initialize AI client
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
    
    # Define system message once (used for all segments)
    system_message = """You are a video content analyzer. 

CRITICAL: You MUST respond with ONLY valid JSON. 
- Do NOT include markdown code blocks
- Do NOT include any text before or after the JSON
- Start directly with { and end with }"""
    
    # API usage tracking
    api_calls_made = 0
    tokens_used = 0
    
    # Get batch size and other config
    BATCH_SIZE = model_config.get('batch_size', 6)  # Process 6 segments per API call
    inter_request_delay = model_config.get('inter_request_delay', 1.5)
    max_cooldown_threshold = model_config.get('max_cooldown_threshold', 60)
    
    # Process segments in batches
    for batch_start in range(0, len(segments_to_score), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(segments_to_score))
        batch_segments = segments_to_score[batch_start:batch_end]
        
        # For single segment, use original logic; for multiple, use batch
        if len(batch_segments) == 1:
            segment = batch_segments[0]
            idx = batch_start
            
            try:
                # Format prompt with segment data using token replacement
                prompt = (
                    prompt_template
                    .replace("{{SEGMENT_TEXT}}", segment["text"])
                    .replace("{{DURATION}}", f"{segment['duration']:.1f}")
                )
                
                ai_analysis = None
                used_local = False
                
                # Try local model first if available
                if ollama_available:
                    try:
                        ai_analysis = score_with_ollama(
                            segment=segment,
                            prompt=prompt,
                            model_name=local_model_name,
                            temperature=temperature,
                            endpoint=local_endpoint
                        )
                        used_local = True
                        logger.debug(f"Segment {idx + 1}: scored with local LLM")
                        
                    except Exception as local_error:
                        logger.warning(f"Local LLM failed for segment {idx + 1}: {local_error}")
                        logger.info("Falling back to remote API")
                        ai_analysis = None  # Force API fallback
                
                # Fallback to API if local failed or unavailable
                if ai_analysis is None:
                    ai_response = None
                    api_call_succeeded = False
                    max_retries = 3  # Increased from 1
                    
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
                                
                                # Track token usage
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
                                
                                # Track token usage
                                if hasattr(response, 'usage'):
                                    tokens_used += response.usage.total_tokens
                            
                            api_call_succeeded = True
                            break
                            
                        except Exception as api_error:
                            # Check for rate limiting (429)
                            is_rate_limit = False
                            retry_after = None
                            
                            if hasattr(api_error, 'status_code') and api_error.status_code == 429:
                                is_rate_limit = True
                                # Try to extract retry-after
                                if hasattr(api_error, 'response') and hasattr(api_error.response, 'headers'):
                                    retry_after = api_error.response.headers.get('retry-after')
                                    if retry_after:
                                        retry_after = int(retry_after)
                            
                            if is_rate_limit and retry_after and retry_after > 60:
                                logger.error(f"Rate limit with long cooldown ({retry_after}s). Stopping.")
                                raise RuntimeError(f"Rate limit exceeded: retry after {retry_after}s")
                            
                            if attempt < max_retries:
                                # Exponential backoff with jitter
                                if is_rate_limit and retry_after:
                                    backoff = retry_after + random.uniform(1, 5)
                                else:
                                    backoff = min(60, (2 ** attempt) + random.uniform(0, 1))
                                
                                logger.warning(f"API call failed for segment {idx + 1}, retrying in {backoff:.1f}s... ({api_error})")
                                time.sleep(backoff)
                            else:
                                logger.error(f"API call failed for segment {idx + 1} after {max_retries + 1} attempts: {api_error}")
                                raise
                    
                    if not api_call_succeeded or ai_response is None:
                        raise RuntimeError("API call failed and no response received")
                    
                    # Parse API response
                    try:
                        ai_analysis = extract_json_safe(ai_response)
                        logger.debug(f"Segment {idx + 1}: scored with API")
                    except ValueError as e:
                        logger.warning(f"Failed to parse API response for segment {idx + 1}: {e}")
                        raise
                
                # Log raw output for first segment only
                if idx == 0:
                    source = "local LLM" if used_local else "API"
                    logger.info(f"Using {source} for scoring")
                
                # Process single segment response
                scored_segment = process_single_segment_response(segment, ai_analysis, idx)
                scored_segments.append(scored_segment)
                
                # Add delay between requests (only for API calls)
                if not used_local and idx < len(segments_to_score) - 1:
                    time.sleep(inter_request_delay)
                
            except Exception as e:
                logger.error(f"Failed to score segment {idx + 1}: {str(e)}")
                scored_segments.append(create_fallback_segment(segment))
        
        else:
            # Batch processing for multiple segments
            try:
                # Create batch prompt
                batch_prompt = create_batch_prompt(batch_segments, prompt_template)
                
                # Call AI model with retry logic
                ai_response = None
                api_call_succeeded = False
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
                                temperature=0.2,  # Changed from 0.7
                                max_tokens=4096,  # Larger for batch responses
                                response_format={"type": "json_object"}
                            )
                            
                            ai_response = response.choices[0].message.content
                            
                            # Track token usage
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                            
                        else:  # OpenAI SDK
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[
                                    {"role": "system", "content": system_message},
                                    {"role": "user", "content": batch_prompt}
                                ],
                                temperature=0.2,  # Changed from 0.7
                                max_tokens=4096,  # Larger for batch responses
                                response_format={"type": "json_object"}
                            )
                            
                            ai_response = response.choices[0].message.content
                            
                            # Track token usage
                            if hasattr(response, 'usage'):
                                tokens_used += response.usage.total_tokens
                        
                        # API call succeeded
                        api_call_succeeded = True
                        api_calls_made += 1
                        logger.info(f"API call {api_calls_made}: {len(batch_segments)} segments, {tokens_used} tokens used so far")
                        
                        # Add inter-request delay
                        if batch_start > 0:
                            time.sleep(inter_request_delay)
                        
                        break
                        
                    except Exception as api_error:
                        # Check if it's a 429 rate limit error
                        if hasattr(api_error, 'status_code') and api_error.status_code == 429:
                            retry_after = extract_retry_after(api_error)
                            if retry_after and retry_after > max_cooldown_threshold:
                                logger.error(f"Rate limit exceeded with long cooldown ({retry_after}s). Stopping scoring.")
                                remaining = segments_to_score[batch_start:]
                                save_pipeline_state(scored_segments, remaining)
                                return scored_segments
                            
                            sleep_time = (retry_after or 10) + random.uniform(1, 5)
                            logger.warning(f"Rate limited. Sleeping for {sleep_time:.1f}s")
                            time.sleep(sleep_time)
                            continue
                        
                        if attempt < max_retries:
                            backoff = min(300, (2 ** attempt) + random.uniform(0, 1))
                            logger.warning(f"API call failed for batch starting at {batch_start + 1}, retrying in {backoff:.1f}s... ({api_error})")
                            time.sleep(backoff)
                        else:
                            logger.error(f"API call failed for batch after {max_retries + 1} attempts: {api_error}")
                            raise
                
                if not api_call_succeeded or ai_response is None:
                    raise RuntimeError("API call failed and no response received")
                
                # Parse batch response
                batch_analysis = extract_json_safe(ai_response)
                
                # Extract results array
                results = batch_analysis.get('results', [])
                
                if not results:
                    logger.warning("Batch response missing 'results' array, falling back to individual parsing")
                    # Fallback: try to treat as single response
                    results = [batch_analysis]
                
                # Process each result and match to original segments
                for i, segment in enumerate(batch_segments):
                    idx = batch_start + i
                    
                    # Find matching result by id
                    result = None
                    for r in results:
                        if r.get('id') == i + 1:
                            result = r
                            break
                    
                    if result is None and i < len(results):
                        # Fallback: use positional matching
                        result = results[i]
                    
                    if result:
                        scored_segment = process_single_segment_response(segment, result, idx)
                        scored_segments.append(scored_segment)
                    else:
                        logger.warning(f"No result found for segment {idx + 1} in batch")
                        scored_segments.append(create_fallback_segment(segment))
                
            except Exception as e:
                logger.error(f"Failed to score batch starting at {batch_start + 1}: {str(e)}")
                # Add fallback for all segments in batch
                for i, segment in enumerate(batch_segments):
                    scored_segments.append(create_fallback_segment(segment))
    
    # Sort by overall score (highest first)
    scored_segments.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    
    logger.info(f"Completed scoring {len(scored_segments)} segments")
    
    if scored_segments:
        # Calculate statistics
        scores = [s.get("overall_score", 0.0) for s in scored_segments]
        final_scores = [s.get("final_score", 0.0) for s in scored_segments]
        max_score = max(scores)
        avg_score = sum(scores) / len(scores) if scores else 0
        max_final = max(final_scores)
        avg_final = sum(final_scores) / len(final_scores) if final_scores else 0
        
        # Get threshold from config
        min_score_threshold = model_config.get('min_score_threshold', 6.0)
        
        # Count high-quality segments
        high_quality = sum(1 for s in scores if s >= min_score_threshold)
        
        logger.info(f"Scoring complete: max={max_score:.1f}/10 (final={max_final:.1f}/100), avg={avg_score:.1f}/10 (final={avg_final:.1f}/100)")
        logger.info(f"High-quality segments (score >= {min_score_threshold}): {high_quality}")
        
        # Sanity check: warn if ALL segments scored 0
        if max_score == 0 and max_final == 0:
            logger.warning("=" * 80)
            logger.warning("WARNING: ALL SEGMENTS SCORED 0!")
            logger.warning("This likely indicates an API or parsing issue:")
            logger.warning("  1. Check if API key is valid and has correct permissions")
            logger.warning("  2. Check if model endpoint is accessible")
            logger.warning("  3. Review raw model output logs above for errors")
            logger.warning("  4. Verify response_format is supported by the model")
            logger.warning("=" * 80)
    else:
        logger.warning("No segments scored successfully")
    
    return scored_segments
