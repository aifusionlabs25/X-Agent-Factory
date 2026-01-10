# Vision Module - Training Data

Place labeled training images here.

## Structure

```
data/
├── raw/                ← Unprocessed scraped images
├── labeled/            ← Labeled and ready for training
│   ├── healthy/
│   ├── skin_issue/
│   ├── eye_concern/
│   └── mobility_issue/
└── exports/            ← Roboflow/HuggingFace format exports
```

## Labeling Guidelines

1. One clear subject per image
2. Good lighting preferred
3. Minimum 50 images per class
4. Use consistent naming: `{class}_{index}.jpg`
