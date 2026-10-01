import React, { useCallback } from "react";
import ReactFlow, { Background, Controls, MiniMap, type NodeTypes, type EdgeTypes } from "@xyflow/react";
import { useFlowStore } from "../store/flowStore";
import { StartNode } from "../nodes/StartNode";
import { NoteNode } from "../nodes/NoteNode";
import { LabeledEdge } from "../edges/LabeledEdge";

const nodeTypes: NodeTypes = {
  start: StartNode,
  note: NoteNode
};

const edgeTypes: EdgeTypes = {
  labeled: LabeledEdge
};

export function FlowCanvas() {
  const nodes = useFlowStore((s) => s.nodes);
  const edges = useFlowStore((s) => s.edges);
  const viewport = useFlowStore((s) => s.viewport);

  const applyNodeChanges = useFlowStore((s) => s.actions.applyNodeChanges);
  const applyEdgeChanges = useFlowStore((s) => s.actions.applyEdgeChanges);
  const connect = useFlowStore((s) => s.actions.connect);
  const setViewport = useFlowStore((s) => s.actions.setViewport);

  const onNodesChange = useCallback(applyNodeChanges, [applyNodeChanges]);
  const onEdgesChange = useCallback(applyEdgeChanges, [applyEdgeChanges]);
  const onConnect = useCallback(connect, [connect]);

  return (
    <div className="canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultViewport={viewport}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onMoveEnd={(_, vp) => setViewport(vp)}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
