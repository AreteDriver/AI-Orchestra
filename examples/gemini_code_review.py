"""Example: Using Google Gemini for code review.

This example demonstrates how to use the GeminiClient to review code,
generate completions, and create summaries.

Prerequisites:
    - Set GOOGLE_API_KEY environment variable
    - pip install google-generativeai
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_ai.api_clients.gemini_client import GeminiClient


def main():
    """Demonstrate Gemini client capabilities."""
    
    # Initialize client
    print("Initializing Gemini client...")
    client = GeminiClient()
    
    if not client.is_configured():
        print("❌ Gemini client not configured. Please set GOOGLE_API_KEY environment variable.")
        return
    
    print("✓ Gemini client configured\n")
    
    # Example 1: Code Review
    print("=" * 60)
    print("Example 1: Code Review")
    print("=" * 60)
    
    sample_code = """
def process_user_data(user_id, data):
    # Fetch user from database
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Update user data
    user['name'] = data['name']
    user['email'] = data['email']
    
    # Save to database
    db.save(user)
    return user
"""
    
    print("Reviewing code...")
    review = client.review_code(
        code=sample_code,
        context="Python function for updating user data in a web application"
    )
    print("\nCode Review Results:")
    print(review)
    print()
    
    # Example 2: Text Summarization
    print("=" * 60)
    print("Example 2: Text Summarization")
    print("=" * 60)
    
    long_text = """
    Microservices architecture is an architectural style that structures an application 
    as a collection of loosely coupled services. Each service is fine-grained and the 
    protocols are lightweight. The benefit of decomposing an application into different 
    smaller services is that it improves modularity. This makes the application easier 
    to understand, develop, test, and become more resilient to architecture erosion.
    
    It also parallelizes development by enabling small autonomous teams to develop, 
    deploy and scale their respective services independently. It also allows the 
    architecture of an individual service to emerge through continuous refactoring.
    
    Microservice-based architectures enable continuous delivery and deployment.
    """
    
    print("Summarizing text...")
    summary = client.summarize_text(long_text, max_length=50)
    print("\nSummary:")
    print(summary)
    print()
    
    # Example 3: Generate SOP
    print("=" * 60)
    print("Example 3: Generate Standard Operating Procedure")
    print("=" * 60)
    
    print("Generating SOP...")
    sop = client.generate_sop(
        "Deploying a Python FastAPI application to production using Docker and Kubernetes"
    )
    print("\nGenerated SOP:")
    print(sop)
    print()
    
    # Example 4: Generic Completion
    print("=" * 60)
    print("Example 4: Generic Completion")
    print("=" * 60)
    
    print("Generating completion...")
    completion = client.generate_completion(
        prompt="Explain the key differences between REST and GraphQL APIs in 3 bullet points",
        temperature=0.5
    )
    print("\nCompletion:")
    print(completion)
    print()


if __name__ == "__main__":
    main()
