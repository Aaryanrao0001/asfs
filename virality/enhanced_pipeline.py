"""
Enhanced viral clip pipeline integrating all virality layers.

Two-stage pipeline:
1. Fast rule-based filter (bottom 80%)
2. Deep LLM + semantic scoring (top 20%)
"""

import logging
from typing import Dict, List

from virality import (
    EmotionAnalyzer,
    TranscriptScorer,
    HookAnalyzer,
    NarrativeArcDetector,
    SemanticDeduplicator,
    PsychologicalScorer
)
from virality.metadata_generator import ViralMetadataGenerator

logger = logging.getLogger(__name__)


class EnhancedViralPipeline:
    """
    Two-stage viral clip detection pipeline.
    
    Stage 1: Fast filtering using heuristics
    Stage 2: Deep analysis with LLM scoring
    """
    
    def __init__(
        self,
        transcript_segments: List[Dict],
        config: Dict = None
    ):
        """
        Initialize enhanced pipeline.
        
        Args:
            transcript_segments: Full transcript segments with timing
            config: Configuration dictionary
        """
        self.transcript_segments = transcript_segments
        self.config = config or {}
        
        # Initialize analyzers
        self.emotion_analyzer = EmotionAnalyzer()
        self.transcript_scorer = TranscriptScorer()
        self.hook_analyzer = HookAnalyzer()
        self.narrative_detector = NarrativeArcDetector()
        self.psychological_scorer = PsychologicalScorer(
            threshold=self.config.get('psychological_threshold', 65.0)
        )
        self.semantic_dedup = SemanticDeduplicator(
            similarity_threshold=self.config.get('similarity_threshold', 0.85)
        )
        self.metadata_generator = ViralMetadataGenerator()
        
        logger.info("Enhanced viral pipeline initialized")
    
    def stage1_fast_filter(self, candidates: List[Dict]) -> List[Dict]:
        """
        Stage 1: Fast rule-based filtering.
        
        Filters by:
        - Emotion density (top 15%)
        - Hook quality (first 7s)
        - Narrative arc presence
        - Duration limits
        
        Args:
            candidates: Raw candidate clips
            
        Returns:
            Filtered candidates (top ~20%)
        """
        logger.info(f"Stage 1: Fast filtering {len(candidates)} candidates")
        
        # Step 1: Emotion density scoring
        logger.info("Analyzing emotion density...")
        for candidate in candidates:
            text = candidate.get('text', '')
            emotion_analysis = self.emotion_analyzer.analyze_text(text)
            candidate['emotion_analysis'] = emotion_analysis
            candidate['emotion_density'] = self.emotion_analyzer.get_emotion_density(text)
        
        # Filter by emotion density (top 15%)
        candidates.sort(key=lambda x: x.get('emotion_density', 0), reverse=True)
        emotion_threshold_idx = int(len(candidates) * 0.15)
        emotion_filtered = candidates[:max(emotion_threshold_idx, 10)]  # At least 10
        
        logger.info(
            f"Emotion filter: {len(emotion_filtered)}/{len(candidates)} "
            f"(top 15% emotion-dense)"
        )
        
        # Step 2: Hook quality filter (first 7 seconds)
        logger.info("Analyzing hook quality...")
        min_hook_score = self.config.get('min_hook_score', 6.0)
        hook_filtered = self.hook_analyzer.filter_by_hook_quality(
            emotion_filtered,
            self.transcript_segments,
            min_hook_score=min_hook_score
        )
        
        # Step 3: Enhance with narrative arcs
        logger.info("Detecting narrative arcs...")
        arc_enhanced = self.narrative_detector.enhance_candidates_with_arcs(
            hook_filtered,
            self.transcript_segments
        )
        
        # Step 4: Duration filtering (platform-specific)
        duration_filtered = []
        for candidate in arc_enhanced:
            duration = candidate.get('duration', 0)
            # Accept 15-75s clips (covers all platforms)
            if 15 <= duration <= 75:
                duration_filtered.append(candidate)
        
        logger.info(
            f"Duration filter: {len(duration_filtered)}/{len(arc_enhanced)} "
            f"(15-75s)"
        )
        
        logger.info(
            f"Stage 1 complete: {len(duration_filtered)}/{len(candidates)} "
            f"candidates passed ({len(duration_filtered)/len(candidates)*100:.1f}%)"
        )
        
        return duration_filtered
    
    def stage2_deep_analysis(
        self,
        candidates: List[Dict],
        llm_scorer_func = None
    ) -> List[Dict]:
        """
        Stage 2: Deep analysis with psychological + LLM scoring.
        
        Args:
            candidates: Filtered candidates from Stage 1
            llm_scorer_func: Optional LLM scoring function (from ai.scorer)
            
        Returns:
            Top-scoring candidates with full analysis
        """
        logger.info(f"Stage 2: Deep analysis of {len(candidates)} candidates")
        
        # Step 1: Psychological scoring
        logger.info("Applying psychological virality model...")
        psych_scored = self.psychological_scorer.score_and_filter_clips(candidates)
        
        logger.info(
            f"Psychological filter: {len(psych_scored)}/{len(candidates)} "
            f"passed threshold"
        )
        
        # Step 2: LLM scoring (if available and enabled)
        llm_scored = psych_scored
        if llm_scorer_func and self.config.get('use_llm_scoring', True):
            logger.info("Applying LLM scoring to top candidates...")
            try:
                llm_scored = llm_scorer_func(psych_scored)
            except Exception as e:
                logger.error(f"LLM scoring failed: {e}")
                logger.info("Continuing with psychological scores only")
        
        # Step 3: Semantic deduplication
        logger.info("Semantic deduplication...")
        deduplicated = self.semantic_dedup.deduplicate_clips(
            llm_scored,
            score_key='psychological_score'
        )
        
        # Step 4: Generate metadata for top clips
        logger.info("Generating metadata...")
        for clip in deduplicated:
            metadata = self.metadata_generator.generate_all_metadata(clip)
            clip['viral_metadata'] = metadata
        
        # Sort by final score (psychological or LLM if available)
        if 'final_score' in deduplicated[0] if deduplicated else {}:
            deduplicated.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        else:
            deduplicated.sort(
                key=lambda x: x.get('psychological_score', 0),
                reverse=True
            )
        
        logger.info(f"Stage 2 complete: {len(deduplicated)} final candidates")
        
        return deduplicated
    
    def run_pipeline(
        self,
        candidates: List[Dict],
        llm_scorer_func = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Run full two-stage pipeline.
        
        Args:
            candidates: Raw candidate clips
            llm_scorer_func: Optional LLM scoring function
            top_n: Number of top clips to return
            
        Returns:
            Top N scored clips with full analysis
        """
        logger.info("="*60)
        logger.info("ENHANCED VIRAL DETECTION PIPELINE")
        logger.info("="*60)
        
        if not candidates:
            logger.warning("No candidates provided")
            return []
        
        # Stage 1: Fast filter
        stage1_results = self.stage1_fast_filter(candidates)
        
        if not stage1_results:
            logger.warning("No candidates passed Stage 1 filtering")
            return []
        
        # Stage 2: Deep analysis
        stage2_results = self.stage2_deep_analysis(
            stage1_results,
            llm_scorer_func=llm_scorer_func
        )
        
        # Return top N
        top_clips = stage2_results[:top_n]
        
        logger.info("="*60)
        logger.info(f"PIPELINE COMPLETE: Top {len(top_clips)} clips selected")
        logger.info("="*60)
        
        # Log summary of top clips
        for i, clip in enumerate(top_clips, 1):
            psych_score = clip.get('psychological_score', 0)
            final_score = clip.get('final_score', psych_score)
            start = clip.get('start', 0)
            
            logger.info(
                f"{i}. Start: {start:.1f}s | "
                f"Psych: {psych_score:.1f} | "
                f"Final: {final_score:.1f}"
            )
        
        return top_clips
    
    def get_pipeline_stats(self, candidates: List[Dict]) -> Dict:
        """
        Get statistics about candidates without full processing.
        
        Args:
            candidates: Candidate clips
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_candidates': len(candidates),
            'avg_duration': 0.0,
            'emotion_stats': {},
            'hook_stats': {},
            'arc_stats': {}
        }
        
        if not candidates:
            return stats
        
        # Duration stats
        durations = [c.get('duration', 0) for c in candidates]
        stats['avg_duration'] = sum(durations) / len(durations)
        stats['min_duration'] = min(durations)
        stats['max_duration'] = max(durations)
        
        return stats
