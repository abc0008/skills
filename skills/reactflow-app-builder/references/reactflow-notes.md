# React Flow Notes (Practical Patterns)

This file is intentionally detailed and is meant to be opened only when needed.

## Baseline requirements

- Import the React Flow stylesheet from `@xyflow/react/dist/style.css`.
- Ensure the parent container of `<ReactFlow />` has an explicit width/height (e.g., 100vh).

## Custom nodes pattern

- Implement nodes as React components.
- Register them via `nodeTypes` on `<ReactFlow />`.
- Keep node `data` serializable if you plan to persist state.

## Custom edges pattern

- Implement edges as React components.
- Use `<BaseEdge />` plus a path generator like `getStraightPath` / `getBezierPath`.
- If you render labels, ensure `pointerEvents` behavior is intentional.

## State architecture recommendations

Start simple:
- `useNodesState` / `useEdgesState` is fine for small apps.

Scale path:
- Use a centralized store (Zustand works well) when:
  - nodes need to update global state from inside a node component
  - you have undo/redo, multi-document flows, or collaboration needs

## Persistence

Two complementary layers:
1) App persistence:
- persist nodes/edges/viewport as the "current document" in localStorage
- version your stored format and provide migration hooks

2) Import/export:
- allow downloading a JSON file (FlowDocument)
- allow uploading and validating a JSON file before applying

## Undo/redo

Snapshot-based approach is usually the fastest to implement and reason about:
- Keep history.past[], history.future[]
- Push snapshot before meaningful changes
- Avoid pushing on "selection" changes and pixel-by-pixel drag updates
- Commit a single snapshot on drag end

## Keyboard shortcuts

Common conventions:
- Ctrl/Cmd + Z => undo
- Ctrl/Cmd + Shift + Z => redo
- Ctrl/Cmd + Y => redo (optional)

## Testing

- Unit test history reducer logic (pure functions)
- Unit test serialization: export + import + validation
- UI tests can focus on:
  - adding nodes/edges updates the store
  - undo/redo restore prior states
