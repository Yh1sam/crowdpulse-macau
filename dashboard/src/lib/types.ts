export type CongestionClass = "SAFE" | "WARNING" | "CRITICAL";

export interface ZoneState {
  zone_id: string; bin_start: string; density: number; person_count_visible: number; flow_direction_deg: number | null;
  flow_speed_mps: number; flow_coherence: number; n_obs: number; n_sensors: number; reliability: number; disagreement: number;
  obstructed_fraction: number; mean_stability?: number; mean_gps_accuracy_m?: number; mean_vision_confidence?: number;
  congestion_state: CongestionClass; inflow_proxy: number; outflow_proxy: number;
  neighbour_density_mean: number | null; neighbour_density_max: number | null; neighbour_inflow_sum: number;
}

export interface Contribution { feature: string; label: string; delta: number; value: number | null; reference: number | null }

export interface Prediction {
  id?: number | null; zone_id: string; created_at: string; horizon_min: number; target_time: string; status: "ok" | "insufficient_data" | "fallback";
  predicted_class: CongestionClass | null; probabilities: Record<string, number>; model_confidence: number; reliability: number;
  effective_confidence: number; low_confidence: boolean; human_review_required: boolean; ood_flag: boolean; ood_score: number | null;
  ood_reasons: string[]; ood_message: string | null; predicted_density: number | null; reasons: string[]; contributions: Contribution[];
  model_type: string; model_version: string; current_state: CongestionClass | null; message?: string | null;
}

export interface Zone {
  id: string; name: string; lat: number; lon: number; kind: string; capacity: number; polygon_radius_m: number; neighbours: string[];
  state: ZoneState | null; stale: boolean; seconds_since_update: number | null; sensors: string[]; sensors_online: number; sensors_expected: number;
  predictions: Prediction[]; risk: CongestionClass | "UNKNOWN"; active_intervention_id: number | null;
}

export interface Sensor {
  sensor_id: string; zone_id: string | null; status: "online" | "stale" | "offline"; last_seen: string; seconds_since_seen: number;
  latitude: number; longitude: number; location_accuracy_m: number; heading_deg: number; device_motion_stability: number; camera_obstructed: boolean;
  vision_confidence: number; person_count: number; estimated_density: number; model_version: string; mode: string | null; observation_count: number;
  reliability_score: number; issues: string[];
}

export interface Alert { id: number; zone_id: string; created_at: string; level: string; title: string; message: string; horizon_min: number | null; prediction_id: number | null; confidence: number | null; acknowledged: boolean }

export interface Route { from: string; to: string; via: string[]; edges: string[]; length_m: number; has_stairs: boolean; steep: boolean; min_capacity_per_min: number; accessibility_penalty: number; score: number }

export interface Intervention {
  id: number; zone_id: string; created_at: string; status: "pending" | "approved" | "rejected" | "expired" | "superseded"; kind: string; title: string; recommendation: string;
  rationale: string[]; predicted_class: CongestionClass | null; horizon_min: number | null; confidence: number | null; low_confidence: boolean;
  route: Route | null; route_alternatives: Route[]; accessibility: Record<string, unknown> & { note?: string }; messages: Record<string, string>;
  assumed_effect: Record<string, unknown>; projected_after: { inflow_multiplier: number; note: string; horizons: Record<string, { predicted_class: CongestionClass; confidence: number; predicted_density?: number }> } | null;
  prediction_id: number | null; decided_at: string | null; decided_by: string | null; decision_note: string | null; effect_applied: boolean;
}

export interface AuditEntry { id: number; timestamp: string; actor: string; action: string; target_type: string; target_id: string; details: Record<string, unknown> }

export interface Health {
  status: string; time: string; clock: "simulated" | "wall"; privacy_mode: boolean; models_loaded: boolean; model_version: string;
  live_sim: { running: boolean; scenario: string; acceleration: number; sim_time: string; elapsed_sim_min: number; ground_truth: Record<string, { occupancy: number; density: number }> } | null;
  last_refresh: string | null; stats: Record<string, number>;
}

export interface Config {
  congestion_thresholds: { label: string; warning: number; critical: number; note: string };
  confidence: { low_confidence_threshold: number; ood_confidence_multiplier: number };
  density_index: { note: string };
  forecast_horizons_min: number[];
  zone_graph: { zones: { id: string; name: string; lat: number; lon: number; capacity: number; kind: string }[]; edges: { id: string; from: string; to: string; name: string; has_stairs: boolean; length_m: number }[]; sensors: { sensor_id: string; zone_id: string; lat: number; lon: number; heading_deg: number }[] };
  privacy_mode_effective: boolean;
}
