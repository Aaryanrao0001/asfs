# CSV Metadata Import

The ASFS application now supports importing randomized metadata from CSV files. This allows you to maintain a library of titles, captions, descriptions, and tags that will be randomly selected for each upload.

## CSV Format

Your CSV file should have the following columns (all optional):

- `title` or `titles`: Video title
- `caption` or `captions`: Video caption (Instagram/TikTok)
- `description` or `descriptions`: Video description (YouTube)
- `tags` or `hashtags`: Comma-separated tags (e.g., "viral,trending,awesome")

### Example CSV

```csv
title,caption,description,tags
This is absolutely insane!,Check out this incredible moment 🔥,Watch this amazing video that will blow your mind,viral,trending,amazing
You won't believe what happened!,This is wild! 😱,The most unbelievable thing you'll see today,mindblowing,shocking,incredible
Wait for it...,Patience pays off 👀,The ending will surprise you - watch until the end!,patience,surprise,mustwatch
```

See `metadata/example_metadata.csv` for a complete example.

## Usage

1. **In the UI**: 
   - Go to the "Metadata" tab
   - Set mode to "Randomized"
   - Click "Browse..." in the "Import from CSV" section
   - Select your CSV file

2. **Combining CSV with UI fields**:
   - CSV values are merged with any values entered in the UI fields
   - This gives you flexibility to add extra options without editing the CSV

3. **How randomization works**:
   - In "Randomized" mode, the app will randomly select ONE title, ONE caption, ONE description for each upload
   - Tags are shuffled (all tags are used, but in random order)
   - This creates variety across your uploads without manual intervention

## Benefits

- **Variety**: Different metadata for each upload helps with algorithmic discovery
- **Efficiency**: Create a library once, use it for all uploads
- **A/B Testing**: Try different hooks and captions to see what performs best
- **Bulk Operations**: Upload multiple videos with varied metadata automatically

## Notes

- CSV files must be UTF-8 encoded
- Empty rows are skipped
- Column names are case-insensitive
- Tags within a cell should be comma-separated (they'll be split automatically)
- You can have as many rows as you want (more = more variety)
