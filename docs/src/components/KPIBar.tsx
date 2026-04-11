"use client";

import { Card } from "@/components/ui/card";
import type { KPIPanel } from "@/types";

interface KPIs {
  uniqueAddresses: number;
  avgEcart: number;
  totalGainsGWh: number;
}

interface Props {
  kpis: KPIs;
  activePanel: KPIPanel;
  onTogglePanel: (panel: KPIPanel) => void;
}

export default function KPIBar({ kpis, activePanel, onTogglePanel }: Props) {
  const items: { id: KPIPanel; label: string; value: string; sub: string }[] = [
    {
      id: "addresses",
      label: "Adresses analysees",
      value: kpis.uniqueAddresses.toLocaleString("fr-FR"),
      sub: "Paris & Hauts-de-Seine — Cliquer pour details",
    },
    {
      id: "ecarts",
      label: "Ecart moyen DPE vs Reel",
      value: `+${kpis.avgEcart}%`,
      sub: "Surestimation theorique — Cliquer pour details",
    },
    {
      id: "gains",
      label: "Gains potentiels",
      value: `${kpis.totalGainsGWh} GWh/an`,
      sub: "Si renovation vers classe C — Cliquer pour details",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {items.map((item) => (
        <Card
          key={item.id}
          onClick={() => onTogglePanel(activePanel === item.id ? null : item.id)}
          className={`px-4 py-3 backdrop-blur-sm cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:border-white/20 ${
            activePanel === item.id
              ? "bg-white/10 border-white/20 ring-1 ring-white/10"
              : "bg-card/50 border-white/5"
          }`}
        >
          <p className="text-xs text-muted-foreground uppercase tracking-wider">
            {item.label}
          </p>
          <p className="text-2xl font-bold mt-1 tracking-tight">{item.value}</p>
          <p className="text-xs text-muted-foreground mt-0.5">{item.sub}</p>
        </Card>
      ))}
    </div>
  );
}
