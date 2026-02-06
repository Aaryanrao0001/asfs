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


def safe_json_parse(text: str) -> dict:
    """
    Extract and parse JSON from model response.
    
    Handles cases where the model wraps JSON in:
    - Markdown code blocks (```json ... ```)
    - Extra whitespace or newlines
    - Explanatory text before/after JSON
    
    Args:
        text: Raw model response
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If no valid JSON found
    """
    # Remove markdown code blocks if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # Try to find JSON object by counting braces to handle nested objects
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError(f"No JSON object found in model output: {text[:200]}")
    
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
        raise ValueError(f"Unbalanced braces in JSON object: {text[start_idx:start_idx+200]}")
    
    json_str = text[start_idx:end_idx]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Show context around the error position
        error_pos = getattr(e, 'pos', 0)
        context_start = max(0, error_pos - 50)
        context_end = min(len(json_str), error_pos + 50)
        context = json_str[context_start:context_end]
        raise ValueError(f"Invalid JSON in model output: {e}\nContext: ...{context}...")



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
            # Format prompt with segment data
            prompt = prompt_template.format(
                segment_text=segment["text"],
                duration=f"{segment['duration']:.1f}"
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
            
            # Parse AI response using safe parser
            try:
                ai_analysis = safe_json_parse(ai_response)
            except ValueError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"Response was: {ai_response[:200]}")
                # Create default analysis (new format)
                ai_analysis = {
                    "hook_score": 5,
                    "retention_score": 5,
                    "emotion_score": 5,
                    "relatability_score": 5,
                    "completion_score": 5,
                    "platform_fit_score": 5,
                    "final_score": 50,
                    "verdict": "skip",
                    "key_strengths": ["AI analysis failed"],
                    "key_weaknesses": ["Unable to parse response"],
                    "first_3_seconds": segment["text"][:100],
                    "primary_emotion": "neutral",
                    "optimal_platform": "none"
                }
            
            # Map new format to existing structure for backward compatibility
            # Check if using new format (direct keys) or old format (nested)
            if "hook_score" in ai_analysis:
                # New viral evaluation format
                final_score = ai_analysis.get("final_score", 0)
                verdict = ai_analysis.get("verdict", "skip")
                
                # Convert final_score (0-100) to overall_score (0-10) for compatibility
                overall_score = final_score / 10.0
                
                scored_segment = {
                    **segment,
                    "ai_analysis": ai_analysis,
                    "overall_score": overall_score,
                    "hook_score": ai_analysis.get("hook_score", 0),
                    "retention_score": ai_analysis.get("retention_score", 0),
                    "emotion_score": ai_analysis.get("emotion_score", 0),
                    "relatability_score": ai_analysis.get("relatability_score", 0),
                    "completion_score": ai_analysis.get("completion_score", 0),
                    "platform_fit_score": ai_analysis.get("platform_fit_score", 0),
                    "final_score": final_score,
                    "verdict": verdict,
                    "key_strengths": ai_analysis.get("key_strengths", []),
                    "key_weaknesses": ai_analysis.get("key_weaknesses", []),
                    "first_3_seconds": ai_analysis.get("first_3_seconds", ""),
                    "primary_emotion": ai_analysis.get("primary_emotion", "neutral"),
                    "optimal_platform": ai_analysis.get("optimal_platform", "none")
                }
                
                logger.info(f"Scored segment {idx + 1}/{len(segments_to_score)}: "
                           f"{final_score}/100 ({verdict.upper()})")
            else:
                # Old format fallback (nested scores)
                scores = ai_analysis.get("scores", {})
                overall_score = ai_analysis.get("overall_score", 5.0)
                
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
            # Add segment without AI score
            scored_segments.append({
                **segment,
                "ai_analysis": {
                    "error": str(e),
                    "overall_score": 0.0
                },
                "overall_score": 0.0
            })
    
    # Sort by overall score (highest first)
    scored_segments.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    
    logger.info(f"Completed scoring {len(scored_segments)} segments")
    
    if scored_segments:
        top_score = scored_segments[0].get("overall_score", 0)
        logger.info(f"Top segment score: {top_score:.1f}/10")
    
    return scored_segments
