# Contributing to Automated Short-Form Content Clipping System

Thank you for your interest in contributing!

## Development Setup

1. Fork and clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install FFmpeg (system dependency)
4. Copy `.env.example` to `.env` and configure

## Code Quality Standards

- **No placeholders**: All code must be fully implemented
- **No TODOs**: Either implement or create an issue
- **Type hints**: Use type annotations for function parameters
- **Docstrings**: Document all public functions and classes
- **Error handling**: All exceptions must be caught and logged
- **Testing**: Add tests for new features

## Project Structure

- `ingest/` - Video normalization
- `transcript/` - Speech-to-text
- `segmenter/` - Candidate generation
- `ai/` - Highlight scoring
- `validator/` - Deduplication
- `clipper/` - Video extraction
- `metadata/` - Caption/hashtag generation
- `scheduler/` - Upload queue management
- `uploaders/` - Platform APIs
- `audit/` - Logging system

## Adding New Features

### New Platform Support

1. Create `uploaders/new_platform.py`
2. Implement `upload_to_platform(video_path, caption, hashtags, credentials)`
3. Add configuration to `config/platforms.json`
4. Update rate limits in `config/rate_limits.json`
5. Add to platform list in `main.py`

### New Segmentation Strategy

1. Create `segmenter/new_strategy.py`
2. Implement function that returns list of candidate segments
3. Add to `segmenter/__init__.py`
4. Call from `main.py` pipeline

### Improving AI Prompts

Edit `ai/prompt.txt` to modify scoring criteria

## Testing

Run the verification script:
```bash
python verify_structure.py
```

Test imports:
```bash
python -c "from ingest import normalize_video; print('OK')"
```

## Pull Request Process

1. Create a feature branch
2. Make your changes
3. Ensure all files are non-empty and functional
4. Update documentation if needed
5. Submit PR with clear description

## Code Review

PRs will be reviewed for:
- Completeness (no placeholders)
- Code quality
- Documentation
- Security best practices
- Performance impact

## Questions?

Open an issue for discussion before implementing major changes.
