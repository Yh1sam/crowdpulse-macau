import type { Comparison, ProfileId, SensitivityRow } from "../core/types";
import { PROFILES } from "../core/model";

export const minutes = (seconds: number | null) =>
  seconds === null ? "—" : `${(seconds / 60).toFixed(1)} 分`;
export const changeText = (seconds: number | null) =>
  seconds === null
    ? "沒有配對結果"
    : Math.abs(seconds) < 0.5
      ? "大致相同"
      : `${seconds < 0 ? "快" : "慢"} ${Math.abs(seconds) < 60 ? `${Math.round(Math.abs(seconds))} 秒` : `${Math.abs(seconds / 60).toFixed(1)} 分`}`;
const signedMinutes = (seconds: number) =>
  Math.abs(seconds) < 3 ? "0.0" : (seconds / 60).toFixed(1);

export default function Results({
  comparison,
  selected,
  onSelect,
  busy,
}: {
  comparison: Comparison | null;
  selected: ProfileId | "all";
  onSelect: (id: ProfileId | "all") => void;
  busy: boolean;
}) {
  return (
    <aside className="results-panel">
      <div className="panel-heading">
        <span className="eyebrow">改動前 → 你的方案</span>
        <h2 className="sr-only">比較結果</h2>
      </div>
      <p className="panel-description">
        點選使用者，查看地圖路線。兩邊使用同一批出發者。
      </p>
      {PROFILES.map((profile) => {
        const b = comparison?.baseline.profiles[profile.id],
          a = comparison?.proposal.profiles[profile.id];
        const paired = comparison?.paired[profile.id];
        const delta = paired?.delta ?? null;
        const band = comparison?.ranges[profile.id].delta;
        const changedReach = !!a && !!b && a.arrived !== b.arrived;
        return (
          <article
            key={profile.id}
            className={`profile-result ${selected === profile.id ? "selected" : ""}`}
            style={{ "--profile-color": profile.color } as React.CSSProperties}
          >
            <button
              className="profile-select"
              onClick={() =>
                onSelect(selected === profile.id ? "all" : profile.id)
              }
              aria-pressed={selected === profile.id}
            >
              <span className="profile-heading">
                <span className={`profile-symbol ${profile.id}`} />
                <strong>{profile.name}</strong>
                <span className="profile-selection" aria-hidden="true">
                  {selected === profile.id ? "✓" : "›"}
                </span>
              </span>
            </button>
            {busy ? (
              <div className="result-loading">正在比較相同出發條件…</div>
            ) : a && b ? (
              <>
                <div
                  className={`delta ${a.arrived < b.arrived || (a.arrived === b.arrived && delta !== null && delta > 0.5) ? "slower" : ""}`}
                >
                  {a.arrived !== b.arrived
                    ? `${a.arrived > b.arrived ? "多" : "少"} ${Math.abs(a.arrived - b.arrived)} 人到達`
                    : changeText(delta)}
                </div>
                <div className="metric-pair">
                  <span>
                    原狀 <b>{minutes(b.meanTime)}</b>
                  </span>
                  <span className="metric-arrow">→</span>
                  <span>
                    方案 <b>{minutes(a.meanTime)}</b>
                  </span>
                </div>
                <div className="reach-row">
                  到達{" "}
                  <b>
                    {b.arrived}/{b.people}
                  </b>
                  <span>→</span>
                  <b>
                    {a.arrived}/{a.people}
                  </b>
                </div>
                {a.unreachable || a.unfinished ? (
                  <p className="result-note">
                    模型中：{a.unreachable} 人無可用路線，{a.unfinished}{" "}
                    人仍在途中。
                  </p>
                ) : null}
                {changedReach ? (
                  <p className="result-note">
                    到達人數有變化；平均時間只計各方案已到達者。
                  </p>
                ) : null}
                {paired ? (
                  <div className="paired-note">
                    同一批到達者 {paired.count} 人 · {changeText(delta)}
                  </div>
                ) : null}
                {band ? (
                  <div className="range-note">
                    {comparison!.repeats} 次配對差值 {signedMinutes(band[0])} 至{" "}
                    {signedMinutes(band[1])} 分
                  </div>
                ) : null}
                <details className="profile-details">
                  <summary>等待與路程</summary>
                  <div className="small-metrics">
                    <span>
                      平均等待{" "}
                      <b>
                        {minutes(b.meanWait)} → {minutes(a.meanWait)}
                      </b>
                    </span>
                    <span>
                      平均路程{" "}
                      <b>
                        {b.meanDistance === null
                          ? "—"
                          : Math.round(b.meanDistance)}{" "}
                        →{" "}
                        {a.meanDistance === null
                          ? "—"
                          : Math.round(a.meanDistance)}{" "}
                        m
                      </b>
                    </span>
                  </div>
                </details>
              </>
            ) : (
              <div className="result-empty">
                執行比較後，查看路程、等待與可達率。
              </div>
            )}
          </article>
        );
      })}
      <div className="results-footnote">
        平均旅程時間只計已到達者；快慢差值配對同一批人。範圍是多次模擬結果，並非真實成效或信賴區間。
      </div>
    </aside>
  );
}

export function Sensitivity({
  rows,
  busy,
  onRun,
}: {
  rows: SensitivityRow[] | null;
  busy: boolean;
  onRun: () => void;
}) {
  return (
    <section className="sensitivity-section">
      <div className="section-title">
        <div>
          <span className="eyebrow">人流與步行速度</span>
          <h2>檢查不同條件</h2>
        </div>
        <button className="secondary-button" onClick={onRun} disabled={busy}>
          {busy ? "正在檢查…" : "檢查 9 種條件 ↗"}
        </button>
      </div>
      <p>
        固定相同出發者，分別改變人流與速度。時間差只配對兩邊都到達的同一批人；負值代表較快。此處每個條件跑一次。
      </p>
      {rows ? (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>條件</th>
                {PROFILES.map((p) => (
                  <th key={p.id}>{p.name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label}>
                  <th>{row.label}</th>
                  {PROFILES.map((p) => {
                    const cell = row.profiles[p.id];
                    return (
                      <td
                        key={p.id}
                        className={
                          cell.delta !== null && cell.delta < -0.5
                            ? "faster-cell"
                            : cell.delta !== null && cell.delta > 0.5
                              ? "slower-cell"
                              : ""
                        }
                      >
                        {cell.delta === null
                          ? "—"
                          : `${cell.delta > 0 ? "+" : ""}${(cell.delta / 60).toFixed(1)} 分`}
                        <small>
                          到達 {cell.beforeArrived} → {cell.afterArrived}
                        </small>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="sensitivity-empty">
          改變人流與速度，檢查方案的取捨是否仍然成立。
        </div>
      )}
    </section>
  );
}
