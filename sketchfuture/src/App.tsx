import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import rawMap from "./data/macau.json";
import type {
  Comparison,
  Edge,
  Edit,
  MapData,
  ProfileId,
  SensitivityRow,
  Settings,
  Workspace,
} from "./core/types";
import { applyEdits, freshWorkspace, PROFILES } from "./core/model";
import {
  download,
  loadWorkspace,
  parseWorkspace,
  reportCSV,
  reportJSON,
  STORAGE_KEY,
} from "./core/storage";
import { decodePlan, type SharedPlan } from "./core/plan";
import MapCanvas, { type Tool } from "./components/MapCanvas";
import Results, { Sensitivity } from "./components/Results";
import FloatingPanel from "./components/FloatingPanel";
import Icon, { type IconName } from "./components/Icon";

const MAP = rawMap as MapData;
const PRIMARY_STEPS = MAP.edges.find((e) => e.osmId === 670357826)!;
const TOOLS: { id: Tool; icon: IconName; label: string; hint: string }[] = [
  {
    id: "inspect",
    icon: "inspect",
    label: "查看",
    hint: "點選通道，查看距離及模擬條件。放大後可拖曳地圖。",
  },
  {
    id: "link",
    icon: "link",
    label: "畫連接",
    hint: "從一個圓點畫到另一個圓點，新增構想步行通道。",
  },
  {
    id: "ramp",
    icon: "ramp",
    label: "無階梯",
    hint: "點選棕色樓梯，提出無階梯改造。",
  },
  {
    id: "close",
    icon: "close",
    label: "暫封路",
    hint: "點選通道暫時封閉，再點一次取消。",
  },
];
type History = { past: Workspace[]; present: Workspace; future: Workspace[] };
const clock = (s: number) =>
  `${Math.floor(s / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(s % 60)
    .toString()
    .padStart(2, "0")}`;

