# Lumina — Multimodal Image Generation Studio

A modular Streamlit application for text-to-image generation with OpenAI, image integrity checks, downloadable outputs, and local SQLite history.

## Requirements
- Python 3.11+
- OpenAI API key with access to the configured image model
- An API account with billing enabled

## Quick start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
streamlit run app.py
```

The app loads environment variables through the process environment. For local `.env` loading, add `from dotenv import load_dotenv; load_dotenv()` near the top of `app.py` (or export the key in your shell). Never commit `.env`.

## Architecture
- `app.py`: Streamlit presentation and session state.
- `studio/providers/base.py`: provider contract.
- `studio/providers/openai_provider.py`: OpenAI Images API adapter.
- `studio/service.py`: prompt composition and Pillow integrity validation.
- `studio/config.py`: model, styles, and supported canvas presets.
- `studio/db.py`: SQLite persistence of image bytes and metadata.
- `tests/`: offline unit tests.

## Provider notes and supported controls
The adapter uses the official OpenAI Python SDK `client.images.generate` interface and the `gpt-image-2` image model. It sends `prompt`, `size`, `quality`, `output_format`, and `n`. The application deliberately exposes only settings represented in this adapter; negative prompts are translated into natural-language prompt constraints because a separate `negative_prompt` argument is not assumed. Seed is omitted because reproducibility controls are not part of this provider contract.

Canvas presets are mapped to square `1024x1024`, landscape `1536x1024`, and portrait `1024x1536`. These are explicit dimensions rather than the PDF's illustrative 1344x768 / 768x1344 values. Model support can change; verify current model-specific constraints before expanding presets. Image bytes are read from base64 response data, decoded, then verified and loaded with Pillow before persistence.

## Tests
```bash
pytest -q
```
Tests do not call the paid API. A live generation requires a valid API key, network access, model access, and available billing quota.

