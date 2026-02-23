"""Virality detection modules for advanced transcript intelligence."""

from .emotion_analyzer import EmotionAnalyzer
from .transcript_scorer import TranscriptScorer
from .hook_analyzer import HookAnalyzer
from .narrative_detector import NarrativeArcDetector
from .psychological_scorer import PsychologicalScorer
from .metadata_generator import ViralMetadataGenerator
from .enhanced_pipeline import EnhancedViralPipeline

# SemanticDeduplicator requires numpy – import gracefully
try:
    from .semantic_dedup import SemanticDeduplicator
except ImportError:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "numpy not available – SemanticDeduplicator disabled"
    )
    SemanticDeduplicator = None  # type: ignore[assignment,misc]

# Dynamic Clip Reconstruction Engine (Phases 1–5)
from .atomic_units import build_atomic_units
from .sentence_scorer import score_all_units, score_sentence_unit
from .reorder_engine import generate_candidates
from .clip_constraints import apply_clip_constraints
from .competitive_eval import competitive_evaluate
from .reconstruction_engine import reconstruct_clips

__all__ = [
    'EmotionAnalyzer',
    'TranscriptScorer',
    'HookAnalyzer',
    'NarrativeArcDetector',
    'SemanticDeduplicator',
    'PsychologicalScorer',
    'ViralMetadataGenerator',
    'EnhancedViralPipeline',
    # Reconstruction Engine
    'build_atomic_units',
    'score_all_units',
    'score_sentence_unit',
    'generate_candidates',
    'apply_clip_constraints',
    'competitive_evaluate',
    'reconstruct_clips',
]
