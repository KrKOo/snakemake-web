# GDI Workflow Runner

The GDI Workflow Runner serves as the central orchestration component of the Genome Data Infrastructure (GDI) compute service. Its primary functions are to manage user-submitted workflows, securely handle authentication and authorization, and execute computational jobs via the [Snakemake](https://snakemake.readthedocs.io/) workflow engine. The runner is designed to interact with [Task Execution Service (TES)](https://github.com/ga4gh/task-execution-schemas) APIs, ensuring strict access control to sensitive data.

---

## Architecture Overview

### REST API

The API (FastAPI, Python >=3.9) exposes endpoints for full lifecycle management of workflows. All endpoints (except workflow definitions listing) require a valid OAuth2 token in the `Authorization` header.

| Method | Endpoint                           | Description                                                        |
|--------|------------------------------------|--------------------------------------------------------------------|
| POST   | `/api/run`                         | Initiate a workflow run. Returns workflow ID on success.           |
| GET    | `/api/workflow`                    | List all workflows submitted by authenticated user.                |
| DELETE | `/api/workflow/{workflow_id}`      | Cancel running workflow (checked for user ownership).              |
| GET    | `/api/workflow/{workflow_id}`      | Fetch workflow details, status, and logs.                          |
| GET    | `/api/workflow_definition`         | List available workflow definitions and metadata (public endpoint).|

Interactive documentation with examples is available at `/docs` (Swagger UI).

---

### Database Layer

To enable easy integration with different backend stores, the workflow runner provides a database **abstraction interface** with the following mandatory methods (implemented for MongoDB by default):

| Method                     | Description                                                       |
|----------------------------|-------------------------------------------------------------------|
| `get_one(model, filter)`   | Retrieve a single record matching filter.                         |
| `get_many(model, filter)`  | Retrieve multiple records matching filter criteria.                |
| `insert_one(model, data)`  | Insert new record, return with DB-generated fields.               |
| `update_one(model, filter, data)` | Update record matching filter, return the updated entry.   |
| `delete_one(model, filter)`| Delete single record matching the filter.                         |

To support a new database, implement the minimal interface above.

---


### Job Management with Celery

Workflow execution is managed asynchronously using [Celery](https://docs.celeryq.dev/) workers. When a workflow is submitted:

- A Celery task is dispatched with all necessary credentials and parameters.
- The worker launches Snakemake with:
  - S3 storage credentials (for intermediate data)
  - TES endpoint (Funnel) and authentication
  - User's OAuth tokens for sensitive data access
  - Workflow definitions, input/output paths, and mappings
- Celery monitors the workflow lifecycle and updates workflow status in real-time.

**Workflow States:**

- `Unknown`   – Initial, undetermined state
- `Running`   – Jobs executing or queued
- `Finished`  – All steps completed successfully
- `Failed`    – Execution aborted with error
- `Canceled`  – Stopped on user request

Status can be queried via `GET /api/workflow/{workflow_id}`.


## Workflow Submission

Workflows are submitted via the `POST /api/run` endpoint of the API. This endpoint serves as the main entry point for launching workflows.

### Required Parameters

When submitting a workflow, the request must include:

- `workflow_definition_id`:  
  A unique identifier for the workflow, corresponding to a predefined workflow definition stored in a [dedicated Git repository](https://github.com/KrKOo/snakemake-web-workflows).

- `input_directory`:  
  The path to the input dataset directory to be used by the workflow.

- `output_directory`:  
  The destination path where workflow outputs and results will be stored.

- **User Access Token**:  
  An OAuth2 access token, included in the HTTP Authorization header (e.g., `Authorization: Bearer <token>`). This token authenticates the user and authorizes access to sensitive resources (using embedded GA4GH Visas).

### Submission Flow

1. **Authentication & Authorization**  
   The workflow runner validates the provided OAuth2 access token and, if necessary, checks the user’s entitlements as required by the workflow definition (see below).

2. **Workflow Definition Retrieval**  
   The runner fetches the workflow definition based on the Workflow Definition ID. Each workflow in the Git repository includes a `metadata.json` file which defines:
   - `id` — Unique workflow identifier.
   - `name` — Human-readable name.
   - `allowed_entitlements` (optional) — User entitlement groups required to run the workflow. If specified, the runner verifies that the user's access token contains a matching entitlement (see example below).
   - `input_mapping`(optional) — Mappings for generic input paths, allowing workflows to be written generically without dataset-specific hardcoding.

   Example `allowed_entitlements` in `metadata.json`:
   ```json
   "allowed_entitlements": [
     {
       "prefix": "urn:geant:lifescience-ri\\.eu:",
       "values": [".*:entitled:.*", ".*:students:.*"],
       "suffix": ".*"
     }
   ]
   ```

   Example `input_mapping` for generic dataset access:

  ```json
  "input_mapping": {
    "dataset": "sda://{dataset}"
  }
  ```
3. **Dynamic Input Mapping**
The runner uses the `input_mapping` property to support generic workflow definitions. Local input references in the workflow are mapped at runtime to actual SDA paths using user-supplied input directories.


4. **Task Dispatch and Execution**
Upon successful validation, the runner submits an asynchronous Celery task to execute the workflow on one of the configured TES nodes. Currently the dataset->TES mapping has to be defined in the workflow runner configuration, since there is no way to discover data stored in each nodes SDA.

The Celery worker launches Snakemake with all necessary arguments and credentials and monitors the output logs of the Snakemake process. 


## License

Distributed under the MIT License. See [LICENSE.md](LICENSE.md)