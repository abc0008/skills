# Security and Privacy Considerations

## Principles

- Minimize permissions: do not assume write access; ask before modifying user work.
- No network required for core workflows:
  - the starter app is bundled locally
  - validation is local
- Keep persisted data local:
  - localStorage persistence is user-device scoped

## Safe file handling (scripts)

The scaffolder uses safe path handling to prevent:
- writing outside the destination directory via path traversal
- accidental overwrite of non-empty directories by default

## Data handling

Flow JSON may contain:
- user-entered node text
- labels
- potentially sensitive workflow content

Treat it as sensitive application data:
- avoid logging full flow documents in CI logs
- if you add server persistence, validate and sanitize inputs
- add authentication/authorization and audit logging in backends

## Extending with remote storage

If you add API calls:
- implement retries with exponential backoff and jitter
- implement client-side rate limiting
- separate secrets from code (env vars, secret stores)
- never embed tokens in exported FlowDocument
