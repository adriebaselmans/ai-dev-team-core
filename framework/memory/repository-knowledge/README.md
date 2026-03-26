# Repository Knowledge Store

Use this directory for compact, durable knowledge about repositories that the AI team has analyzed.

## Purpose
- Avoid repeated rediscovery of the same repository.
- Give requirements, architecture, development, review, and testing roles grounded repo context.
- Keep repository knowledge separate from project-wide memory.

## Layout
- `index.md`: inventory of analyzed repositories and their briefs.
- `<repo-slug>/brief.md`: compact human-readable repository brief.
- `<repo-slug>/facts.json`: machine-readable repo facts for later retrieval or tooling.

## Rules
- Keep entries concise and evidence-based.
- Include source path or URL and revision when available.
- Refresh the entry when repo truth changes materially.
- Record uncertainty explicitly.
