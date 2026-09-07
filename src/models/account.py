from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Account(BaseModel):
	"""Normalized account information used by the application."""

	model_config = ConfigDict(extra="ignore")

	account_id: str | None = Field(default=None, alias="accountId")
	account_id_key: str = Field(alias="accountIdKey")
	account_mode: str | None = Field(default=None, alias="accountMode")
	description: str | None = Field(default=None, alias="accountDesc")
	name: str | None = Field(default=None, alias="accountName")
	account_type: str | None = Field(default=None, alias="accountType")
	institution_type: str | None = Field(default=None, alias="institutionType")
	status: str | None = Field(default=None, alias="accountStatus")
	closed_date: int | None = Field(default=None, alias="closedDate")
	share_works_account: bool | None = Field(
		default=None, alias="shareWorksAccount"
	)
	fc_managed_mssb_closed_account: bool | None = Field(
		default=None, alias="fcManagedMssbClosedAccount"
	)

	@property
	def display_name(self) -> str:
		return self.name or self.description or self.account_id_key


class AccountList(BaseModel):
	"""Normalized response from E*TRADE's account-list endpoint."""

	model_config = ConfigDict(extra="ignore")

	accounts: list[Account] = Field(default_factory=list)

	@classmethod
	def from_etrade_payload(cls, payload: dict) -> AccountList:
		response = payload.get("AccountListResponse", {})
		account_items = response.get("Accounts", {}).get("Account", [])
		if isinstance(account_items, dict):
			account_items = [account_items]
		return cls(accounts=[Account.model_validate(item) for item in account_items])
