const paths = {
  map: "M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2V5zm6-2v16m6-14v16",
  inspect: "M4 3l5 17 3-7 7-3L4 3z",
  link: "M6 18L18 6M5 15v4h4M15 5h4v4",
  ramp: "M4 19h16M5 15l12-10M12 5h5v5",
  close: "M5 5l14 14M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  undo: "M9 5L4 10l5 5M4 10h9a7 7 0 017 7",
  redo: "M15 5l5 5-5 5m5-5h-9a7 7 0 00-7 7",
  download: "M12 3v12m-5-5l5 5 5-5M4 16v5h16v-5",
  upload: "M12 16V4M7 9l5-5 5 5M4 17v4h16v-4",
  info: "M12 11v6m0-10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  layers: "M3 7l9-4 9 4-9 4-9-4zm0 5l9 4 9-4M3 17l9 4 9-4",
  play: "M7 4l13 8-13 8V4z",
  pause: "M8 5v14M16 5v14",
  chevron: "M8 5l7 7-7 7",
  check: "M5 12l4 4L19 6",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  locate: "M12 2v4m0 12v4M2 12h4m12 0h4M18 12a6 6 0 11-12 0 6 6 0 0112 0z",
  x: "M6 6l12 12M18 6L6 18",
} as const;

export type IconName = keyof typeof paths;

export default function Icon({
  name,
  className = "",
}: {
  name: IconName;
  className?: string;
}) {
  return (
    <svg
      className={`icon ${className}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}
