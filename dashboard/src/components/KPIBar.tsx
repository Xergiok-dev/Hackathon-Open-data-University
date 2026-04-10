"use client";

import { Card } from "@/components/ui/card";

interface KPIs {
  uniqueAddresses: number;
  avgEcart: number;
  totalGainsGWh: number;
}

export default function KPIBar({ kpis }: { kpis: KPIs }) {
  const items = [
    {
      label: "Adresses analysees",
      value: kpis.uniqueAddresses.toLocaleString("fr-FR"),
      sub: "Paris & Hauts-de-Seine",
    },
    {
      label: "Ecart moyen DPE vs Reel",
      value: `+${kpis.avgEcart}%`,
      sub: "Surestimation theorique",
    },
    {
      label: "Gains potentiels",
      value: `${kpis.totalGainsGWh} GWh/an`,
      sub: "Si renovation vers classe C",
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {items.map((item) => (
        <Card
          key={item.label}
          className="bg-card/50 border-white/5 px-4 py-3 backdrop-blur-sm"
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
