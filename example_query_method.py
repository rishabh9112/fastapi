#!/usr/bin/env python3
"""
FastAPI QUERY Method Example

This script demonstrates the new QUERY HTTP method support in FastAPI.
The QUERY method allows for safe HTTP requests with a request body,
following the IETF draft specification for safe methods with body.

Run this script and navigate to http://localhost:8000/docs to see
the QUERY method in the automatically generated documentation.
"""

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="FastAPI QUERY Method Demo",
    description="Demonstration of the new QUERY HTTP method support",
    version="1.0.0"
)

# Example models
class QueryFilter(BaseModel):
    """Schema for query filters."""
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    tags: list[str] = []

class FieldSelector(BaseModel):
    """Schema for selecting which fields to return."""
    fields: list[str] = ["id", "name", "price"]
    include_metadata: bool = False

class SearchQuery(BaseModel):
    """Complete search query with filters and field selection."""
    filters: QueryFilter = QueryFilter()
    fields: FieldSelector = FieldSelector()
    limit: int = 10
    offset: int = 0

class Item(BaseModel):
    """Example item model."""
    id: int
    name: str
    price: float
    category: str
    tags: list[str] = []
    metadata: dict = {}

# Sample data
SAMPLE_ITEMS = [
    Item(id=1, name="Laptop", price=999.99, category="electronics", tags=["computer", "portable"], metadata={"weight": "2kg"}),
    Item(id=2, name="Book", price=19.99, category="education", tags=["reading", "paperback"], metadata={"pages": 300}),
    Item(id=3, name="Coffee Mug", price=12.50, category="kitchen", tags=["ceramic", "dishwasher-safe"], metadata={"capacity": "350ml"}),
    Item(id=4, name="Smartphone", price=599.99, category="electronics", tags=["mobile", "5G"], metadata={"storage": "128GB"}),
    Item(id=5, name="Cookbook", price=29.99, category="education", tags=["recipes", "cooking"], metadata={"cuisine": "Italian"}),
]

@app.get("/")
def root():
    """Welcome message with links to documentation."""
    return {
        "message": "Welcome to FastAPI QUERY Method Demo!",
        "documentation": "/docs",
        "alternative_docs": "/redoc",
        "example_endpoints": {
            "search_items": "/search (QUERY method)",
            "search_by_category": "/search/{category} (QUERY method)", 
            "simple_search": "/simple-search (QUERY method, no body)",
            "all_items": "/items (GET method for comparison)"
        }
    }

@app.query("/search")
def search_items(query: SearchQuery):
    """
    Advanced search using QUERY method with request body.
    
    This endpoint demonstrates the power of the QUERY method:
    - Safe operation (no side effects)
    - Complex query parameters in request body
    - Flexible field selection
    - Better than GET for complex queries that don't fit in URL parameters
    """
    # Apply filters
    filtered_items = SAMPLE_ITEMS.copy()
    
    if query.filters.category:
        filtered_items = [item for item in filtered_items if item.category == query.filters.category]
    
    if query.filters.min_price is not None:
        filtered_items = [item for item in filtered_items if item.price >= query.filters.min_price]
        
    if query.filters.max_price is not None:
        filtered_items = [item for item in filtered_items if item.price <= query.filters.max_price]
        
    if query.filters.tags:
        filtered_items = [item for item in filtered_items if any(tag in item.tags for tag in query.filters.tags)]
    
    # Apply pagination
    total = len(filtered_items)
    start = query.offset
    end = start + query.limit
    paged_items = filtered_items[start:end]
    
    # Apply field selection
    results = []
    for item in paged_items:
        result = {}
        item_dict = item.model_dump()
        
        for field in query.fields.fields:
            if field in item_dict:
                result[field] = item_dict[field]
        
        if query.fields.include_metadata:
            result["metadata"] = item.metadata
            
        results.append(result)
    
    return {
        "query": query.model_dump(),
        "results": results,
        "pagination": {
            "total": total,
            "offset": query.offset,
            "limit": query.limit,
            "has_more": end < total
        }
    }

@app.query("/search/{category}")
def search_by_category(category: str, query: FieldSelector):
    """
    Search items in a specific category using QUERY method.
    
    Combines path parameters with request body - something that's
    awkward with GET but natural with QUERY.
    """
    # Filter by category
    category_items = [item for item in SAMPLE_ITEMS if item.category == category]
    
    # Apply field selection
    results = []
    for item in category_items:
        result = {}
        item_dict = item.model_dump()
        
        for field in query.fields:
            if field in item_dict:
                result[field] = item_dict[field]
        
        if query.include_metadata:
            result["metadata"] = item.metadata
            
        results.append(result)
    
    return {
        "category": category,
        "field_selector": query.model_dump(),
        "results": results,
        "count": len(results)
    }

@app.query("/simple-search")
def simple_search():
    """
    Simple QUERY method without request body.
    
    Demonstrates that QUERY methods work fine without request bodies,
    just like GET methods.
    """
    return {
        "message": "Simple QUERY executed successfully",
        "method": "QUERY",
        "total_items": len(SAMPLE_ITEMS),
        "note": "This QUERY method doesn't require a request body"
    }

# Traditional endpoints for comparison
@app.get("/items")
def get_all_items():
    """Traditional GET endpoint for comparison."""
    return {
        "items": SAMPLE_ITEMS,
        "count": len(SAMPLE_ITEMS),
        "note": "This is a traditional GET endpoint for comparison"
    }

@app.post("/items")
def create_item(item: Item):
    """Traditional POST endpoint for comparison."""
    return {
        "message": "Item would be created",
        "item": item,
        "note": "This is a traditional POST endpoint for comparison"
    }

if __name__ == "__main__":
    print("Starting FastAPI QUERY Method Demo...")
    print("Navigate to http://localhost:8000/docs to see the interactive documentation")
    print("Try the QUERY endpoints to see how they work!")
    print("\nExample QUERY request:")
    print("curl -X QUERY http://localhost:8000/search \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"filters\": {\"category\": \"electronics\"}, \"fields\": {\"fields\": [\"name\", \"price\"]}}'")
    print()
    
    uvicorn.run(app, host="127.0.0.1", port=8000)