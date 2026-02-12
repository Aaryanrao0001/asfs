#!/usr/bin/env python3
"""
Unit tests for enhanced viral detection modules.

Tests:
1. Emotion analysis
2. Transcript scoring
3. Hook detection
4. Narrative arc detection
5. Psychological scoring
"""

import unittest
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from virality import (
    EmotionAnalyzer,
    TranscriptScorer,
    HookAnalyzer,
    NarrativeArcDetector,
    PsychologicalScorer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestEmotionAnalyzer(unittest.TestCase):
    """Test emotion analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = EmotionAnalyzer()
    
    def test_emotion_analysis_viral_triggers(self):
        """Test detection of viral trigger words."""
        text = "Nobody told me this shocking secret about money"
        analysis = self.analyzer.analyze_text(text)
        
        self.assertIn('viral_triggers', analysis)
        self.assertGreater(len(analysis['viral_triggers']), 0)
        self.assertGreater(analysis['viral_trigger_score'], 0)
    
    def test_emotion_density(self):
        """Test emotion density calculation."""
        # High emotion text
        high_emotion = "I'm shocked and angry! This is insane and unbelievable!"
        density_high = self.analyzer.get_emotion_density(high_emotion)
        
        # Low emotion text
        low_emotion = "The meeting is scheduled for tomorrow at 3pm."
        density_low = self.analyzer.get_emotion_density(low_emotion)
        
        self.assertGreater(density_high, density_low)
    
    def test_filler_word_detection(self):
        """Test filler word detection."""
        text_with_fillers = "Um, like, you know, it's basically pretty good"
        count, found = self.analyzer.detect_filler_words(text_with_fillers)
        
        self.assertGreater(count, 0)
        self.assertGreater(len(found), 0)


class TestTranscriptScorer(unittest.TestCase):
    """Test transcript sentence scoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = TranscriptScorer()
    
    def test_shock_word_scoring(self):
        """Test scoring of shock words."""
        shock_text = "I can't believe this crazy, insane thing happened"
        score = self.scorer.score_sentence(shock_text)
        
        self.assertGreater(score.shock_score, 0)
        self.assertGreater(score.overall_score, 0)
    
    def test_hook_pattern_scoring(self):
        """Test scoring of hook patterns."""
        hook_text = "Wait, you won't believe what happened next"
        score = self.scorer.score_sentence(hook_text)
        
        self.assertGreater(score.hook_score, 0)
    
    def test_numeric_pattern_scoring(self):
        """Test scoring of numeric specifics."""
        numeric_text = "I made $10,000 in 30 days using this method"
        score = self.scorer.score_sentence(numeric_text)
        
        self.assertGreater(score.numeric_score, 0)
    
    def test_high_scoring_sentences(self):
        """Test extraction of high-scoring sentences."""
        text = """
        Wait, this is shocking news. 
        The meeting was scheduled. 
        Nobody tells you this secret about success.
        I went to the store.
        """
        high_scores = self.scorer.get_high_scoring_sentences(text, threshold=1.0)
        
        # Should find at least 2 high-scoring sentences
        self.assertGreaterEqual(len(high_scores), 2)


class TestHookAnalyzer(unittest.TestCase):
    """Test hook quality analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = HookAnalyzer()
    
    def test_strong_hook(self):
        """Test detection of strong hook."""
        strong_hook = "Nobody tells you this shocking truth about money"
        analysis = self.analyzer.analyze_hook(strong_hook)
        
        self.assertTrue(analysis['has_strong_opening'])
        self.assertGreater(analysis['hook_score'], 6.0)
        self.assertTrue(analysis['passes_threshold'])
    
    def test_weak_hook_greeting(self):
        """Test rejection of greeting-based hooks."""
        weak_hook = "Hey guys, welcome back to my channel"
        analysis = self.analyzer.analyze_hook(weak_hook)
        
        self.assertTrue(analysis['has_death_signal'])
        self.assertLess(analysis['hook_score'], 6.0)
        self.assertFalse(analysis['passes_threshold'])
    
    def test_hook_with_fillers(self):
        """Test penalty for filler words."""
        filler_hook = "Um, like, you know, this is interesting"
        analysis = self.analyzer.analyze_hook(filler_hook)
        
        self.assertGreater(analysis['filler_count'], 0)
        self.assertIn('filler', ' '.join(analysis['issues']).lower())


class TestNarrativeArcDetector(unittest.TestCase):
    """Test narrative arc detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = NarrativeArcDetector(
            min_window=10.0,
            max_window=30.0,
            overlap=5.0
        )
    
    def test_arc_detection(self):
        """Test detection of narrative arcs."""
        # Create mock segments with narrative structure
        segments = [
            {'start': 0, 'end': 5, 'text': 'So this happened to me yesterday'},
            {'start': 5, 'end': 10, 'text': 'But then I realized something was wrong'},
            {'start': 10, 'end': 15, 'text': 'Finally I discovered the solution'},
            {'start': 15, 'end': 20, 'text': 'And that is the answer'}
        ]
        
        arcs = self.detector.detect_arcs(segments)
        
        # Should detect at least one arc
        self.assertGreaterEqual(len(arcs), 1)
        
        if arcs:
            arc = arcs[0]
            self.assertGreater(arc.arc_score, 0)
    
    def test_enhance_candidates(self):
        """Test enhancement of candidates with arc info."""
        segments = [
            {'start': 0, 'end': 5, 'text': 'So this story begins'},
            {'start': 5, 'end': 10, 'text': 'But there was a problem'},
            {'start': 10, 'end': 15, 'text': 'Finally we found the solution'}
        ]
        
        candidates = [
            {'start': 0, 'end': 15, 'text': 'full story', 'duration': 15}
        ]
        
        enhanced = self.detector.enhance_candidates_with_arcs(candidates, segments)
        
        self.assertEqual(len(enhanced), 1)
        self.assertIn('has_narrative_arc', enhanced[0])
        self.assertIn('arc_score', enhanced[0])


class TestPsychologicalScorer(unittest.TestCase):
    """Test psychological virality scoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = PsychologicalScorer(threshold=65.0)
    
    def test_high_virality_clip(self):
        """Test scoring of high-virality clip."""
        clip = {
            'text': "Nobody tells you this shocking secret about making $10,000. "
                   "Everyone thinks it's impossible, but here's the truth you need to know.",
            'duration': 25,
            'emotion_intensity': 8.0
        }
        
        result = self.scorer.score_clip(clip)
        
        self.assertGreater(result['psychological_score'], 50)
        self.assertGreater(result['curiosity_score'], 5.0)
        # Contrarian score may vary, just check it exists
        self.assertIn('contrarian_score', result)
    
    def test_low_virality_clip(self):
        """Test scoring of low-virality clip."""
        clip = {
            'text': "The meeting was scheduled for tomorrow at three pm.",
            'duration': 30,
            'emotion_intensity': 2.0
        }
        
        result = self.scorer.score_clip(clip)
        
        self.assertLess(result['psychological_score'], 65)
    
    def test_filtering_by_threshold(self):
        """Test filtering clips by threshold."""
        clips = [
            {
                'text': "Shocking revelation about this crazy method",
                'duration': 30,
                'emotion_intensity': 8.0
            },
            {
                'text': "Just a normal conversation",
                'duration': 30,
                'emotion_intensity': 2.0
            }
        ]
        
        filtered = self.scorer.score_and_filter_clips(clips)
        
        # Should filter out low-scoring clip
        self.assertLess(len(filtered), len(clips))


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEmotionAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestTranscriptScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestHookAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestNarrativeArcDetector))
    suite.addTests(loader.loadTestsFromTestCase(TestPsychologicalScorer))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
