"""Google Gemini API client wrapper."""

from typing import Optional, List, Dict

from test_ai.config import get_settings

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiClient:
    """Wrapper for Google Gemini API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_api_key
        if self.api_key and genai:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    def is_configured(self) -> bool:
        """Check if Gemini client is configured."""
        return self.model is not None and bool(self.api_key)

    def generate_completion(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a completion from a prompt.

        Args:
            prompt: The user prompt
            model: Gemini model to use
            temperature: Temperature for generation
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt

        Returns:
            Generated text content
        """
        if not self.is_configured():
            raise RuntimeError("Gemini client not configured")

        # Create model with specified name if different from default
        if model != "gemini-1.5-flash":
            generation_model = genai.GenerativeModel(model)
        else:
            generation_model = self.model

        # Build the full prompt with system prompt if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens

        response = generation_model.generate_content(
            full_prompt,
            generation_config=generation_config,
        )

        return response.text

    def review_code(self, code: str, context: Optional[str] = None) -> str:
        """Review code using Gemini.

        Args:
            code: The code to review
            context: Optional context about the code

        Returns:
            Code review comments and suggestions
        """
        system_prompt = """You are a code review agent. Analyze the implementation for:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

Provide constructive, actionable feedback with specific line references where applicable."""

        prompt = f"Review the following code:\n\n```\n{code}\n```"
        if context:
            prompt += f"\n\nContext:\n{context}"

        return self.generate_completion(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower temperature for more focused reviews
        )

    def summarize_text(self, text: str, max_length: int = 500) -> str:
        """Summarize text using Gemini.

        Args:
            text: Text to summarize
            max_length: Maximum length in words

        Returns:
            Summary text
        """
        prompt = f"Please provide a concise summary (max {max_length} words) of the following text:\n\n{text}"
        return self.generate_completion(
            prompt=prompt,
            system_prompt="You are a helpful assistant that creates clear, concise summaries.",
            temperature=0.5,
        )

    def generate_sop(self, task_description: str) -> str:
        """Generate a Standard Operating Procedure.

        Args:
            task_description: Description of the task

        Returns:
            Generated SOP
        """
        prompt = f"Create a detailed Standard Operating Procedure (SOP) for: {task_description}"
        return self.generate_completion(
            prompt=prompt,
            system_prompt="You are an expert at creating clear, detailed Standard Operating Procedures.",
            temperature=0.5,
        )
