---
name: databricks-pdf-genie-report
description: Build Databricks workflows that ingest PDFs, parse documents with ai_parse_document V2, extract structured JSON or Delta tables with ai_extract, expose the results to Genie or Agent Bricks for natural-language questions, and generate governed HTML/PDF reports. Use this whenever the user mentions Databricks Genie, Agent Bricks, Knowledge Assistant, document intelligence, PDF ingestion, ai_parse_document, ai_extract, Lakeflow document pipelines, or wants reports from PDF-derived data.
---

# Databricks PDF Genie Report

Use this skill to design or implement a governed Databricks document-intelligence workflow:

1. Ingest PDFs into Unity Catalog storage or tables.
2. Parse them with `ai_parse_document(content, map('version', '2.0'))`.
3. Extract structured JSON/table fields with `ai_extract`.
4. Prepare source-backed search chunks for document Q&A.
5. Expose structured tables to Genie and source chunks to a Knowledge Assistant or retrieval tool.
6. Generate an HTML report and matching PDF artifact with traceable sources.

## First Decision

Choose the path before writing code:

- **Ad hoc Genie PDF upload**: Use only when the user wants quick, temporary analysis of small PDFs inside one Genie conversation. PDF upload currently requires Agent mode, is UI-only, applies only to the current conversation, and has small file/page limits. Do not present this as durable ingestion, table loading, API automation, or cross-session knowledge.
- **Production governed workflow**: Use when the user wants JSON output, Delta tables, repeatable ingestion, natural-language questions after ingestion, dashboards, reports, or orchestration. This is the default for the scenario in this skill.

If details are missing, proceed with placeholders instead of stalling. Ask only for values that block execution: workspace host/profile, catalog, schema, source volume/table, extraction fields, and report audience.

## Architecture

Use this pattern unless the existing workspace clearly has a better one:

```text
PDF sources
  -> Unity Catalog volume or ingestion table
  -> Bronze binary file table
  -> Silver parsed document table using ai_parse_document V2
  -> Gold extracted table using ai_extract with schema, citations, and confidence
  -> Search chunk table using ai_prep_search for RAG/source-backed answers
  -> Genie Space for structured NL-to-SQL over Gold
  -> Knowledge Assistant or retrieval tool for source passages from chunks
  -> Agent/Supervisor/App report tool that writes HTML and PDF artifacts
```

This split matters because Genie is strongest over curated structured tables, while source-document Q&A needs page/chunk context. For complex answers, route through an Agent Bricks supervisor or app layer that can call both and then render the final report.

## Readiness Checks

Confirm these before committing to a design:

- Unity Catalog and serverless compute are enabled.
- AI Functions are available in the workspace region.
- `ai_parse_document` requirements are satisfied, including Databricks Runtime 17.3+ where applicable and serverless environment version 3+ for `VARIANT`.
- `ai_extract` is acceptable for preview use and the workspace supports the chosen version. Prefer v2.1 when available.
- `ai_prep_search` is beta and needs Runtime 18.2+ where applicable.
- For ad hoc Genie PDF upload, the workspace preview toggles and Partner-Powered AI settings are enabled. Note that compliance security profile workspaces may not support uploaded PDFs.
- The user has permissions to create volumes, tables, functions, jobs, Genie Spaces, and Agent Bricks assets in the target catalog/schema.

## Implementation Workflow

### 1. Define the output contract

Write this down before coding:

- Target JSON schema or table columns.
- Required source traceability: document path, page, element id, citation, confidence score.
- Report sections and delivery path.
- Refresh pattern: one-time upload, scheduled Lakeflow job, or continuous/incremental pipeline.

Prefer explicit schemas over "extract everything." For contracts, invoices, filings, compliance documents, and product manuals, create typed fields with descriptions and enum constraints where useful.

### 2. Ingest PDFs

Use Unity Catalog volumes for durable storage. For simple local or volume-backed files, read them with `READ_FILES(..., format => 'binaryFile')`. For enterprise sources such as SharePoint, use Lakeflow Connect or a managed ingestion pipeline when available.

Keep one row per source file with at least:

- `path`
- `modificationTime`
- `length`
- `content` as binary
- ingestion timestamp
- source-system metadata

### 3. Parse documents with V2

Use `ai_parse_document` with `version = 2.0` and store the raw `VARIANT` output. Preserve errors, not just successful rows.

Use `imageOutputPath` when visual traceability, tables, charts, diagrams, or PDF page references matter. Use `descriptionElementTypes` for figures only when useful, because figure descriptions can add cost. Use `pageRange` for large documents or targeted validation.

Tables from V2 can appear as HTML in parsed elements. Do not flatten them into plain text too early if the report or downstream extraction may need table structure.

### 4. Extract structured fields

Use `ai_extract` on the parsed `VARIANT` output. Prefer:

- v2.1 when supported.
- typed JSON schemas with field descriptions.
- global `instructions` for document domain and extraction rules.
- `enableCitations = true` when answers or reports need source grounding.
- `enableConfidenceScores = true` when humans will review low-confidence outputs.

Write a curated Gold table from the extraction response rather than leaving all business users to query raw nested JSON.

### 5. Prepare natural-language access

For structured questions:

- Add the Gold table and useful dimension tables to a Genie Space.
- Add table/column descriptions, trusted joins, common filters, and example questions.
- Keep extracted fields business-readable; avoid exposing raw JSON as the primary Genie table.

