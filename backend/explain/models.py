"""Structured shapes the explanation agents must return."""
from pydantic import BaseModel, Field


class Claim(BaseModel):
    """One factual statement and the insight fields that support it."""

    text: str = Field(description="One sentence stating a single fact about the play.")
    evidence: list[str] = Field(description="Names of the insight fields this sentence relies on.")


class Explanation(BaseModel):
    headline: str = Field(description="A short headline, at most 12 words.")
    claims: list[Claim] = Field(description="Two to four claims that together explain the insight.")


class Review(BaseModel):
    approved: bool
    issues: list[str] = Field(description="Each claim or phrase not supported by the insight, and why.")
