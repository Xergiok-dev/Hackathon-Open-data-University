"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { TopAdresse } from "@/types";
import { getDPEColorHex } from "@/lib/colors";

export default function TopAddresses({ data }: { data: TopAdresse[] }) {
  return (
    <div>
      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
        Top 20 — Adresses les plus consommatrices
      </h3>
      <div className="max-h-64 overflow-y-auto rounded-lg border border-white/5">
        <Table>
          <TableHeader>
            <TableRow className="border-white/5 hover:bg-transparent">
              <TableHead className="text-xs text-muted-foreground">#</TableHead>
              <TableHead className="text-xs text-muted-foreground">Adresse</TableHead>
              <TableHead className="text-xs text-muted-foreground text-right">kWh/m2</TableHead>
              <TableHead className="text-xs text-muted-foreground text-center">DPE</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, i) => (
              <TableRow key={row.ban_id ?? i} className="border-white/5 text-sm">
                <TableCell className="font-mono text-muted-foreground py-1.5">
                  {i + 1}
                </TableCell>
                <TableCell className="max-w-[180px] truncate py-1.5" title={row.adresse}>
                  {row.adresse}
                </TableCell>
                <TableCell className="text-right font-mono py-1.5">
                  {row.conso_reelle_par_m2?.toFixed(0)}
                </TableCell>
                <TableCell className="text-center py-1.5">
                  <Badge
                    variant="outline"
                    className="font-bold text-xs border-0"
                    style={{
                      backgroundColor: getDPEColorHex(row.classe_dpe_modale) + "30",
                      color: getDPEColorHex(row.classe_dpe_modale),
                    }}
                  >
                    {row.classe_dpe_modale}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
