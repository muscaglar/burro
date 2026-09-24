"""The one configuration every record shares."""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class Record(BaseModel):
    """Frozen and closed to unknown fields: a typo fails loudly, nothing changes in place."""

    # A validation error is likely to be logged. What failed to validate may be
    # what a person typed, so the error says where and why and never shows it.
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)

    def replace(self, **changes: Any) -> Self:
        """A copy with some fields changed, validated like any other record.

        `model_copy(update=...)` skips validation, so it would let through a
        weight that was never snapped or a tuple that was never sorted.
        """
        fields = {name: getattr(self, name) for name in type(self).model_fields}
        return type(self)(**(fields | changes))
