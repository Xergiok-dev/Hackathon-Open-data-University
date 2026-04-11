"use client";

import { useState, useEffect } from "react";
import type { DPERecord, TopAdresse, GainParClasse, Variabilite, LayerMode, KPIPanel } from "@/types";
import { loadMainData, loadTopAdresses, loadGainsParClasse, loadVariabilite, computeKPIs } from "@/lib/data";
import KPIBar from "@/components/KPIBar";
import KPIDetailPanel from "@/components/KPIDetailPanel";
import MapView from "@/components/MapView";
import MapControls from "@/components/MapControls";
import Sidebar from "@/components/Sidebar";

export default function Dashboard() {
  const [data, setData] = useState<DPERecord[]>([]);
  const [topAdresses, setTopAdresses] = useState<TopAdresse[]>([]);
  const [gains, setGains] = useState<GainParClasse[]>([]);
  const [variabilite, setVariabilite] = useState<Variabilite[]>([]);
  const [layerMode, setLayerMode] = useState<LayerMode>("dpe_classes");
  const [activePanel, setActivePanel] = useState<KPIPanel>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      loadMainData(),
      loadTopAdresses(),
      loadGainsParClasse(),
      loadVariabilite(),
    ]).then(([main, top, g, v]) => {
      setData(main);
      setTopAdresses(top);
      setGains(g);
      setVariabilite(v);
      setLoading(false);
    });
  }, []);

  const kpis = data.length > 0
    ? computeKPIs(data)
    : { uniqueAddresses: 0, avgEcart: 0, totalGainsGWh: 0 };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white/80 rounded-full animate-spin" />
          <p className="text-sm text-muted-foreground">Chargement des donnees...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="shrink-0 border-b border-white/5 bg-card/30 backdrop-blur-md px-4 py-3">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-lg font-bold tracking-tight">
              Pipeline DPE x Enedis
            </h1>
            <p className="text-xs text-muted-foreground">
              Analyse croisee performance energetique vs consommation reelle — Paris & 92
            </p>
          </div>
          <div className="text-xs text-muted-foreground font-mono">
            {data.length.toLocaleString("fr-FR")} enregistrements | 2018-2024
          </div>
        </div>
        <KPIBar kpis={kpis} activePanel={activePanel} onTogglePanel={setActivePanel} />
      </header>

      {/* Expandable KPI detail panels */}
      <KPIDetailPanel
        panel={activePanel}
        data={data}
        gains={gains}
        variabilite={variabilite}
      />

      {/* Main content: Map + Sidebar */}
      <div className="flex-1 flex min-h-0">
        <div className="flex-1 relative">
          <MapView data={data} layerMode={layerMode} />
          <MapControls active={layerMode} onChange={setLayerMode} />
        </div>
        <Sidebar data={data} topAdresses={topAdresses} />
      </div>
    </div>
  );
}
