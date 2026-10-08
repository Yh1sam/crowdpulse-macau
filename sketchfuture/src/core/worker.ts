import { compare, sensitivity } from "./simulation";
import type { Edit, MapData, Settings } from "./types";

self.onmessage = (
  event: MessageEvent<{
    id: number;
    map: MapData;
    edits: Edit[];
    settings: Settings;
    sensitivity: boolean;
  }>,
) => {
  const data = event.data;
  try {
    const result = data.sensitivity
      ? sensitivity(data.map, data.edits, data.settings)
      : compare(data.map, data.edits, data.settings);
    self.postMessage({ id: data.id, result });
  } catch (error) {
    self.postMessage({
      id: data.id,
      error: error instanceof Error ? error.message : "模擬失敗，請檢查方案。",
    });
  }
};
