"use client";

import type { DPERecord, TopAdresse } from "@/types";
import DPEDistribution from "./DPEDistribution";
import TemporalChart from "./TemporalChart";
import TopAddresses from "./TopAddresses";

interface Props {
  data: DPERecord[];
  topAdresses: TopAdresse[];
}

export default function Sidebar({ data, topAdresses }: Props) {
  return (
    <aside className="w-[420px] shrink-0 bg-card/30 backdrop-blur-md border-l border-white/5 overflow-y-auto p-4 flex flex-col gap-5">
      <DPEDistribution data={data} />
      <div className="h-px bg-white/5" />
      <TemporalChart data={data} />
      <div className="h-px bg-white/5" />
      <TopAddresses data={topAdresses} />
    </aside>
  );
}
