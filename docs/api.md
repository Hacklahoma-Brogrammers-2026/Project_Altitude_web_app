# API Expectations (Frontend)

This document describes the HTTP requests the frontend currently makes and the JSON shape it expects in responses.

## Base URL

The frontend uses `VITE_API_BASE_URL` when set; otherwise, it calls the same origin.

## GET /person/:id

Fetch a single contact by ID for the Profile page.

### Request

- Method: GET
- Path param: `id` (string or numeric contact identifier)
- Body: none
- Query: none

### Response (required fields)

```json
{
  "contact_id": "string",
  "first_name": "string",
  "last_name": "string",
  "photo": "https://..."
}
```

### Response (optional fields)

```json
{
  "note": "string summary about the person",
  "notes": [
    {
      "label": "string",
      "content": "string"
    }
  ]
}
```

### Notes

- `note` is rendered under the name as a short summary if present.
- The accordion list is generated from `notes[]` using `label` and `content`.

## GET /api/profile/:id/search

Search within a single profile for the Profile page search box.

### Request

- Method: GET
- Path param: `id` (string or numeric contact identifier)
- Query param: `q` (string search query)

Example:

```
GET /api/profile/123/search?q=last%20seen
```

### Response

Accepts either an array or a JSON object with a `results` array.

```json
[
  {
    "label": "string",
    "content": "string"
  }
]
```

Or:

```json
{
  "results": [
    {
      "label": "string",
      "content": "string"
    }
  ]
}
```

### Notes

- If the search returns no results, the UI displays "No data.".

## GET /api/searchUser

Search people by name for the Search Results page.

### Request

- Method: GET
- Query param: `q` (string search query)

Example:

```
GET /api/searchUser?q=ashley
```

### Response

Accepts either an array or a JSON object with a `results` array.

```json
[
  {
    "id": "string or number",
    "name": "string",
    "avatar": "https://..."
  }
]
```

Or:

```json
{
  "results": [
    {
      "id": "string or number",
      "name": "string",
      "avatar": "https://..."
    }
  ]
}
```

## GET /api/searchInfo

Semantic search for the Search Results page based on context labels/notes.

### Request

- Method: GET
- Query param: `q` (string search query)

Example:

```
GET /api/searchInfo?q=front%20door%20morning
```

### Response

Accepts either an array or a JSON object with a `results` array.

```json
[
  {
    "id": "string or number",
    "name": "string",
    "avatar": "https://...",
    "label": "string"
  }
]
```

Or:

```json
{
  "results": [
    {
      "id": "string or number",
      "name": "string",
      "avatar": "https://...",
      "label": "string"
    }
  ]
}
```

## GET /api/getPeople

Fetch all contacts for the Home "Last Modified" section and the Person Database page.

### Request

- Method: GET
- Query param: `sort` (string)
  - `alphabetical` (Person Database filter)
  - `last_modified` (Home "Last Modified" and Person Database filter)

Example:

```
GET /api/getPeople?sort=alphabetical
```

### Response

Returns an array of contacts aligned with the Contact model.

```json
[
  {
    "contact_id": "string",
    "first_name": "string",
    "last_name": "string",
    "photo": "https://..."
  }
]
```
