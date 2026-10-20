import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OperatorField } from "@/components/OperatorField";
import { getOperatorName, OPERATOR_STORAGE_KEY, operatorNameProblem, setOperatorName } from "@/lib/operator";
import type { Alert, Intervention } from "@/lib/types";

const api = vi.hoisted(() => ({ post: vi.fn(), data: {} as Record<string, unknown> }));
vi.mock("@/lib/api", () => ({
  useApi: (path: string | null) => ({ data: path ? api.data[path.split("?")[0]] : undefined, mutate: vi.fn(async () => undefined) }),
  post: api.post,
}));

import Interventions from "@/app/interventions/page";
import Alerts from "@/app/alerts/page";

const pendingIv: Intervention = {
  id: 7, zone_id: "senado_square", created_at: "2026-10-03T06:09:00Z", status: "pending", kind: "deploy_staff", title: "Deploy staff to Senado Square",
  recommendation: "Senado Square is predicted WARNING in 10 min.", rationale: [], predicted_class: "WARNING", horizon_min: 10, confidence: 0.8, low_confidence: false,
  route: null, route_alternatives: [], accessibility: {}, messages: {}, assumed_effect: {}, projected_after: null,
  prediction_id: null, decided_at: null, decided_by: null, decision_note: null, effect_applied: false,
};
const openAlert: Alert = { id: 3, zone_id: "senado_square", created_at: "2026-10-03T06:05:00Z", level: "warning", title: "WARNING expected", message: "test", horizon_min: 10, prediction_id: null, confidence: 0.8, acknowledged: false, acknowledged_by: null };
const ackedAlert: Alert = { ...openAlert, id: 2, title: "earlier", acknowledged: true, acknowledged_by: "demo-operator-2" };

const typeName = (value: string) => fireEvent.change(screen.getByLabelText("Deciding as"), { target: { value } });
const button = (name: string) => screen.getByRole("button", { name }) as HTMLButtonElement;

