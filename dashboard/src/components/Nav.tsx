"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ITEMS = [
  ["/", "Overview"], ["/map", "Live map"], ["/alerts", "Alerts"], ["/interventions", "Interventions"], ["/explain", "AI explanation"],
  ["/reliability", "Reliability"], ["/evaluation", "Evaluation"], ["/privacy", "Privacy"],
];

export function Nav() {
  const path = usePathname();
  return (
    <nav className="hidden w-48 shrink-0 border-r border-zinc-800 bg-[#151514] p-3 md:block">
      <ul className="space-y-1">
        {ITEMS.map(([href, label]) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return (
            <li key={href}>
              <Link href={href} className={`block rounded px-3 py-1.5 text-sm ${active ? "bg-zinc-800 font-semibold text-white" : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-100"}`}>{label}</Link>
            </li>
          );
        })}
      </ul>
      <p className="mt-6 px-3 text-[10px] leading-relaxed text-zinc-500">Decision-support prototype. The AI recommends; a human operator decides. No facial recognition, no identifiable video.</p>
    </nav>
  );
}
