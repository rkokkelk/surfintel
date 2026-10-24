"""Mitre classification.
"""
import instructor
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.enrichment.base import EnrichmentModule
from app.models.item import Item


class ItemTTP(BaseModel):
    tactic_id: str = Field(description="The exact Mitre ATT&CK tactic id")
    tactic_name: str = Field(description="The name of the Mitre ATT&CK tactic")
    technique_id: str = Field(description="The exact MITRE ATT&CK Technique ID (e.g., T1059.001)")
    technique_name: str = Field(description="The name of the Mitre ATT&CK Technique")
    quote: str = Field(description="The short extract of content on which you based the TTP classification on")

class ItemMitreClassificaiton(BaseModel):
    ttps: list[ItemTTP] | None  = Field(description="List of identified TTPs, may be empty.")

class MitreCategorizer(EnrichmentModule):
    version = "1"
    name = "mitre_categorizer"
    source_toggle = "enrich_mitre"

    def run(self, item: Item, db: Session) -> dict:
        self.log = logger.bind(source=item.source_id, item=item.id)
        client = instructor.from_provider(
            settings.azure_openai_model,
            api_key=settings.azure_openai_key,
            azure_endpoint=settings.azure_openai_url,
            api_version=settings.azure_openai_version
        )

        self.log.trace("{}[{}] - starting classification", self.name, item.id)

        # Extract structured data from natural language
        classification = client.create(
            response_model=ItemMitreClassificaiton,
            messages=[
                {"role": "system", "content": "You are an expert AI classifier for classifying Cyber Threat Intelligence articles to the Mitre Attack framework. Make the classifications ONLY if there is a clear indicator of a used TTP."},
                {"role": "user", "content": item.extracted_text}
            ],
        )

        self.log.info("finished {}: classification finished", self.name, item.id)

        return classification.model_dump()

    def match_fields(self, data: dict) -> dict:
        technique_ids = sorted({ttp["technique_id"] for ttp in (data.get("ttps") or []) if ttp.get("technique_id")})
        return {"ttp": technique_ids} if technique_ids else {}
