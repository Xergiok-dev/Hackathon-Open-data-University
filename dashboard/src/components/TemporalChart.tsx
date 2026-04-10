"use client";

import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { DPERecord } from "@/types";

export default function TemporalChart({ data }: { data: DPERecord[] }) {
  const chartData = useMemo(() => {
    const byYear = new Map<number, { sum: number; count: number }>();
    for (const d of data) {
      if (!d.annee || !d.conso_reelle_par_m2) continue;
      const entry = byYear.get(d.annee) ?? { sum: 0, count: 0 };
      entry.sum += d.conso_reelle_par_m2;
      entry.count += 1;
      byYear.set(d.annee, entry);
    }
    return Array.from(byYear.entries())
      .sort(([a], [b]) => a - b)
      .map(([year, { sum, count }]) => ({
        annee: year,
        conso_moy: +(sum / count).toFixed(1),
        nb_points: count,
      }));
  }, [data]);

  return (
    <div className="h-48">
      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        Evolution conso moyenne (kWh/m2)
      </h3>
      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="annee"
            tick={{ fill: "#94a3b8", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={35}
            domain={["dataMin - 5", "dataMax + 5"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(15,15,20,0.95)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "#e2e8f0",
              fontSize: 13,
            }}
            formatter={(value, name) => {
              if (name === "conso_moy") return [`${value} kWh/m2`, "Conso moyenne"];
              return [String(value), String(name)];
            }}
          />
          <Line
            type="monotone"
            dataKey="conso_moy"
            stroke="#60a5fa"
            strokeWidth={2.5}
            dot={{ fill: "#60a5fa", r: 4 }}
            activeDot={{ r: 6, stroke: "#3b82f6" }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
