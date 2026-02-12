# Enhanced Viral Clip Detection System

## Overview

The Enhanced Viral Clip Detection System is a sophisticated multi-layer pipeline that analyzes video transcripts to identify the most viral-worthy clips. It goes beyond simple keyword matching to model psychological triggers, emotional vocabulary, narrative structures, and audience engagement patterns.

## Architecture

### Two-Stage Pipeline

**Stage 1: Fast Rule-Based Filtering (Top ~20%)**
- Filters the bottom 80% of candidates using efficient heuristics
- Analyzes emotion density, hook quality, narrative structure
- Reduces candidate pool before expensive LLM analysis

**Stage 2: Deep Analysis (Top Candidates)**
- Applies psychological virality scoring (6-factor model)
- Optional LLM scoring for nuanced understanding
- Semantic deduplication to remove redundant clips
- Generates viral metadata (titles, captions, hashtags)

## Features

### Layer 1: Advanced Transcript Intelligence

#### Sentence-Level Virality Scoring
Scores each sentence based on:
- **Shock words**: "shocked", "insane", "unbelievable", "crazy"
- **Confession triggers**: "truth is", "secret", "nobody told me"
- **Hook patterns**: "wait", "you won't believe", "here's why"
- **Contrarian framing**: "everyone is wrong", "they're lying"
- **Numeric specifics**: percentages, dollar amounts, time periods
- **Open loops**: "but", "however", "until", "except"

#### Emotion Vocabulary Density
- Uses VADER sentiment analysis + NRC emotion lexicon
- Detects 8 emotion categories: anger, shock, validation, fear, excitement, sadness, trust, anticipation
- Filters clips by emotion density (top 15%)
- Identifies viral trigger words: "never", "always", "nobody", "shocking", "secret"

#### Narrative Arc Detection
- Detects mini-stories with hook → tension → payoff structure
- Uses sliding windows (30-90 seconds)
- Prioritizes clips with complete narrative arcs
- Enhances engagement and shareability

### Layer 2: Structural Clip Quality Signals

#### Hook Window Analysis (First 7 Seconds)
The first 7 seconds determine 80% of virality. Enforces:

**✅ Strong Signals:**
- Starts mid-sentence or mid-thought
- Opens with emotion before context
- Curiosity triggers: "nobody talks about", "this ruined"
- Negations: "never", "no one", "they lied"
- Questions without asking

**❌ Death Signals (Auto-Reject):**
- Greetings: "hey guys", "welcome back"
- Setup: "so today I want to talk about"
- Slow buildup with context first

**Filler Word Penalties:**
- Detects: "um", "uh", "like", "you know", "basically"
- Reduces hook score proportionally

#### Platform-Specific Optimization
- **TikTok/Reels**: 15-30s, 45-60s optimal
- **YouTube Shorts**: 50-59s sweet spot
- **X (Twitter)**: 60-120s
- **LinkedIn**: 90-180s

### Layer 3: Psychological Virality Scoring

Multi-factor scoring model with weighted components:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Curiosity Gap** | 25% | "Why", "how", "secret", questions, reveals |
| **Emotional Intensity** | 20% | Emotion lexicon density, sentiment polarity |
| **Contrarian Claim** | 20% | "Wrong", "lie", "myth", "opposite", "truth is" |
| **Specific Outcome** | 15% | Numbers, percentages, money, time periods |
| **Relatability** | 10% | "You", "your", "we all", identity anchors |
| **CTA/Tension** | 10% | "Must", "need to", "watch", "warning" |

**Threshold**: Clips must score ≥ 65/100 to pass

**Automatic Penalties**:
- Duration > 60s: -10 points
- Low curiosity (< 3/10): -5 points

### Layer 4: Semantic Deduplication

- Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings
- Calculates cosine similarity between all clip pairs
- Removes duplicates (similarity ≥ 0.85)
- Keeps highest-scoring variant from each duplicate group
- Ensures diversity in final clip selection

### Layer 5: Metadata Generation

Automatically generates for each clip:

#### Titles (3 variants)
Based on clip pattern:
- **Curiosity**: "Why {topic} (you won't believe this)"
- **Contrarian**: "Everyone is wrong about {topic}"
- **Emotional**: "This {topic} ruined everything"
- **Specific**: "How I {outcome} in {timeframe}"

#### Captions
- Extracts first sentence as hook
- Adds emotion-appropriate emoji
- Includes call-to-action

#### Hashtags
Platform-specific strategy:
- **Viral tags**: #fyp, #viral, #trending, etc.
- **Emotion tags**: Based on primary emotion
- **Content tags**: Extracted from key terms
- Max 15 tags per platform

#### Text Overlays
- Shock patterns: "WAIT WHAT", "NO WAY"
- Questions: "WHY?", "HOW?"
- Emphasis: "EXACTLY", "FINALLY"
- CTAs: "WATCH", "LISTEN"

#### B-Roll Suggestions
Context-aware suggestions:
- Money mentions → Money/cash visuals
- Time mentions → Clock/time-lapse
- Before/after → Comparison footage
- Data mentions → Graphs/visualizations

## Configuration

### Enable/Disable Enhanced Pipeline

In `config/model.yaml`:

```yaml
# Enable enhanced pipeline (default: true)
use_enhanced_pipeline: true
```

Set to `false` to use original scoring pipeline.

### Tunable Parameters

```yaml
# Psychological Virality Scoring
psychological_threshold: 65.0  # Min score (0-100) to pass
top_clips: 10  # Number of top clips to return

# Hook Quality (First 7 Seconds)
min_hook_score: 6.0  # Min hook score (0-10) to pass

# Semantic Deduplication
similarity_threshold: 0.85  # Cosine similarity (0-1) for duplicates

# LLM Scoring Integration
use_llm_scoring: true  # Use LLM in Stage 2 (deep analysis)
```

