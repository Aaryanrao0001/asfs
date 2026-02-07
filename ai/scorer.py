"""AI highlight scoring using GitHub Models API."""

import os
import json
import re
import logging
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
    
    for idx, segment in enumerate(segments_to_score):
        try:
            # Format prompt with segment data using token replacement
            # This avoids conflicts with JSON braces in the prompt
            prompt = (
                prompt_template
                .replace("{{SEGMENT_TEXT}}", segment["text"])
                .replace("{{DURATION}}", f"{segment['duration']:.1f}")
            )
            
            # Call AI model
            if AZURE_SDK_AVAILABLE and isinstance(client, ChatCompletionsClient):
                response = client.complete(
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    model=model_name,
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
                
            else:  # OpenAI SDK
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                ai_response = response.choices[0].message.content
            
            # DEBUG: Log raw output (temporary for debugging)
            logger.debug(f"Raw model output (first 200 chars): {ai_response[:200]}")
            
            # Parse AI response using extract_json_safe
            try:
                ai_analysis = extract_json_safe(ai_response)
            except ValueError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response was: {ai_response[:200]}")
                # Create default analysis (new format)
                ai_analysis = {
                    "hook_score": 0,
                    "retention_score": 0,
                    "emotion_score": 0,
                    "relatability_score": 0,
                    "completion_score": 0,
                    "platform_fit_score": 0,
                    "final_score": 0,
                    "verdict": "skip",
                    "key_strengths": [],
                    "key_weaknesses": ["AI analysis failed - Unable to parse response"],
                    "first_3_seconds": segment["text"][:100] if segment.get("text") else "",
                    "primary_emotion": "neutral",
                    "optimal_platform": "none"
                }
            
            # Map new format to existing structure for backward compatibility
            # Check if using new format (direct keys) or old format (nested)
            if "hook_score" in ai_analysis or "scores" in ai_analysis:
                # Extract scores safely with fallbacks
                hook_score = extract_score_safe(ai_analysis, "hook_score", 0.0)
                retention_score = extract_score_safe(ai_analysis, "retention_score", 0.0)
                emotion_score = extract_score_safe(ai_analysis, "emotion_score", 0.0)
                relatability_score = extract_score_safe(ai_analysis, "relatability_score", 0.0)
                completion_score = extract_score_safe(ai_analysis, "completion_score", 0.0)
                platform_fit_score = extract_score_safe(ai_analysis, "platform_fit_score", 0.0)
                
                # Extract final score with fallback calculation
                # Check if final_score was explicitly provided in the response
                final_score = extract_score_safe(ai_analysis, "final_score", None)
                
                # If final_score not provided, calculate weighted average from individual scores
                # Individual scores are expected to be on 0-10 scale, final_score on 0-100 scale
                if final_score is None:
                    final_score = (
                        hook_score * 0.35 +
                        retention_score * 0.25 +
                        emotion_score * 0.20 +
                        completion_score * 0.15 +
                        platform_fit_score * 0.05 +
                        relatability_score * 0.05
                    ) * 10.0  # Scale from 0-10 range to 0-100 range
                elif final_score == 0.0 and not any([hook_score, retention_score, emotion_score]):
                    # If final_score is explicitly 0 and all other scores are also 0, keep it as 0
                    pass
                # Otherwise use the provided final_score as-is
                
                # Convert final_score (0-100) to overall_score (0-10) for compatibility
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
            else:
                # Old format fallback (nested scores) - shouldn't happen with new prompt
                scores = ai_analysis.get("scores", {})
                overall_score = ai_analysis.get("overall_score", 0.0)
                
                scored_segment = {
                    **segment,
                    "ai_analysis": ai_analysis,
                    "overall_score": overall_score,
                    "scores": scores,
                    "recommendation": ai_analysis.get("recommendation", "AVERAGE")
                }
                
                logger.info(f"Scored segment {idx + 1}/{len(segments_to_score)}: "
                           f"{overall_score:.1f}/10 "
                           f"({ai_analysis.get('recommendation', 'UNKNOWN')})")
            
            scored_segments.append(scored_segment)
            
        except Exception as e:
            logger.error(f"Failed to score segment {idx + 1}: {str(e)}")
            # Add fallback with zero scores
            # Note: final_score appears both in ai_analysis and top-level for backward compatibility
            scored_segments.append({
                **segment,
                "ai_analysis": {
                    "error": str(e),
                    "final_score": 0
                },
                "overall_score": 0.0,
                "final_score": 0,  # Top-level for easy access
                "verdict": "skip",
                "hook_score": 0,
                "retention_score": 0,
                "emotion_score": 0,
                "relatability_score": 0,
                "completion_score": 0,
                "platform_fit_score": 0
            })
    
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
    else:
        logger.warning("No segments scored successfully")
    
    return scored_segments
