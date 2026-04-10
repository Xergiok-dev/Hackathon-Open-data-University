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
} from "recharts";
import type { DPERecord } from "@/types";
import { DPE_ORDER, getDPEColorHex } from "@/lib/colors";

export default function DPEDistribution({ data }: { data: DPERecord[] }) {
  const chartData = useMemo(() => {
    const counts = new Map<string, number>();
    for (const d of data) {
      const cls = d.classe_dpe_modale;
      counts.set(cls, (counts.get(cls) ?? 0) + 1);
    }
    return DPE_ORDER.map((cls) => ({
      classe: cls,
      count: counts.get(cls) ?? 0,
    }));
  }, [data]);

  return (
    <div className="h-48">
      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        Repartition des classes DPE
      </h3>
      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={chartData} barSize={28}>
          <XAxis
            dataKey="classe"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={35}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "rgba(15,15,20,0.95)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color: "#e2e8f0",
              fontSize: 13,
            }}
            formatter={(value) => [`${value} enregistrements`, "Nombre"]}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {chartData.map((entry) => (
              <Cell
                key={entry.classe}
                fill={getDPEColorHex(entry.classe)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
