import test from "node:test";
import assert from "node:assert/strict";

function validateFlowDocument(doc) {
  const errors = [];
  if (!doc || typeof doc !== "object") return ["Document is not an object."];

  if (!Number.isInteger(doc.version) || doc.version < 1) errors.push("version");
  if (typeof doc.createdAt !== "string") errors.push("createdAt");
  if (!doc.flow || typeof doc.flow !== "object") errors.push("flow");
  else {
    if (!Array.isArray(doc.flow.nodes)) errors.push("nodes");
    if (!Array.isArray(doc.flow.edges)) errors.push("edges");
    const vp = doc.flow.viewport;
    if (!vp || typeof vp !== "object") errors.push("viewport");
  }
  return errors;
}

test("validateFlowDocument accepts minimal valid doc", () => {
  const doc = {
    version: 1,
    createdAt: new Date().toISOString(),
    flow: { nodes: [], edges: [], viewport: { x: 0, y: 0, zoom: 1 } }
  };
  assert.deepEqual(validateFlowDocument(doc), []);
});

test("validateFlowDocument rejects invalid doc", () => {
  const doc = { version: 0, createdAt: 123, flow: {} };
  const errors = validateFlowDocument(doc);
  assert.ok(errors.length > 0);
});
