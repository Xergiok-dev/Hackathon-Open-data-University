import Papa from "papaparse";
import type { DPERecord, TopAdresse, StatsParClasse, GainParClasse, Variabilite } from "@/types";

const basePath = '/Hackathon-Open-data-University';

async function fetchCSV<T>(url: string): Promise<T[]> {
  const res = await fetch(url);
  const text = await res.text();
  const { data } = Papa.parse<T>(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true,
  });
  return data;
}

export async function loadMainData(): Promise<DPERecord[]> {
  return fetchCSV<DPERecord>(`${basePath}/data/dpe_enedis_joined.csv`);
}

export async function loadTopAdresses(): Promise<TopAdresse[]> {
  return fetchCSV<TopAdresse>(`${basePath}/data/top_20_adresses_conso.csv`);
}

export async function loadStatsParClasse(): Promise<StatsParClasse[]> {
  return fetchCSV<StatsParClasse>(`${basePath}/data/stats_descriptives_par_classe.csv`);
}

export async function loadGainsParClasse(): Promise<GainParClasse[]> {
  return fetchCSV<GainParClasse>(`${basePath}/data/gains_par_classe.csv`);
}

export async function loadVariabilite(): Promise<Variabilite[]> {
  return fetchCSV<Variabilite>(`${basePath}/data/variabilite_comportements.csv`);
}

// Compute global KPIs from the main dataset
export function computeKPIs(data: DPERecord[]) {
  const uniqueAddresses = new Set(data.map((d) => d.ban_id)).size;
  const avgEcart =
    data.reduce((sum, d) => sum + (d.ecart_pct ?? 0), 0) / data.length;

  // Total theoretical savings if all buildings reached class C (50 kWh/m2)
  const targetConsoM2 = 50;
  const totalGains = data.reduce((sum, d) => {
    const excess = (d.conso_reelle_par_m2 ?? 0) - targetConsoM2;
    if (excess > 0) {
      return sum + excess * (d.surface_med ?? 65) * (d.nb_logements ?? 1);
    }
    return sum;
  }, 0);

  return {
    uniqueAddresses,
    avgEcart: Math.round(avgEcart),
    totalGainsGWh: +(totalGains / 1_000_000).toFixed(1),
  };
}
