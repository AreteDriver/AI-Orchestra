"""Prompt template management."""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from test_ai.config import get_settings


class PromptTemplate(BaseModel):
    """A reusable prompt template."""

    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Template description")
    system_prompt: Optional[str] = Field(None, description="System prompt")
    user_prompt: str = Field(..., description="User prompt template")
    variables: List[str] = Field(
        default_factory=list, description="Variables in the prompt"
    )
    model: str = Field("gpt-4o-mini", description="Default model to use")
    temperature: float = Field(0.7, description="Default temperature")

    def format(self, **kwargs) -> str:
        """Format the prompt with variables."""
        return self.user_prompt.format(**kwargs)


class PromptTemplateManager:
    """Manages prompt templates stored as JSON files."""

    def __init__(self):
        settings = get_settings()
        self.templates_dir = settings.prompts_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, template: PromptTemplate) -> bool:
        """Save a template to disk."""
        try:
            file_path = self.templates_dir / f"{template.id}.json"
            with open(file_path, "w") as f:
                json.dump(template.model_dump(), f, indent=2)
            return True
        except Exception:
            return False

    def load_template(self, template_id: str) -> Optional[PromptTemplate]:
        """Load a template from disk."""
        try:
            file_path = self.templates_dir / f"{template_id}.json"
            with open(file_path, "r") as f:
                data = json.load(f)
            return PromptTemplate(**data)
        except Exception:
            return None

    def list_templates(self) -> List[Dict]:
        """List all available templates."""
        templates = []
        for file_path in self.templates_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                templates.append(
                    {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "description": data.get("description"),
                    }
                )
            except Exception:
                continue
        return templates

    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        try:
            file_path = self.templates_dir / f"{template_id}.json"
            file_path.unlink()
            return True
        except Exception:
            return False

    def create_default_templates(self):
        """Create default templates."""
        default_templates = [
            PromptTemplate(
                id="email_summary",
                name="Email Summary",
                description="Summarize email content",
                system_prompt="You are a helpful assistant that creates concise email summaries.",
                user_prompt="Please summarize this email:\n\n{email_content}",
                variables=["email_content"],
            ),
            PromptTemplate(
                id="sop_generator",
                name="SOP Generator",
                description="Generate Standard Operating Procedures",
                system_prompt="You are an expert at creating clear, detailed Standard Operating Procedures.",
                user_prompt="Create a detailed SOP for: {task_description}",
                variables=["task_description"],
            ),
            PromptTemplate(
                id="meeting_notes",
                name="Meeting Notes",
                description="Generate meeting notes from transcript",
                system_prompt="You are an expert at organizing meeting notes.",
                user_prompt="Create structured meeting notes from this transcript:\n\n{transcript}\n\nInclude: key points, action items, and decisions.",
                variables=["transcript"],
            ),
            PromptTemplate(
                id="code_review",
                name="Code Review",
                description="Generate code review comments",
                system_prompt="You are an experienced software engineer reviewing code.",
                user_prompt="Review this code and provide constructive feedback:\n\n{code}",
                variables=["code"],
            ),
        ]

        for template in default_templates:
            self.save_template(template)
