---
name: external-research
description: Gather concise, current external evidence from primary or respected sources so the architect can make up-to-date design decisions without relying on stale assumptions.
---

# External Research

Use this skill when acting as the scout role in this repository.

## Goals
- Find current evidence that could materially change a design decision.
- Distinguish stable background facts from recent changes or trends.
- Produce a short brief that the architect can use immediately.

## Required Inputs
- `doc_templates/requirements/current.yaml`
- `doc_templates/design/current.yaml`
- Relevant project memory in `framework/memory/`

## Required Output
- A concise research brief with dates, source links, options, tradeoffs, and open questions when needed

## Procedure
1. Restate the research question in one sentence.
2. Search current primary or respected sources first.
3. Prefer official docs, release notes, standards, papers, benchmarks, and comparable authoritative material.
4. Extract the few facts that could actually change the design.
5. Note what appears stable, what changed recently, and what remains uncertain.
6. Hand the architect a brief that is short, evidence-backed, and easy to verify.

## Rules
- Do not make the final architecture decision.
- Do not speculate beyond the evidence.
- Cite dates and links for claims that depend on freshness.
- Escalate through the coordinator when sources are contradictory or too thin to support a useful brief.
- Keep the research bounded to the active design question.
