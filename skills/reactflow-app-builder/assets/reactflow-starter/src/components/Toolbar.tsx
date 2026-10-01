import React, { useRef } from "react";
import { useReactFlow } from "@xyflow/react";
import { useFlowStore } from "../store/flowStore";
import { defaultExportFilename, downloadJson, readFileAsJson } from "../utils/serialization";

export function Toolbar() {
  const addNoteNode = useFlowStore((s) => s.actions.addNoteNode);
  const undo = useFlowStore((s) => s.actions.undo);
  const redo = useFlowStore((s) => s.actions.redo);
  const canUndo = useFlowStore((s) => s.actions.canUndo());
  const canRedo = useFlowStore((s) => s.actions.canRedo());
  const exportDocument = useFlowStore((s) => s.actions.exportDocument);
  const importDocument = useFlowStore((s) => s.actions.importDocument);
  const reset = useFlowStore((s) => s.actions.reset);

  const fileRef = useRef<HTMLInputElement | null>(null);

  const rf = useReactFlow();

  return (
    <div className="toolbar">
      <button onClick={() => addNoteNode()}>Add note node</button>

      <button onClick={() => undo()} disabled={!canUndo}>
        Undo
      </button>
      <button onClick={() => redo()} disabled={!canRedo}>
        Redo
      </button>

      <button
        onClick={() => {
          const doc = exportDocument();
          downloadJson(defaultExportFilename(doc), doc);
        }}
      >
        Export JSON
      </button>

      <input
        ref={fileRef}
        type="file"
        accept="application/json"
        style={{ display: "none" }}
        onChange={async (e) => {
          const f = e.target.files?.[0];
          if (!f) return;
          const doc = await readFileAsJson(f);
          const res = importDocument(doc);
          if (!res.ok) {
            alert(res.error || "Import failed");
          }
          if (fileRef.current) fileRef.current.value = "";
        }}
      />

      <button onClick={() => fileRef.current?.click()}>Import JSON</button>

      <button onClick={() => rf.fitView()}>Fit view</button>
      <button onClick={() => reset()}>Reset</button>

      <span className="small">
        Shortcuts: Ctrl/Cmd+Z undo · Ctrl/Cmd+Shift+Z redo
      </span>
    </div>
  );
}
