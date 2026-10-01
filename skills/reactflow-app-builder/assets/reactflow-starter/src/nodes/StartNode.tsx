import type { NodeProps } from "@xyflow/react";
import { Handle, Position } from "@xyflow/react";

export function StartNode(props: NodeProps<{ label: string }>) {
  const { data } = props;

  return (
    <div style={{ padding: 12, border: "1px solid #333", borderRadius: 10, background: "#f8f8f8" }}>
      <strong>{data.label}</strong>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
