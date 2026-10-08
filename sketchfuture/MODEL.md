# Model and interpretation

Version: `sf-route-queue-1.0`.

## Inputs and extraction

The included OSM snapshot covers longitude 113.5372–113.5426 and latitude 22.1923–22.1984. The public walking/street-way subset excludes explicit `foot=no` and `access=private/no`. Routes connect only shared OSM node IDs; visual intersections and nearby endpoints do not create connections. Degree-two geometry vertices are compressed while retaining the original polyline. The largest connected component is kept: 575 nodes and 692 edges. Pedestrian area boundaries are represented by their perimeter ways, not a full free-space polygon routing model.

Latitude/longitude are projected locally using `x=(lon-west)*111320*cos(22.195°)` and `y=(north-lat)*111320`. Baseline lengths are sums along retained polylines. Landmark anchors are hand-selected approximate coordinates snapped to neighbouring network nodes, not verified building entrances.

All permitted edges are treated as bidirectional walking links. Car `oneway` tags are not pedestrian direction rules. This prototype does not model buildings, indoor paths, elevators, kerbs, road crossing permissions or changing surface quality; street centreline geometry is not a surveyed sidewalk. Missing topology can therefore produce model-unreachable journeys even where a real route exists.

## Demonstration profiles

| Profile | Free speed | Minimum width | Maximum assumed slope | Stairs |
|---|---:|---:|---:|---|
| General walking | 1.3 m/s | 0.7 m | 18% | permitted |
| Wheelchair | 0.9 m/s | 1.2 m | 5% | excluded |
| Stroller | 1.05 m/s | 1.0 m | 8% | excluded |

These are illustrative settings, not standards or descriptions of everyone's abilities. Unrecorded width defaults to 2 m and slope to 0%. Defaults are **unknown-condition assumptions**, not evidence that a street is level, sufficiently wide or accessible.

## Routing and service queues

Before departure, each person chooses a shortest generalized-time path among permitted links. Traversal time is

`length / (profileSpeed * personSpeedScale * scenarioSpeedFactor * terrainFactor)`.

Stairs use terrain factor 0.65; other links use `max(0.55, 1 - slopePercent*0.035)`. These functions are prototype assumptions. Each person's speed multiplier is a seeded draw from 0.9–1.1. A signal-gated link can add its uniform-arrival expected wait `(cycle-green)^2/(2*cycle)` to routing cost. The current snapshot has no calibrated signal links; it does not model vehicles or crossing safety.

Actual modeled waiting uses event-driven, first-in-first-out entrance service. A link shares a service clock across both directions. Entry capacity defaults to `width * 0.55 persons/second`, multiplied by the scenario capacity factor. Service begins no earlier than arrival and the previous service slot, and is shifted to the next green window if applicable. Travel completion triggers arrival at the next node. There is no adaptive rerouting in response to a queue, no collision avoidance, and no physical queue-space constraint. Animation dots show itinerary/queue state, not calibrated trajectories.

## Demand and proposals

Profiles cycle evenly across generated person IDs. Origins are randomly selected from Senado, St. Dominic's and Tercena anchors; destinations from Ruins, Museum and Senado, excluding identical origins/destinations. Departure is uniform over the configured window. The default is 120 people, 120-second departure window, seed 42, five repeats and a 1,800-second horizon. Demand is entirely synthetic.

- **New link:** straight-line endpoint distance, with user-set width/slope and assumed capacity. Intersections with buildings, elevation and land ownership are not checked. This is a proposed link, not an existing street.
- **Step-free conversion:** removes the stairs exclusion, uses the selected slope/width (minimum width 1.5 m), and multiplies the original length by 1.8 as a construction-length assumption. It does not verify the rise/run or engineering feasibility.
- **Closure:** excludes an edge; a second closure action reopens it.

All three edits may make a scenario worse or leave it unchanged. Outcomes are not pre-scripted to improve.

## Comparison and evidence boundaries

Each repeat generates a cohort once and passes that identical cohort to both plans. An unchanged proposal must give byte-equivalent run results. Every person is arrived, unfinished or topologically unreachable; counts must sum to the planned cohort. Unfinished and unreachable journeys are never included as zero-time arrivals.

All-arrival averages describe each plan's completed trips, with arrival denominators displayed. The primary time difference and repeat ranges instead **pair the same IDs that arrive in both plans**, avoiding a false slowdown/improvement caused by a changed completion population. Reachability gains/losses take priority in the result-card headline. Every repeat's summaries and paired counts are included in the full report.

The repeated-seed range is a min/max over synthetic cohorts, not a confidence interval. Sensitivity compares demand 70/100/140% and speed 85/100/115%, nine conditions, one seed per condition. It probes this model's assumptions and does not calibrate them.

The model can support reproducible explanation and scenario comparison. Real claims require independently sourced street/accessibility audits, demand, trajectories or measured travel times. A calibrated simulator comparison alone still does not prove a causal effect of an actual urban intervention.
