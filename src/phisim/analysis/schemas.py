from pydantic import BaseModel, Field


class Indicator(BaseModel):
    code: str = Field(description="Stable identifier for the indicator type")
    category: str = Field(description="General category of the indicator")
    context: str = Field(description="Severity or contextual weight")
    evidence: str = Field(
        description="The specific string or value that triggered the rule"
    )
    explanation: str = Field(
        description="Why this is considered an indicator of phishing"
    )
