import { describe, expect, it } from "vitest";
import { canRedo, canUndo, createUndoRedo, pushSnapshot, redo, undo } from "../store/undoRedo";
import type { FlowSnapshot } from "../types/flow";

function snap(id: string): FlowSnapshot {
  return {
    nodes: [{ id, position: { x: 0, y: 0 }, data: {}, type: "note" } as any],
    edges: [],
    viewport: { x: 0, y: 0, zoom: 1 }
  };
}

describe("undo/redo", () => {
  it("pushSnapshot adds to past and clears future", () => {
    let h = createUndoRedo(10);
    const before = snap("a");
    const after = snap("b");

    h = pushSnapshot(h, after, before);
    expect(canUndo(h)).toBe(true);
    expect(canRedo(h)).toBe(false);
  });

  it("undo returns past snapshot and pushes current to future", () => {
    let h = createUndoRedo(10);
    const before = snap("a");
    const after = snap("b");

    h = pushSnapshot(h, after, before);
    const res = undo(h, after);
    expect(res.snapshot?.nodes[0].id).toBe("a");
    expect(res.h.future.length).toBe(1);
  });

  it("redo returns future snapshot", () => {
    let h = createUndoRedo(10);
    const before = snap("a");
    const after = snap("b");

    h = pushSnapshot(h, after, before);
    const u = undo(h, after);
    const r = redo(u.h, before);

    expect(r.snapshot?.nodes[0].id).toBe("b");
  });
});