For source-backed document questions:

- Build a chunk table with `ai_prep_search(parsed_doc)` when available.
- Create or configure a Knowledge Assistant, vector search index, or retrieval tool over `chunk_to_embed` and return `chunk_to_retrieve`, page refs, and source URI.

For combined questions:

- Use a supervisor/agent layer to ask Genie for structured aggregates, ask retrieval for supporting passages, and pass both into the report generator.

### 6. Generate HTML and PDF reports

Do not claim Genie alone can durably export governed HTML/PDF files unless the workspace has a custom tool that does so. Use a notebook task, Databricks App, Unity Catalog function, or MCP-backed tool to render report artifacts.

The report generator should:

- Accept the user question, result tables/JSON, citations, and source chunk references.
- Produce `report.html` and `report.pdf`.
- Store artifacts in a Unity Catalog volume.
- Write a report manifest table with run id, prompt, source tables, document paths, artifact URIs, created timestamp, and status.
- Include extraction warnings and low-confidence fields.

Use `templates/genie_agent_instructions.md` when the user needs instructions to paste into a Genie/Agent Bricks assistant. Use `templates/lakeflow_document_pipeline.sql` as the starting SQL scaffold.

## Example Repo Adaptation

When the user references the Databricks blogposts accelerator, treat it as the concrete starter implementation:

https://github.com/databricks-solutions/databricks-blogposts/tree/main/2026-04-Intelligent-document-processing

Use `templates/databricks_blogposts_idp_adaptation.md` for the detailed repo map and modification plan.

The repo already includes:

- `demo/demo_notebook.ipynb`: a single notebook that creates catalog/schema/volume, parses PDFs, extracts structured fields, flattens results, and evaluates extraction quality.
- `productmanuals/`: sample Bosch, DeWalt, Makita, and Milwaukee PDF manuals.
- `databricks_etl/`: the production Asset Bundle with Lakeflow Spark Declarative Pipeline, Lakeflow Job, MLflow evaluation, Genie Space creation, Knowledge Assistant creation, and Supervisor Agent creation.
- `databricks_app/`: a FastAPI + React Databricks App for PDF upload, job triggering, structured-result browsing, and chat with the Supervisor Agent.

Important implementation notes from the repo:

- Bundle roots are subdirectories: run ETL bundle commands from `databricks_etl/` and app bundle commands from `databricks_app/`, not the repo root.
- ETL variables are `catalog`, `schema`, `table_prefix`, `volume`, `warehouse_id`, and `evaluation_experiment`.
- The Lakeflow transformation files are Python pipeline modules under `databricks_etl/src/transformations/productmanuals/`.
- The core table names follow `{table_prefix}_productmanuals_parsed`, `{table_prefix}_productmanuals_extract`, and `{table_prefix}_productmanuals_processed`.
- The sample extraction schema is product-manual specific. For contracts, compliance docs, invoices, or filings, replace that schema and table flattening logic rather than only renaming fields.
- The repo's Databricks App demonstrates upload, job execution, result browsing, and Supervisor chat. Add a report-generation endpoint/job/task to satisfy HTML/PDF report output.

For the user's requested scenario, extend the repo in this order:

1. Keep the repo's upload -> job -> processed table -> chat pattern.
2. Replace the product-manual extraction schema with the user's PDF domain schema.
3. Add citations/confidence options to `ai_extract` when source grounding is required.
4. Add a report output volume and report manifest table.
5. Add a report task or app endpoint that renders HTML and PDF from structured results plus source evidence.
6. Add UI controls or chat tool instructions that return the generated HTML/PDF artifact URIs.

## Report Structure

Use this structure unless the user asks for a different one:

1. Title, run id, and timestamp.
2. User question and scope.
3. Executive answer.
4. Key findings with source-backed citations.
5. Structured data table or metrics.
6. Document evidence appendix with source URI, page, element/chunk id, confidence, and excerpts.
7. Extraction quality notes and unresolved items.

## Validation Checklist

Before saying the workflow is done:

- Source PDFs appear in the expected volume/table.
- Bronze count matches expected file count.
- Parsed table contains V2 metadata and elements.
- Parse errors are captured and visible.
- Extracted table has typed business columns, not only opaque JSON.
- Citations and confidence scores are present when requested.
- Genie can answer at least three structured questions against Gold.
- Retrieval can answer at least three source-document questions with page/source references.
- HTML and PDF reports are created and listed in the report manifest.
- Permissions allow intended users to query tables and read report artifacts.

## Source Anchors

Use these as the live documentation starting points when refreshing details:

- Genie file upload: https://learn.microsoft.com/en-us/azure/databricks/genie/file-upload
- `ai_parse_document`: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document
- `ai_extract`: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract
- `ai_prep_search`: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_prep_search
- Agent Bricks Document Parsing: https://docs.databricks.com/aws/en/generative-ai/agent-bricks/document-parsing
- Databricks bundle example: https://github.com/databricks/bundle-examples/tree/main/contrib/job_with_ai_parse_document
- Agent Bricks multi-agent example: https://github.com/databricks-industry-solutions/agent-bricks-fins-mag7
- Databricks blogposts IDP accelerator: https://github.com/databricks-solutions/databricks-blogposts/tree/main/2026-04-Intelligent-document-processing
