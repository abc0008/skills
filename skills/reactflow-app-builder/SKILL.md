---
name: reactflow-app-builder
description: "Builds or refactors React Flow (@xyflow/react) applications: custom nodes/edges, state management, persistence, and undo/redo. Use when the task involves React Flow diagrams, node-based editors, workflow builders, graph UI scaffolding, saving/restoring flows, or adding undo/redo to a flow editor. Do not use for generic React UI work that does not involve graphs/flows."
license: MIT
compatibility: Designed for Claude apps, Claude Code, Claude Agent SDK, and Skills API code execution. No network required for core workflows; includes offline template assets.
metadata:
  author: community
  version: "1.0.0"
---

# React Flow App Builder

This Skill helps build production-quality React Flow applications by providing:

- A repeatable implementation workflow
- A working reference template app you can copy
- Deterministic helper scripts for scaffolding and validation

## Quick start workflow (copy/paste checklist)

- [ ] Confirm requirements: nodes/edges, custom nodes, persistence, undo/redo, testing
- [ ] Choose architecture: local state vs store (default: Zustand store)
- [ ] Implement core canvas (ReactFlow + handlers)
- [ ] Add custom nodes and custom edges
- [ ] Implement save/restore (local persistence + import/export JSON)
- [ ] Implement undo/redo (snapshot history + shortcuts)
- [ ] Add tests for history + serialization
- [ ] Run build and validate output

## Primary asset

A complete starter template is bundled at:

- `assets/reactflow-starter/`

Preferred approach:
1. Copy the template into the target project directory (or scaffold with the script below).
2. Rename components and node types to fit the domain.
3. Extend persistence schema and node data types.

## Scaffolding script

To copy the starter app into a destination directory:

- `node scripts/scaffold-reactflow-app.mjs --dest ./my-reactflow-app`

Then install and run in the destination folder.

## Validation script

To validate an exported flow JSON file:

- `node scripts/validate-flow-json.mjs --file ./path/to/flow.json`

Schema is shipped at:
- `references/flow.schema.json`

## Implementation rules (high leverage)

- Keep graph state in one place (single source of truth).
- Make persistence explicit (version your saved JSON).
- Avoid recording undo history for every drag pixel; commit on drag end.
- Prefer deterministic scripts for repeatable transformations (scaffold, validate).
- Be conservative with permissions and file writes; do safe path handling.

## References (open these on demand)

- React Flow patterns and gotchas: `references/reactflow-notes.md`
- API usage + script contract: `references/usage-and-api.md`
- Security/privacy posture: `references/security.md`
- Troubleshooting checklist: `references/troubleshooting.md`
