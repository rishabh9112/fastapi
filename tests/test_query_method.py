from typing import Optional

from dirty_equals import IsDict
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()


class QuerySchema(BaseModel):
    """Schema for query requests with fields and filters."""
    fields: list[str] = []
    filter: dict = {}
    limit: Optional[int] = None


class Item(BaseModel):
    """Example item model."""
    name: str
    price: Optional[float] = None
    tags: list[str] = []


@app.query("/search")
def query_items(query: QuerySchema):
    """Example query endpoint that accepts a request body."""
    return {
        "query": query.model_dump(),
        "results": ["item1", "item2", "item3"]
    }


@app.query("/search/{category}")
def query_items_by_category(category: str, query: QuerySchema):
    """Query endpoint with path parameter and request body."""
    return {
        "category": category,
        "query": query.model_dump(),
        "results": [f"{category}_item1", f"{category}_item2"]
    }


@app.query("/empty-query")
def query_empty_test():
    """Query endpoint without request body."""
    return {"message": "Empty query executed"}


# Add regular endpoints for comparison
@app.get("/items")
def get_items():
    return {"items": ["item1", "item2"]}


@app.post("/items")
def create_item(item: Item):
    return {"created": item.model_dump()}


client = TestClient(app)


def test_query_with_body():
    """Test QUERY method with request body."""
    query_data = {
        "fields": ["name", "price"],
        "filter": {"category": "electronics"},
        "limit": 10
    }
    response = client.request("QUERY", "/search", json=query_data)
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json["query"] == query_data
    assert "results" in response_json
    assert len(response_json["results"]) == 3


def test_query_with_path_param():
    """Test QUERY method with path parameter and request body."""
    query_data = {
        "fields": ["name"],
        "filter": {},
        "limit": 5
    }
    response = client.request("QUERY", "/search/electronics", json=query_data)
    assert response.status_code == 200, response.text
    response_json = response.json()
    assert response_json["category"] == "electronics"
    assert response_json["query"] == query_data
    assert len(response_json["results"]) == 2


def test_query_without_body():
    """Test QUERY method without request body."""
    response = client.request("QUERY", "/empty-query")
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Empty query executed"}


def test_query_validation_error():
    """Test QUERY method with invalid request body."""
    # Send invalid data - fields should be array, not string
    invalid_data = {
        "fields": "invalid",  # Should be array
        "filter": {"category": "electronics"}
    }
    response = client.request("QUERY", "/search", json=invalid_data)
    assert response.status_code == 422, response.text
    error_detail = response.json()
    assert "detail" in error_detail


def test_query_missing_required_body():
    """Test QUERY method when request body is required but missing."""
    response = client.request("QUERY", "/search")
    assert response.status_code == 422, response.text


def test_openapi_schema_includes_query():
    """Test that the OpenAPI schema includes QUERY methods."""
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    openapi_schema = response.json()
    
    # Check that the schema includes our QUERY endpoints
    paths = openapi_schema["paths"]
    
    # Basic query endpoint
    assert "/search" in paths
    assert "query" in paths["/search"]
    query_operation = paths["/search"]["query"]
    assert query_operation["summary"] == "Query Items"
    assert query_operation["operationId"] == "query_items_search_query"
    
    # Check request body is included
    assert "requestBody" in query_operation
    request_body = query_operation["requestBody"]
    assert request_body["required"] is True
    assert "application/json" in request_body["content"]
    
    # Query with path parameter
    assert "/search/{category}" in paths
    assert "query" in paths["/search/{category}"]
    category_operation = paths["/search/{category}"]["query"]
    assert category_operation["summary"] == "Query Items By Category"
    
    # Check path parameter is included
    assert "parameters" in category_operation
    parameters = category_operation["parameters"]
    assert len(parameters) == 1
    assert parameters[0]["name"] == "category"
    assert parameters[0]["in"] == "path"
    
    # Query without body
    assert "/empty-query" in paths
    assert "query" in paths["/empty-query"]
    empty_operation = paths["/empty-query"]["query"]
    assert empty_operation["summary"] == "Query Empty Test"
    # Should not have requestBody since no body parameter
    assert "requestBody" not in empty_operation


def test_query_vs_other_methods():
    """Test that QUERY method coexists with other HTTP methods."""
    # Test GET endpoint still works
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == {"items": ["item1", "item2"]}
    
    # Test POST endpoint still works
    item_data = {"name": "test item", "price": 10.0, "tags": ["test"]}
    response = client.post("/items", json=item_data)
    assert response.status_code == 200
    assert response.json()["created"] == item_data


def test_query_content_type():
    """Test QUERY method with different content types."""
    query_data = {
        "fields": ["name"],
        "filter": {},
        "limit": 1
    }
    
    # Test with JSON content type
    response = client.request(
        "QUERY", 
        "/search", 
        json=query_data,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    
    # Test response content type
    assert "application/json" in response.headers.get("content-type", "")


def test_query_method_case_sensitivity():
    """Test that QUERY method works with different case variations."""
    query_data = {"fields": ["name"], "filter": {}}
    
    # Test uppercase QUERY
    response = client.request("QUERY", "/search", json=query_data)
    assert response.status_code == 200
    
    # Test lowercase query
    response = client.request("query", "/search", json=query_data)
    assert response.status_code == 200


if __name__ == "__main__":
    import uvicorn
    # Run the test app to see it in action
    uvicorn.run(app, host="127.0.0.1", port=8000)