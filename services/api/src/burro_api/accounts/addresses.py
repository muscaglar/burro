"""The address a person signs in with: made regular, and checked for its shape.

An account is known by its address as it is made regular here, and a link is sent to
that and to nothing else. So two ways of writing an address come to one account only
where they come to one mailbox. The letters are put in lower case, and nothing else is
changed: a full stop or a plus sign before the `@` is part of the address, because some
hosts of mail read them as one mailbox and some as two.

An address that is not in plain letters is refused. Folded into plain letters it may be
the address of somebody else, and an account that two mailboxes can open is an account
that the wrong one can.
"""

import re

LONGEST = 254
LONGEST_LOCAL = 64
LONGEST_DOMAIN = 253

# The part before the `@`: words of letters, digits and the marks the standard for mail
# allows, with one full stop between two of them. No space, no quote, and nothing that
# could begin a line of its own in a message.
_LOCAL = re.compile(r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*")
# A label of a host: letters, digits and hyphens, with a letter or a digit at each end.
_LABEL = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?")


def regular(typed: str) -> str | None:
    """The address made regular, or `None` where what was typed is not in the shape of one."""
    address = typed.strip()
    if not address.isascii() or len(address) > LONGEST:
        return None
    local, at, domain = address.lower().rpartition("@")
    if not at or not 0 < len(local) <= LONGEST_LOCAL or len(domain) > LONGEST_DOMAIN:
        return None
    if _LOCAL.fullmatch(local) is None:
        return None
    labels = domain.split(".")
    # Mail goes to a name, of two parts at the least, and never to a machine by its number.
    if len(labels) < 2 or labels[-1].isdigit():
        return None
    if not all(_LABEL.fullmatch(label) for label in labels):
        return None
    return f"{local}@{domain}"
