import type { FlowSnapshot } from "../types/flow";

export type UndoRedoState = {
  past: FlowSnapshot[];
  future: FlowSnapshot[];
  limit: number;
};

export function createUndoRedo(limit = 50): UndoRedoState {
  return { past: [], future: [], limit };
}

function normalizeSnapshot(s: FlowSnapshot): FlowSnapshot {
  // Ensure deterministic ordering to reduce false-diff history pushes.
  const nodes = [...s.nodes].sort((a, b) => a.id.localeCompare(b.id));
  const edges = [...s.edges].sort((a, b) => a.id.localeCompare(b.id));
  return { nodes, edges, viewport: s.viewport };
}

function fingerprint(s: FlowSnapshot): string {
  const n = normalizeSnapshot(s);
  return JSON.stringify({
    nodes: n.nodes,
    edges: n.edges,
    viewport: n.viewport
  });
}

export function canUndo(h: UndoRedoState): boolean {
  return h.past.length > 0;
}

export function canRedo(h: UndoRedoState): boolean {
  return h.future.length > 0;
}

export function pushSnapshot(h: UndoRedoState, current: FlowSnapshot, prev: FlowSnapshot): UndoRedoState {
  const prevFp = fingerprint(prev);
  const curFp = fingerprint(current);
  if (prevFp === curFp) return h;

  const past = [...h.past, normalizeSnapshot(prev)];
  const trimmed = past.length > h.limit ? past.slice(past.length - h.limit) : past;
  return { past: trimmed, future: [], limit: h.limit };
}

export function undo(h: UndoRedoState, current: FlowSnapshot): { h: UndoRedoState; snapshot: FlowSnapshot | null } {
  if (!canUndo(h)) return { h, snapshot: null };
  const past = [...h.past];
  const snapshot = past.pop()!;
  const future = [normalizeSnapshot(current), ...h.future];
  return { h: { ...h, past, future }, snapshot };
}

export function redo(h: UndoRedoState, current: FlowSnapshot): { h: UndoRedoState; snapshot: FlowSnapshot | null } {
  if (!canRedo(h)) return { h, snapshot: null };
  const future = [...h.future];
  const snapshot = future.shift()!;
  const past = [...h.past, normalizeSnapshot(current)];
  return { h: { ...h, past, future }, snapshot };
}
