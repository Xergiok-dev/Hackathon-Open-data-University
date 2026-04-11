export interface DPERecord {
  annee: number;
  adresse: string;
  nb_logements: number;
  dept: number;
  conso_totale_kwh: number;
  conso_par_logement_kwh: number;
  code_iris: string;
  nom_commune: string;
  lat: number;
  lon: number;
  score: number;
  ban_id: string;
  classe_dpe_modale: string;
  nb_dpe: number;
  surface_med: number;
  pct_elec_chauffage: number;
  conso_5_usages_par_m2_med: number;
  conso_reelle_par_m2: number;
  conso_estimee_med: number;
  ecart_estime_vs_reel: number;
  ecart_pct: number;
}

export interface StatsParClasse {
  classe_dpe_modale: string;
  conso_reelle_par_m2_mean: number;
  conso_reelle_par_m2_median: number;
  conso_reelle_par_m2_std: number;
  conso_reelle_par_m2_count: number;
  ecart_pct_mean: number;
  ecart_pct_median: number;
}

export interface GainParClasse {
  transition: string;
  gain_kwh_m2_an: number;
  gain_euros_m2_an: number;
  gain_euros_65m2: number;
}

export interface TopAdresse {
  adresse: string;
  ban_id: string;
  conso_reelle_par_m2: number;
  classe_dpe_modale: string;
  surface_med: number;
  lat: number;
  lon: number;
}

export interface Variabilite {
  classe_dpe: string;
  n_logements: number;
  "ecart_moyen_%": number;
  "ecart_std_%": number;
  "ecart_min_%": number;
  "ecart_max_%": number;
  "cv_%": number;
}

export type KPIPanel = "addresses" | "ecarts" | "gains" | null;

export type LayerMode = "dpe_classes" | "heatmap" | "ecarts";

export type DPEClass = "A" | "B" | "C" | "D" | "E" | "F" | "G";
