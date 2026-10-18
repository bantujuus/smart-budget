"""Small post-processing step for the generated OpenAPI document."""

CSRF_HEADER = {
    "name": "X-CSRFToken",
    "in": "header",
    "required": True,
    "description": "Value of the `csrftoken` cookie (get it from `GET /auth/csrf/`).",
    "schema": {"type": "string"},
}


def add_csrf_header(result, generator, request, public):
    """Every state-changing request needs the CSRF header; say so on each operation."""
    for path_item in result.get("paths", {}).values():
        for method in ("post", "patch", "put", "delete"):
            operation = path_item.get(method)
            if operation is not None:
                operation.setdefault("parameters", []).append(CSRF_HEADER)
    return result