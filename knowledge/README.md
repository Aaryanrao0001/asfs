# Knowledge Directory

This directory stores self-healing selector intelligence data collected during automation runs.

## Purpose

The automation system logs UI element variants and selector patterns to enable:
- Self-healing selector logic
- Adaptive selector priority ranking
- Historical tracking of UI changes
- Debugging and troubleshooting

## Files

### instagram_menu_variants.json
Logs Instagram Create menu items captured during automation runs, including:
- Menu item text
- ARIA labels
- SVG ARIA labels
- Item order in the menu

This data helps the system adapt to Instagram's A/B testing and UI changes.

## Data Retention

- JSON data files are automatically maintained by the automation system
- Latest 50 entries are kept for each file
- Timestamped entries allow historical analysis
- JSON data files (*.json) are excluded from git commits via .gitignore, but directory structure and documentation are committed

## Privacy

These files contain only UI metadata (button labels, menu structure) and no user data or credentials.
