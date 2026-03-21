#!/usr/bin/env python3
"""
Test RAG Search Functionality
"""
import requests
import json

def test_rag_search():
    """Test the RAG search endpoint"""
    try:
        # Test health first
        health_response = requests.get('http://localhost:8000/health')
        print(f"✅ Health check: {health_response.status_code}")
        print(f"Response: {health_response.json()}")
        print()

        # Test RAG search
        query = "sugar regulations"
        response = requests.get(f'http://localhost:8000/rag-search?query={query}&top_k=2')

        if response.status_code == 200:
            result = response.json()
            print('🎯 RAG SEARCH RESULTS:')
            print(f'Query: "{result["query"]}"')
            print(f'Found: {result["found"]}')
            print(f'Total results: {result["total"]}')
            print()

            if result['results']:
                for i, r in enumerate(result['results'], 1):
                    print(f'📄 Result {i}:')
                    print(f'   Source: {r.get("source_file", "Unknown")}')
                    print(f'   Score: {r.get("score", "N/A"):.3f}')
                    text = r.get("text", "")
                    print(f'   Text: {text[:300]}{"..." if len(text) > 300 else ""}')
                    print()
            else:
                print('❌ No results found - RAG vector store may need more documents')
        else:
            print(f"❌ RAG search failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rag_search()