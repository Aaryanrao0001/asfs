#!/usr/bin/env python3
"""
Automated Short-Form Content Clipping & Distribution System

Main orchestrator that runs the full pipeline:
1. Audio extraction (fast, for transcription)
2. Transcript generation
3. Transcript quality validation
4. Candidate segment building
5. AI highlight scoring
6. Clip validation & deduplication
7. FFmpeg clip extraction from original video
8. Crop clips to 9:16 (vertical format)
9. Metadata generation
10. Scheduling & rate control
11. Platform uploads
12. Audit logging

Note: Video normalization removed for MVP performance.
Aspect ratio conversion happens only on final clips.
"""

import os
import sys

# Fix Windows console encoding issues
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # Fallback for older Python versions
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import logging
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, List

# Import pipeline modules
from transcript import transcribe_video, check_transcript_quality, extract_audio
from transcript.transcribe import load_transcript, load_and_validate_transcript
from segmenter import build_sentence_windows, build_pause_windows
from ai import score_segments
from validator import deduplicate_clips, remove_overlapping_clips
from clipper import extract_clips
from metadata import generate_captions, generate_hashtags
from scheduler import UploadQueue
from scheduler.queue import load_rate_limits
from uploaders import upload_to_tiktok, upload_to_instagram, upload_to_youtube
from audit import AuditLogger
from cache import PipelineCache


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_config() -> Dict:
    """Load configuration from files."""
    config = {}
    
    # Load model config
    model_config_path = "config/model.yaml"
    if os.path.exists(model_config_path):
        with open(model_config_path, 'r') as f:
            config['model'] = yaml.safe_load(f)['model']
    else:
        logger.warning(f"Model config not found: {model_config_path}")
        config['model'] = {
            'endpoint': 'https://models.inference.ai.azure.com',
            'model_name': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 500
        }
    
    # Load platform config
    platforms_config_path = "config/platforms.json"
    if os.path.exists(platforms_config_path):
        with open(platforms_config_path, 'r') as f:
            config['platforms'] = json.load(f)
    else:
        logger.warning(f"Platforms config not found: {platforms_config_path}")
        config['platforms'] = {}
    
    # Load rate limits
    rate_limits_path = "config/rate_limits.json"
    config['rate_limits'] = load_rate_limits(rate_limits_path)
    
    return config


