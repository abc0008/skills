import type { EdgeProps } from "@xyflow/react";
import { BaseEdge, EdgeLabelRenderer, getStraightPath } from "@xyflow/react";

export function LabeledEdge(props: EdgeProps<{ label?: string }>) {
  const { id, sourceX, sourceY, targetX, targetY, data, markerEnd } = props;

  const [path, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY
  });

  return (
    <>
      <BaseEdge id={id} path={path} markerEnd={markerEnd} />
      {data?.label ? (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
              background: "white",
              border: "1px solid #ddd",
              borderRadius: 6,
              padding: "2px 6px",
              fontSize: 12
            }}
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}
