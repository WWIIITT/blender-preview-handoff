# Blender Preview Handoff

A Codex skill that turns each creative update into a versioned, verified local preview webpage.

Review Blender previz, depth videos, images, storyboards, scripts, and prompts in one place. The skill packages existing deliverables; it does not render Blender or generate media.

## What it does

- Preserves delivered versions and records what changed.
- Shows images, native video/audio players, copyable prompts, and source downloads.
- Separates local file readiness, browser verification, Canvas sync, and final video acceptance.
- Checks paths and playback; includes a loopback-only server with byte-range support for seeking.
- Uses only explicitly selected files. No automatic uploads, paid generation, or public hosting.

## Install in Codex

Requires Python 3.9+ for the included helpers. No Python packages are required to build or serve previews.

```sh
git clone https://github.com/WWIIITT/blender-preview-handoff.git ~/.codex/skills/blender-preview-handoff
```

If that folder already exists, inspect it before updating; do not overwrite local changes. Refresh the skill list or start a new chat if the new skill is not yet visible.

## Invoke

```text
Use $blender-preview-handoff after each substantive creative update in this project.
Create and verify a versioned preview webpage, and give me the preview link.
```

中文：

```text
使用 $blender-preview-handoff。以后这个项目每次创作更新完成后，
整理素材、标明修改与同步状态，并提供经过验证的预览网页。
```

This is a task workflow, not an unconditional hook across all chats. The skill instructions and generated review UI currently use Simplified Chinese; the skill can be invoked in English.

## Build and serve

See [manifest format](references/manifest.md) for the selected-file JSON schema.

```sh
python3 scripts/preview.py build /path/to/manifest.json --out /path/to/reviews/v2
python3 scripts/preview.py serve /path/to/reviews --port 8768
```

Open `http://127.0.0.1:8768/v2/index.html`. Keep the server running while reviewing. This address works on the host computer only; it is not a public share link. An existing output directory is rejected to prevent accidental overwrites.

The generated package contains `index.html`, `preview-manifest.json`, and selected files under `media/`. Browser playback and visual correctness still need to be checked: metadata loading alone is not proof that a video plays correctly.

## Validate

```sh
python3 scripts/test_preview.py
```

Tests cover packaging, text escaping, missing inputs, overwrite protection, HTTP/HEAD, byte ranges, and preventing symlink escape from the server root.

## Files

- [SKILL.md](SKILL.md): workflow and verification requirements.
- [agents/openai.yaml](agents/openai.yaml): Codex display metadata.
- [references/manifest.md](references/manifest.md): input format and serving guidance.
- [scripts/preview.py](scripts/preview.py): standard-library builder and local server.
- [scripts/test_preview.py](scripts/test_preview.py): focused regression checks.

Only the reusable skill and tools belong in this repository. Keep private media, credentials, project deliverables, and machine-specific manifests outside it.
