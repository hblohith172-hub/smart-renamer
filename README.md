# Smart Renamer

An AI-powered image renamer that uses local Ollama models to describe images and rename them into clean,filenames.

## Features
- **AI Powered**: Uses `batiai/gemma4-26b:iq4` via Ollama `/api/generate`.
- **Smart Naming**: Converts descriptions to `snake_case` and handles collisions.
- **Safety First**: Defaults to a dry-run mode. Use `--execute` to apply changes.
- **Undo System**: Maintains `undo.json` to revert the last session with `--undo`.

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Ollama**:
   Ensure Ollama is running and pull the model:
   ```bash
   ollama pull batiai/gemma4-26b:iq4
   ```

## Usage

**Dry Run (Preview):**
```bash
python renamer.py ~/Downloads
```

**Execute Renaming:**
```bash
python renamer.py ~/Downloads --execute
```

**Undo Last Session:**
```bash
python renamer.py ~/Downloads --undo
```

## License
MIT
