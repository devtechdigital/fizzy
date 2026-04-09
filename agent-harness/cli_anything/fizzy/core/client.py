"""HTTP client for the Fizzy API."""

import requests


class FizzyAPIError(Exception):
    """Raised when the Fizzy API returns an error."""

    def __init__(self, status_code: int, message: str, response_body=None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(f"[{status_code}] {message}")


class FizzyClient:
    """HTTP client for Fizzy's JSON API.

    All requests include Bearer token auth and JSON headers.
    """

    def __init__(self, base_url: str, access_token: str, account_prefix: str = "/1"):
        self.base_url = base_url.rstrip("/")
        self.account_prefix = account_prefix.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _url(self, path: str) -> str:
        """Build full URL from path, prepending the account prefix."""
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{self.account_prefix}{path}"

    def _handle_response(self, resp: requests.Response):
        """Parse response, raising descriptive errors on failure."""
        if resp.status_code in (200, 201, 204):
            if resp.status_code == 204 or not resp.content:
                return None
            return resp.json()

        # Build error message
        try:
            body = resp.json()
        except Exception:
            body = resp.text

        error_messages = {
            401: "Authentication failed. Check your access token.",
            403: "Permission denied. Your token may lack the required scope.",
            404: "Resource not found.",
            422: f"Validation error: {body}",
            500: "Internal server error. Try again later.",
        }
        message = error_messages.get(
            resp.status_code,
            f"Unexpected error: {body}",
        )
        raise FizzyAPIError(resp.status_code, message, body)

    def get(self, path: str, params: dict | None = None):
        """GET request."""
        resp = self.session.get(self._url(path), params=params)
        return self._handle_response(resp)

    def post(self, path: str, data: dict | None = None):
        """POST request."""
        resp = self.session.post(self._url(path), json=data)
        return self._handle_response(resp)

    def patch(self, path: str, data: dict | None = None):
        """PATCH request."""
        resp = self.session.patch(self._url(path), json=data)
        return self._handle_response(resp)

    def delete(self, path: str):
        """DELETE request."""
        resp = self.session.delete(self._url(path))
        return self._handle_response(resp)
