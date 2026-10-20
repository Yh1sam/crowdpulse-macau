"""Rule-based intervention engine with an accessibility penalty and multilingual messages.

The system RECOMMENDS; a human operator approves or rejects. Nothing here controls
real infrastructure."""
from __future__ import annotations

from itertools import count
from typing import Any

from shared.geo import bearing_deg

_NOTICE_TEXT = {
    "redirect_flow": {
        "en": "{zone} is very crowded. Please use the alternative route via {route} to continue. Staff are available to assist visitors with reduced mobility.",
        "zh": "{zone}目前非常擁擠。請改經{route}前往。工作人員可協助行動不便的遊客。",
        "pt": "{zone}: grande afluência de visitantes. Por favor utilize o percurso alternativo: {route}. Há pessoal disponível para apoiar visitantes com mobilidade reduzida.",
    },
    "reduce_inflow": {
        "en": "{zone} is reaching capacity. Entry is temporarily slowed for safety. Thank you for your patience.",
        "zh": "{zone}人流即將飽和。為安全起見，入口暫時放慢放行。感謝您的耐心。",
        "pt": "{zone}: lotação quase esgotada. A entrada está temporariamente condicionada por segurança. Obrigado pela sua paciência.",
    },
    "deploy_staff": {
        "en": "{zone} is busy. Please follow staff guidance and keep moving.",
        "zh": "{zone}人流較多。請聽從工作人員指示並保持前行。",
        "pt": "{zone}: grande afluência de visitantes. Siga as indicações do pessoal e continue a circular.",
    },
    "increase_monitoring": {"en": "", "zh": "", "pt": ""},
}
# Every public notice tells the public that the advice comes from an AI forecast and that a person approved it.
# The zh and pt wording is a first draft awaiting a fluent team member's check; pt says "afluência", like the
# notices above.
AI_NOTICE = {
    "en": "Advice from an AI crowd forecast, approved by staff.",
    "zh": "此建議來自人工智能人流預測，並經工作人員批准。",
    "pt": "Recomendação baseada numa previsão de afluência feita por inteligência artificial, aprovada pelo pessoal.",
}
_SENTENCE_GAP = {"en": " ", "zh": "", "pt": " "}
# The notice templates with the AI clause appended; an empty template (internal-only action) stays empty.
PUBLIC_MESSAGES = {kind: {lang: f"{text}{_SENTENCE_GAP[lang]}{AI_NOTICE[lang]}" if text else "" for lang, text in texts.items()}
                   for kind, texts in _NOTICE_TEXT.items()}
# Portuguese notices put the place name before a colon, so the sentence never depends on its gender or article.
ROUTE_SEPARATOR = {"en": " / ", "zh": "、", "pt": " / "}


def place_name(item: dict[str, Any], lang: str) -> str:
    """A zone's or corridor's name in a notice language (name_zh / name_pt in shared/zones.json; English otherwise)."""
    return item.get(f"name_{lang}") or item["name"]


def public_messages(kind: str, zone: dict[str, Any], route_edges: list[dict[str, Any]] = ()) -> dict[str, str]:
    """Public notices in every language, with place names in that language."""
    return {lang: text.format(zone=place_name(zone, lang), route=ROUTE_SEPARATOR[lang].join(place_name(e, lang) for e in route_edges))
            for lang, text in PUBLIC_MESSAGES[kind].items()}


def _paths(graph_nbrs: dict[str, list[tuple[str, dict]]], src: str, dst: str, avoid: str, max_len: int = 4) -> list[list[tuple[str, dict]]]:
    """Simple paths src->dst (as edge lists) avoiding ``avoid``."""
    out: list[list[tuple[str, dict]]] = []

    def dfs(node: str, visited: set[str], path: list[tuple[str, dict]]):
        if len(path) > max_len:
            return
        if node == dst and path:
            out.append(list(path))
            return
        for n, e in graph_nbrs[node]:
            if n in visited or n == avoid:
                continue
            path.append((n, e))
            dfs(n, visited | {n}, path)
            path.pop()

    dfs(src, {src}, [])
    return out


def route_score(path: list[tuple[str, dict]], acc_cfg: dict[str, float]) -> dict[str, Any]:
    length = sum(e["length_m"] for _, e in path)
    stairs = any(e.get("has_stairs") for _, e in path)
    steep = any(e.get("steep") for _, e in path)
    cap = min(e["capacity_per_min"] for _, e in path)
    penalty = acc_cfg["length_penalty_per_100m"] * length / 100.0 + (acc_cfg["stairs_penalty"] if stairs else 0.0) + (acc_cfg["steep_penalty"] if steep else 0.0)
    return {"length_m": length, "has_stairs": stairs, "steep": steep, "min_capacity_per_min": cap, "accessibility_penalty": round(penalty, 3), "score": round(penalty - cap / 1000.0, 3)}


