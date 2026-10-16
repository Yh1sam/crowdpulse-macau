"use client";
import { OPERATOR_NAME_MAX, useOperatorName } from "@/lib/operator";

/** "Deciding as" name field shown next to the decision controls. The name goes into the audit log with every
 * approve / reject / acknowledge; until one is set those buttons stay disabled. The prototype has no login, so the
 * label must not say or imply "signed in". */
export function OperatorField() {
  const { name, setName, problem } = useOperatorName();
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm" data-testid="operator-field">
      <label htmlFor="operator-name" className="font-semibold text-zinc-300">Deciding as</label>
      <input
        id="operator-name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        maxLength={OPERATOR_NAME_MAX}
        placeholder="your name"
        autoComplete="off"
        spellCheck={false}
        className="w-52 max-w-full rounded border border-zinc-600 bg-zinc-950 px-2 py-0.5 text-zinc-100 placeholder:text-zinc-600"
      />
      <span className={`text-xs ${problem ? "text-amber-200" : "text-zinc-500"}`} data-testid="operator-hint">
        {problem ?? "Recorded in the audit log with each decision (prototype: no password)."}
      </span>
    </div>
  );
}
