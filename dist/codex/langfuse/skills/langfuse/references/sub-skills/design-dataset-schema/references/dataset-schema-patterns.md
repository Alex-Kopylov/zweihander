# Dataset Schema Patterns

Common `input` schema patterns for different experiment pipeline types. Use these as starting points when designing dataset items.

## Pattern: HTTP Endpoint Pipeline

For webhook experiments that POST to HTTP endpoints.

**Structure:** Separate URL path parameters from the request body.

```json
{
  "path_param_1": "value",
  "path_param_2": "value",
  "request": { "... endpoint request body ..." }
}
```

### Example: SSP Control Generation

Endpoint: `POST /api/v1/ssp/catalogs/{catalog_id}/{control_id}/generate`

```json
{
  "catalog_id": "bc413ad0-23d7-4ff0-a7af-b48a03294873",
  "control_id": "ac-1",
  "request": {
    "system_characteristics": {
      "system_name": "Example Cloud Platform",
      "description": "Cloud-native SaaS platform for enterprise customers",
      "components": [
        { "type": "software", "title": "Frontend Web Application", "description": "React + Next.js" },
        { "type": "software", "title": "Backend Services", "description": "FastAPI microservices" },
        { "type": "software", "title": "PostgreSQL Database", "description": "PostgreSQL with pgvector" }
      ],
      "props": {
        "environment": "production",
        "deployment-model": "cloud",
        "hosting-provider": "Government-accredited cloud provider"
      },
      "responsible_parties": [
        { "party": "person", "role_id": "authorizing-official", "description": "Jane Doe – CTO" },
        { "party": "person", "role_id": "system-owner", "description": "John Smith – Director of Engineering" }
      ]
    },
    "policy": null,
    "procedure": null,
    "reference_content": null
  }
}
```

### Example: HTML Control Generation

Endpoint: `POST /api/v1/html_controls/catalogs/{catalog_id}/{control_id}/generate`

Same structure as SSP — only the endpoint URL differs.

### Example: HTML Tag Generation

Endpoint: `POST /api/v1/html_tags/generate`

No path parameters — only request body:

```json
{
  "request": {
    "control_id": "ac-1",
    "tags": [
      {
        "tag_name": "ac_1_a",
        "comment": "Access control policy enforcement",
        "context": null,
        "reference_content": null
      }
    ],
    "profile_id": "bc413ad0-23d7-4ff0-a7af-b48a03294873",
    "system_characteristics": { "...same as above..." },
    "control_context": null,
    "control_implementation": null,
    "sequential": true
  }
}
```

## Pattern: SDK Task Function

For `langfuse.run_experiment(task=my_task)` or `dataset.run_experiment(task=my_task)`, use a flat object with everything the task function needs. The task receives `item.input` directly.

### Example: Question Answering

```json
{
  "question": "What are the key components of the AC-1 control?",
  "context": "NIST SP 800-53 Rev 5 defines AC-1 as..."
}
```

### Example: Classification

```json
{
  "text": "The system shall implement multi-factor authentication...",
  "label_options": ["AC", "IA", "SC", "AU"]
}
```

### Example: Summarization

```json
{
  "document": "Full text of the control implementation...",
  "max_length": 200
}
```

## Pattern: Expected Output

### For Exact Comparison
```json
{
  "expectedOutput": "The AC-1 control requires organizations to develop, document, and disseminate access control policy."
}
```

### For Criteria-Based Evaluation
```json
{
  "expectedOutput": {
    "must_contain_concepts": ["policy development", "documentation", "dissemination"],
    "min_word_count": 50,
    "tone": "professional"
  }
}
```

### For Multi-Aspect Scoring
```json
{
  "expectedOutput": {
    "accuracy_criteria": "Must correctly identify the AC-1 control requirements",
    "completeness_criteria": "Must cover all enhancement items listed in the catalog",
    "format_criteria": "Must use valid HTML with proper heading structure"
  }
}
```

## JSON Schema Templates

### Minimal — No Validation
```json
null
```

### Flexible Object
```json
{
  "type": "object"
}
```

### Required Fields Only
```json
{
  "type": "object",
  "required": ["request"],
  "properties": {
    "request": { "type": "object" }
  }
}
```

### Strict with Pattern Validation
```json
{
  "type": "object",
  "required": ["catalog_id", "control_id", "request"],
  "properties": {
    "catalog_id": { "type": "string", "format": "uuid" },
    "control_id": { "type": "string", "pattern": "^[a-z]{2}-[0-9]+([.][0-9]+)?$" },
    "request": {
      "type": "object",
      "required": ["system_characteristics"],
      "properties": {
        "system_characteristics": {
          "type": "object",
          "required": ["system_name", "description"]
        }
      }
    }
  },
  "additionalProperties": false
}
```
