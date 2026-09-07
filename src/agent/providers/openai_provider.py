from __future__ import annotations

from openai import OpenAI

from ...config import settings


class OpenAIProvider:
  """OpenAI implementation of the provider-independent model interface."""

  def __init__(
      self,
      *,
      api_key: str | None = None,
      model: str | None = None,
    ):
      self._client = OpenAI(
        api_key=api_key or settings.OPENAI_API_KEY,
      )
      self._model = model or settings.OPENAI_MODEL

  def explain(
    self,
    *,
    system_prompt: str,
    user_input: str,
  ) -> str:
    response = self._client.responses.create(
      model=self._model,
      instructions=system_prompt,
      input=user_input,
    )
    return response.output_text