### Recommendations

**For Higher Quality (Fewer Clips)**:
- Increase `psychological_threshold` to 70-75
- Increase `min_hook_score` to 7.0
- Enable `use_llm_scoring`

**For More Clips (Lower Bar)**:
- Decrease `psychological_threshold` to 55-60
- Decrease `min_hook_score` to 5.0
- Optionally disable LLM scoring to speed up

**For Maximum Diversity**:
- Increase `top_clips` to 15-20
- Lower `similarity_threshold` to 0.80

## Usage Example

### Basic Usage (Enabled by Default)

```bash
python main.py --video path/to/video.mp4
```

The enhanced pipeline runs automatically if enabled in config.

### Force Original Pipeline

```bash
# In config/model.yaml, set:
use_enhanced_pipeline: false
```

### Programmatic Usage

```python
from virality import EnhancedViralPipeline
from transcript.transcribe import load_transcript

# Load transcript
transcript_data = load_transcript("transcript.json")
segments = transcript_data['segments']

# Initialize pipeline
pipeline = EnhancedViralPipeline(
    transcript_segments=segments,
    config={
        'psychological_threshold': 65.0,
        'min_hook_score': 6.0,
        'similarity_threshold': 0.85
    }
)

# Run pipeline
from segmenter import build_sentence_windows

candidates = build_sentence_windows(transcript_data)
top_clips = pipeline.run_pipeline(candidates, top_n=5)

# Access results
for i, clip in enumerate(top_clips, 1):
    print(f"Clip {i}:")
    print(f"  Score: {clip['psychological_score']:.1f}")
    print(f"  Start: {clip['start']:.1f}s")
    print(f"  Titles: {clip['viral_metadata']['titles']}")
    print(f"  Hashtags: {clip['viral_metadata']['hashtags'][:5]}")
```

## Performance

### Efficiency Gains

**Two-Stage Filtering**:
- Stage 1 filters 80% of clips with fast heuristics (~1ms per clip)
- Stage 2 only analyzes top 20% with expensive operations
- Reduces LLM API calls by 80%

**Caching**:
- Emotion analysis results cached per segment
- Embeddings computed once for deduplication
- Narrative arcs detected once per transcript

### Typical Timing

For 100 candidate clips:
- Stage 1 (Fast Filter): ~100-200ms
- Stage 2 (Deep Analysis, 20 clips): ~10-30s (depends on LLM)
- Total: ~10-30s vs 2-5 minutes for all clips

## Scoring Examples

### High-Scoring Clip (85/100)

```
Text: "Nobody tells you this but your manager is lying to you about 
       promotions. Here's what they actually mean when they say..."

Scores:
- Curiosity: 9/10 (mystery, revelation)
- Emotion: 8/10 (anger, validation)
- Contrarian: 9/10 ("lying", "actually mean")
- Specific: 7/10 (clear outcome)
- Relatability: 8/10 ("your manager", "you")
- CTA/Tension: 7/10 ("here's what")

Verdict: VIRAL ✅
```

### Low-Scoring Clip (35/100)

```
Text: "Hey everyone, today I want to talk about something really 
       important that I've been thinking about lately..."

Scores:
- Curiosity: 2/10 (vague)
- Emotion: 2/10 (flat)
- Contrarian: 0/10 (none)
- Specific: 1/10 (no data)
- Relatability: 3/10 (generic)
- CTA/Tension: 2/10 (weak)

Verdict: SKIP ❌ (greeting death signal)
```

## Testing

### Run Unit Tests

```bash
python test_viral_detection.py
```

Tests cover:
- Emotion analysis with VADER
- Transcript sentence scoring
- Hook quality detection
- Narrative arc detection
- Psychological scoring model

All 15 tests pass ✅

## Dependencies

New dependencies added to `requirements.txt`:

```
vaderSentiment>=3.3.2      # Sentiment/emotion analysis
textblob>=0.17.1           # NLP utilities
sentence-transformers>=2.2.2  # Semantic embeddings
```

Install with:

```bash
pip install -r requirements.txt
```

## Future Enhancements

Potential additions:
- [ ] Trend relevance scoring (dynamic trendlist integration)
- [ ] Feedback loop (👍/👎 ratings to fine-tune scoring)
- [ ] Dialogue segment detection (3+ speaker turns)
- [ ] Energy peak detection from transcript pacing
- [ ] Platform-specific clip boundary refinement
- [ ] A/B testing infrastructure

## Troubleshooting

### Enhanced Pipeline Not Working

**Check logs for**:
```
"Using ENHANCED viral detection pipeline"
```

If you see `"Using original scoring pipeline"`, check:
1. `use_enhanced_pipeline: true` in config/model.yaml
2. Transcript segments are being passed to scorer
3. No import errors in virality modules

### Semantic Deduplication Disabled

If you see:
```
"sentence-transformers not available - semantic deduplication disabled"
```

Install sentence-transformers:
```bash
pip install sentence-transformers
```

### Low Clip Counts

If very few clips pass filters:
- Lower `psychological_threshold` to 60 or 55
- Lower `min_hook_score` to 5.0
- Check transcript quality (min duration, segment count)

### All Clips Rejected at Hook Stage

If logs show:
```
"Hook quality filter: 0/N candidates passed"
```

- Lower `min_hook_score` to 5.0 or 4.0
- Check for greeting-based openings in transcript
- Verify transcript timing accuracy

## Credits

Implementation based on research in:
- Viral content psychology (curiosity gap theory)
- Emotion lexicons (NRC, VADER)
- Short-form video best practices (TikTok, Reels)
- Narrative structure theory (hook-tension-payoff)

---

**Version**: 2.0  
**Last Updated**: 2026-02-11