beforeEach(() => {
  try { window.localStorage.clear(); } catch { /* storage may be mocked to throw */ }
  setOperatorName("");
  api.post.mockReset();
  api.post.mockResolvedValue({});
  api.data = { "/interventions": [pendingIv], "/audit": [], "/alerts": [openAlert, ackedAlert] };
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("operator name rules", () => {
  it("refuses an empty name, the placeholder 'operator' and the automatic actor 'system', like the backend", () => {
    expect(operatorNameProblem("")).toMatch(/Deciding as/);
    expect(operatorNameProblem("   ")).toMatch(/Deciding as/);
    expect(operatorNameProblem("operator")).toMatch(/not a name/);
    expect(operatorNameProblem(" Operator ")).toMatch(/not a name/);
    expect(operatorNameProblem("system")).toMatch(/automatic log entries/);
    expect(operatorNameProblem(" SYSTEM ")).toMatch(/automatic log entries/);
    expect(operatorNameProblem("System")).toMatch(/automatic log entries/);
    expect(operatorNameProblem("demo-operator-1")).toBeNull();
    expect(operatorNameProblem("systems-lead")).toBeNull();
  });
  it("never labels the field as a login", () => {
    render(<OperatorField />);
    expect(screen.getByTestId("operator-field")).not.toHaveTextContent(/signed in|log ?in/i);
  });
});

describe("Deciding as field", () => {
  it("shows the stored name and saves a typed one in localStorage", () => {
    window.localStorage.setItem(OPERATOR_STORAGE_KEY, "demo-operator-1");
    render(<OperatorField />);
    expect(screen.getByLabelText("Deciding as")).toHaveValue("demo-operator-1");
    expect(screen.getByTestId("operator-hint")).toHaveTextContent("Recorded in the audit log");
    typeName("demo-operator-2");
    expect(window.localStorage.getItem(OPERATOR_STORAGE_KEY)).toBe("demo-operator-2");
    expect(screen.getByLabelText("Deciding as")).toHaveValue("demo-operator-2");
  });
  it("asks for a name while none is set", () => {
    render(<OperatorField />);
    expect(screen.getByLabelText("Deciding as")).toHaveValue("");
    expect(screen.getByTestId("operator-hint")).toHaveTextContent("Enter your name");
  });
  it("picks up a name set in another tab", () => {
    render(<OperatorField />);
    act(() => {
      window.localStorage.setItem(OPERATOR_STORAGE_KEY, "demo-operator-1");
      window.dispatchEvent(new StorageEvent("storage", { key: OPERATOR_STORAGE_KEY }));
    });
    expect(screen.getByLabelText("Deciding as")).toHaveValue("demo-operator-1");
  });
  it("still works when browser storage throws", () => {
    const blocked = () => { throw new DOMException("storage blocked", "SecurityError"); };
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(blocked);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(blocked);
    render(<OperatorField />);
    expect(screen.getByLabelText("Deciding as")).toHaveValue("");
    typeName("demo-operator-1");
    expect(screen.getByLabelText("Deciding as")).toHaveValue("demo-operator-1");
    expect(getOperatorName()).toBe("demo-operator-1");
  });
});

describe("decisions carry the operator's name", () => {
  it("keeps APPROVE / REJECT disabled with a hint until a name is set, then sends that name", async () => {
    render(<Interventions />);
    expect(button("APPROVE")).toBeDisabled();
    expect(button("REJECT")).toBeDisabled();
    expect(screen.getByTestId("decision-hint")).toHaveTextContent("Enter your name");
    fireEvent.click(button("APPROVE"));
    expect(api.post).not.toHaveBeenCalled();
    typeName("operator");
    expect(button("APPROVE")).toBeDisabled();
    expect(screen.getByTestId("decision-hint")).toHaveTextContent("not a name");
    typeName(" System ");
    expect(button("APPROVE")).toBeDisabled();
    expect(button("REJECT")).toBeDisabled();
    expect(screen.getByTestId("decision-hint")).toHaveTextContent("automatic log entries");
    fireEvent.click(button("APPROVE"));
    expect(api.post).not.toHaveBeenCalled();
    typeName("demo-operator-1");
    expect(button("APPROVE")).toBeEnabled();
    expect(screen.queryByTestId("decision-hint")).toBeNull();
    await act(async () => { fireEvent.click(button("APPROVE")); });
    expect(api.post).toHaveBeenCalledWith("/interventions/7/approve", { operator: "demo-operator-1", note: "approved from dashboard" });
  });
  it("sends the name with a rejection, trimmed", async () => {
    window.localStorage.setItem(OPERATOR_STORAGE_KEY, " demo-operator-2 ");
    render(<Interventions />);
    await act(async () => { fireEvent.click(button("REJECT")); });
    expect(api.post).toHaveBeenCalledWith("/interventions/7/reject", { operator: "demo-operator-2", note: "rejected from dashboard" });
  });
  it("disables ack until a name is set, sends it, and shows who acknowledged", async () => {
    render(<Alerts />);
    expect(button("ack")).toBeDisabled();
    expect(screen.getByText("ack by demo-operator-2")).toBeInTheDocument();
    typeName("demo-operator-1");
    await act(async () => { fireEvent.click(button("ack")); });
    expect(api.post).toHaveBeenCalledWith("/alerts/3/ack", { operator: "demo-operator-1" });
  });
});

describe("unverified diversion review", () => {
  const diversion: Intervention = {
    ...pendingIv, kind: "redirect_flow", title: "Proposed diversion around Senado Square",
    approval_blocked: false, // even a legacy/incorrect allow flag must not bypass the route policy
    accessibility: { note: "Map records no stairs; field evidence is missing." },
  };
  it("blocks approval with a valid name while allowing field-check requests and rejection", async () => {
    api.data['/interventions'] = [diversion];
    render(<Interventions />);
    typeName('demo-operator-1');
    expect(button('APPROVE')).toBeDisabled();
    expect(button('REJECT')).toBeEnabled();
    expect(screen.getByTestId('route-review')).toHaveTextContent('ACCESSIBILITY NOT VERIFIED');
    fireEvent.click(button('APPROVE'));
    expect(api.post).not.toHaveBeenCalled();
    await act(async () => { fireEvent.click(button('REQUEST FIELD CHECK')); });
    expect(api.post).toHaveBeenCalledWith('/interventions/7/request-field-check', {
      operator: 'demo-operator-1', note: 'Route accessibility not verified; request on-site inspection.',
    });
  });
  it("keeps requested checks visibly unverified and records the reason for rejection", async () => {
    api.data['/interventions'] = [{ ...diversion, accessibility: {
      verification_status: 'not_verified', field_check_requested_at: '2026-10-20T04:00:00Z',
      field_check_requested_by: 'demo-operator-1',
    } }];
    render(<Interventions />);
    typeName('demo-operator-2');
    expect(screen.getByRole('status')).toHaveTextContent('Request logged; route still not verified');
    expect(screen.queryByRole('button', { name: 'REQUEST FIELD CHECK' })).toBeNull();
    expect(button('APPROVE')).toBeDisabled();
    await act(async () => { fireEvent.click(button('REJECT')); });
    expect(api.post).toHaveBeenCalledWith('/interventions/7/reject', {
      operator: 'demo-operator-2', note: 'Rejected: route accessibility not verified; field check required.',
    });
  });
});
