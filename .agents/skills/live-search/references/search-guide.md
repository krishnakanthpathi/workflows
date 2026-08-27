# Live Search Reference Guide

## Advanced Search Tips

### 1. Domain-Specific Searching
You can restrict your query to specific domains directly:
```bash
live-search "site:github.com nousresearch hermes"
live-search "site:docs.python.org whatsnew 3.13"
```

### 2. Filetype Filtering
Search for specific documents:
```bash
live-search "filetype:pdf machine learning survey"
```

### 3. Exact Phrase Matching
Wrap quotes inside the query:
```bash
live-search '"Claude Agent SDK" installation'
```

### 4. Programmatic Piping (with jq)
Extract only URLs from JSON mode:
```bash
live-search --json "Python 3.13 downloads" | jq -r '.results[].url'
```
