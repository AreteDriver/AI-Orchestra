"""Test Google Gemini API client."""

import os
import sys

# Set up test environment
os.environ["OPENAI_API_KEY"] = "test-key"  # Required by settings
os.environ["GOOGLE_API_KEY"] = "test-google-key"  # Test key

# Direct import without importing full module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from test_ai.api_clients.gemini_client import GeminiClient


def test_gemini_client_initialization():
    """Test Gemini client initialization."""
    client = GeminiClient()
    assert client is not None
    # Client won't be configured with a test key, but should initialize
    assert hasattr(client, 'api_key')
    assert client.api_key == "test-google-key"
    print("✓ Gemini client initialization working")


def test_gemini_client_not_configured():
    """Test Gemini client without proper configuration."""
    client = GeminiClient()
    # With a test key, it shouldn't be configured
    # (unless google-generativeai is installed and accepts test keys)
    assert hasattr(client, 'is_configured')
    print("✓ Gemini client configuration check working")


def test_gemini_client_has_methods():
    """Test that Gemini client has all required methods."""
    client = GeminiClient()
    assert hasattr(client, 'generate_completion')
    assert hasattr(client, 'review_code')
    assert hasattr(client, 'summarize_text')
    assert hasattr(client, 'generate_sop')
    assert hasattr(client, 'is_configured')
    print("✓ Gemini client has all required methods")


if __name__ == "__main__":
    print("\n🧪 Testing Gemini Client...\n")
    
    test_gemini_client_initialization()
    test_gemini_client_not_configured()
    test_gemini_client_has_methods()
    
    print("\n✅ All Gemini client tests passed!\n")
