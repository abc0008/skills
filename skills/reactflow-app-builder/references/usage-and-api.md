# Usage and API Surface

This package provides two "APIs":

1) Node scripts (deterministic tooling)
2) The template app store/actions (for extension)

## Script: scaffold-reactflow-app.mjs

Purpose: Copy `assets/reactflow-starter/` into a destination folder.

CLI:
- `node scripts/scaffold-reactflow-app.mjs --dest <path> [--name <pkg-name>] [--force]`

Behavior:
- creates dest if missing
- copies files recursively
- updates package.json name if provided
- refuses to overwrite non-empty directories unless --force

Outputs:
- prints structured logs to stdout
- exits non-zero on failure

## Script: validate-flow-json.mjs

Purpose: Validate a FlowDocument JSON (import/export format).

CLI:
- `node scripts/validate-flow-json.mjs --file <path>`

Outputs:
- prints OK summary on success
- prints a list of validation errors on failure
- exits non-zero on failure

## Template app store API (flowStore.ts)

State:
- nodes: Node[]
- edges: Edge[]
- viewport: { x, y, zoom }
- history: { past[], future[], limit }

Actions (high-level):
- applyNodeChanges(changes)
- applyEdgeChanges(changes)
- connect(connection)
- addNoteNode()
- undo(), redo()
- exportDocument(): FlowDocument
- importDocument(doc: unknown): { ok: boolean, error?: string }
- reset()

Extension guideline:
- add new node types by:
  - creating `src/nodes/<NewNode>.tsx`
  - registering in `nodeTypes` in FlowCanvas.tsx
  - updating `add...Node()` action to create the node with correct `type` and `data`

## FlowDocument format

See: `references/flow.schema.json`

Example:
{
  "version": 1,
  "createdAt": "2026-01-01T00:00:00.000Z",
  "flow": {
    "nodes": [...],
    "edges": [...],
    "viewport": { "x": 0, "y": 0, "zoom": 1 }
  }
}
