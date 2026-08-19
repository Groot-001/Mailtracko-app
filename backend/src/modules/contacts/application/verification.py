import asyncio
from typing import Any

import httpx

from src.core.config.settings import config
from src.shared.exceptions.base_exceptions import InvalidError, ServerError


class EmailVerificationService:
    """Live Bouncer email verification with bounded retries."""

    max_attempts = 3
    retry_delays = (0.25, 0.75)

    @property
    def endpoint(self) -> str:
        return f"{config.BOUNCER_API_BASE_URL.rstrip('/')}/email/verify"

    async def _request(
        self,
        client: httpx.AsyncClient,
        email: str,
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(self.max_attempts):
            try:
                response = await client.get(
                    self.endpoint,
                    params={
                        "email": email,
                    },
                    headers={
                        "x-api-key": config.BOUNCER_API_KEY,
                        "Accept": "application/json",
                        "User-Agent": "MailTracko/1.0",
                    },
                )

                if response.status_code in {401, 403}:
                    raise InvalidError(
                        error=(
                            "Email verification is temporarily unavailable because "
                            "the verification provider rejected the credentials. "
                            "Contact your administrator."
                        )
                    )

                if response.status_code == 402:
                    raise InvalidError(
                        error=(
                            "Email verification credits are unavailable. "
                            "Contact your administrator."
                        )
                    )

                if response.status_code == 429:
                    raise ServerError(
                        error=(
                            "Email verification is temporarily rate limited. "
                            "Please try again shortly."
                        )
                    )

                if 400 <= response.status_code < 500:
                    raise InvalidError(
                        error=(
                            "The verification provider rejected the verification request."
                        )
                    )

                response.raise_for_status()

                try:
                    payload = response.json()
                except ValueError as exc:
                    raise ServerError(
                        error=(
                            "The email verification provider returned "
                            "an invalid response."
                        )
                    ) from exc

                if not isinstance(payload, dict):
                    raise ServerError(
                        error=(
                            "The email verification provider returned "
                            "an unexpected response."
                        )
                    )

                return payload

            except InvalidError:
                raise

            except ServerError:
                raise

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc

                status_code = (
                    exc.response.status_code
                    if isinstance(exc, httpx.HTTPStatusError)
                    and exc.response is not None
                    else None
                )

                retryable = (
                    status_code is None
                    or status_code >= 500
                )

                if (
                    not retryable
                    or attempt == self.max_attempts - 1
                ):
                    break

                await asyncio.sleep(
                    self.retry_delays[
                        min(attempt, len(self.retry_delays) - 1)
                    ]
                )

        raise ServerError(
            error=(
                "The email verification provider is currently unavailable."
            ),
            internal_details=str(last_error) if last_error else None,
        ) from last_error

    @staticmethod
    def _yes(value: Any) -> bool:
        return str(value or "").strip().lower() == "yes"

    async def verify(self, email: str) -> dict[str, Any]:
        if not config.BOUNCER_API_KEY:
            raise InvalidError(
                error=(
                    "Email verification is not available in this "
                    "MailTracko environment yet. "
                    "Contact your administrator to enable the "
                    "verification service."
                )
            )

        async with httpx.AsyncClient(timeout=35.0) as client:
            payload = await self._request(client, email)

        provider_status = str(
            payload.get("status") or ""
        ).strip().lower()

        if provider_status not in {
            "deliverable",
            "risky",
            "undeliverable",
            "unknown",
        }:
            raise ServerError(
                error=(
                    "The email verification provider returned "
                    "an unknown status."
                )
            )

        domain = payload.get("domain") or {}
        account = payload.get("account") or {}
        dns = payload.get("dns") or {}

        accept_all = self._yes(domain.get("acceptAll"))
        disposable = self._yes(domain.get("disposable"))
        free_email = self._yes(domain.get("free"))
        role_account = self._yes(account.get("role"))
        disabled = self._yes(account.get("disabled"))
        full_mailbox = self._yes(account.get("fullMailbox"))

        # Convert Bouncer statuses into the existing MailTracko
        # verification status vocabulary.
        if provider_status == "deliverable":
            mailtracko_status = "valid"
            bounce_risk = "low"
            default_score = 100

        elif provider_status == "undeliverable":
            mailtracko_status = "invalid"
            bounce_risk = "critical"
            default_score = 0

        elif provider_status == "risky":
            if accept_all:
                mailtracko_status = "catch-all"
                bounce_risk = "medium"
                default_score = 60
            else:
                mailtracko_status = "unknown"
                bounce_risk = "high"
                default_score = 40

        else:
            mailtracko_status = "unknown"
            bounce_risk = "high"
            default_score = 40

        raw_score = payload.get("score")

        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            score = default_score

        score = max(0, min(score, 100))

        return {
            "status": mailtracko_status,
            "sub_status": payload.get("reason"),
            "score": score,
            "bounce_risk": bounce_risk,
            "details": {
                "provider": "bouncer",
                "provider_status": provider_status,
                "reason": payload.get("reason"),
                "free_email": free_email,
                "accept_all": accept_all,
                "disposable": disposable,
                "role_account": role_account,
                "disabled": disabled,
                "full_mailbox": full_mailbox,
                "account": account,
                "domain": domain.get("name"),
                "smtp_provider": payload.get("provider"),
                "mx_found": bool(dns.get("record")),
                "mx_record": dns.get("record"),
                "dns_type": dns.get("type"),
                "toxic": payload.get("toxic"),
                "toxicity": payload.get("toxicity"),
                "retry_after": payload.get("retryAfter"),
            },
        }

    async def verify_many(
        self,
        emails: list[str],
    ) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(10)

        async def guarded(email: str) -> dict[str, Any]:
            async with semaphore:
                return await self.verify(email)

        return await asyncio.gather(
            *(guarded(email) for email in emails)
        )
