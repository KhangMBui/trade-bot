from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class ModelProvider(Protocol):
  """Provider-independent interface for language models."""

  def explain(
    self,
    *,
    system_prompt: str,
    user_input: str,
  ) -> str:
    ...