export default function App() {
  const [loaded] = useState(() => loadWorkspace(MAP));
  // A plan in the URL fragment (`#plan=…`, e.g. from a CrowdPulse intervention card) replaces
  // the saved plan like a file import: validated first, undoable, and never kept in the URL.
  const [shared] = useState<{ plan: SharedPlan | null; error?: string }>(() => {
    try {
      return { plan: decodePlan(window.location.hash, MAP) };
    } catch (e) {
      return {
        plan: null,
        error: e instanceof Error ? e.message : "連結中的方案無法讀取。",
      };
    }
  });
  const [history, setHistory] = useState<History>(() =>
    shared.plan
      ? { past: [loaded.workspace], present: shared.plan.workspace, future: [] }
      : { past: [], present: loaded.workspace, future: [] },
  );
  const workspace = history.present;
  const currentWorkspace = useRef(workspace);
  useEffect(() => {
    currentWorkspace.current = workspace;
  }, [workspace]);
  const [saveBlocked, setSaveBlocked] = useState(!!loaded.error);
  const [saveMessage, setSaveMessage] = useState(
    loaded.error ? "本機保存暫停；原始資料已保留。" : "已在這個瀏覽器保存",
  );
  const [error, setError] = useState(loaded.error ?? shared.error ?? "");
  const [notice, setNotice] = useState(
    shared.plan
      ? `已載入${shared.plan.source ? `來自 ${shared.plan.source} 的` : "連結中的"}方案，正在比較；按「撤銷」可回到原有方案。`
      : "",
  );
  const [tool, setTool] = useState<Tool>("inspect");
  const [selected, setSelected] = useState<string>(() => {
    const first = shared.plan?.workspace.edits[0];
    return first ? (first.type === "link" ? first.id : first.edgeId) : PRIMARY_STEPS.id;
  });
  const [profile, setProfile] = useState<ProfileId | "all">("all");
  const [view, setView] = useState<"proposal" | "split">("proposal");
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [checks, setChecks] = useState<SensitivityRow[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [checking, setChecking] = useState(false);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(10);
  const [linkWidth, setLinkWidth] = useState(2);
  const [linkSlope, setLinkSlope] = useState(4);
  const [landmarkFrom, setLandmarkFrom] = useState(
    MAP.places.find((p) => p.id === "senado")!.node,
  );
  const [landmarkTo, setLandmarkTo] = useState(
    MAP.places.find((p) => p.id === "ruins")!.node,
  );
  const [panelTab, setPanelTab] = useState<"plan" | "conditions" | "checks">(
    "plan",
  );
  const [plannerOpen, setPlannerOpen] = useState(
    () => window.matchMedia("(min-width: 901px)").matches,
  );
  const [resultsOpen, setResultsOpen] = useState(
    () => window.matchMedia("(min-width: 1100px)").matches,
  );
  const [dialog, setDialog] = useState<"assumptions" | "reset" | null>(null);
  const importInput = useRef<HTMLInputElement>(null);
  const workspaceElement = useRef<HTMLElement>(null);
  const focusResults = useRef(false);
  const modal = useRef<HTMLElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const worker = useRef<Worker | null>(null);
  const request = useRef(0);
  const edges = useMemo(
    () => applyEdits(MAP, workspace.edits),
    [workspace.edits],
  );
  const selectedEdge =
    edges.find((e) => e.id === selected) ??
    edges.find((e) => e.id === PRIMARY_STEPS.id);
  const bottlenecks = comparison
    ? Object.entries(comparison.proposal.queues)
        .filter(([, queue]) => queue.max > 0)
        .sort((a, b) => b[1].max - a[1].max)
        .slice(0, 3)
    : [];
  const duration = comparison
    ? Math.max(comparison.baseline.duration, comparison.proposal.duration)
    : 1800;
  const dirty = !comparison;

  const compute = useCallback(
    (snapshot: Workspace, robustness = false, reveal = false) => {
      worker.current?.terminate();
      request.current++;
      setError("");
      setPlaying(false);
      if (robustness) setChecking(true);
      else {
        setBusy(true);
        setChecking(false);
      }
      try {
        const current = new Worker(
          new URL("./core/worker.ts", import.meta.url),
          {
            type: "module",
          },
        );
        worker.current = current;
        const id = request.current;
        current.onmessage = (event) => {
          if (event.data.id !== request.current) return;
          if (event.data.error) setError(event.data.error);
          else if (robustness) {
            setChecks(event.data.result as SensitivityRow[]);
            setNotice("9 種條件已完成，可在「檢查」查看。");
          } else {
            setComparison(event.data.result as Comparison);
            setTime(80);
            if (reveal) {
              setNotice("比較完成，點選使用者查看路線。");
              setResultsOpen(true);
              if (window.matchMedia("(max-width: 900px)").matches) {
              const focusWasInPlanner =
                document.activeElement === document.body ||
                document.activeElement?.closest(".planner-panel");
                setPlannerOpen(false);
                focusResults.current = !!focusWasInPlanner;
              }
            }
          }
          setBusy(false);
          setChecking(false);
          current.terminate();
          worker.current = null;
        };
        current.onerror = () => {
          if (id !== request.current) return;
          setError("模擬未完成，請重新比較。原有方案仍保留。");
          setBusy(false);
          setChecking(false);
          current.terminate();
        };
        current.postMessage({
          id,
          map: { ...MAP, buildings: [], context: [] },
          edits: snapshot.edits,
          settings: snapshot.settings,
          sensitivity: robustness,
        });
      } catch {
        setError("這個瀏覽器無法啟動模擬，請用較新的 Chrome、Safari 或 Edge。");
        setBusy(false);
        setChecking(false);
      }
    },
    [],
  );

  useEffect(() => {
    const mobile = window.matchMedia("(max-width: 900px)");
    const adapt = () => {
      if (mobile.matches) setResultsOpen(false);
    };
    mobile.addEventListener("change", adapt);
    return () => mobile.removeEventListener("change", adapt);
  }, []);

  useLayoutEffect(() => {
    if (!focusResults.current || !resultsOpen || plannerOpen) return;
    focusResults.current = false;
    // Move focus only when the initiating panel has become hidden.
    if (!document.querySelector('[role="dialog"]')) {
      workspaceElement.current
        ?.querySelector<HTMLButtonElement>(
          ".results-container .floating-panel-toggle",
        )
        ?.focus();
    }
  }, [resultsOpen, plannerOpen]);
  useEffect(() => {
    compute(currentWorkspace.current);
    return () => worker.current?.terminate();
  }, [compute]);
  useEffect(() => {
    if (/(^|[#&])plan=/.test(window.location.hash))
      window.history.replaceState(
        null,
        "",
        window.location.pathname + window.location.search,
      );
  }, []);
  useEffect(() => {
    if (saveBlocked) return;
    const save = () => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(workspace));
        setSaveMessage("已在這個瀏覽器保存");
      } catch {
        setSaveMessage("無法自動保存，請匯出方案檔案。");
      }
    };
    save();
    window.addEventListener("pagehide", save);
    return () => window.removeEventListener("pagehide", save);
  }, [workspace, saveBlocked]);
  useEffect(() => {
    if (!playing) return;
    let last = performance.now();
    const timer = setInterval(() => {
      const now = performance.now(),
        increment = ((now - last) / 1000) * playSpeed;
      last = now;
      setTime((t) => Math.min(duration, t + increment));
    }, 100);
    return () => clearInterval(timer);
  }, [playing, playSpeed, duration]);
  useEffect(() => {
    if (time >= duration && playing) setPlaying(false);
  }, [time, duration, playing]);
  useEffect(() => {
    if (!dialog) return;
    const listener = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setDialog(null);
      }
      if (event.key === "Tab") {
        const controls = Array.from(
          modal.current?.querySelectorAll<HTMLElement>(
            'button:not(:disabled), a[href], input, select, [tabindex="0"]',
          ) ?? [],
        );
        const first = controls[0],
          last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", listener);
    return () => {
      document.removeEventListener("keydown", listener);
      previousFocus.current?.focus();
    };
  }, [dialog]);

  function invalidate() {
    worker.current?.terminate();
    request.current++;
    setBusy(false);
    setChecking(false);
    setComparison(null);
    setChecks(null);
    setPlaying(false);
    setTime(0);
  }
  function openDialog(type: "assumptions" | "reset") {
    previousFocus.current = document.activeElement as HTMLElement | null;
    setDialog(type);
  }
  function change(next: Workspace, message?: string) {
    try {
      const validated = parseWorkspace(JSON.stringify(next), MAP);
      invalidate();
      setError("");
      setHistory((h) => ({
        past: [...h.past, h.present].slice(-40),
        present: validated,
        future: [],
      }));
      if (message) setNotice(message);
      return validated;
    } catch (e) {
      setError(e instanceof Error ? e.message : "無法套用改動。");
      return null;
    }
  }
  function addEdit(edit: Edit, message: string) {
    const next = change(
      { ...workspace, edits: [...workspace.edits, edit] },
      message,
    );
    if (next) setSelected(edit.type === "link" ? edit.id : edit.edgeId);
  }
  function chooseEdge(edge: Edge) {
    setSelected(edge.id);
    if (tool === "inspect") {
      setPanelTab("plan");
      setPlannerOpen(true);
      if (window.matchMedia("(max-width: 900px)").matches)
        setResultsOpen(false);
    }
    if (tool === "close")
      addEdit(
        { type: "close", edgeId: edge.id },
        edge.closed
          ? "通道已重新開放。按「比較方案」更新結果。"
          : "已暫封通道。按「比較方案」看看取捨。",
      );
    else if (tool === "ramp") {
      if (edge.kind !== "steps") {
        setError("請選擇一段棕色樓梯。只有樓梯支援這種改造。");
        return;
      }
      addEdit(
        {
          type: "ramp",
          edgeId: edge.id,
          slope: Math.min(5, linkSlope),
          width: Math.max(1.5, linkWidth),
        },
        "已加入構想無階梯通道，長度按原樓梯的 1.8 倍計。",
      );
    }
  }
  function addLink(from: string, to: string) {
    addEdit(
      {
        type: "link",
        id: `link-${Date.now()}-${workspace.edits.length}`,
        from,
        to,
        width: linkWidth,
        slope: linkSlope,
      },
      "新連接已畫出。位置是構想，未校驗建物、高差或施工可行性。",
    );
  }
  function undo(redo = false) {
    invalidate();
    setError("");
    setHistory((h) => {
      if (redo) {
        if (!h.future.length) return h;
        return {
          past: [...h.past, h.present],
          present: h.future[0],
          future: h.future.slice(1),
        };
      }
      if (!h.past.length) return h;
      return {
        past: h.past.slice(0, -1),
        present: h.past[h.past.length - 1],
        future: [h.present, ...h.future],
      };
    });
    setNotice(redo ? "已重做；請重新比較。" : "已撤銷；請重新比較。");
  }
  function setting<K extends keyof Settings>(key: K, value: Settings[K]) {
    change({ ...workspace, settings: { ...workspace.settings, [key]: value } });
  }
  function preset(kind: "ramp" | "close" | "link") {
    let edit: Edit;
    if (kind === "ramp")
      edit = { type: "ramp", edgeId: PRIMARY_STEPS.id, slope: 4, width: 2 };
    else if (kind === "close") {
      const street = MAP.edges
        .filter((e) => e.name === "大三巴街")
        .sort(
          (a, b) =>
            (comparison?.baseline.queues[b.id]?.entries ?? 0) -
              (comparison?.baseline.queues[a.id]?.entries ?? 0) ||
            b.length - a.length,
        )[0];
      edit = { type: "close", edgeId: street.id };
    } else
      edit = {
        type: "link",
        id: `link-example-${Date.now()}`,
        from: PRIMARY_STEPS.from,
        to: MAP.places.find((p) => p.id === "ruins")!.node,
        width: 2,
        slope: 4,
      };
    const next = change(
      { ...workspace, edits: [edit] },
      "範例已套用，正在比較同一批出發者。",
    );
    if (next) {
      setSelected(edit.type === "link" ? edit.id : edit.edgeId);
      setProfile("wheelchair");
      compute(next, false, true);
    }
  }
  async function importPlan(file: File | undefined) {
    if (!file) return;
    try {
      if (file.size > 250_000)
        throw new Error("檔案太大，請選擇匯出的方案 JSON。");
      const next = parseWorkspace(await file.text(), MAP);
      if (change(next, "方案已匯入，正在重新比較。"))
        compute(next, false, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "無法讀取方案檔案。");
    } finally {
      if (importInput.current) importInput.current.value = "";
    }
  }
  function reset() {
    if (saveBlocked) {
      if (loaded.original)
        download(
          "sketchfuture-original-backup.txt",
          loaded.original,
          "text/plain",
        );
      setSaveBlocked(false);
    }
    const next = change(freshWorkspace(MAP), "已重設街區。");
    if (next) compute(next);
    setDialog(null);
    setSelected(PRIMARY_STEPS.id);
    setProfile("all");
  }

  function chooseTool(next: Tool) {
    setTool(next);
    setError("");
    if (next === "link" || next === "ramp") {
      setPanelTab("plan");
      setPlannerOpen(true);
      if (window.matchMedia("(max-width: 900px)").matches)
        setResultsOpen(false);
    }
    if (next === "ramp") {
      setLinkWidth((w) => Math.max(1.5, w));
      setLinkSlope((s) => Math.min(5, s));
    }
  }
  function togglePanel(panel: "planner" | "results") {
    const mobile = window.matchMedia("(max-width: 900px)").matches;
    if (panel === "planner") {
      setPlannerOpen((open) => !open);
      if (mobile) setResultsOpen(false);
    } else {
      setResultsOpen((open) => !open);
      if (mobile) setPlannerOpen(false);
    }
  }

  return (
    <div
      className="app-shell"
      data-planner-open={plannerOpen}
      data-results-open={resultsOpen}
    >
      <header className="app-header">
        <a
          className="brand"
          href="#workspace"
          aria-label="SketchFuture 街道實驗室"
        >
          <span className="brand-mark">
            <Icon name="map" />
          </span>
          <span>
            SketchFuture<small>澳門街道實驗室</small>
          </span>
        </a>
        <div className="header-actions glass">
          <button
            onClick={() => togglePanel("results")}
            aria-pressed={resultsOpen}
          >
            <Icon name="layers" />
            <span>比較結果</span>
          </button>
          <button
            onClick={() => openDialog("assumptions")}
            aria-label="資料與假設"
            title="資料與假設"
          >
            <Icon name="info" />
          </button>
        </div>
      </header>
      <main
        ref={workspaceElement}
        id="workspace"
        className="map-workspace"
        aria-label="澳門街道方案工作區"
      >
        <div className={`map-grid ${view === "split" ? "split" : ""}`}>
          {view === "split" ? (
            <MapCanvas
              map={MAP}
              edges={MAP.edges}
              run={comparison?.baseline}
              time={time}
              profile={profile}
              tool="inspect"
              editable={false}
              onEdge={() => {}}
              onLink={() => {}}
              title="改動前"
            />
          ) : null}
          <MapCanvas
            map={MAP}
            edges={edges}
            run={comparison?.proposal}
            time={time}
            profile={profile}
            tool={tool}
            editable
            selected={selectedEdge?.id}
            onEdge={chooseEdge}
            onLink={addLink}
            title="你的方案"
          />
        </div>
        <div className="map-top-controls">
          <div
            className="tool-strip glass"
            role="toolbar"
            aria-label="街道改動工具"
          >
            {TOOLS.map((t) => (
              <button
                key={t.id}
                className={tool === t.id ? "active" : ""}
                aria-pressed={tool === t.id}
                onClick={() => chooseTool(t.id)}
                title={t.hint}
              >
                <Icon name={t.icon} />
                <span>{t.label}</span>
              </button>
            ))}
          </div>
          <div className="view-toggle glass" aria-label="地圖呈現">
            <button
              aria-pressed={view === "proposal"}
              className={view === "proposal" ? "active" : ""}
              onClick={() => setView("proposal")}
            >
              方案
            </button>
            <button
              aria-pressed={view === "split"}
              className={view === "split" ? "active" : ""}
              onClick={() => setView("split")}
            >
              並排比較
            </button>
          </div>
        </div>
        <p className="tool-hint glass">
          {TOOLS.find((t) => t.id === tool)!.hint}
        </p>
        <FloatingPanel
          id="planner"
          className="planner-panel"
          title="街區方案"
          subtitle="議事亭 · 板樟堂 · 大三巴"
          expanded={plannerOpen}
          onToggle={() => togglePanel("planner")}
        >
          <nav className="panel-tabs" aria-label="方案面板">
            {(
              [
                ["plan", "方案"],
                ["conditions", "條件"],
                ["checks", "檢查"],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                aria-pressed={panelTab === id}
                className={panelTab === id ? "active" : ""}
                onClick={() => setPanelTab(id)}
              >
                {label}
              </button>
            ))}
          </nav>
          <div className="panel-scroll">
            {panelTab === "plan" ? (
              <>
                <div className="plan-name">
                  <label htmlFor="plan-title">方案名稱</label>
                  <input
                    id="plan-title"
                    value={workspace.title}
                    maxLength={80}
                    onChange={(e) =>
                      setHistory((h) => ({
                        ...h,
                        present: { ...h.present, title: e.target.value },
                      }))
                    }
                  />
                  <span className="save-status">
                    <Icon name={saveBlocked ? "info" : "check"} />
                    {saveMessage}
                  </span>
                </div>
                <div className="plan-actions">
                  <button
                    onClick={() => importInput.current?.click()}
                    aria-label="匯入方案"
                    title="匯入方案"
                  >
                    <Icon name="upload" />
                  </button>
                  <button
                    onClick={() =>
                      download(
                        "sketchfuture-plan.json",
                        JSON.stringify(workspace, null, 2),
                      )
                    }
                    aria-label="匯出方案"
                    title="匯出方案"
                  >
                    <Icon name="download" />
                  </button>
                  <span className="action-divider" />
                  <button
                    onClick={() => undo()}
                    disabled={!history.past.length}
                    aria-label="撤銷上一步"
                    title="撤銷上一步"
                  >
                    <Icon name="undo" />
                  </button>
                  <button
                    onClick={() => undo(true)}
                    disabled={!history.future.length}
                    aria-label="重做上一步"
                    title="重做上一步"
                  >
                    <Icon name="redo" />
                  </button>
                  <button
                    className="text-button"
                    onClick={() => openDialog("reset")}
                  >
                    重設
                  </button>
                </div>
                <section className="examples-section" aria-label="範例方案">
                  <h2>從一個改動開始</h2>
                  <p>範例會取代目前改動，可撤銷。</p>
                  <button onClick={() => preset("ramp")}>
                    <span className="example-icon">
                      <Icon name="ramp" />
                    </span>
                    <span>
                      <strong>大三巴樓梯改造</strong>
                      <small>加入無階梯通道</small>
                    </span>
                    <Icon name="chevron" />
                  </button>
                  <button onClick={() => preset("close")}>
                    <span className="example-icon closure">
                      <Icon name="close" />
                    </span>
                    <span>
                      <strong>大三巴街暫封一段</strong>
                      <small>看看人流怎樣繞行</small>
                    </span>
                    <Icon name="chevron" />
                  </button>
                  <button onClick={() => preset("link")}>
                    <span className="example-icon">
                      <Icon name="link" />
                    </span>
                    <span>
                      <strong>加入構想捷徑</strong>
                      <small>少繞路，會多排隊嗎？</small>
                    </span>
                    <Icon name="chevron" />
                  </button>
                </section>
                <div className="selected-panel">
                  <div>
                    <span className="eyebrow">已選通道</span>
                    <h3>{selectedEdge?.name ?? "選一段通道"}</h3>
                    <select
                      className="edge-picker"
                      aria-label="選擇通道"
                      value={selectedEdge?.id ?? ""}
                      onChange={(e) => setSelected(e.target.value)}
                    >
                      {edges.map((edge) => (
                        <option key={edge.id} value={edge.id}>
                          {edge.name} · {Math.round(edge.length)} m
                          {edge.kind === "steps" ? " · 樓梯" : ""}
                        </option>
                      ))}
                    </select>
                    {selectedEdge && (tool === "ramp" || tool === "close") ? (
                      <button
                        className="apply-tool"
                        onClick={() => chooseEdge(selectedEdge)}
                      >
                        套用目前工具
                      </button>
                    ) : null}
                  </div>
                  {selectedEdge ? (
                    <div className="edge-facts">
                      <span>
                        <b>{Math.round(selectedEdge.length)}</b> m
                      </span>
                      <span>
                        <b>{selectedEdge.width.toFixed(1)}</b> m 寬
                      </span>
                      <span>
                        {selectedEdge.kind === "steps"
                          ? "樓梯"
                          : selectedEdge.slope === null
                            ? "坡度未記錄，模型按 0%"
                            : `坡度 ${selectedEdge.slope}%`}
                      </span>
                      <span>{selectedEdge.closed ? "已封閉" : "開放"}</span>
                    </div>
                  ) : null}
                </div>
                {comparison ? (
                  <div className="bottleneck-list">
                    <span>排隊最多的通道</span>
                    {bottlenecks.length ? (
                      bottlenecks.map(([id, queue]) => (
                        <button key={id} onClick={() => setSelected(id)}>
                          {edges.find((e) => e.id === id)?.name ?? "通道"}
                          <b>最多 {queue.max} 人</b>
                        </button>
                      ))
                    ) : (
                      <span>這次模擬沒有入口排隊。</span>
                    )}
                  </div>
                ) : null}
                {tool === "link" || tool === "ramp" ? (
                  <div className="connection-options">
                    {tool === "link" ? (
                      <details className="landmark-link">
                        <summary>用地標選擇起終點</summary>
                        <div>
                          <label>
                            起點
                            <select
                              aria-label="連接起點"
                              value={landmarkFrom}
                              onChange={(e) => setLandmarkFrom(e.target.value)}
                            >
                              {MAP.places.map((place) => (
                                <option key={place.id} value={place.node}>
                                  {place.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            終點
                            <select
                              aria-label="連接終點"
                              value={landmarkTo}
                              onChange={(e) => setLandmarkTo(e.target.value)}
                            >
                              {MAP.places.map((place) => (
                                <option key={place.id} value={place.node}>
                                  {place.name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <button
                            className="secondary-button"
                            onClick={() => addLink(landmarkFrom, landmarkTo)}
                          >
                            新增此連接
                          </button>
                        </div>
                      </details>
                    ) : null}
                    <label>
                      構想寬度{" "}
                      <select
                        value={linkWidth}
                        onChange={(e) => setLinkWidth(Number(e.target.value))}
                      >
                        <option value="1" disabled={tool === "ramp"}>
                          1 m
                        </option>
                        <option value="1.5">1.5 m</option>
                        <option value="2">2 m</option>
                        <option value="3">3 m</option>
                      </select>
                    </label>
                    <label>
                      構想坡度{" "}
                      <select
                        value={linkSlope}
                        onChange={(e) => setLinkSlope(Number(e.target.value))}
                      >
                        <option value="0">0%</option>
                        <option value="4">4%</option>
                        <option value="5">5%</option>
                        <option value="8" disabled={tool === "ramp"}>
                          8%
                        </option>
                      </select>
                    </label>
                    <span>
                      未校驗建物、地形或施工可行性；坡道寬度至少 1.5 m。
                    </span>
                  </div>
                ) : null}

                <p className="model-caption">
                  真實 OSM 路網 · 通行條件待校準
                  <br />
                  新通道是構想，尚未驗證建物與地形。
                </p>
              </>
            ) : panelTab === "conditions" ? (
              <section className="assumption-controls">
                <div>
                  <span className="eyebrow">相同出發者，相同條件</span>
                  <h2>比較條件</h2>
                  <p>改動前後使用完全相同的出發者。調整後請重新比較。</p>
                </div>
                <label>
                  模擬人數 <b>{workspace.settings.people}</b>
                  <input
                    aria-label="模擬人數"
                    type="range"
                    min="30"
                    max="300"
                    step="15"
                    value={workspace.settings.people}
                    onChange={(e) => setting("people", Number(e.target.value))}
                  />
                </label>
                <label>
                  出發時段 <b>{workspace.settings.releaseSeconds} 秒</b>
                  <input
                    aria-label="出發時段"
                    type="range"
                    min="30"
                    max="300"
                    step="30"
                    value={workspace.settings.releaseSeconds}
                    onChange={(e) =>
                      setting("releaseSeconds", Number(e.target.value))
                    }
                  />
                </label>
                <label>
                  通道容量{" "}
                  <b>{workspace.settings.capacityFactor.toFixed(1)}×</b>
                  <input
                    aria-label="通道容量"
                    type="range"
                    min="0.3"
                    max="2"
                    step="0.1"
                    value={workspace.settings.capacityFactor}
                    onChange={(e) =>
                      setting("capacityFactor", Number(e.target.value))
                    }
                  />
                </label>
                <details>
                  <summary>重複與重現設定</summary>
                  <div className="advanced-settings">
                    <label>
                      起始種子{" "}
                      <input
                        type="number"
                        min="0"
                        max="2147483647"
                        value={workspace.settings.seed}
                        onChange={(e) =>
                          setting("seed", Number(e.target.value))
                        }
                      />
                    </label>
                    <label>
                      重複次數{" "}
                      <select
                        value={workspace.settings.repeats}
                        onChange={(e) =>
                          setting("repeats", Number(e.target.value))
                        }
                      >
                        {[1, 3, 5, 10].map((n) => (
                          <option key={n} value={n}>
                            {n} 次
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      速度{" "}
                      <select
                        value={workspace.settings.speedFactor}
                        onChange={(e) =>
                          setting("speedFactor", Number(e.target.value))
                        }
                      >
                        <option value="0.85">0.85×</option>
                        <option value="1">1×</option>
                        <option value="1.15">1.15×</option>
                      </select>
                    </label>
                  </div>
                </details>
              </section>
            ) : (
              <div className="checks-content">
                <Sensitivity
                  rows={checks}
                  busy={checking || busy}
                  onRun={() => compute(workspace, true)}
                />
                <section className="export-section">
                  <div>
                    <h2>把你的方案和依據帶走。</h2>
                    <p>方案 JSON 可重新匯入；報告保留資料來源、參數和結果。</p>
                  </div>
                  <div>
                    <button
                      className="secondary-button"
                      disabled={!comparison}
                      onClick={() =>
                        comparison &&
                        download(
                          "sketchfuture-report.json",
                          reportJSON(MAP, workspace, comparison, checks),
                        )
                      }
                    >
                      匯出完整報告
                    </button>
                    <button
                      className="secondary-button"
                      disabled={!comparison}
                      onClick={() =>
                        comparison &&
                        download(
                          "sketchfuture-metrics.csv",
                          reportCSV(comparison),
                          "text/csv",
                        )
                      }
                    >
                      匯出結果 CSV
                    </button>
                  </div>
                </section>
              </div>
            )}
          </div>
          <div className="panel-bottom">
            <span className="comparison-status">
              {workspace.edits.length} 項改動 ·{" "}
              {dirty ? "等待比較" : "已完成比較"}
            </span>
            <button
              className="primary-button compare-button"
              onClick={() => compute(workspace, false, true)}
              disabled={busy || checking}
            >
              <Icon name={busy ? "layers" : "play"} />
              {busy ? "正在比較…" : dirty ? "比較方案" : "重新比較"}
            </button>
          </div>
        </FloatingPanel>
        <FloatingPanel
          id="results"
          className="results-container"
          title="旅程比較"
          subtitle="同一批人，改動前與改動後"
          expanded={resultsOpen}
          onToggle={() => togglePanel("results")}
        >
          <Results
            comparison={comparison}
            selected={profile}
            onSelect={setProfile}
            busy={busy}
          />
        </FloatingPanel>
        <div className="map-bottom-controls">
          <div className="profile-filter glass" aria-label="顯示使用者">
            <button
              className={profile === "all" ? "active" : ""}
              aria-pressed={profile === "all"}
              onClick={() => setProfile("all")}
            >
              全部
            </button>
            {PROFILES.map((p) => (
              <button
                key={p.id}
                className={profile === p.id ? "active" : ""}
                onClick={() => setProfile(profile === p.id ? "all" : p.id)}
                aria-pressed={profile === p.id}
              >
                <span
                  className={`profile-symbol ${p.id}`}
                  style={{ background: p.color }}
                />
                {p.short}
              </button>
            ))}
          </div>
          <div className="playback-bar glass">
            <button
              className="play-button"
              aria-label={playing ? "暫停模擬播放" : "播放模擬"}
              disabled={!comparison || busy}
              onClick={() => {
                if (time >= duration) setTime(0);
                setPlaying((p) => !p);
              }}
            >
              <Icon name={playing ? "pause" : "play"} />
            </button>
            <span className="timecode">{clock(time)}</span>
            <input
              aria-label="模擬時間"
              type="range"
              min="0"
              max={duration}
              step="1"
              value={time}
              disabled={!comparison}
              onChange={(e) => {
                setTime(Number(e.target.value));
                setPlaying(false);
              }}
            />
            <span className="timecode">{clock(duration)}</span>
            <select
              aria-label="播放速度"
              value={playSpeed}
              onChange={(e) => setPlaySpeed(Number(e.target.value))}
            >
              <option value="1">1×</option>
              <option value="10">10×</option>
              <option value="30">30×</option>
            </select>
          </div>
          <div className="map-legend">
            <span>
              <i className="proposal-line" />
              構想通道
            </span>
            <span>
              <i className="closed-line" />
              暫封路
            </span>
            <span>
              <i className="steps-line" />
              樓梯
            </span>
          </div>
        </div>
        <div className="notification-stack">
          {error ? (
            <div className="alert error" role="alert">
              <Icon name="info" />
              <span>{error}</span>
              {saveBlocked ? (
                <button onClick={() => openDialog("reset")}>
                  備份並重新開始
                </button>
              ) : (
                <button aria-label="關閉錯誤提示" onClick={() => setError("")}>
                  <Icon name="x" />
                </button>
              )}
            </div>
          ) : null}
          {notice ? (
            <div className="alert notice" role="status">
              <Icon name="check" />
              <span>{notice}</span>
              <button aria-label="關閉提示" onClick={() => setNotice("")}>
                <Icon name="x" />
              </button>
            </div>
          ) : null}
        </div>
      </main>
      <input
        ref={importInput}
        type="file"
        accept=".json,application/json"
        hidden
        aria-label="方案 JSON 檔案"
        onChange={(e) => void importPlan(e.target.files?.[0])}
      />
      {dialog ? (
        <div
          className="modal-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) setDialog(null);
          }}
        >
          <section
            ref={modal}
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dialog-title"
          >
            <button
              autoFocus
              className="modal-close"
              onClick={() => setDialog(null)}
              aria-label="關閉對話框"
            >
              ×
            </button>
            {dialog === "reset" ? (
              <>
                <h2 id="dialog-title">重新開始這個街區？</h2>
                <p>
                  目前改動會清空，你仍可用撤銷恢復。
                  {saveBlocked
                    ? "無法讀取的原始保存資料會先下載備份。"
                    : "如要另存，可先匯出方案。"}
                </p>
                <div className="dialog-actions">
                  <button
                    className="secondary-button"
                    onClick={() => setDialog(null)}
                  >
                    保留目前方案
                  </button>
                  <button className="primary-button" onClick={reset}>
                    重新開始
                  </button>
                </div>
              </>
            ) : (
              <>
                <span className="eyebrow">
                  READ THE MODEL BEFORE THE NUMBERS
                </span>
                <h2 id="dialog-title">地圖是真的，條件有假設。</h2>
                <h3>真實資料</h3>
                <p>
                  此街區使用 {MAP.timestamp} 取得的 OpenStreetMap
                  街道座標、連接及樓梯標記，共 {MAP.nodes.length} 個路網節點、
                  {MAP.edges.length}{" "}
                  段通道。地標對應鄰近路網入口，並非建築內部或正式入口測量。
                </p>
                <p>
                  <a
                    href="https://www.openstreetmap.org/copyright"
                    target="_blank"
                    rel="noreferrer"
                  >
                    © OpenStreetMap contributors · ODbL
                  </a>{" "}
                  ·{" "}
                  <a href={MAP.source} target="_blank" rel="noreferrer">
                    原始資料查詢
                  </a>
                </p>
                <h3>通行與模擬假設</h3>
                <ul>
                  <li>
                    未標記寬度按 2 m、未標記坡度按 0%
                    計算；這不代表實際平坦或無障礙。街道中心線不等於實測行人道；模型未納入電梯、建物內部通行或路緣資料。
                  </li>
                  <li>
                    三類是示範通行設定：速度 1.3 / 0.9 / 1.05
                    m/s；輪椅及嬰兒車不走樓梯。並不代表每個人的能力或法定標準。
                  </li>
                  <li>
                    通道入口按先到先走排隊、雙向共享容量；不模擬碰撞、車輛、路緣或途中因擁擠改道。
                  </li>
                  <li>
                    構想坡道長度是原樓梯 1.8 倍，寬度至少 1.5
                    m。新連接是直線構想，沒有地形、建物、土地或施工校驗。
                  </li>
                  <li>起終點及出發時間是合成需求；這不是實際澳門人流。</li>
                  <li>
                    平均時間只計已到達者；不可達及仍在途中者另外列出。種子範圍不是信賴區間。
                  </li>
                </ul>
                <p className="model-boundary">
                  適合比較模型內取捨、解釋方案與課堂探索。不能作為現場導航、安全認證或城市改造效果預測。
                </p>
              </>
            )}
          </section>
        </div>
      ) : null}
    </div>
  );
}
