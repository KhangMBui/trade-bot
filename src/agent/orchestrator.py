from __future__ import annotations

import json

from .provider import ModelProvider
from .schemas import PortfolioAgentAnswer
from .tools.portfolio import get_current_portfolio_analysis


SYSTEM_PROMPT = """
You are a cautious personal portfolio research assistant.

You explain validated portfolio analytics supplied by the application.

Rules:
- Use only the supplied data.
- Never invent prices, percentages, dates, holdings, or facts.
- Do not claim that an investment will rise or fall.
- Do not place trades.
- Do not provide personalized financial advice.
- Treat risk flags as warnings, not automatic trade instructions.
- Clearly distinguish observations from suggestions.
- Recommend no action when the data is insufficient.
- Mention missing or stale data.
- Keep the response concise and practical.
"""


def analyze_current_portfolio(
    provider: ModelProvider,
) -> PortfolioAgentAnswer:
  """
  Analyze the latest saved portfolio and ask the model to explain it.
  """
  analysis = get_current_portfolio_analysis()

  analysis_json = analysis.model_dump(
    mode="json",
  )

  response_text = provider.explain(
    system_prompt=SYSTEM_PROMPT,
    user_input=json.dumps(
      {
        "task": "Explain the current portfolio analysis.",
        "portfolio_analysis": analysis_json,
      },
      indent=2,
    ),
  )

  return PortfolioAgentAnswer(
    summary=response_text,
    risk_flags=list(analysis.risk_flags),
  )