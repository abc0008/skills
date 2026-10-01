import type { NodeProps } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";
import { useFlowStore } from "../store/flowStore";

export function NoteNode(props: NodeProps<{ label: string; text: string }>) {
  const { id, data } = props;
  const updateNodeText = useFlowStore((s) => s.actions.updateNodeText);

  return (
    <div style={{ padding: 12, border: "1px solid #aaa", borderRadius: 10, background: "white", width: 220 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <strong>{data.label}</strong>
        <span style={{ fontSize: 12, opacity: 0.7 }}>{id}</span>
      </div>

      <textarea
        value={data.text ?? ""}
        onChange={(e) => updateNodeText(id, e.target.value)}
        placeholder="Type node text..."
        style={{ width: "100%", minHeight: 70, resize: "vertical" }}
      />

      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
