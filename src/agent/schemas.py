from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class PortfolioAgentAnswer(BaseModel):
  """Validated response produced by the research agent."""

  model_config = ConfigDict(extra="forbid")

  summary: str
  observations: list[str] = Field(default_factory=list)
  risk_flags: list[str] = Field(default_factory=list)
  data_warnings: list[str] = Field(default_factory=list)
  suggested_next_steps: list[str] = Field(default_factory=list)

  disclaimer: str = (
    "This is research assistance, not financial advice. "
    "Review all information before making an investment decision."
  )