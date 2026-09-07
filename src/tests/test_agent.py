from decimal import Decimal

from src.agent.orchestrator import analyze_current_portfolio
from src.agent.schemas import PortfolioAgentAnswer


class FakeProvider:
  def explain(self, *, system_prompt: str, user_input: str) -> str:
    assert "portfolio_analysis" in user_input
    return "The portfolio analysis was reviewed successfully."


def test_agent_returns_validated_answer(monkeypatch) -> None:
  class FakeAnalysis:
    risk_flags = ["Cash is below 5% minimum"]

    def model_dump(self, mode: str) -> dict:
      return {
        "account_id_key": "account-key",
        "position_count": 2,
        "total_market_value": "10000",
        "cash_weight": "0.05",
        "risk_flags": self.risk_flags,
      }

  monkeypatch.setattr(
    "src.agent.orchestrator.get_current_portfolio_analysis",
    lambda: FakeAnalysis(),
  )

  result = analyze_current_portfolio(FakeProvider())

  assert isinstance(result, PortfolioAgentAnswer)
  assert "successfully" in result.summary
  assert result.risk_flags == ["Cash is below 5% minimum"]