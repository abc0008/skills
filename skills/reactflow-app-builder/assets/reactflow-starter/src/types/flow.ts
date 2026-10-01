import type { Edge, Node, Viewport } from "@xyflow/react";

export type FlowSnapshot = {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
};

export type FlowDocument = {
  version: number;
  createdAt: string;
  flow: FlowSnapshot;
};
