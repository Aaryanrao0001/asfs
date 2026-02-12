"""
Narrative arc detection for mini-stories within clips.

Detects: hook → tension → payoff patterns
Uses sliding windows (30-90s) to find complete arcs.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NarrativeArc:
    """Represents a narrative arc within the transcript."""
    start: float
    end: float
    duration: float
    hook_text: str
    tension_text: str
    payoff_text: str
    arc_score: float
    has_complete_arc: bool


# Hook indicators (beginning of story)
HOOK_INDICATORS = [
    'so', 'once', 'imagine', 'picture this', 'story', 'remember when',
    'let me tell you', 'this happened', 'i was', 'we were'
]

# Tension indicators (conflict/problem)
TENSION_INDICATORS = [
    'but', 'however', 'then', 'suddenly', 'problem', 'issue', 'challenge',
    'difficulty', 'until', 'except', 'unfortunately', 'wrong', 'failed'
]

# Payoff indicators (resolution/lesson)
PAYOFF_INDICATORS = [
    'finally', 'eventually', 'turns out', 'realized', 'learned', 'discovered',
    'solution', 'answer', 'thats when', 'thats why', 'so now', 'result'
]


class NarrativeArcDetector:
    """
    Detects narrative mini-arcs in transcript segments.
    
    Looks for hook → tension → payoff patterns that create
    engaging story-like structures.
    """
    
    def __init__(
        self,
        min_window: float = 30.0,
        max_window: float = 90.0,
        overlap: float = 15.0
    ):
        """
        Initialize narrative arc detector.
        
        Args:
            min_window: Minimum arc duration in seconds
            max_window: Maximum arc duration in seconds
            overlap: Overlap between sliding windows
        """
        self.min_window = min_window
        self.max_window = max_window
        self.overlap = overlap
        
        logger.info(
            f"Narrative arc detector initialized "
            f"(window: {min_window}-{max_window}s, overlap: {overlap}s)"
        )
    
    def _has_pattern(self, text: str, patterns: List[str]) -> bool:
        """Check if text contains any pattern from list."""
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in patterns)
    
    def _extract_window_text(
        self,
        segments: List[Dict],
        start_time: float,
        end_time: float
    ) -> str:
        """Extract text from segments within time window."""
        window_text = []
        for seg in segments:
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            
            # Check if segment overlaps with window
            if seg_start < end_time and seg_end > start_time:
                window_text.append(seg.get('text', ''))
        
        return ' '.join(window_text)
    
    def _analyze_window_for_arc(
        self,
        segments: List[Dict],
        start_time: float,
        end_time: float
    ) -> Optional[NarrativeArc]:
        """
        Analyze a time window for narrative arc.
        
        Args:
            segments: Transcript segments
            start_time: Window start time
            end_time: Window end time
            
        Returns:
            NarrativeArc if found, None otherwise
        """
        duration = end_time - start_time
        
        # Divide window into thirds for hook/tension/payoff
        third = duration / 3
        
        hook_end = start_time + third
        tension_end = hook_end + third
        payoff_end = end_time
        
        # Extract text for each section
        hook_text = self._extract_window_text(segments, start_time, hook_end)
        tension_text = self._extract_window_text(segments, hook_end, tension_end)
        payoff_text = self._extract_window_text(segments, tension_end, payoff_end)
        
        # Check for arc indicators in each section
        has_hook = self._has_pattern(hook_text, HOOK_INDICATORS)
        has_tension = self._has_pattern(tension_text, TENSION_INDICATORS)
        has_payoff = self._has_pattern(payoff_text, PAYOFF_INDICATORS)
        
        # Calculate arc score
        arc_score = 0.0
        if has_hook:
            arc_score += 3.0
        if has_tension:
            arc_score += 4.0  # Tension most important
        if has_payoff:
            arc_score += 3.0
        
        has_complete_arc = has_hook and has_tension and has_payoff
        
        # Only return if at least 2/3 components present
        if arc_score >= 6.0:
            return NarrativeArc(
                start=start_time,
                end=end_time,
                duration=duration,
                hook_text=hook_text[:100],  # Truncate for readability
                tension_text=tension_text[:100],
                payoff_text=payoff_text[:100],
                arc_score=arc_score,
                has_complete_arc=has_complete_arc
            )
        
        return None
    
    def detect_arcs(self, segments: List[Dict]) -> List[NarrativeArc]:
        """
        Detect all narrative arcs in transcript using sliding windows.
        
        Args:
            segments: List of transcript segments with start/end times
            
        Returns:
            List of detected NarrativeArc objects
        """
        if not segments:
            return []
        
        # Get transcript duration
        first_start = segments[0].get('start', 0)
        last_end = segments[-1].get('end', 0)
        total_duration = last_end - first_start
        
        arcs = []
        current_start = first_start
        
        # Slide window across transcript
        while current_start < last_end:
            # Try different window sizes
            for window_size in [self.max_window, 60.0, self.min_window]:
                current_end = min(current_start + window_size, last_end)
                
                # Skip if window too small
                if (current_end - current_start) < self.min_window:
                    continue
                
                arc = self._analyze_window_for_arc(segments, current_start, current_end)
                if arc:
                    arcs.append(arc)
                    # Move past this arc to avoid too much overlap
                    current_start = arc.end - self.overlap
                    break
            else:
                # No arc found, move window forward
                current_start += self.overlap
        
        # Sort by score and remove overlaps (keep best)
        arcs.sort(key=lambda x: x.arc_score, reverse=True)
        filtered_arcs = self._remove_overlapping_arcs(arcs)
        
        logger.info(
            f"Detected {len(filtered_arcs)} narrative arcs "
            f"(complete: {sum(1 for a in filtered_arcs if a.has_complete_arc)})"
        )
        
        return filtered_arcs
    
    def _remove_overlapping_arcs(self, arcs: List[NarrativeArc]) -> List[NarrativeArc]:
        """
        Remove overlapping arcs, keeping higher scoring ones.
        
        Args:
            arcs: List of arcs sorted by score (descending)
            
        Returns:
            Filtered list without overlaps
        """
        if not arcs:
            return []
        
        filtered = [arcs[0]]
        
        for arc in arcs[1:]:
            # Check if this arc overlaps with any kept arc
            overlaps = False
            for kept_arc in filtered:
                # Check for time overlap
                if not (arc.end <= kept_arc.start or arc.start >= kept_arc.end):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered.append(arc)
        
        return filtered
    
    def enhance_candidates_with_arcs(
        self,
        candidates: List[Dict],
        segments: List[Dict]
    ) -> List[Dict]:
        """
        Enhance candidate clips with narrative arc information.
        
        Args:
            candidates: List of candidate clips
            segments: Transcript segments
            
        Returns:
            Candidates with arc_score and has_arc fields added
        """
        # Detect all arcs
        arcs = self.detect_arcs(segments)
        
        # Match candidates to arcs
        for candidate in candidates:
            clip_start = candidate.get('start', 0)
            clip_end = candidate.get('end', 0)
            
            # Find best matching arc
            best_arc = None
            best_overlap = 0.0
            
            for arc in arcs:
                # Calculate overlap
                overlap_start = max(clip_start, arc.start)
                overlap_end = min(clip_end, arc.end)
                
                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    clip_duration = clip_end - clip_start
                    overlap_ratio = overlap_duration / clip_duration
                    
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_arc = arc
            
            # Enhance candidate
            if best_arc and best_overlap > 0.5:  # At least 50% overlap
                candidate['has_narrative_arc'] = True
                candidate['arc_score'] = best_arc.arc_score
                candidate['arc_complete'] = best_arc.has_complete_arc
                candidate['arc_overlap'] = best_overlap
            else:
                candidate['has_narrative_arc'] = False
                candidate['arc_score'] = 0.0
                candidate['arc_complete'] = False
                candidate['arc_overlap'] = 0.0
        
        return candidates
