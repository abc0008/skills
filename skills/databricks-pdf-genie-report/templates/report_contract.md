# HTML/PDF Report Contract

Use this contract when implementing the report generation notebook, Databricks App, Unity Catalog function, or MCP-backed tool.

## Input

- `run_id`: Unique report id.
- `user_question`: Original natural-language request.
- `structured_results`: Rows or JSON returned from Genie/SQL over the Gold table.
- `source_evidence`: Chunks, parsed elements, citations, page references, confidence scores, and source URIs.
- `warnings`: Parse errors, low-confidence extractions, missing fields, unsupported file types, or permission gaps.
- `output_path`: `/Volumes/{catalog}/{schema}/{report_volume}/reports/{run_id}/`

## Output Files

- `report.html`
- `report.pdf`
- Optional supporting assets under `assets/`

## Manifest Row

Append one row to `{catalog}.{schema}.{report_manifest_table}`:

```sql
INSERT INTO ${catalog}.${schema}.${report_manifest_table}
SELECT
  '${run_id}' AS run_id,
  '${user_question}' AS user_question,
  '${html_uri}' AS html_uri,
  '${pdf_uri}' AS pdf_uri,
  array('${gold_table}', '${search_chunks_table}') AS source_tables,
  array(${source_document_uris}) AS source_documents,
  '${status}' AS status,
  current_timestamp() AS created_at;
```

## HTML Sections

1. Report title, run id, and timestamp.
2. User question and data scope.
3. Executive answer.
4. Key findings.
5. Structured results table.
6. Source evidence appendix.
7. Extraction quality notes.

## PDF Requirements

- Render the HTML to PDF without dropping citations or appendix tables.
- Use stable page breaks for long evidence tables.
- Include source URI and page/chunk references in printable text, not only hyperlinks.
- Store the PDF in the same output directory as the HTML.

