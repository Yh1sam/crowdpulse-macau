// @vitest-environment jsdom
import { act, createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";
import rawMap from "../src/data/macau.json";
import { freshWorkspace } from "../src/core/model";
import { encodePlan } from "../src/core/plan";
import { download, STORAGE_KEY } from "../src/core/storage";
import type { MapData, Workspace } from "../src/core/types";

// Keep the real App, import validation, controls and persistence. The map/results
// presentation is unrelated to whether a rejected input remains visible.
vi.mock("../src/components/MapCanvas", () => ({ default: () => null }));
vi.mock("../src/components/Results", () => ({
  default: () => null,
  Sensitivity: () => null,
}));
vi.mock("../src/core/storage", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../src/core/storage")>()),
  download: vi.fn(),
}));

const map = rawMap as MapData;
const saved: Workspace = {
  ...freshWorkspace(map),
  title: "保留的街區方案",
  edits: [{ type: "close", edgeId: map.edges[0].id }],
};

class ControlledWorker {
  static instances: ControlledWorker[] = [];
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  requestId = 0;

  constructor() {
    ControlledWorker.instances.push(this);
  }
  postMessage(message: { id: number }) {
    this.requestId = message.id;
  }
  terminate() {}
  complete() {
    this.onmessage?.({
      data: {
        id: this.requestId,
        result: {
          baseline: { duration: 1800 },
          proposal: { duration: 1800, queues: {} },
        },
      },
    } as MessageEvent);
  }
}

let container: HTMLDivElement;
let root: Root;

beforeEach(() => {
  localStorage.clear();
  window.history.replaceState(null, "", "/");
  ControlledWorker.instances = [];
  vi.clearAllMocks();
  vi.stubGlobal("IS_REACT_ACT_ENVIRONMENT", true);
  vi.stubGlobal("Worker", ControlledWorker);
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query.includes("min-width"),
    addEventListener() {},
    removeEventListener() {},
  }));
  vi.stubGlobal("ResizeObserver", class {
    observe() {}
    disconnect() {}
  });
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(async () => {
  await act(async () => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

const alerts = () =>
  Array.from(container.querySelectorAll('[role="alert"]')).map(
    (node) => node.textContent,
  );
const title = () =>
  container.querySelector<HTMLInputElement>("#plan-title")!.value;
const stored = () => JSON.parse(localStorage.getItem(STORAGE_KEY)!);
const latestWorker = () => ControlledWorker.instances.at(-1)!;

async function mount() {
  await act(async () => root.render(createElement(App)));
}
async function click(button: HTMLButtonElement) {
  await act(async () => button.click());
}
function buttonNamed(name: string) {
  const button = Array.from(container.querySelectorAll("button")).find(
    (element) =>
      element.textContent?.trim() === name ||
      element.querySelector("strong")?.textContent === name,
  );
  expect(button, `Expected button ${name}`).toBeDefined();
  return button!;
}
async function completeComparison() {
  await act(async () => latestWorker().complete());
}
async function importWorkspace(workspace: Workspace | string) {
  const text = typeof workspace === "string"
    ? workspace
    : JSON.stringify(workspace);
  const file = new File([text], "plan.json", { type: "application/json" });
  // jsdom's File lacks Blob.text; retain the file-input change path used by App.
  Object.defineProperty(file, "text", { value: async () => text });
  const input = container.querySelector<HTMLInputElement>('input[type="file"]')!;
  Object.defineProperty(input, "files", { configurable: true, value: [file] });
  await act(async () => input.dispatchEvent(new Event("change", { bubbles: true })));
}

describe("rejected plans in the mounted workspace", () => {
  it.each([
    ["malformed", "not-base64-json"],
    ["empty", ""],
    ["foreign map", encodePlan({ workspace: { ...saved, mapVersion: "other-map" } })],
  ])("preserves the %s link error through initial comparison and retry", async (_, plan) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    window.history.replaceState(null, "", `/#plan=${plan}`);
    await mount();
    expect(alerts().join()).toContain("原有方案未被替換");
    expect(title()).toBe(saved.title);
    expect(stored()).toEqual(saved);
    expect(window.location.hash).toBe("");

    await completeComparison();
    expect(alerts().join()).toContain("原有方案未被替換");
    await click(container.querySelector<HTMLButtonElement>(".compare-button")!);
    await completeComparison();
    expect(alerts().join()).toContain("原有方案未被替換");
    expect(stored()).toEqual(saved);

    await click(container.querySelector<HTMLButtonElement>('[aria-label="關閉載入錯誤提示"]')!);
    expect(alerts()).toEqual([]);
    expect(title()).toBe(saved.title);
  });

  it("keeps a rejected file visible across edits until a valid import replaces it", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    await mount();
    await completeComparison();
    await importWorkspace({ ...saved, mapVersion: "other-map" });
    expect(alerts().join()).toContain("原有方案未被替換");
    expect(stored()).toEqual(saved);

    await click(buttonNamed("加入構想捷徑"));
    await completeComparison();
    expect(alerts().join()).toContain("原有方案未被替換");

    const valid = { ...saved, title: "有效的匯入方案" };
    await importWorkspace(valid);
    await completeComparison();
    expect(alerts()).toEqual([]);
    expect(title()).toBe(valid.title);
    expect(stored()).toEqual(valid);
  });

  it("keeps corrupt storage and its warning until backup/reset, even after a valid import", async () => {
    const original = "{broken saved workspace";
    localStorage.setItem(STORAGE_KEY, original);
    await mount();
    const warning = alerts()[0];
    expect(warning).toBeTruthy();
    await completeComparison();
    expect(alerts()[0]).toBe(warning);
    expect(localStorage.getItem(STORAGE_KEY)).toBe(original);

    await importWorkspace(saved);
    await completeComparison();
    expect(alerts()[0]).toBe(warning);
    expect(localStorage.getItem(STORAGE_KEY)).toBe(original);
    await click(buttonNamed("備份並重新開始"));
    await click(buttonNamed("保留目前方案"));
    expect(alerts()[0]).toBe(warning);
    expect(localStorage.getItem(STORAGE_KEY)).toBe(original);

    await click(buttonNamed("備份並重新開始"));
    await click(buttonNamed("重新開始"));
    await completeComparison();
    expect(download).toHaveBeenCalledWith(
      "sketchfuture-original-backup.txt", original, "text/plain",
    );
    expect(alerts()).toEqual([]);
    expect(stored()).toEqual(freshWorkspace(map));
  });

  it("keeps input rejection alongside a worker failure and clears it on confirmed reset", async () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
    window.history.replaceState(null, "", "/#plan=invalid");
    await mount();
    await act(async () => latestWorker().onerror?.());
    expect(alerts()).toHaveLength(2);
    expect(alerts().join()).toContain("原有方案未被替換");
    expect(alerts().join()).toContain("模擬未完成");
    await click(container.querySelector<HTMLButtonElement>('[aria-label="關閉錯誤提示"]')!);
    expect(alerts()).toHaveLength(1);

    await click(buttonNamed("重設"));
    await click(buttonNamed("重新開始"));
    await completeComparison();
    expect(alerts()).toEqual([]);
    expect(stored()).toEqual(freshWorkspace(map));
  });
});
