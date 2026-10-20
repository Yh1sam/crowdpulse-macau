"""Approval policy while the prototype has no field-verification evidence workflow.

Map attributes and a runnable closure model do not verify an actual diversion.
Keep this independent of UI metadata so legacy rows and direct API calls fail closed.
"""

ROUTE_REVIEW_REASON = (
    "Route accessibility has not been verified on site. "
    "Request a field check or reject this diversion. "
    "Approval remains blocked; requesting a check does not verify the route."
)


def approval_block_reason(kind: str) -> str | None:
    return ROUTE_REVIEW_REASON if kind == "redirect_flow" else None
