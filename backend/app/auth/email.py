from html import escape
from typing import Protocol

import resend


class VerificationEmailSender(Protocol):
    async def send_verification(
        self, recipient: str, verification_url: str
    ) -> None: ...


class ResendVerificationEmailSender:
    """Deliver account confirmation links through Resend's asynchronous API."""

    def __init__(self, api_key: str, from_email: str) -> None:
        self._api_key = api_key
        self._from_email = from_email

    async def send_verification(self, recipient: str, verification_url: str) -> None:
        resend.api_key = self._api_key
        safe_url = escape(verification_url, quote=True)
        await resend.Emails.send_async(
            {
                "from": self._from_email,
                "to": [recipient],
                "subject": "Confirm your email",
                "html": (
                    "<p>Confirm your email address to finish creating your account.</p>"
                    f'<p><a href="{safe_url}">Confirm email</a></p>'
                    "<p>This link expires in one hour.</p>"
                ),
            }
        )


class UnavailableVerificationEmailSender:
    """Fail safely when local development has no Resend API key configured."""

    async def send_verification(self, recipient: str, verification_url: str) -> None:
        raise RuntimeError("Resend is not configured")


class RecordingVerificationEmailSender:
    """Capture verification deliveries for tests without external requests."""

    def __init__(self) -> None:
        self.deliveries: list[tuple[str, str]] = []

    async def send_verification(self, recipient: str, verification_url: str) -> None:
        self.deliveries.append((recipient, verification_url))
