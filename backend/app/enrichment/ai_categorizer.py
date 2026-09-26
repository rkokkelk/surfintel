"""Severity/category classification.

This first version is a plain keyword heuristic, not an LLM call — no AI
provider/API key has been chosen for the project yet. It is a genuine,
working v1 (not a stub): swapping it for an LLM-backed classifier later is a
drop-in replacement behind the same EnrichmentModule interface, and the
result shape (`severity`, `category`) stays the same either way.
"""
import os
from typing import Literal

import instructor
from pydantic import BaseModel, Field, PositiveInt
from pydantic_extra_types.country import CountryAlpha2

from app.enrichment.base import EnrichmentModule
from app.models.item import Item


class ItemClassification(BaseModel):
    victim_country: CountryAlpha2 | None = Field(description="The country code that is the vicim within the article.")
    victim_industry: Literal[
        'government', 'defense', 'finance', 'healthcare', 'energy', 'utilities',
        'telecom', 'technology', 'manufacturing', 'transportation',
        'retail', 'media', 'education', 'ngo'
    ] | None = Field(description="The industry that is the vicim within the article.")
    actor: str | None = Field(description="The name of the malicious group or actor.")
    severity: Literal['critical', 'high', 'medium', 'low'] = Field(description="The risk associated with the content.")
    entity: list[str] | None = Field(description="The names of all related entities or vendors.")
    impact: PositiveInt = Field(description='The impact score associated with the article.', ge=1, le=5)
    chance: PositiveInt = Field(description='The change score associated with the article.', ge=1, le=5)


class AiCategorizer(EnrichmentModule):
    version = "2"
    name = "ai_categorizer"
    source_toggle = "enrich_ai"

    def run(self, item: Item) -> dict:
        client = instructor.from_provider(
            "azure_openai/gpt-5.4-mini",
            api_key=os.environ['AZURE_OPENAI_KEY'],
            azure_endpoint="https://swedencentral.api.cognitive.microsoft.com/",
            api_version="2024-12-01-preview"
        )

        # Extract structured data from natural language
        classification = client.create(
            response_model=ItemClassification,
            messages=[
                {"role": "system", "content": "You are an expert AI classifier for classifying Cyber Threat Intelligence articles. Make the classifications as short as possible."},
                {"role": "user", "content": item.extracted_text}
            ],
        )

        return classification.model_dump()

    def match_fields(self, data: dict) -> dict:
        fields: dict[str, list[str]] = {}
        if data.get("severity"):
            fields["severity"] = [data["severity"]]
        if data.get("category"):
            fields["category"] = [data["category"]]
        return fields
