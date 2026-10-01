export function isUndoShortcut(e: KeyboardEvent): boolean {
  const key = e.key.toLowerCase();
  const meta = e.metaKey || e.ctrlKey;
  return meta && key === "z" && !e.shiftKey;
}

export function isRedoShortcut(e: KeyboardEvent): boolean {
  const key = e.key.toLowerCase();
  const meta = e.metaKey || e.ctrlKey;
  // Cmd/Ctrl+Shift+Z or Cmd/Ctrl+Y
  return (meta && key === "z" && e.shiftKey) || (meta && key === "y");
}
