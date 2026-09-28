import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfidenceBadge, OodBadge, RiskBadge } from "@/components/Badges";
import { PredictionRow, Reasons } from "@/components/PredictionCard";
import { ZoneCard } from "@/components/ZoneCard";
import type { Prediction, Zone } from "@/lib/types";

const basePred: Prediction = {
  zone_id: "senado_square", created_at: "2026-10-03T06:00:00Z", horizon_min: 15, target_time: "2026-10-03T06:15:00Z", status: "ok",
  predicted_class: "CRITICAL", probabilities: { SAFE: 0.05, WARNING: 0.08, CRITICAL: 0.87 }, model_confidence: 0.87, reliability: 0.98, effective_confidence: 0.86,
  low_confidence: false, human_review_required: false, ood_flag: false, ood_score: 0.1, ood_reasons: [], ood_message: null, predicted_density: 0.81,
  reasons: ["density increased 32% in the last 3 minutes (now 0.62)", "inflow exceeds outflow by 38% (net inflow)"], contributions: [], model_type: "random_forest", model_version: "crowdpulse-clf-0.1", current_state: "WARNING",
};

describe("responsible-AI badges", () => {
  it("shows the confidence for confident predictions", () => {
    render(<ConfidenceBadge prediction={basePred} />);
    expect(screen.getByTestId("confidence")).toHaveTextContent("86% confidence");
  });
  it("shows HUMAN REVIEW REQUIRED for low-confidence predictions", () => {
    render(<ConfidenceBadge prediction={{ ...basePred, effective_confidence: 0.41, low_confidence: true, human_review_required: true }} />);
    expect(screen.getByTestId("confidence")).toHaveTextContent("LOW CONFIDENCE — HUMAN REVIEW REQUIRED");
  });
  it("shows the no-data state as requiring human review", () => {
    render(<ConfidenceBadge prediction={{ ...basePred, status: "insufficient_data", predicted_class: null }} />);
    expect(screen.getByTestId("confidence")).toHaveTextContent("HUMAN REVIEW REQUIRED");
  });
  it("renders the out-of-distribution warning only when flagged", () => {
    const { rerender } = render(<OodBadge prediction={basePred} />);
    expect(screen.queryByTestId("ood")).toBeNull();
    rerender(<OodBadge prediction={{ ...basePred, ood_flag: true, ood_message: "Conditions differ from training data. Prediction reliability may be reduced." }} />);
    expect(screen.getByTestId("ood")).toHaveTextContent("Conditions differ from training data");
  });
  it("renders risk levels", () => {
    render(<RiskBadge level="WARNING" />);
    expect(screen.getByTestId("risk-badge")).toHaveTextContent("WARNING");
  });
});

describe("prediction rendering", () => {
  it("renders horizon, class, probabilities and reasons", () => {
    render(<div><PredictionRow p={basePred} /><Reasons p={basePred} /></div>);
    expect(screen.getByText("+15 min")).toBeInTheDocument();
    expect(screen.getByText("CRITICAL")).toBeInTheDocument();
    expect(screen.getByText(/5% \/ 8% \/ 87%/)).toBeInTheDocument();
    expect(screen.getByText(/density increased 32%/)).toBeInTheDocument();
  });
});

describe("zone card", () => {
  it("renders state, forecast and stale warning", () => {
    const z: Zone = {
      id: "senado_square", name: "Senado Square", lat: 22.19, lon: 113.54, kind: "square", capacity: 1200, polygon_radius_m: 55, neighbours: [],
      state: { zone_id: "senado_square", bin_start: "2026-10-03T06:00:00Z", density: 0.62, person_count_visible: 190, flow_direction_deg: 180, flow_speed_mps: 0.55, flow_coherence: 0.8, n_obs: 24, n_sensors: 2, reliability: 0.97, disagreement: 0.02, obstructed_fraction: 0, mean_stability: 0.95, mean_gps_accuracy_m: 6, mean_vision_confidence: 0.8, congestion_state: "WARNING", inflow_proxy: 0.3, outflow_proxy: 0.2, neighbour_density_mean: 0.5, neighbour_density_max: 0.7, neighbour_inflow_sum: 0.4 },
      stale: true, seconds_since_update: 130, sensors: ["node-a", "node-b"], sensors_online: 1, sensors_expected: 2, predictions: [basePred], risk: "CRITICAL", active_intervention_id: 3,
    };
    render(<ZoneCard z={z} />);
    expect(screen.getByText("Senado Square")).toBeInTheDocument();
    expect(screen.getByText("0.62")).toBeInTheDocument();
    expect(screen.getByText(/STALE/)).toBeInTheDocument();
    expect(screen.getByText(/intervention #3/)).toBeInTheDocument();
    expect(screen.getByText(/1\/2 sensors/)).toBeInTheDocument();
  });
});
