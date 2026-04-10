"use client";

import type { LayerMode } from "@/types";

const MODES: { id: LayerMode; label: string; icon: string }[] = [
  { id: "dpe_classes", label: "Classes DPE", icon: "A-G" },
  { id: "heatmap", label: "Heatmap conso", icon: "kWh" },
  { id: "ecarts", label: "Ecarts DPE vs Reel", icon: "%" },
];

interface Props {
  active: LayerMode;
  onChange: (mode: LayerMode) => void;
}

export default function MapControls({ active, onChange }: Props) {
  return (
    <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5">
      {MODES.map((m) => (
        <button
          key={m.id}
          onClick={() => onChange(m.id)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all
            ${
              active === m.id
                ? "bg-white/15 text-white border border-white/20 shadow-lg backdrop-blur-md"
                : "bg-black/40 text-white/60 border border-white/5 backdrop-blur-sm hover:bg-white/10 hover:text-white/90"
            }`}
        >
          <span className="text-xs font-mono w-6 text-center opacity-60">{m.icon}</span>
          {m.label}
        </button>
      ))}
    </div>
  );
}
