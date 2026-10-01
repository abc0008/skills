import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type Viewport
} from "@xyflow/react";

import type { FlowDocument, FlowSnapshot } from "../types/flow";
import { canRedo, canUndo, createUndoRedo, pushSnapshot, redo, undo, type UndoRedoState } from "./undoRedo";

type StoreState = {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;

  history: UndoRedoState;

  // Internal: prevents multiple pushes in the same JS tick (e.g., node delete triggers edge+node changes).
  _historyLock: boolean;

  actions: {
    reset: () => void;

    applyNodeChanges: (changes: NodeChange[]) => void;
    applyEdgeChanges: (changes: EdgeChange[]) => void;
    connect: (connection: Connection) => void;

    setViewport: (viewport: Viewport) => void;

    addNoteNode: () => void;
    updateNodeText: (nodeId: string, text: string) => void;

    canUndo: () => boolean;
    canRedo: () => boolean;
    undo: () => void;
    redo: () => void;

    exportDocument: () => FlowDocument;
    importDocument: (doc: unknown) => { ok: boolean; error?: string };
  };
};

const INITIAL_VIEWPORT: Viewport = { x: 0, y: 0, zoom: 1 };

function nowIso(): string {
  return new Date().toISOString();
}

function snapshotFromState(s: Pick<StoreState, "nodes" | "edges" | "viewport">): FlowSnapshot {
  return {
    nodes: s.nodes,
    edges: s.edges,
    viewport: s.viewport
  };
}

function isNumber(x: unknown): x is number {
  return typeof x === "number" && Number.isFinite(x);
}

function isFlowDocument(doc: unknown): doc is FlowDocument {
  if (!doc || typeof doc !== "object") return false;
  const d = doc as any;
  if (!Number.isInteger(d.version) || d.version < 1) return false;
  if (typeof d.createdAt !== "string") return false;
  if (!d.flow || typeof d.flow !== "object") return false;
  if (!Array.isArray(d.flow.nodes) || !Array.isArray(d.flow.edges)) return false;
  const vp = d.flow.viewport;
  if (!vp || typeof vp !== "object") return false;
  if (!isNumber(vp.x) || !isNumber(vp.y) || !isNumber(vp.zoom)) return false;
  return true;
}

export const useFlowStore = create<StoreState>()(
  persist(
    (set, get) => ({
      nodes: [
        {
          id: "start",
          type: "start",
          position: { x: 0, y: 0 },
          data: { label: "Start" }
        },
        {
          id: "note-1",
          type: "note",
          position: { x: 220, y: 120 },
          data: { label: "Note", text: "Edit me" }
        }
      ],
      edges: [
        {
          id: "e-start-note-1",
          source: "start",
          target: "note-1",
          type: "labeled",
          data: { label: "edge label" }
        }
      ],
      viewport: INITIAL_VIEWPORT,

      history: createUndoRedo(50),
      _historyLock: false,

      actions: {
        reset: () => {
          set({
            nodes: [],
            edges: [],
            viewport: INITIAL_VIEWPORT,
            history: createUndoRedo(50)
          });
        },

        applyNodeChanges: (changes) => {
          const meaningful = changes.some((c: any) => {
            if (c.type === "select") return false;
            if (c.type === "position") return c.dragging === false; // commit at drag end
            return true;
          });

          if (meaningful) {
            const st = get();
            if (!st._historyLock) {
              set({ _historyLock: true, history: pushSnapshot(st.history, snapshotFromState(st), snapshotFromState(st)) });
              queueMicrotask(() => set({ _historyLock: false }));
            } else {
              // no-op: already captured a snapshot this tick
            }

            // Correct snapshot push: push the "before" snapshot into history.
            // We compute before/after by applying changes to a copy.
            const before = snapshotFromState(get());
            const nextNodes = applyNodeChanges(changes, get().nodes);
            const after = { ...before, nodes: nextNodes };
            const h2 = pushSnapshot(get().history, after, before);
            set({ history: h2, nodes: nextNodes, future: [] } as any);
            return;
          }

          set({ nodes: applyNodeChanges(changes, get().nodes) });
        },

        applyEdgeChanges: (changes) => {
          const meaningful = changes.some((c: any) => (c.type === "select" ? false : true));
          if (meaningful) {
            const before = snapshotFromState(get());
            const nextEdges = applyEdgeChanges(changes, get().edges);
            const after = { ...before, edges: nextEdges };
            const h2 = pushSnapshot(get().history, after, before);
            set({ history: h2, edges: nextEdges });
            return;
          }

          set({ edges: applyEdgeChanges(changes, get().edges) });
        },

        connect: (connection) => {
          const before = snapshotFromState(get());
          const nextEdges = addEdge(
            { ...connection, type: "labeled", data: { label: "new edge" } },
            get().edges
          );
          const after = { ...before, edges: nextEdges };
          const h2 = pushSnapshot(get().history, after, before);
          set({ history: h2, edges: nextEdges });
        },

        setViewport: (viewport) => set({ viewport }),

        addNoteNode: () => {
          const before = snapshotFromState(get());
          const id = `note-${Math.floor(Math.random() * 1e9)}`;
          const node: Node = {
            id,
            type: "note",
            position: { x: 80, y: 80 },
            data: { label: "Note", text: "" }
          };
          const nextNodes = [...get().nodes, node];
          const after = { ...before, nodes: nextNodes };
          const h2 = pushSnapshot(get().history, after, before);
          set({ history: h2, nodes: nextNodes });
        },

        updateNodeText: (nodeId, text) => {
          const before = snapshotFromState(get());
          const nextNodes = get().nodes.map((n) => {
            if (n.id !== nodeId) return n;
            const data = { ...(n.data as any), text };
            return { ...n, data };
          });
          const after = { ...before, nodes: nextNodes };
          const h2 = pushSnapshot(get().history, after, before);
          set({ history: h2, nodes: nextNodes });
        },

        canUndo: () => canUndo(get().history),
        canRedo: () => canRedo(get().history),

        undo: () => {
          const st = get();
          const cur = snapshotFromState(st);
          const { h, snapshot } = undo(st.history, cur);
          if (!snapshot) return;
          set({
            history: h,
            nodes: snapshot.nodes,
            edges: snapshot.edges,
            viewport: snapshot.viewport
          });
        },

        redo: () => {
          const st = get();
          const cur = snapshotFromState(st);
          const { h, snapshot } = redo(st.history, cur);
          if (!snapshot) return;
          set({
            history: h,
            nodes: snapshot.nodes,
            edges: snapshot.edges,
            viewport: snapshot.viewport
          });
        },

        exportDocument: () => {
          const st = get();
          return {
            version: 1,
            createdAt: nowIso(),
            flow: snapshotFromState(st)
          };
        },

        importDocument: (doc) => {
          if (!isFlowDocument(doc)) return { ok: false, error: "Invalid FlowDocument shape." };

          const before = snapshotFromState(get());
          const after = doc.flow;
          const h2 = pushSnapshot(get().history, after, before);

          set({
            history: h2,
            nodes: doc.flow.nodes,
            edges: doc.flow.edges,
            viewport: doc.flow.viewport
          });
          return { ok: true };
        }
      }
    }),
    {
      name: "reactflow-starter-store",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        nodes: state.nodes,
        edges: state.edges,
        viewport: state.viewport
        // Intentionally do not persist history to keep storage smaller and avoid stale undo stacks.
      })
    }
  )
);
