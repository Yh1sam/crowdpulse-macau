import type { Intervention } from "@/lib/types";

/** Fail closed for redirects, including responses from an older backend without the policy fields. */
export function diversionApprovalBlocked(iv: Intervention): boolean {
  return iv.kind === "redirect_flow" || iv.approval_blocked === true;
}

export function RouteReview({ iv, disabled, onRequest }: {
  iv: Intervention; disabled: boolean; onRequest: () => void;
}) {
  if (iv.kind !== "redirect_flow") return null;
  const requestedAt = iv.accessibility?.field_check_requested_at;
  const requestedBy = iv.accessibility?.field_check_requested_by;
  return (
    <div className="my-3 rounded-lg border border-amber-500/70 bg-amber-950/30 p-4" data-testid="route-review">
      <p className="text-sm font-bold tracking-wide text-amber-200">ACCESSIBILITY NOT VERIFIED</p>
      <p className="mt-1 text-sm text-zinc-200">A field check is required. Map attributes and scenario simulations do not verify this route. Approval is blocked.</p>
      {requestedAt ? (
        <p className="mt-3 text-sm text-amber-100" role="status">Field check requested by {String(requestedBy)}. Request logged; route still not verified.</p>
      ) : (
        <button className="mt-3 rounded bg-amber-200 px-3 py-2 text-sm font-semibold text-zinc-950 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled} onClick={onRequest}>REQUEST FIELD CHECK</button>
      )}
    </div>
  );
}
