# Backend (Lambda Handlers)

Minimal handlers are scaffolded in `src/handlers`:

- `upload.js`: creates metadata + returns presigned `putObject` URL
- `download.js`: reads metadata + returns presigned `getObject` URL
- `list.py`: returns paginated photo metadata for authenticated user (`GET /photos`)

These handlers are packaged by Terraform using the `archive_file` data source in `infrastructure/lambda.tf`.
