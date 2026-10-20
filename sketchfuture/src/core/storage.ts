import type { Edit, MapData, Settings, Workspace, Comparison, SensitivityRow } from "./types";
import { applyEdits, freshWorkspace, MODEL_VERSION, PROFILES } from "./model";

export const STORAGE_KEY = "sketchfuture.workspace.v1";
export function parseWorkspace(text: string, map: MapData): Workspace {
  if (text.length > 250_000)
    throw new Error("方案檔案太大，請使用 CrowdPulse 方案模擬匯出的 JSON。");
  const value = JSON.parse(text) as Record<string, unknown>;
  if (
    !value ||
    typeof value !== "object" ||
    value.version !== 1 ||
    value.mapVersion !== map.version
  ) {
    throw new Error("方案版本或街區不符，原有方案未被替換。");
  }
  if (typeof value.title !== "string" || value.title.length > 80)
    throw new Error("方案名稱需要少於 80 個字。");
  const settings = value.settings as Settings;
  const limits: Record<keyof Settings, [number, number, boolean]> = {
    people: [3, 300, true],
    releaseSeconds: [20, 600, false],
    speedFactor: [0.5, 1.5, false],
    capacityFactor: [0.2, 3, false],
    seed: [0, 2_147_483_647, true],
    repeats: [1, 10, true],
    horizon: [300, 3600, true],
  };
  if (!settings || typeof settings !== "object")
    throw new Error("缺少模擬設定。");
  for (const [key, [min, max, integer]] of Object.entries(limits)) {
    const n = settings[key as keyof Settings];
    if (
      typeof n !== "number" ||
      !Number.isFinite(n) ||
      n < min ||
      n > max ||
      (integer && !Number.isInteger(n))
    ) {
      throw new Error(`模擬參數 ${key} 超出允許範圍。`);
    }
  }
  if (!Array.isArray(value.edits) || value.edits.length > 30)
    throw new Error("每個方案最多包含 30 項改動。");
  if (settings.horizon < settings.releaseSeconds)
    throw new Error("模擬時間不能短於出發時段。");
  const nodes = new Set(map.nodes.map((n) => n.id));
  const edits: Edit[] = [];
  for (const entry of value.edits) {
    if (!entry || typeof entry !== "object")
      throw new Error("方案含有無效改動。");
    const edit = entry as Edit;
    const edges = applyEdits(map, edits);
    if (edit.type === "link") {
      if (
        !nodes.has(edit.from) ||
        !nodes.has(edit.to) ||
        edit.from === edit.to ||
        typeof edit.id !== "string" ||
        !/^link-[a-zA-Z0-9-]+$/.test(edit.id) ||
        edges.some((e) => e.id === edit.id) ||
        !Number.isFinite(edit.width) ||
        edit.width < 0.8 ||
        edit.width > 6 ||
        !Number.isFinite(edit.slope) ||
        edit.slope < 0 ||
        edit.slope > 15 ||
        edges.some(
          (e) =>
            (e.from === edit.from && e.to === edit.to) ||
            (e.from === edit.to && e.to === edit.from),
        )
      ) {
        throw new Error("新增通道的端點、寬度或坡度無效，或連接已存在。");
      }
      edits.push({
        type: "link",
        id: edit.id,
        from: edit.from,
        to: edit.to,
        width: edit.width,
        slope: edit.slope,
      });
    } else if (edit.type === "ramp") {
      if (
        !edges.some((e) => e.id === edit.edgeId && e.kind === "steps") ||
        !Number.isFinite(edit.slope) ||
        edit.slope < 0 ||
        edit.slope > 5 ||
        (edit.width !== undefined &&
          (!Number.isFinite(edit.width) || edit.width < 1.5 || edit.width > 6))
      ) {
        throw new Error("無階梯改造只能套用在尚未改造的樓梯，坡度須為 0–5%。");
      }
      edits.push({
        type: "ramp",
        edgeId: edit.edgeId,
        slope: edit.slope,
        ...(edit.width === undefined ? {} : { width: edit.width }),
      });
    } else if (edit.type === "close") {
      if (!edges.some((e) => e.id === edit.edgeId))
        throw new Error("封路所指定的通道不存在。");
      edits.push({ type: "close", edgeId: edit.edgeId });
    } else throw new Error("不支援這種改動。");
  }
  return {
    version: 1,
    mapVersion: map.version,
    title: value.title,
    edits,
    settings: Object.fromEntries(
      Object.keys(limits).map((k) => [k, settings[k as keyof Settings]]),
    ) as Settings,
  };
}

export function loadWorkspace(map: MapData): {
  workspace: Workspace;
  error?: string;
  original?: string;
} {
  try {
    const text = localStorage.getItem(STORAGE_KEY);
    return {
      workspace: text ? parseWorkspace(text, map) : freshWorkspace(map),
    };
  } catch (error) {
    let original: string | undefined;
    try {
      original = localStorage.getItem(STORAGE_KEY) ?? undefined;
    } catch {
      /* Storage itself is unavailable. */
    }
    return {
      workspace: freshWorkspace(map),
      error: error instanceof Error ? error.message : "無法讀取本機保存。",
      original,
    };
  }
}
export function download(
  name: string,
  contents: string,
  type = "application/json",
) {
  const url = URL.createObjectURL(new Blob([contents], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function reportJSON(
  map: MapData,
  workspace: Workspace,
  comparison: Comparison,
  sensitivityResults: SensitivityRow[] | null = null,
): string {
  return JSON.stringify(
    {
      model: MODEL_VERSION,
      generatedAt: new Date().toISOString(),
      map: {
        version: map.version,
        source: map.source,
        timestamp: map.timestamp,
      },
      interpretation:
        "模型內方案比較；未經現場校準；不是導航或安全認證。時間平均值只計已到達者，另列不可達與未完成。快慢差值只配對兩邊都到達的同一批人。多次範圍是種子結果範圍，不是信賴區間。",
      assumptions: {
        profiles: PROFILES,
        routing:
          "出發前按自由行走時間及固定過路期望等待選路；途中不因排隊改道。",
        queues:
          "雙向共享通道入口 FIFO 服務；不模擬碰撞或車輛。未標記坡度按 0% 計；未標記寬度按 2m 計。",
        ramp: "構想坡道長度為原樓梯 1.8 倍，寬度至少 1.5m；沒有地形或施工可行性校驗。",
      },
      workspace,
      results: comparison,
      sensitivity: sensitivityResults,
    },
    null,
    2,
  );
}
export function reportCSV(comparison: Comparison): string {
  const rows = [
    [
      "profile",
      "scenario",
      "people",
      "arrived",
      "unreachable",
      "unfinished",
      "mean_time_s_arrived_only",
      "mean_wait_s_arrived_only",
      "mean_distance_m_arrived_only",
      "paired_people_arrived_in_both",
      "paired_mean_delta_s",
    ],
  ];
  for (const p of PROFILES)
    for (const scenario of ["baseline", "proposal"] as const) {
      const m = comparison[scenario].profiles[p.id];
      rows.push([
        p.id,
        scenario,
        ...[
          m.people,
          m.arrived,
          m.unreachable,
          m.unfinished,
          m.meanTime,
          m.meanWait,
          m.meanDistance,
          comparison.paired[p.id].count,
          comparison.paired[p.id].delta,
        ].map((v) => (v === null ? "" : String(v))),
      ]);
    }
  return rows
    .map((row) =>
      row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(","),
    )
    .join("\n");
}
