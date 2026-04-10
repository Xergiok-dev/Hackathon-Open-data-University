import type { DPEClass } from "@/types";

// Official DPE color palette (French energy performance labels)
export const DPE_COLORS: Record<DPEClass, [number, number, number]> = {
  A: [0, 128, 0],       // Dark green
  B: [85, 170, 0],      // Light green
  C: [204, 204, 0],     // Yellow-green
  D: [255, 204, 0],     // Yellow
  E: [255, 153, 0],     // Orange
  F: [255, 68, 0],      // Red-orange
  G: [204, 0, 0],       // Red
};

export const DPE_COLORS_HEX: Record<DPEClass, string> = {
  A: "#008000",
  B: "#55aa00",
  C: "#cccc00",
  D: "#ffcc00",
  E: "#ff9900",
  F: "#ff4400",
  G: "#cc0000",
};

export const DPE_ORDER: DPEClass[] = ["A", "B", "C", "D", "E", "F", "G"];

export function getDPEColor(classe: string): [number, number, number] {
  return DPE_COLORS[classe as DPEClass] ?? [128, 128, 128];
}

export function getDPEColorHex(classe: string): string {
  return DPE_COLORS_HEX[classe as DPEClass] ?? "#808080";
}

// Color scale for heatmap (blue → red)
export function getHeatColor(value: number, min: number, max: number): [number, number, number] {
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return [
    Math.round(255 * t),
    Math.round(80 * (1 - t)),
    Math.round(255 * (1 - t)),
  ];
}

// Diverging color scale for ecarts (green → white → red)
export function getEcartColor(ecart_pct: number): [number, number, number] {
  const clamped = Math.max(-100, Math.min(500, ecart_pct));
  if (clamped < 0) {
    const t = (clamped + 100) / 100;
    return [Math.round(50 * t), Math.round(180 + 75 * t), Math.round(50 * t)];
  }
  const t = Math.min(1, clamped / 300);
  return [Math.round(255 * t + 200 * (1 - t)), Math.round(200 * (1 - t)), Math.round(50 * (1 - t))];
}
