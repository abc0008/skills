# Databricks Blogposts IDP Accelerator Adaptation

Use this when adapting:

https://github.com/databricks-solutions/databricks-blogposts/tree/main/2026-04-Intelligent-document-processing

The accelerator is a strong starting point for PDF ingestion, AI extraction, Genie, Knowledge Assistant, Supervisor Agent, and a Databricks App. It does not, by itself, satisfy the final HTML/PDF report artifact requirement. Add that as an explicit extension.

## Repo Map

- `README.md`: overview and directory structure.
- `productmanuals/`: sample PDFs: Bosch, DeWalt, Makita, Milwaukee.
- `demo/demo_notebook.ipynb`: single-notebook demo for setup, parse, extract, flatten, and MLflow evaluation.
- `databricks_etl/`: production Databricks Asset Bundle for the pipeline and agent setup.
- `databricks_etl/databricks.yml`: ETL bundle variables.
- `databricks_etl/resources/extract_productmanuals.pipeline.yml`: serverless Lakeflow Spark Declarative Pipeline.
- `databricks_etl/resources/extract_productmanuals.job.yml`: orchestration job.
- `databricks_etl/src/transformations/productmanuals/01_parsed.py`: binary PDF ingestion and `ai_parse_document`.
- `databricks_etl/src/transformations/productmanuals/02_extract.py`: product-manual extraction schema and `ai_extract`.
- `databricks_etl/src/transformations/productmanuals/03_process.py`: flattening to a business-user table.
- `databricks_etl/src/evaluation/evaluate_extraction.ipynb`: MLflow GenAI extraction evaluation.
- `databricks_etl/src/genie_space/`: Genie Space creation helpers/notebook.
- `databricks_etl/src/knowledge_assistant/`: Knowledge Assistant creation helpers/notebook.
- `databricks_etl/src/supervisor_agent/`: Supervisor Agent creation helpers/notebook.
- `databricks_app/`: FastAPI + React Databricks App bundle.
- `databricks_app/app.yml`: local/APX app environment settings.
- `databricks_app/databricks.yml`: Databricks App bundle with app scopes.
- `databricks_app/src/data_extraction_app/backend/router.py`: upload PDFs, trigger job, query processed table, chat with Supervisor.

## ETL Bundle Variables

Configure these in `databricks_etl/databricks.yml`:

- `catalog`: Unity Catalog catalog.
- `schema`: target schema.
- `table_prefix`: prefix for generated tables and job/pipeline display names.
- `volume`: source PDF volume path, for example `/Volumes/<CATALOG>/<SCHEMA>/<VOLUME_NAME>`.
- `warehouse_id`: SQL warehouse for Genie Space creation.
- `evaluation_experiment`: MLflow experiment path.

The generated tables are:

- `{table_prefix}_productmanuals_parsed`
- `{table_prefix}_productmanuals_extract`
- `{table_prefix}_productmanuals_processed`

Rename or generalize these if the use case is not product manuals.

## Existing Flow

The ETL job does this:

1. Runs the Lakeflow pipeline.
2. Optionally creates or updates the Knowledge Assistant.
3. Creates the Genie Space after extraction.
4. Evaluates extraction quality with MLflow.
5. Creates the Supervisor Agent after Genie and Knowledge Assistant exist.

The app does this:

1. Lists PDFs in the configured volume.
2. Uploads PDF files to the volume.
3. Runs the configured extraction job.
4. Reads the processed table through SQL Warehouse.
5. Sends chat messages to the Supervisor Agent endpoint.

## Domain Adaptation Steps

1. Replace `productmanuals` naming with the user's document domain.
2. Update `02_extract.py`:
   - Replace the product-manual instructions.
   - Replace the JSON schema fields.
   - Prefer typed fields and field descriptions.
   - Add `enableCitations` and `enableConfidenceScores` when reports need source grounding.
3. Update `03_process.py`:
   - Flatten the new extraction fields.
   - Include source columns such as `path`, `file_name`, and any citation/confidence columns needed for reports.
4. Update Genie creation:
   - Point the Genie Space at the processed table.
   - Add column descriptions, sample questions, and query guidance for the new domain.
5. Update Knowledge Assistant creation:
   - Point sources at the PDF volume.
   - Set display names and instructions for the new domain.
6. Update Supervisor instructions:
   - Route structured aggregation/comparison questions to Genie.
   - Route source-text, page, clause, procedure, or evidence questions to Knowledge Assistant.
   - Route report requests to the new report tool/job.
7. Update Databricks App env:
   - `WAREHOUSE_ID`
   - `JOB_ID`
   - `VOLUME_PATH`
   - `AI_EXTRACT_PROCESSED_TABLE`
   - `AGENT_ENDPOINT`

## HTML/PDF Report Extension

Add this because the accelerator app does not ship as a durable report exporter.

Recommended additions:

- New output volume: `/Volumes/<CATALOG>/<SCHEMA>/<REPORT_VOLUME>/reports/`
- New manifest table: `<CATALOG>.<SCHEMA>.<table_prefix>_report_manifest`
- New app environment variable: `REPORT_VOLUME_PATH`
- New backend endpoint: `POST /api/reports`
- Optional backend endpoint: `GET /api/reports/{run_id}`
- New job/notebook task if report rendering should run asynchronously.

The report endpoint or job should:

1. Accept a user question and optional filters.
2. Query the processed table for structured facts.
3. Call the Supervisor Agent or Knowledge Assistant for source evidence.
4. Render `report.html`.
5. Render `report.pdf` from the same HTML.
6. Upload both files to the report volume.
7. Append the artifact URIs and source document list to the manifest table.

## Validation

- Upload at least one sample PDF through the app.
- Run the ETL job from the app and verify the job run completes.
- Confirm the parsed, extract, and processed tables exist and contain rows.
- Ask Genie a structured question against the processed table.
- Ask Knowledge Assistant a source-document question.
- Ask Supervisor a mixed question that requires both tools.
- Generate one HTML/PDF report and verify both artifacts exist in the report volume.
- Confirm the report manifest has the report row and source document references.

