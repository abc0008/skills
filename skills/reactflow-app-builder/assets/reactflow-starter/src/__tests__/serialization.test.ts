import { describe, expect, it } from "vitest";
import type { FlowDocument } from "../types/flow";
import { defaultExportFilename } from "../utils/serialization";

describe("serialization utilities", () => {
  it("defaultExportFilename produces a .json filename", () => {
    const doc: FlowDocument = {
      version: 1,
      createdAt: "2026-01-01T01:02:03.000Z",
      flow: { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } }
    };
    const name = defaultExportFilename(doc);
    expect(name.endsWith(".json")).toBe(true);
    expect(name.includes("flow-")).toBe(true);
  });
});
