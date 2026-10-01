# Troubleshooting

## React Flow renders blank

Checklist:
- Did you import `@xyflow/react/dist/style.css`?
- Does the ReactFlow parent container have a non-zero width AND height?

## Edges don't appear

Checklist:
- Verify each edge `source` and `target` match existing node ids
- Ensure your custom edge returns a BaseEdge path
- If using conditional rendering for edges, ensure the edge type is registered

## Undo feels "too granular" during drag

Fix:
- Do not record history on pixel-by-pixel drag updates
- Record a single snapshot on drag end

## Persistence breaks after schema changes

Fix:
- version your persisted store slice
- implement a migrate function if you change the persisted structure
- consider clearing localStorage for development resets
