import { useLayoutEffect, useRef, type ReactNode } from "react";

type FloatingPanelProps = {
  id: string;
  className?: string;
  title: string;
  subtitle?: string;
  expanded: boolean;
  onToggle: () => void;
  children: ReactNode;
};

export default function FloatingPanel({
  id,
  className = "",
  title,
  subtitle,
  expanded,
  onToggle,
  children,
}: FloatingPanelProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const spring = useRef({ height: 0, velocity: 0, initialized: false });

  useLayoutEffect(() => {
    const body = bodyRef.current;
    const content = contentRef.current;
    if (!body || !content) return;

    if (!expanded && body.contains(document.activeElement)) {
      toggleRef.current?.focus();
    }
    body.hidden = false;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const state = spring.current;
    let target = expanded ? content.getBoundingClientRect().height : 0;
    let frame = 0;
    let lastTime = performance.now();

    const paint = () => {
      body.style.height = `${Math.max(0, state.height)}px`;
    };
    const settle = () => {
      state.height = target;
      state.velocity = 0;
      paint();
      body.hidden = !expanded;
    };
    const step = (time: number) => {
      frame = 0;
      const dt = Math.min((time - lastTime) / 1000, 0.05);
      lastTime = time;
      // Exact critically damped spring: retarget without losing position or velocity.
      const omega = (2 * Math.PI) / 0.3;
      const displacement = state.height - target;
      const decay = Math.exp(-omega * dt);
      const carry = (state.velocity + omega * displacement) * dt;
      state.height = target + (displacement + carry) * decay;
      state.velocity = (state.velocity - omega * carry) * decay;
      if (
        Math.abs(state.height - target) < 0.25 &&
        Math.abs(state.velocity) < 2
      ) {
        settle();
      } else {
        paint();
        frame = requestAnimationFrame(step);
      }
    };
    const animate = () => {
      if (motion.matches) {
        cancelAnimationFrame(frame);
        frame = 0;
        settle();
      } else if (!frame) {
        lastTime = performance.now();
        frame = requestAnimationFrame(step);
      }
    };

    if (!state.initialized) {
      state.initialized = true;
      settle();
    } else {
      animate();
    }

    const resize = () => {
      if (!expanded) return;
      target = content.getBoundingClientRect().height;
      animate();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(content);
    motion.addEventListener("change", animate);
    return () => {
      observer.disconnect();
      motion.removeEventListener("change", animate);
      cancelAnimationFrame(frame);
    };
  }, [expanded]);

  return (
    <section
      className={`floating-panel ${expanded ? "is-expanded" : "is-collapsed"} ${className}`.trim()}
      aria-labelledby={`${id}-title`}
    >
      <header className="floating-panel-header">
        <div className="floating-panel-title">
          <h2 id={`${id}-title`}>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <button
          ref={toggleRef}
          className="floating-panel-toggle"
          type="button"
          onClick={onToggle}
          aria-label={`${expanded ? "收合" : "展開"}${title}`}
          aria-expanded={expanded}
          aria-controls={`${id}-body`}
        >
          <span className="floating-panel-toggle-label">
            {expanded ? "收合" : "展開"}
          </span>
          <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
            <path
              d="m4 6 4 4 4-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </header>
      <div
        ref={bodyRef}
        id={`${id}-body`}
        className="floating-panel-body"
        aria-hidden={!expanded}
        inert={!expanded}
        style={{ overflow: "hidden" }}
      >
        <div ref={contentRef} className="floating-panel-content">
          {children}
        </div>
      </div>
    </section>
  );
}
