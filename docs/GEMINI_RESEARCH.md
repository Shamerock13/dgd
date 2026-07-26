# Gemini research provider

DGD uses Gemini with Google Search grounding for the combined **Daten & Duftzwillinge suchen** action.

## Configuration

Add these variables to the development backend container:

```env
GEMINI_API_KEY=replace-with-your-key
GEMINI_MODEL=gemini-2.5-flash
```

Never commit the API key to the repository.

After changing the container variables, recreate or restart the development backend.

## Behaviour

- Processes at most five pending fragrances per run.
- Requests grounded web research through Gemini's `googleSearch` tool.
- Extracts year, concentration, perfumer, description, image, accords and note pyramids.
- Creates field-level entries in `enrichment_findings`.
- Creates grounded twin suggestions only when the response contains explicit comparison evidence.
- Existing fragrance records are never overwritten automatically.
- Every result remains pending until editorial approval.
- Usage token counts and the number of grounding sources are returned in the run summary.

## Status endpoint

```http
GET /api/enrichment/provider-status
```

The endpoint reports whether `GEMINI_API_KEY` is available without exposing the key.

## Combined run

```http
POST /api/enrichment/run?finding_limit=5&twin_limit=5
```

When the key is missing, the endpoint returns a clear `configured: false` result instead of attempting the obsolete DuckDuckGo workflow.
