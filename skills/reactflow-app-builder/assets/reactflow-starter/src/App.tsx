import React, { useEffect } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { FlowCanvas } from "./components/FlowCanvas";
import { Toolbar } from "./components/Toolbar";
import { useFlowStore } from "./store/flowStore";
import { isRedoShortcut, isUndoShortcut } from "./utils/keyboard";

export function App() {
  const undo = useFlowStore((s) => s.actions.undo);
  const redo = useFlowStore((s) => s.actions.redo);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (isUndoShortcut(e)) {
        e.preventDefault();
        undo();
      } else if (isRedoShortcut(e)) {
        e.preventDefault();
        redo();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [undo, redo]);

  return (
    <div className="app">
      <ReactFlowProvider>
        <Toolbar />
        <FlowCanvas />
      </ReactFlowProvider>
    </div>
  );
}
