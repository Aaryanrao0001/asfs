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

## Dynamic Clip Reconstruction Engine

The **Dynamic Clip Reconstruction Engine** replaces the legacy contiguous window extraction with a five-phase flow that builds non-contiguous, intelligently reordered clips from individual sentence-level units.

### Architecture Overview

```
Transcript Data
      │
      ▼
Phase 1 ─ Atomic Units          (virality/atomic_units.py)
      │   sentence-level units with timestamps, speaker, word count
      ▼
Phase 2 ─ Sentence Scoring      (virality/sentence_scorer.py)
      │   hook_score, emotional_charge, claim_strength,
      │   identity_trigger, energy_score, delivery_intensity
      ▼
Phase 3 ─ Reordering Engine     (virality/reorder_engine.py)
      │   non-contiguous combinations in three patterns:
      │   • Hook → Context → Punchline
      │   • Strong claim → Data → Stronger claim
      │   • Punchline first → Explanation → Reinforcement
      ▼
Phase 4 ─ Clip Constraints      (virality/clip_constraints.py)
      │   duration 20–60 s, top-20% hook start, high-impact ending,
      │   coherence threshold, 20–50 candidates
      ▼
Phase 5 ─ Competitive Evaluation (virality/competitive_eval.py)
      │   LLM or heuristic scoring on:
      │   scroll_stop_probability, share_trigger, debate_potential,
      │   clarity, ending_strength
      │   → top 3 candidates returned
      ▼
  Final Clips  (virality/reconstruction_engine.py orchestrates all phases)
```

### Phase 1 – Atomic Units

`build_atomic_units(transcript_data, default_speaker="speaker_0")`

- Splits each transcript segment into individual sentences.
- When word-level timestamps are present (`words` key on segments), assigns precise per-sentence start/end times from the matching word tokens.
- Falls back to proportional interpolation when word timestamps are absent.
- Supports multi-speaker transcripts via the `speaker` field on each segment.

Each unit carries: `start`, `end`, `text`, `speaker`, `word_count`, `index`.

### Phase 2 – Sentence Scoring

`score_all_units(units)` / `score_sentence_unit(unit)`

Per-sentence dimension scores (0–10):

| Dimension | What it measures |
|-----------|-----------------|
| `hook_score` | Attention-grabbing opening quality |
| `emotional_charge` | Emotional intensity / valence |
| `claim_strength` | Bold assertions, stats, specifics |
| `identity_trigger` | "you" framing / personal relevance |
| `energy_score` | Pace, exclamation marks, caps |
| `delivery_intensity` | Composite energy + emotion proxy |

All scores are persisted on each unit dict and available to later stages.

### Phase 3 – Reordering Engine

`generate_candidates(scored_units, k=5)`

Builds candidate clips by combining top-*k* units per role across three patterns. Candidates are non-contiguous (constituent sentences need not be adjacent in the original transcript).  Units are sorted back into logical order (by `index`) within each candidate so playback is coherent.

De-duplicates by constituent unit set and returns results sorted by `pattern_score` descending.

### Phase 4 – Clip Construction Constraints

`apply_clip_constraints(candidates, scored_units, ...)`

Configuration:

| Key | Default | Description |
|-----|---------|-------------|
| `min_duration` | `20.0` | Minimum clip duration (seconds) |
| `max_duration` | `60.0` | Maximum clip duration (seconds) |
| `coherence_threshold` | `0.25` | Minimum coherence score (0–1) |
| `target_min_candidates` | `20` | Minimum candidates to surface |
| `target_max_candidates` | `50` | Maximum candidates to return |

When fewer than `target_min_candidates` survive the strict filters, the duration constraint is relaxed to surface additional candidates.

Each passing candidate is annotated with `hook_score_first`, `impact_score_last`, `coherence`, and a composite `constraint_score`.

### Phase 5 – Competitive Evaluation

`competitive_evaluate(candidates, llm_scorer=None, top_n=3)`

Treats candidates as competitors.  When `llm_scorer` is provided it should be a callable `(candidates) -> candidates` that adds the five dimension scores plus `competitive_score` to each dict.  On failure (or when not provided) the module falls back to heuristic regex-based scoring.

Dimension weights:

| Dimension | Weight |
|-----------|--------|
| `scroll_stop_probability` | 30% |
| `share_trigger` | 20% |
| `clarity` | 20% |
| `debate_potential` | 15% |
| `ending_strength` | 15% |

Returns the top-3 candidates sorted by `competitive_score` descending.

### Pipeline Integration

The engine is enabled by default via `use_reconstruction_engine: true` (default) in `config/model.yaml`.  Set to `false` to revert to the legacy contiguous window extraction.

Engine-specific settings live under a dedicated `reconstruction` key in config:

```yaml
model:
  use_reconstruction_engine: true  # default

reconstruction:
  min_duration: 20.0
  max_duration: 60.0
  coherence_threshold: 0.25
  target_min_candidates: 20
  target_max_candidates: 50
  reorder_k: 5                # top-k units per role in reordering
  default_speaker: speaker_0  # fallback when transcript has no speaker labels
```

### Output Format

Each reconstructed clip is a dict compatible with the existing downstream clipper, metadata generator, and scheduler:

```python
{
    "start": 12.5,          # seconds
    "end": 48.3,            # seconds
    "duration": 35.8,
    "text": "...",
    "pattern": "hook_context_punchline",
    "pattern_score": 7.42,
    "unit_indices": [2, 5, 9],
    "is_contiguous": False,
    "competitive_score": 6.8,
    "scroll_stop_probability": 7.5,
    "share_trigger": 6.0,
    "debate_potential": 5.0,
    "clarity": 8.0,
    "ending_strength": 6.5,
    "constraint_score": 3.94,
    "hook_score_first": 8.0,
    "impact_score_last": 7.2,
    "coherence": 0.62,
}
```

---

**Version**: 3.0
**Last Updated**: 2026-02-23