def run_pipeline(video_path: str, output_dir: str = "output", use_cache: bool = True):
    """
    Run the complete pipeline.
    
    Args:
        video_path: Path to input video
        output_dir: Directory for output files
        use_cache: Enable caching to resume from last completed stage (default: True)
    """
    logger.info("=" * 80)
    logger.info("AUTOMATED SHORT-FORM CONTENT CLIPPING PIPELINE")
    logger.info("=" * 80)
    
    # Verify input video exists
    if not os.path.exists(video_path):
        logger.error(f"Input video not found: {video_path}")
        sys.exit(1)
    
    # Load configuration
    logger.info("Loading configuration...")
    config = load_config()
    
    # Log critical config values for debugging
    logger.info("=" * 80)
    logger.info("CONFIGURATION VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Model endpoint: {config['model'].get('endpoint', 'not set')}")
    logger.info(f"Model name: {config['model'].get('model_name', 'not set')}")
    logger.info(f"Min score threshold: {config['model'].get('min_score_threshold', 'not set')}")
    logger.info(f"Max segments to score: {config['model'].get('max_segments_to_score', 'not set')}")
    logger.info("=" * 80)
    
    # Initialize pipeline cache
    cache = PipelineCache(cache_dir=os.path.join(output_dir, "cache"))
    pipeline_state = {}
    
    # Try to load cached state if caching is enabled
    if use_cache:
        logger.info("\n" + "=" * 80)
        logger.info("CHECKING FOR CACHED STATE")
        logger.info("=" * 80)
        cached_state = cache.load_state(video_path)
        
        if cached_state:
            pipeline_state = cached_state
            logger.info("[OK] Will resume from last completed stage")
            logger.info("  (Use --no-cache to force full reprocessing)")
        else:
            logger.info("[OK] No cache found - starting fresh")
    else:
        logger.info("[OK] Cache disabled - starting fresh pipeline")
    
    # Initialize audit logger
    audit = AuditLogger()
    audit.log_pipeline_event("initialization", "started", video_path)
    
    # Create output directories
    work_dir = os.path.join(output_dir, "work")
    clips_dir = os.path.join(output_dir, "clips")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)
    
    try:
        # Stage 1: Audio Extraction (fast)
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 1: AUDIO EXTRACTION")
        logger.info("=" * 80)
        
        # Check if this stage is cached
        if cache.has_completed_stage(pipeline_state, 'audio_extraction'):
            audio_path = cache.get_stage_result(pipeline_state, 'audio_extraction', 'audio_path')
            logger.info(f"[OK] SKIPPED (using cached result): {audio_path}")
            
            # Verify file still exists
            if not os.path.exists(audio_path):
                logger.warning("Cached audio file not found, re-extracting...")
                cache_hit = False
            else:
                cache_hit = True
        else:
            cache_hit = False
        
        if not cache_hit:
            audit.log_pipeline_event("audio_extraction", "started", video_path)
            
            try:
                audio_path = extract_audio(video_path, work_dir)
                logger.info(f"[OK] Audio extracted: {audio_path}")
                audit.log_pipeline_event("audio_extraction", "completed", audio_path)
                
                # Save to cache
                if use_cache:
                    pipeline_state['audio_extraction'] = {
                        'completed': True,
                        'audio_path': audio_path
                    }
                    cache.save_state(video_path, pipeline_state, 'audio_extraction')
                    
            except Exception as e:
                logger.error(f"[FAIL] Audio extraction failed: {str(e)}")
                audit.log_pipeline_event("audio_extraction", "failed", video_path, 
                                        error_message=str(e))
                raise
        
        # Stage 2: Transcript Generation (uses audio, not video)
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 2: TRANSCRIPT GENERATION")
        logger.info("=" * 80)
        
        # Define transcript path
        transcript_path = os.path.join(work_dir, "transcript.json")
        
        # Check if this stage is cached OR if transcript.json already exists
        if cache.has_completed_stage(pipeline_state, 'transcription'):
            cached_transcript_path = cache.get_stage_result(pipeline_state, 'transcription', 'transcript_path')
            logger.info(f"[OK] SKIPPED (using cached result): {cached_transcript_path}")
            
            # Verify file still exists
            if not os.path.exists(cached_transcript_path):
                logger.warning("Cached transcript file not found, re-transcribing...")
                cache_hit = False
            else:
                transcript_path = cached_transcript_path
                transcript_data = load_transcript(transcript_path)
                cache_hit = True
        elif use_cache and os.path.exists(transcript_path):
            # Transcript exists but not in cache - load and validate it
            is_valid, transcript_data = load_and_validate_transcript(transcript_path)
            
            if is_valid:
                # Valid transcript - use it
                logger.info(f"[OK] SKIPPED (using cached transcript): {transcript_path}")
                logger.info(f"[OK] Cached transcript has {len(transcript_data['segments'])} segments")
                audit.log_pipeline_event("transcription", "skipped_cached", transcript_path)
                cache_hit = True
                
                # Update cache with this transcript
                if use_cache:
                    pipeline_state['transcription'] = {
                        'completed': True,
                        'transcript_path': transcript_path,
                        'segment_count': len(transcript_data.get("segments", []))
                    }
                    cache.save_state(video_path, pipeline_state, 'transcription')
            else:
                logger.warning("Cached transcript invalid or corrupt")
                logger.info("Re-generating transcript...")
                cache_hit = False
        else:
            cache_hit = False
        
        if not cache_hit:
            audit.log_pipeline_event("transcription", "started", audio_path)
            
            try:
                transcript_path = transcribe_video(audio_path, work_dir)
                logger.info(f"[OK] Transcript saved: {transcript_path}")
                
                transcript_data = load_transcript(transcript_path)
                audit.log_pipeline_event("transcription", "completed", audio_path,
                                        {"segments": len(transcript_data.get("segments", []))})
                
                # Save to cache
                if use_cache:
                    pipeline_state['transcription'] = {
                        'completed': True,
                        'transcript_path': transcript_path,
                        'segment_count': len(transcript_data.get("segments", []))
                    }
                    cache.save_state(video_path, pipeline_state, 'transcription')
                    
            except Exception as e:
                logger.error(f"[FAIL] Transcription failed: {str(e)}")
                audit.log_pipeline_event("transcription", "failed", video_path,
                                        error_message=str(e))
                raise
        
        # Stage 3: Transcript Quality Check
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 3: TRANSCRIPT QUALITY VALIDATION")
        logger.info("=" * 80)
        audit.log_pipeline_event("quality_check", "started", video_path)
        
        try:
            quality_score, passed, quality_metrics = check_transcript_quality(transcript_data)
            
            logger.info(f"[OK] Quality Score: {quality_score:.2f}/1.0")
            logger.info(f"[OK] Quality Check: {'PASSED' if passed else 'FAILED'}")
            
            if not passed:
                logger.warning("Transcript quality is below threshold")
                logger.warning("Proceeding with caution - results may be suboptimal")
            
            audit.log_pipeline_event("quality_check", "completed", video_path,
                                    {"score": quality_score, "passed": passed})
        except Exception as e:
            logger.error(f"[FAIL] Quality check failed: {str(e)}")
            audit.log_pipeline_event("quality_check", "failed", video_path,
                                    error_message=str(e))
            raise
        
        # Stage 4: Candidate Segment Building
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 4: CANDIDATE SEGMENT BUILDING")
        logger.info("=" * 80)
        
        # Check if this stage is cached
        if cache.has_completed_stage(pipeline_state, 'segmentation'):
            all_candidates = cache.get_stage_result(pipeline_state, 'segmentation', 'candidates')
            logger.info(f"[OK] SKIPPED (using cached result): {len(all_candidates)} candidates")
            cache_hit = True
        else:
            cache_hit = False
        
        if not cache_hit:
            audit.log_pipeline_event("segmentation", "started", video_path)
            
            try:
                # Build sentence-based windows
                sentence_candidates = build_sentence_windows(transcript_data)
                logger.info(f"[OK] Sentence-based candidates: {len(sentence_candidates)}")
                
                # Build pause-based windows
                pause_candidates = build_pause_windows(transcript_data)
                logger.info(f"[OK] Pause-based candidates: {len(pause_candidates)}")
                
                # Combine candidates
                all_candidates = sentence_candidates + pause_candidates
                logger.info(f"[OK] Total candidates: {len(all_candidates)}")
                
                audit.log_pipeline_event("segmentation", "completed", video_path,
                                        {"total_candidates": len(all_candidates)})
                
                # Save to cache
                if use_cache:
                    pipeline_state['segmentation'] = {
                        'completed': True,
                        'candidates': all_candidates,
                        'sentence_count': len(sentence_candidates),
                        'pause_count': len(pause_candidates)
                    }
                    cache.save_state(video_path, pipeline_state, 'segmentation')
                    
            except Exception as e:
                logger.error(f"[FAIL] Segmentation failed: {str(e)}")
                audit.log_pipeline_event("segmentation", "failed", video_path,
                                        error_message=str(e))
                raise
        
        if not all_candidates:
            logger.error("No candidate segments generated")
            audit.log_pipeline_event("pipeline", "failed", video_path,
                                    error_message="No candidate segments")
            return
        
        # Stage 5: AI Highlight Scoring
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 5: AI HIGHLIGHT SCORING")
        logger.info("=" * 80)
        
        # Check if cache is valid
        should_invalidate_cache = cache.should_invalidate_ai_scoring(video_path, config['model'], pipeline_state)
        should_skip_scoring = (
            use_cache and 
            cache.has_completed_stage(pipeline_state, 'ai_scoring') and
            not should_invalidate_cache
        )
        
        if should_skip_scoring:
            # Load cached scores
            scored_segments = cache.get_stage_result(pipeline_state, 'ai_scoring', 'scored_segments')
            logger.info(f"[OK] SKIPPED (using cached result): {len(scored_segments)} scored segments")
            
            # Additional validation: check if all cached scores are 0
            if scored_segments:
                all_zero = all(
                    seg.get("overall_score", 0) == 0 and seg.get("final_score", 0) == 0
                    for seg in scored_segments
                )
                if all_zero:
                    logger.warning("Cached scores are all 0 - this should have been caught by cache invalidation")
                    logger.warning("Force re-scoring despite cache...")
                    cache_hit = False
                    should_skip_scoring = False
                else:
                    cache_hit = True
            else:
                cache_hit = True
        
        if not should_skip_scoring:
            cache_hit = False
            
            # Log reason for re-scoring
            if not use_cache:
                logger.info("Cache disabled via --no-cache flag")
            elif should_invalidate_cache:
                logger.info("Re-running AI scoring due to config changes")
            
            audit.log_pipeline_event("ai_scoring", "started", video_path)
            
            try:
                scored_segments = score_segments(all_candidates, config['model'])
                logger.info(f"[OK] Scored segments: {len(scored_segments)}")
                
                audit.log_pipeline_event("ai_scoring", "completed", video_path,
                                        {"scored": len(scored_segments)})
                
                # Save to cache
                if use_cache:
                    pipeline_state['ai_scoring'] = {
                        'completed': True,
                        'scored_segments': scored_segments
                    }
                    cache.save_state(video_path, pipeline_state, 'ai_scoring', config=config['model'])
                    
            except Exception as e:
                logger.error(f"[FAIL] AI scoring failed: {str(e)}")
                audit.log_pipeline_event("ai_scoring", "failed", video_path,
                                        error_message=str(e))
                raise
        
        # Filter by minimum score threshold
        min_score_threshold = config['model'].get('min_score_threshold', 6.0)
        
        logger.info("=" * 80)
        logger.info(f"FILTERING WITH THRESHOLD: {min_score_threshold}")
        logger.info("=" * 80)
        
        high_quality_segments = [
            seg for seg in scored_segments 
            if seg.get('overall_score', 0) >= min_score_threshold
        ]
        
        logger.info(f"[OK] High-quality segments (score >= {min_score_threshold}): {len(high_quality_segments)}")
        
        
        if not high_quality_segments:
            logger.info("=" * 80)
            logger.warning("NO HIGH-QUALITY SEGMENTS FOUND")
            logger.info("=" * 80)
            logger.warning(f"Current threshold: {min_score_threshold}")
            
            # Show score distribution
            if scored_segments:
                scores = [s.get("overall_score", 0) for s in scored_segments]
                logger.warning(f"Score distribution:")
                logger.warning(f"  Max: {max(scores):.1f}")
                logger.warning(f"  Avg: {sum(scores)/len(scores):.1f}")
                logger.warning(f"  Min: {min(scores):.1f}")
                
                # Extra warning if all scores are 0
                if max(scores) == 0:
                    logger.warning("")
                    logger.warning("All scores are 0! This indicates a problem with AI scoring:")
                    logger.warning("  - Verify GITHUB_TOKEN (or AI API key) environment variable is set and valid")
                    logger.warning("  - Check API key has correct permissions for the model endpoint")
                    logger.warning("  - Review logs above for API or JSON parsing errors")
                    logger.warning("")
            
            logger.warning("Suggestions:")
            if scored_segments and max(scores) == 0:
                logger.warning("  1. Fix the AI scoring issue above (API key, permissions, etc.)")
                logger.warning("  2. Use --no-cache to force complete re-processing")
            else:
                logger.warning("  1. Lower min_score_threshold in config/model.yaml")
                logger.warning("     (Cache will auto-invalidate and re-score)")
                logger.warning("  2. Use --no-cache to force complete re-processing")
            logger.info("=" * 80)
            
            audit.log_pipeline_event("pipeline", "completed", video_path,
                                    {"clips": 0, "reason": "No high-quality segments"})
            return
        
        # Stage 6: Clip Validation & Deduplication
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 6: CLIP VALIDATION & DEDUPLICATION")
        logger.info("=" * 80)
        audit.log_pipeline_event("validation", "started", video_path)
        
        try:
            # Remove overlapping clips
            non_overlapping = remove_overlapping_clips(high_quality_segments)
            logger.info(f"[OK] Non-overlapping clips: {len(non_overlapping)}")
            
            # Deduplicate
            unique_clips = deduplicate_clips(non_overlapping)
            logger.info(f"[OK] Unique clips: {len(unique_clips)}")
            
            audit.log_pipeline_event("validation", "completed", video_path,
                                    {"validated_clips": len(unique_clips)})
        except Exception as e:
            logger.error(f"[FAIL] Validation failed: {str(e)}")
            audit.log_pipeline_event("validation", "failed", video_path,
                                    error_message=str(e))
            raise
        
        if not unique_clips:
            logger.warning("No clips remaining after validation")
            return
        
        # Stage 7: Clip Extraction
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 7: CLIP EXTRACTION")
        logger.info("=" * 80)
        audit.log_pipeline_event("extraction", "started", video_path)
        
        try:
            extracted_clips = extract_clips(video_path, unique_clips, clips_dir)
            logger.info(f"[OK] Extracted clips: {len(extracted_clips)}")
            
            # Log each clip
            for clip in extracted_clips:
                audit.log_clip(clip)
            
            audit.log_pipeline_event("extraction", "completed", video_path,
                                    {"extracted": len(extracted_clips)})
        except Exception as e:
            logger.error(f"[FAIL] Extraction failed: {str(e)}")
            audit.log_pipeline_event("extraction", "failed", video_path,
                                    error_message=str(e))
            raise
        
        if not extracted_clips:
            logger.error("No clips were extracted")
            return
        
        # Stage 8: Metadata Generation
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 8: METADATA GENERATION")
        logger.info("=" * 80)
        audit.log_pipeline_event("metadata", "started", video_path)
        
        try:
            platforms = ["TikTok", "Instagram", "YouTube"]
            
            for clip in extracted_clips:
                # Generate captions
                captions = generate_captions(clip, platforms)
                clip['captions'] = captions
                
                # Generate hashtags
                hashtags = generate_hashtags(clip, platforms)
                clip['hashtags'] = hashtags
                
                logger.info(f"[OK] Generated metadata for {clip['clip_id']}")
            
            audit.log_pipeline_event("metadata", "completed", video_path,
                                    {"clips_with_metadata": len(extracted_clips)})
        except Exception as e:
            logger.error(f"[FAIL] Metadata generation failed: {str(e)}")
            audit.log_pipeline_event("metadata", "failed", video_path,
                                    error_message=str(e))
            raise
        
        # Stage 9: Scheduling
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 9: UPLOAD SCHEDULING")
        logger.info("=" * 80)
        audit.log_pipeline_event("scheduling", "started", video_path)
        
        try:
            queue = UploadQueue(config['rate_limits'])
            platforms = ["TikTok", "Instagram", "YouTube"]
            
            scheduled_tasks = queue.schedule_clips(extracted_clips, platforms)
            logger.info(f"[OK] Scheduled {len(scheduled_tasks)} upload tasks")
            
            audit.log_pipeline_event("scheduling", "completed", video_path,
                                    {"scheduled_tasks": len(scheduled_tasks)})
        except Exception as e:
            logger.error(f"[FAIL] Scheduling failed: {str(e)}")
            audit.log_pipeline_event("scheduling", "failed", video_path,
                                    error_message=str(e))
            raise
        
        # Stage 10: Platform Uploads
        logger.info("\n" + "=" * 80)
        logger.info("STAGE 10: PLATFORM UPLOADS")
        logger.info("=" * 80)
        audit.log_pipeline_event("uploads", "started", video_path)
        
        upload_credentials = {
            "TikTok": {},
            "Instagram": {},
            "YouTube": {}
        }
        
        successful_uploads = 0
        failed_uploads = 0
        
        for task in scheduled_tasks:
            clip = task['clip']
            platform = task['platform']
            clip_id = clip['clip_id']
            
            logger.info(f"\nUploading {clip_id} to {platform}...")
            
            # Check if upload is allowed (rate limiting)
            if not queue.can_upload(platform):
                logger.info(f"Rate limit reached for {platform}, skipping for now")
                audit.log_upload_event(clip_id, platform, "rate_limited")
                continue
            
            try:
                caption = clip['captions'].get(platform, "")
                hashtags = clip['hashtags'].get(platform, [])
                video_file = clip['file_path']
                
                upload_id = None
                
                if platform == "TikTok":
                    upload_id = upload_to_tiktok(
                        video_file, caption, hashtags, upload_credentials["TikTok"]
                    )
                elif platform == "Instagram":
                    upload_id = upload_to_instagram(
                        video_file, caption, hashtags, upload_credentials["Instagram"]
                    )
                elif platform == "YouTube":
                    upload_id = upload_to_youtube(
                        video_file, caption, hashtags, upload_credentials["YouTube"]
                    )
                
                if upload_id:
                    logger.info(f"[OK] Upload successful: {upload_id}")
                    queue.record_upload(platform, clip_id, success=True)
                    audit.log_upload_event(clip_id, platform, "success", upload_id)
                    successful_uploads += 1
                else:
                    logger.warning(f"[FAIL] Upload failed (no ID returned)")
                    queue.record_upload(platform, clip_id, success=False)
                    audit.log_upload_event(clip_id, platform, "failed")
                    failed_uploads += 1
                
            except Exception as e:
                logger.error(f"[FAIL] Upload error: {str(e)}")
                queue.record_upload(platform, clip_id, success=False)
                audit.log_upload_event(clip_id, platform, "failed", error_message=str(e))
                failed_uploads += 1
        
        audit.log_pipeline_event("uploads", "completed", video_path,
                                {"successful": successful_uploads,
                                 "failed": failed_uploads})
        
        # Pipeline Summary
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Input video: {video_path}")
        logger.info(f"Clips generated: {len(extracted_clips)}")
        logger.info(f"Upload tasks scheduled: {len(scheduled_tasks)}")
        logger.info(f"Successful uploads: {successful_uploads}")
        logger.info(f"Failed uploads: {failed_uploads}")
        logger.info(f"Clips directory: {clips_dir}")
        logger.info(f"Audit database: {audit.db_path}")
        logger.info("=" * 80)
        
        audit.log_pipeline_event("pipeline", "completed", video_path,
                                {"clips": len(extracted_clips),
                                 "uploads": successful_uploads})
        
    except Exception as e:
        logger.error(f"\nPipeline failed: {str(e)}")
        audit.log_pipeline_event("pipeline", "failed", video_path,
                                error_message=str(e))
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Automated Short-Form Content Clipping & Distribution System'
    )
    parser.add_argument(
        'video_path',
        help='Path to input video file'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='Output directory (default: output)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching and force full reprocessing'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        run_pipeline(args.video_path, args.output, use_cache=not args.no_cache)
    except KeyboardInterrupt:
        logger.info("\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
