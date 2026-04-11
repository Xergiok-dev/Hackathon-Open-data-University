"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ScatterChart,
  Scatter,
  ZAxis,
  CartesianGrid,
  Legend,
} from "recharts";
import type { DPERecord, GainParClasse, Variabilite, KPIPanel } from "@/types";
import { DPE_ORDER, getDPEColorHex } from "@/lib/colors";

interface Props {
  panel: KPIPanel;
  data: DPERecord[];
  gains: GainParClasse[];
  variabilite: Variabilite[];
}

const tooltipStyle = {
  backgroundColor: "rgba(15,15,20,0.95)",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8,
  color: "#e2e8f0",
  fontSize: 13,
};

// Panel "Adresses analysees" — breakdown by commune + DPE class scatter
function AddressesPanel({ data }: { data: DPERecord[] }) {
  const byCommune = useMemo(() => {
    const map = new Map<string, number>();
    for (const d of data) {
      const key = d.nom_commune || "Inconnu";
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return Array.from(map.entries())
      .map(([commune, count]) => ({ commune, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 12);
  }, [data]);

  const byDeptAndClass = useMemo(() => {
    const map = new Map<string, number>();
    for (const d of data) {
      const key = `${d.dept === 75 ? "Paris" : "92"}-${d.classe_dpe_modale}`;
      map.set(key, (map.get(key) ?? 0) + 1);
    }
    return DPE_ORDER.map((cls) => ({
      classe: cls,
      Paris: map.get(`Paris-${cls}`) ?? 0,
      "Hauts-de-Seine": map.get(`92-${cls}`) ?? 0,
    }));
  }, [data]);

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Enregistrements par commune (Top 12)
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={byCommune} layout="vertical" barSize={14}>
            <XAxis type="number" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="commune"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              width={120}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill="#60a5fa" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Classes DPE par departement
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={byDeptAndClass} barSize={16}>
            <XAxis dataKey="classe" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={35} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
            <Bar dataKey="Paris" fill="#818cf8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Hauts-de-Seine" fill="#34d399" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Panel "Ecart moyen" — variabilite par classe + scatter conso vs ecart
function EcartsPanel({ data, variabilite }: { data: DPERecord[]; variabilite: Variabilite[] }) {
  const varData = useMemo(
    () =>
      DPE_ORDER.map((cls) => {
        const v = variabilite.find((x) => x.classe_dpe === cls);
        return {
          classe: cls,
          ecart_moyen: v ? Math.round(v["ecart_moyen_%"]) : 0,
          cv: v ? Math.round(v["cv_%"]) : 0,
          n: v?.n_logements ?? 0,
        };
      }),
    [variabilite]
  );

  // Scatter: conso reelle vs ecart % (sampled for perf)
  const scatterData = useMemo(() => {
    const sampled = data.filter((_, i) => i % 3 === 0);
    return sampled
      .filter((d) => d.conso_reelle_par_m2 && d.ecart_pct)
      .map((d) => ({
        x: d.conso_reelle_par_m2,
        y: d.ecart_pct,
        classe: d.classe_dpe_modale,
        adresse: d.adresse,
      }));
  }, [data]);

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Ecart moyen & variabilite par classe DPE
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={varData} barSize={24}>
            <XAxis dataKey="classe" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={40} unit="%" />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => {
                if (name === "ecart_moyen") return [`${value}%`, "Ecart moyen"];
                if (name === "cv") return [`${value}%`, "Coeff. variation"];
                return [String(value), String(name)];
              }}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
            <Bar dataKey="ecart_moyen" name="Ecart moyen" radius={[4, 4, 0, 0]}>
              {varData.map((entry) => (
                <Cell key={entry.classe} fill={getDPEColorHex(entry.classe)} />
              ))}
            </Bar>
            <Bar dataKey="cv" name="Coeff. variation" fill="#94a3b8" opacity={0.4} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Conso reelle vs Ecart DPE (kWh/m2 vs %)
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis
              dataKey="x"
              name="Conso"
              unit=" kWh"
              tick={{ fill: "#64748b", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              dataKey="y"
              name="Ecart"
              unit="%"
              tick={{ fill: "#64748b", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            <ZAxis range={[15, 15]} />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value, name) => {
                if (name === "Conso") return [`${value} kWh/m2`, "Conso reelle"];
                if (name === "Ecart") return [`${value}%`, "Ecart DPE"];
                return [String(value), String(name)];
              }}
            />
            <Scatter data={scatterData} fill="#f472b6" opacity={0.5} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Panel "Gains potentiels" — gains par transition + economies cumulees
function GainsPanel({ gains }: { gains: GainParClasse[] }) {
  const gainsData = useMemo(
    () =>
      gains.map((g) => ({
        ...g,
        gain_kwh_m2_an: Math.abs(g.gain_kwh_m2_an),
        gain_euros_65m2: Math.abs(g.gain_euros_65m2),
        positive: g.gain_kwh_m2_an > 0,
      })),
    [gains]
  );

  return (
    <div className="grid grid-cols-2 gap-6">
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Gains energetiques par transition (kWh/m2/an)
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={gainsData} barSize={28}>
            <XAxis
              dataKey="transition"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={35} />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [`${value} kWh/m2/an`, "Gain"]}
            />
            <Bar dataKey="gain_kwh_m2_an" radius={[4, 4, 0, 0]}>
              {gainsData.map((entry, i) => (
                <Cell key={i} fill={entry.positive ? "#34d399" : "#f87171"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
          Economies annuelles pour un 65m2 (euros/an)
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={gainsData} barSize={28}>
            <XAxis
              dataKey="transition"
              tick={{ fill: "#94a3b8", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={40} unit="€" />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [`${value} €/an`, "Economies"]}
            />
            <Bar dataKey="gain_euros_65m2" radius={[4, 4, 0, 0]}>
              {gainsData.map((entry, i) => (
                <Cell key={i} fill={entry.positive ? "#60a5fa" : "#fb923c"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function KPIDetailPanel({ panel, data, gains, variabilite }: Props) {
  if (!panel) return null;

  return (
    <div className="shrink-0 border-b border-white/5 bg-card/40 backdrop-blur-md px-4 py-4 animate-in slide-in-from-top-2 duration-300">
      {panel === "addresses" && <AddressesPanel data={data} />}
      {panel === "ecarts" && <EcartsPanel data={data} variabilite={variabilite} />}
      {panel === "gains" && <GainsPanel gains={gains} />}
    </div>
  );
}