def build_recommendation(zone: dict[str, Any], graph: dict[str, Any], states: dict[str, dict[str, Any]], prediction: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """Compose an intervention recommendation for ``zone`` from its current state, its
    prediction and the graph. ``states`` maps zone_id -> latest state dict."""
    icfg = cfg["intervention"]
    acc_cfg = icfg["accessibility"]
    zones = {z["id"]: z for z in graph["zones"]}
    nbrs: dict[str, list[tuple[str, dict]]] = {z: [] for z in zones}
    for e in graph["edges"]:
        nbrs[e["from"]].append((e["to"], e))
        nbrs[e["to"]].append((e["from"], e))
    zid = zone["id"]
    st = states.get(zid) or {}
    pred_class = prediction.get("predicted_class")
    conf = prediction.get("effective_confidence", 0.0)
    low = prediction.get("low_confidence", True)
    horizon = prediction.get("horizon_min")
    rationale = list(prediction.get("reasons", []))
    # dominant source neighbour: the neighbour whose flow points most into this zone
    best_src, best_val = None, 0.0
    for n, e in nbrs[zid]:
        ns = states.get(n)
        if not ns or ns.get("flow_direction_deg") is None:
            continue
        import math
        b = bearing_deg(zones[n]["lat"], zones[n]["lon"], zone["lat"], zone["lon"])
        toward = max(0.0, math.cos(math.radians(ns["flow_direction_deg"] - b))) * (ns.get("flow_coherence") or 0.0)
        val = (ns.get("density") or 0.0) * (ns.get("flow_speed_mps") or 0.0) * toward
        if val > best_val:
            best_src, best_val = n, val
    src_name = zones[best_src]["name"] if best_src else "upstream zones"
    base = {"predicted_class": pred_class, "horizon_min": horizon, "confidence": conf, "low_confidence": low, "route": None, "route_alternatives": [], "accessibility": {}, "assumed_effect": {}, "projected_after": None}
    if low or pred_class is None:
        return {**base, "kind": "increase_monitoring", "title": f"Increase monitoring at {zone['name']}",
                "recommendation": f"Prediction confidence is low ({conf:.0%}). Send a staff member to verify conditions at {zone['name']} before any crowd-control action. No automatic action.",
                "rationale": rationale + ["AI confidence below the operator threshold: human verification required"], "messages": {}}
    if pred_class == "WARNING":
        msgs = public_messages("deploy_staff", zone)
        return {**base, "kind": "deploy_staff", "title": f"Deploy staff to {zone['name']}",
                "recommendation": f"{zone['name']} is predicted WARNING in {horizon} min ({conf:.0%} confidence). Deploy 2 staff to keep pedestrians moving and prepare the alternate route. Display the multilingual notice.",
                "rationale": rationale, "messages": msgs, "assumed_effect": {"note": "Staff presence assumed to keep flow moving; no inflow change modelled."}}
    # CRITICAL: try to redirect part of the inbound flow around this zone
    alternatives = []
    if best_src:
        # destinations: other neighbours of the congested zone (where people are heading)
        for dst, _ in nbrs[zid]:
            if dst == best_src:
                continue
            for path in _paths(nbrs, best_src, dst, avoid=zid):
                sc = route_score(path, acc_cfg)
                alternatives.append({"from": best_src, "to": dst, "via": [n for n, _ in path][:-1], "edges": [e["name"] for _, e in path], **sc})
    alternatives.sort(key=lambda a: a["score"])
    direction = None
    if best_src:
        b = bearing_deg(zones[best_src]["lat"], zones[best_src]["lon"], zone["lat"], zone["lon"])
        direction = ["northbound", "north-eastbound", "eastbound", "south-eastbound", "southbound", "south-westbound", "westbound", "north-westbound"][int(((b + 22.5) % 360) // 45)]
    reduction = icfg["assumed_redirect_inflow_reduction"]
    if alternatives:
        route = alternatives[0]
        route_name = " / ".join(route["edges"])
        access = {
            "route_has_stairs": route["has_stairs"], "route_steep": route["steep"], "route_length_m": route["length_m"], "accessibility_penalty": route["accessibility_penalty"],
            "verification_status": "not_verified",
            "note": ("The zone map records no stairs or steep sections on this candidate route." if not (route["has_stairs"] or route["steep"]) else "The zone map records stairs or steep sections on this candidate route.")
            + " These map attributes do not verify accessibility. An on-site check is required before a diversion can be approved.",
        }
        edges_by_name = {e["name"]: e for e in graph["edges"]}
        msgs = public_messages("redirect_flow", zone, [edges_by_name[name] for name in route["edges"]])
        return {**base, "kind": "redirect_flow", "title": f"Redirect part of {direction or 'inbound'} flow around {zone['name']}",
                "recommendation": f"{zone['name']} is predicted CRITICAL in {horizon} min ({conf:.0%} confidence). Proposed diversion: part of the {direction or 'inbound'} flow from {src_name} via {route_name} (to {zones[route['to']]['name']}). Do not implement this diversion until the route and mobility assistance have been checked on site. Request a field check or reject the suggestion.",
                "rationale": rationale, "route": route, "route_alternatives": alternatives[:4], "accessibility": access, "messages": msgs,
                "assumed_effect": {"inflow_reduction": reduction, "duration_min": 20, "note": f"Assumed effect (configurable prototype assumption, not validated): the forecast what-if scales the zone's inflow by {1 - reduction:.2f}; the live simulation makes routes into the zone {reduction:.0%} less attractive for 20 min, so its inflow falls by less."}}
    msgs = public_messages("reduce_inflow", zone)
    return {**base, "kind": "reduce_inflow", "title": f"Temporarily reduce inflow into {zone['name']}",
            "recommendation": f"{zone['name']} is predicted CRITICAL in {horizon} min ({conf:.0%} confidence) and no alternate route is available. Ask staff at {src_name} to hold groups briefly (metered entry) and display multilingual notices. Do not block reduced-mobility visitors.",
            "rationale": rationale, "messages": msgs, "accessibility": {"note": "Metered entry must keep a priority lane for reduced-mobility visitors."},
            "assumed_effect": {"inflow_reduction": reduction, "duration_min": 15, "note": "Prototype assumption, not validated."}}
