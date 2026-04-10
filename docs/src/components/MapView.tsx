"use client";

import { useMemo } from "react";
import { Map } from "react-map-gl/maplibre";
import DeckGL from "@deck.gl/react";
import { ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer } from "@deck.gl/aggregation-layers";
import type { DPERecord, LayerMode } from "@/types";
import { getDPEColor, getHeatColor, getEcartColor } from "@/lib/colors";

const INITIAL_VIEW = {
  longitude: 2.33,
  latitude: 48.86,
  zoom: 11.5,
  pitch: 45,
  bearing: -10,
};

// Free dark basemap (no API key needed)
const MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

interface Props {
  data: DPERecord[];
  layerMode: LayerMode;
  onHover?: (info: { object?: DPERecord; x: number; y: number }) => void;
}

export default function MapView({ data, layerMode, onHover }: Props) {
  const consoExtent = useMemo(() => {
    const values = data.map((d) => d.conso_reelle_par_m2).filter(Boolean);
    return { min: Math.min(...values), max: Math.max(...values) };
  }, [data]);

  const layers = useMemo(() => {
    switch (layerMode) {
      case "dpe_classes":
        return [
          new ScatterplotLayer<DPERecord>({
            id: "dpe-classes",
            data,
            getPosition: (d) => [d.lon, d.lat],
            getFillColor: (d) => [...getDPEColor(d.classe_dpe_modale), 200],
            getRadius: (d) => Math.max(30, Math.sqrt(d.nb_logements ?? 1) * 20),
            radiusMinPixels: 4,
            radiusMaxPixels: 40,
            pickable: true,
            antialiasing: true,
          }),
        ];

      case "heatmap":
        return [
          new HeatmapLayer<DPERecord>({
            id: "heatmap-conso",
            data,
            getPosition: (d) => [d.lon, d.lat],
            getWeight: (d) => d.conso_reelle_par_m2 ?? 0,
            radiusPixels: 60,
            intensity: 1.2,
            threshold: 0.05,
            colorRange: [
              [0, 0, 255],
              [0, 200, 255],
              [0, 255, 128],
              [255, 255, 0],
              [255, 128, 0],
              [255, 0, 0],
            ],
          }),
          // Small dots for reference
          new ScatterplotLayer<DPERecord>({
            id: "heatmap-dots",
            data,
            getPosition: (d) => [d.lon, d.lat],
            getFillColor: (d) =>
              [...getHeatColor(d.conso_reelle_par_m2, consoExtent.min, consoExtent.max), 160],
            getRadius: 20,
            radiusMinPixels: 2,
            radiusMaxPixels: 8,
            pickable: true,
          }),
        ];

      case "ecarts":
        return [
          new ScatterplotLayer<DPERecord>({
            id: "ecarts",
            data,
            getPosition: (d) => [d.lon, d.lat],
            getFillColor: (d) => [...getEcartColor(d.ecart_pct), 200],
            getRadius: (d) => Math.max(30, Math.abs(d.ecart_pct ?? 0) * 0.5),
            radiusMinPixels: 4,
            radiusMaxPixels: 50,
            pickable: true,
          }),
        ];
    }
  }, [data, layerMode, consoExtent]);

  return (
    <div className="relative w-full h-full">
      <DeckGL
        initialViewState={INITIAL_VIEW}
        controller={true}
        layers={layers}
        onHover={(info) =>
          onHover?.({
            object: info.object as DPERecord | undefined,
            x: info.x,
            y: info.y,
          })
        }
        getTooltip={({ object }: { object?: DPERecord }) => {
          if (!object) return null;
          return {
            html: `
              <div style="padding:8px;font-size:13px;max-width:280px">
                <strong>${object.adresse}</strong><br/>
                <span>Classe DPE: <b>${object.classe_dpe_modale}</b></span><br/>
                <span>Conso reelle: <b>${object.conso_reelle_par_m2?.toFixed(1)} kWh/m2</b></span><br/>
                <span>Conso DPE theorique: <b>${object.conso_5_usages_par_m2_med?.toFixed(1)} kWh/m2</b></span><br/>
                <span>Ecart: <b>${object.ecart_pct?.toFixed(0)}%</b></span><br/>
                <span>${object.nb_logements} logements | ${object.surface_med?.toFixed(0)} m2</span>
              </div>
            `,
            style: {
              backgroundColor: "rgba(15,15,20,0.92)",
              color: "#e2e8f0",
              borderRadius: "8px",
              border: "1px solid rgba(255,255,255,0.1)",
            },
          };
        }}
      >
        <Map mapStyle={MAP_STYLE} />
      </DeckGL>
    </div>
  );
}
