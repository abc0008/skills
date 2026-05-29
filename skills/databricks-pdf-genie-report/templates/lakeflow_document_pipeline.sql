-- Databricks PDF document intelligence scaffold.
-- Replace ${...} placeholders before running.
-- Use as SQL in a Databricks notebook, SQL editor, or Lakeflow Spark Declarative Pipeline.

USE CATALOG ${catalog};
USE SCHEMA ${schema};

CREATE VOLUME IF NOT EXISTS ${source_volume};
CREATE VOLUME IF NOT EXISTS ${page_image_volume};
CREATE VOLUME IF NOT EXISTS ${report_volume};

-- Bronze: one row per source document with binary content.
CREATE OR REFRESH STREAMING TABLE ${bronze_table}
AS
SELECT
  path,
  modificationTime,
  length,
  content,
  _metadata,
  current_timestamp() AS ingested_at
FROM STREAM read_files(
  '${source_path}',
  format => 'binaryFile',
  pathGlobFilter => '*.pdf'
);

-- Silver: preserve full ai_parse_document V2 output.
CREATE OR REFRESH STREAMING TABLE ${parsed_table}
TBLPROPERTIES (
  'delta.feature.variantType-preview' = 'supported'
)
AS
SELECT
  path,
  modificationTime,
  length,
  ai_parse_document(
    content,
    map(
      'version', '2.0',
      'imageOutputPath', '/Volumes/${catalog}/${schema}/${page_image_volume}/pages/',
      'descriptionElementTypes', '${description_element_types}'
    )
  ) AS parsed_doc,
  current_timestamp() AS parsed_at
FROM ${bronze_table};

-- Optional: flatten parsed elements for inspection, source tracing, and table QA.
CREATE OR REFRESH TABLE ${elements_table}
AS
SELECT
  p.path,
  e.value:id::INT AS element_id,
  e.value:type::STRING AS element_type,
  e.value:content::STRING AS content,
  e.value:confidence::DOUBLE AS confidence,
  e.value:bbox AS bbox,
  e.value:description::STRING AS description,
  p.parsed_doc:metadata.file_metadata.file_name::STRING AS file_name,
  p.parsed_at
FROM ${parsed_table} p,
LATERAL variant_explode(p.parsed_doc:document.elements) AS e;

-- Gold JSON extraction. Replace ${extraction_schema_json} and ${domain_instructions}.
CREATE OR REFRESH STREAMING TABLE ${extracted_table}
TBLPROPERTIES (
  'delta.feature.variantType-preview' = 'supported'
)
AS
SELECT
  path,
  ai_extract(
    parsed_doc,
    '${extraction_schema_json}',
    map(
      'version', '2.1',
      'instructions', '${domain_instructions}',
      'enableCitations', 'true',
      'enableConfidenceScores', 'true'
    )
  ) AS extracted,
  current_timestamp() AS extracted_at
FROM ${parsed_table};

-- Search chunks for retrieval and source-backed answers.
CREATE OR REFRESH TABLE ${search_chunks_table}
TBLPROPERTIES (
  'delta.feature.variantType-preview' = 'supported'
)
AS
WITH prepped AS (
  SELECT
    path,
    ai_prep_search(parsed_doc) AS search_doc
  FROM ${parsed_table}
)
SELECT
  path,
  c.value:chunk_id::STRING AS chunk_id,
  c.value:chunk_position::INT AS chunk_position,
  c.value:chunk_to_retrieve::STRING AS chunk_to_retrieve,
  c.value:chunk_to_embed::STRING AS chunk_to_embed,
  c.value:pages AS pages,
  search_doc:document.source_uri::STRING AS source_uri
FROM prepped,
LATERAL variant_explode(search_doc:document.contents) AS c;

-- Report manifest. The report generator should append one row per HTML/PDF output.
CREATE TABLE IF NOT EXISTS ${report_manifest_table} (
  run_id STRING,
  user_question STRING,
  html_uri STRING,
  pdf_uri STRING,
  source_tables ARRAY<STRING>,
  source_documents ARRAY<STRING>,
  status STRING,
  created_at TIMESTAMP
);

