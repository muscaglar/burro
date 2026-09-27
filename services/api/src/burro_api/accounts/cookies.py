"""The two cookies of accounts: what each is called, and how each is set.

One holds the session. The other lasts as long as a link, and binds the link to the
browser that asked for it. Each is the website's own, because a browser asks the routes
of accounts of the website and never of the service: so no browser sends either across
sites.

Each is `Secure`, `HttpOnly`, `SameSite=Lax` and for the whole path, names no domain,
and bears the prefix `__Host-`, which a browser takes only from the host itself over
TLS. So no page's script can read one, and no other host of the same domain can put one
of its own in its place.

**In development the website is in the clear, and a browser need take neither the
prefix nor `Secure` from a page in the clear.** Chrome, tried on 2026-09-26, took
neither from a page at `http://127.0.0.1`, and both from one at `http://localhost`. So
in development, and nowhere else, each bears its plain name and is not `Secure`. The
service is in development only where it listens to its own machine alone.
"""

from dataclasses import dataclass
from typing import Literal

from starlette.responses import Response

HOST_ALONE = "__Host-"
SESSION = "burro_session"
LINK = "burro_link"
EVERYWHERE = "/"
SAME_SITE: Literal["lax"] = "lax"


@dataclass(frozen=True)
class Cookies:
    # False only in development, where the website is in the clear.
    secure: bool

    def _named(self, name: str) -> str:
        return f"{HOST_ALONE}{name}" if self.secure else name

    @property
    def session(self) -> str:
        return self._named(SESSION)

    @property
    def link(self) -> str:
        return self._named(LINK)

    def give(self, response: Response, name: str, value: str, lasts_s: int) -> None:
        response.set_cookie(
            name,
            value,
            max_age=lasts_s,
            path=EVERYWHERE,
            secure=self.secure,
            httponly=True,
            samesite=SAME_SITE,
        )

    def take_back(self, response: Response, name: str) -> None:
        response.delete_cookie(
            name, path=EVERYWHERE, secure=self.secure, httponly=True, samesite=SAME_SITE
        )
