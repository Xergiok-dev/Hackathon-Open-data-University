// "use client";

// import { useMemo } from "react";
// import {
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   Tooltip,
//   ResponsiveContainer,
//   Cell,
//   ScatterChart,
//   Scatter,
//   ZAxis,
//   CartesianGrid,
//   Legend,
// } from "recharts";
// import type { DPERecord, GainParClasse, Variabilite, KPIPanel } from "@/types";
// import { DPE_ORDER, getDPEColorHex } from "@/lib/colors";

// interface Props {
//   panel: KPIPanel;
//   data: DPERecord[];
//   gains: GainParClasse[];
//   variabilite: Variabilite[];
// }

// const tooltipStyle = {
//   backgroundColor: "rgba(15,15,20,0.95)",
//   border: "1px solid rgba(255,255,255,0.1)",
//   borderRadius: 8,
//   color: "#e2e8f0",
//   fontSize: 13,
// };

// // Reusable insight card
// function Insight({
//   emoji,
//   title,
//   children,
//   color = "blue",
// }: {
//   emoji: string;
//   title: string;
//   children: React.ReactNode;
//   color?: "blue" | "amber" | "red" | "green" | "purple";
// }) {
//   const border = {
//     blue: "border-blue-500/30",
//     amber: "border-amber-500/30",
//     red: "border-red-500/30",
//     green: "border-green-500/30",
//     purple: "border-purple-500/30",
//   }[color];
//   const bg = {
//     blue: "bg-blue-500/5",
//     amber: "bg-amber-500/5",
//     red: "bg-red-500/5",
//     green: "bg-green-500/5",
//     purple: "bg-purple-500/5",
//   }[color];

//   return (
//     <div className={`rounded-lg border ${border} ${bg} px-3.5 py-2.5`}>
//       <p className="text-sm font-medium mb-1">
//         <span className="mr-1.5">{emoji}</span>
//         {title}
//       </p>
//       <p className="text-xs text-muted-foreground leading-relaxed">{children}</p>
//     </div>
//   );
// }

// // ──────────────────────────────────────────────
// // Panel "Adresses analysees"
// // ──────────────────────────────────────────────
// function AddressesPanel({ data }: { data: DPERecord[] }) {
//   const byCommune = useMemo(() => {
//     const map = new Map<string, number>();
//     for (const d of data) {
//       const key = d.nom_commune || "Inconnu";
//       map.set(key, (map.get(key) ?? 0) + 1);
//     }
//     return Array.from(map.entries())
//       .map(([commune, count]) => ({ commune, count }))
//       .sort((a, b) => b.count - a.count)
//       .slice(0, 12);
//   }, [data]);

//   const byDeptAndClass = useMemo(() => {
//     const map = new Map<string, number>();
//     for (const d of data) {
//       const key = `${d.dept === 75 ? "Paris" : "92"}-${d.classe_dpe_modale}`;
//       map.set(key, (map.get(key) ?? 0) + 1);
//     }
//     return DPE_ORDER.map((cls) => ({
//       classe: cls,
//       Paris: map.get(`Paris-${cls}`) ?? 0,
//       "Hauts-de-Seine": map.get(`92-${cls}`) ?? 0,
//     }));
//   }, [data]);

//   const uniqueAddresses = new Set(data.map((d) => d.ban_id)).size;
//   const pctClasseEFG = (
//     (data.filter((d) => ["E", "F", "G"].includes(d.classe_dpe_modale)).length /
//       data.length) *
//     100
//   ).toFixed(0);

//   return (
//     <div className="space-y-4">
//       {/* Descriptions narratives */}
//       <div className="grid grid-cols-3 gap-3">
//         <Insight emoji="🏠" title="Ce que represente cette donnee" color="blue">
//           Nous avons croise les diagnostics energetiques (DPE) avec les factures
//           reelles d&apos;electricite Enedis de <strong>{uniqueAddresses} immeubles</strong> a
//           Paris et dans les Hauts-de-Seine, sur 7 ans. Chaque point sur la carte
//           est un batiment pour lequel on peut comparer ce que le DPE predit et ce
//           qui est reellement consomme.
//         </Insight>
//         <Insight emoji="⚠️" title="Pourquoi si peu d'adresses ?" color="amber">
//           Le DPE n&apos;est obligatoire qu&apos;en cas de vente ou de location. Resultat :
//           sur les 522 000 adresses Enedis, seules 0.4% ont un DPE disponible.
//           C&apos;est un echantillon, pas un recensement exhaustif — mais il revele deja
//           des tendances tres marquees.
//         </Insight>
//         <Insight emoji="🔴" title={`${pctClasseEFG}% des batiments en classe E, F ou G`} color="red">
//           Les classes E a G sont considerees comme des &quot;passoires thermiques&quot;.
//           Ces batiments, souvent construits avant 1975, ont une isolation
//           insuffisante. Leurs habitants paient des factures d&apos;energie bien plus
//           elevees — ou renoncent a se chauffer correctement.
//         </Insight>
//       </div>

//       {/* Graphiques */}
//       <div className="grid grid-cols-2 gap-6">
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Enregistrements par commune (Top 12)
//           </h4>
//           <ResponsiveContainer width="100%" height={200}>
//             <BarChart data={byCommune} layout="vertical" barSize={14}>
//               <XAxis type="number" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
//               <YAxis
//                 type="category"
//                 dataKey="commune"
//                 tick={{ fill: "#94a3b8", fontSize: 10 }}
//                 width={120}
//                 axisLine={false}
//                 tickLine={false}
//               />
//               <Tooltip contentStyle={tooltipStyle} />
//               <Bar dataKey="count" fill="#60a5fa" radius={[0, 4, 4, 0]} />
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Classes DPE par departement
//           </h4>
//           <ResponsiveContainer width="100%" height={200}>
//             <BarChart data={byDeptAndClass} barSize={16}>
//               <XAxis dataKey="classe" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
//               <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={35} />
//               <Tooltip contentStyle={tooltipStyle} />
//               <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
//               <Bar dataKey="Paris" fill="#818cf8" radius={[4, 4, 0, 0]} />
//               <Bar dataKey="Hauts-de-Seine" fill="#34d399" radius={[4, 4, 0, 0]} />
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//       </div>
//     </div>
//   );
// }

// // ──────────────────────────────────────────────
// // Panel "Ecart moyen DPE vs Reel"
// // ──────────────────────────────────────────────
// function EcartsPanel({ data, variabilite }: { data: DPERecord[]; variabilite: Variabilite[] }) {
//   const varData = useMemo(
//     () =>
//       DPE_ORDER.map((cls) => {
//         const v = variabilite.find((x) => x.classe_dpe === cls);
//         return {
//           classe: cls,
//           ecart_moyen: v ? Math.round(v["ecart_moyen_%"]) : 0,
//           cv: v ? Math.round(v["cv_%"]) : 0,
//           n: v?.n_logements ?? 0,
//         };
//       }),
//     [variabilite]
//   );

//   const scatterData = useMemo(() => {
//     const sampled = data.filter((_, i) => i % 3 === 0);
//     return sampled
//       .filter((d) => d.conso_reelle_par_m2 && d.ecart_pct)
//       .map((d) => ({
//         x: d.conso_reelle_par_m2,
//         y: d.ecart_pct,
//         classe: d.classe_dpe_modale,
//         adresse: d.adresse,
//       }));
//   }, [data]);

//   // Compute some stats for narrative
//   const classFdata = variabilite.find((x) => x.classe_dpe === "F");
//   const cvF = classFdata ? Math.round(classFdata["cv_%"]) : 0;

//   return (
//     <div className="space-y-4">
//       {/* Descriptions narratives */}
//       <div className="grid grid-cols-3 gap-3">
//         <Insight emoji="📊" title="Que signifie cet ecart ?" color="purple">
//           Le DPE estime combien un logement <em>devrait</em> consommer en theorie.
//           Mais la realite est souvent tres differente. Un ecart de +200% veut dire
//           que le DPE prevoyait 3x plus de consommation que ce qui est reellement
//           mesure sur le compteur.
//         </Insight>
//         <Insight emoji="🥶" title="Le phenomene de precarite energetique" color="red">
//           Un ecart eleve ne signifie pas forcement que le batiment est performant.
//           Souvent, c&apos;est l&apos;inverse : <strong>les habitants consomment moins parce
//           qu&apos;ils n&apos;ont pas les moyens de se chauffer</strong>. Ils enfilent des pulls,
//           utilisent des chauffages d&apos;appoint, ou laissent des pieces froides. Le
//           DPE dit &quot;vous devriez consommer X&quot;, mais la facture dit &quot;je ne peux
//           pas me le permettre&quot;.
//         </Insight>
//         <Insight emoji="🎲" title={`Variabilite extreme (CV ${cvF}% en classe F)`} color="amber">
//           Deux logements avec le meme DPE peuvent avoir des consommations
//           radicalement differentes. Cela depend du comportement des occupants,
//           de leur revenu, de l&apos;exposition du batiment et de la qualite reelle de
//           l&apos;isolation — des facteurs que le DPE ne capture tout simplement pas.
//           En classe F, la variabilite atteint {cvF}%.
//         </Insight>
//       </div>

//       {/* Graphiques */}
//       <div className="grid grid-cols-2 gap-6">
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Ecart moyen & variabilite par classe DPE
//           </h4>
//           <p className="text-[11px] text-muted-foreground mb-2 leading-snug">
//             Les barres colorees montrent l&apos;ecart moyen entre prediction DPE et realite.
//             Les barres grises montrent la variabilite : plus elle est haute, moins le DPE est fiable pour cette classe.
//           </p>
//           <ResponsiveContainer width="100%" height={200}>
//             <BarChart data={varData} barSize={24}>
//               <XAxis dataKey="classe" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
//               <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={40} unit="%" />
//               <Tooltip
//                 contentStyle={tooltipStyle}
//                 formatter={(value, name) => {
//                   if (name === "ecart_moyen") return [`${value}%`, "Ecart moyen"];
//                   if (name === "cv") return [`${value}%`, "Coeff. variation"];
//                   return [String(value), String(name)];
//                 }}
//               />
//               <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
//               <Bar dataKey="ecart_moyen" name="Ecart moyen" radius={[4, 4, 0, 0]}>
//                 {varData.map((entry) => (
//                   <Cell key={entry.classe} fill={getDPEColorHex(entry.classe)} />
//                 ))}
//               </Bar>
//               <Bar dataKey="cv" name="Coeff. variation" fill="#94a3b8" opacity={0.4} radius={[4, 4, 0, 0]} />
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Conso reelle vs Ecart DPE
//           </h4>
//           <p className="text-[11px] text-muted-foreground mb-2 leading-snug">
//             Chaque point est un batiment. En bas a gauche : faible conso, faible ecart (logement performant).
//             En haut a gauche : faible conso mais gros ecart — signal potentiel de precarite energetique.
//           </p>
//           <ResponsiveContainer width="100%" height={200}>
//             <ScatterChart>
//               <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
//               <XAxis
//                 dataKey="x"
//                 name="Conso"
//                 unit=" kWh"
//                 tick={{ fill: "#64748b", fontSize: 10 }}
//                 axisLine={false}
//                 tickLine={false}
//               />
//               <YAxis
//                 dataKey="y"
//                 name="Ecart"
//                 unit="%"
//                 tick={{ fill: "#64748b", fontSize: 10 }}
//                 axisLine={false}
//                 tickLine={false}
//                 width={50}
//               />
//               <ZAxis range={[15, 15]} />
//               <Tooltip
//                 contentStyle={tooltipStyle}
//                 formatter={(value, name) => {
//                   if (name === "Conso") return [`${value} kWh/m2`, "Conso reelle"];
//                   if (name === "Ecart") return [`${value}%`, "Ecart DPE"];
//                   return [String(value), String(name)];
//                 }}
//               />
//               <Scatter data={scatterData} fill="#f472b6" opacity={0.5} />
//             </ScatterChart>
//           </ResponsiveContainer>
//         </div>
//       </div>
//     </div>
//   );
// }

// // ──────────────────────────────────────────────
// // Panel "Gains potentiels"
// // ──────────────────────────────────────────────
// function GainsPanel({ gains, data }: { gains: GainParClasse[]; data: DPERecord[] }) {
//   const gainsData = useMemo(
//     () =>
//       gains.map((g) => ({
//         ...g,
//         gain_kwh_m2_an: Math.abs(g.gain_kwh_m2_an),
//         gain_euros_65m2: Math.abs(g.gain_euros_65m2),
//         positive: g.gain_kwh_m2_an > 0,
//       })),
//     [gains]
//   );

//   // Compute key stats for narrative
//   const nbPassoires = data.filter((d) =>
//     ["E", "F", "G"].includes(d.classe_dpe_modale)
//   ).length;
//   const bestTransition = gains.reduce(
//     (best, g) => (g.gain_euros_65m2 > best.gain_euros_65m2 ? g : best),
//     gains[0]
//   );

//   return (
//     <div className="space-y-4">
//       {/* Descriptions narratives */}
//       <div className="grid grid-cols-3 gap-3">
//         <Insight emoji="💡" title="Comment lire ces gains ?" color="green">
//           Chaque barre represente l&apos;economie d&apos;energie realisee quand un
//           batiment passe d&apos;une classe DPE a la classe superieure. Par exemple,
//           passer de G a F, c&apos;est comme eteindre un radiateur electrique qui
//           tournait en permanence dans une piece. Pas toutes les transitions ne
//           se valent.
//         </Insight>
//         <Insight emoji="💶" title={`Meilleur gain : ${bestTransition?.transition}`} color="blue">
//           La transition <strong>{bestTransition?.transition}</strong> est la
//           plus rentable : elle represente <strong>{bestTransition?.gain_euros_65m2}€
//           d&apos;economies par an</strong> pour un appartement de 65m2. C&apos;est l&apos;equivalent
//           d&apos;un mois de courses en moins chaque annee. Renover ces logements, c&apos;est
//           directement redonner du pouvoir d&apos;achat aux menages.
//         </Insight>
//         <Insight emoji="🏗️" title={`${nbPassoires} enregistrements en passoire thermique`} color="red">
//           Les classes E, F et G representent les batiments les plus mal isoles.
//           Leurs occupants subissent en moyenne des factures 2 a 3 fois plus
//           elevees que des logements equivalents en classe C. La renovation
//           energetique de ces batiments est un enjeu a la fois ecologique,
//           economique et <strong>de justice sociale</strong>.
//         </Insight>
//       </div>

//       {/* Graphiques */}
//       <div className="grid grid-cols-2 gap-6">
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Gains energetiques par transition (kWh/m2/an)
//           </h4>
//           <p className="text-[11px] text-muted-foreground mb-2 leading-snug">
//             En vert : les transitions qui apportent de vraies economies. En rouge :
//             les transitions ou le gain est negatif (la classe suivante consomme
//             paradoxalement plus — souvent lie a des effets de comportement).
//           </p>
//           <ResponsiveContainer width="100%" height={200}>
//             <BarChart data={gainsData} barSize={28}>
//               <XAxis
//                 dataKey="transition"
//                 tick={{ fill: "#94a3b8", fontSize: 10 }}
//                 axisLine={false}
//                 tickLine={false}
//               />
//               <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={35} />
//               <Tooltip
//                 contentStyle={tooltipStyle}
//                 formatter={(value) => [`${value} kWh/m2/an`, "Gain"]}
//               />
//               <Bar dataKey="gain_kwh_m2_an" radius={[4, 4, 0, 0]}>
//                 {gainsData.map((entry, i) => (
//                   <Cell key={i} fill={entry.positive ? "#34d399" : "#f87171"} />
//                 ))}
//               </Bar>
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//         <div>
//           <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
//             Economies annuelles pour un 65m2 (euros/an)
//           </h4>
//           <p className="text-[11px] text-muted-foreground mb-2 leading-snug">
//             Impact concret sur le porte-monnaie. Ces montants representent ce qu&apos;un
//             menage economiserait chaque annee en faisant renover son logement d&apos;une
//             classe. Pour un logement en G, la totalite du chemin jusqu&apos;a C peut
//             representer plus de 800€/an.
//           </p>
//           <ResponsiveContainer width="100%" height={200}>
//             <BarChart data={gainsData} barSize={28}>
//               <XAxis
//                 dataKey="transition"
//                 tick={{ fill: "#94a3b8", fontSize: 10 }}
//                 axisLine={false}
//                 tickLine={false}
//               />
//               <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} width={40} unit="€" />
//               <Tooltip
//                 contentStyle={tooltipStyle}
//                 formatter={(value) => [`${value} €/an`, "Economies"]}
//               />
//               <Bar dataKey="gain_euros_65m2" radius={[4, 4, 0, 0]}>
//                 {gainsData.map((entry, i) => (
//                   <Cell key={i} fill={entry.positive ? "#60a5fa" : "#fb923c"} />
//                 ))}
//               </Bar>
//             </BarChart>
//           </ResponsiveContainer>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default function KPIDetailPanel({ panel, data, gains, variabilite }: Props) {
//   if (!panel) return null;

//   return (
//     <div className="shrink-0 border-b border-white/5 bg-card/40 backdrop-blur-md px-4 py-4 animate-in slide-in-from-top-2 duration-300">
//       {panel === "addresses" && <AddressesPanel data={data} />}
//       {panel === "ecarts" && <EcartsPanel data={data} variabilite={variabilite} />}
//       {panel === "gains" && <GainsPanel gains={gains} data={data} />}
//     </div>
//   );
// }
"use client";

import { useMemo, useState } from "react";
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

// 🎨 TOOLTIP STYLE PRO
const tooltipStyle = {
  backgroundColor: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: 10,
  color: "#0f172a",
  fontSize: 13,
  boxShadow: "0 10px 30px rgba(0,0,0,0.12)",
};

const tooltipProps = {
  contentStyle: tooltipStyle,
  itemStyle: { color: "#0f172a" },
  labelStyle: { color: "#64748b", fontWeight: 500 },
};

// 💡 INSIGHT CARD
function Insight({
  emoji,
  title,
  children,
  color = "blue",
}: {
  emoji: string;
  title: string;
  children: React.ReactNode;
  color?: "blue" | "amber" | "red" | "green" | "purple";
}) {
  const border = {
    blue: "border-blue-500/30",
    amber: "border-amber-500/30",
    red: "border-red-500/30",
    green: "border-green-500/30",
    purple: "border-purple-500/30",
  }[color];

  const bg = {
    blue: "bg-blue-500/5",
    amber: "bg-amber-500/5",
    red: "bg-red-500/5",
    green: "bg-green-500/5",
    purple: "bg-purple-500/5",
  }[color];

  return (
    <div className={`rounded-xl border ${border} ${bg} px-4 py-3 transition hover:scale-[1.02]`}>
      <p className="text-sm font-semibold mb-1">
        <span className="mr-2">{emoji}</span>
        {title}
      </p>
      <p className="text-xs text-muted-foreground leading-relaxed">
        {children}
      </p>
    </div>
  );
}

// ──────────────────────────────────────────────
// PANEL ADDRESSES
// ──────────────────────────────────────────────
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

  const uniqueAddresses = new Set(data.map((d) => d.ban_id)).size;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3">
        <Insight emoji="🏠" title="Adresses analysées">
          {uniqueAddresses} immeubles croisant DPE + consommation réelle.
        </Insight>
      </div>

      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={byCommune} layout="vertical">
          <XAxis type="number" />
          <YAxis dataKey="commune" type="category" width={120} />
          <Tooltip {...tooltipProps} />
          <Bar
            dataKey="count"
            fill="#60a5fa"
            radius={[0, 6, 6, 0]}
            isAnimationActive
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ──────────────────────────────────────────────
// PANEL ECARTS
// ──────────────────────────────────────────────
function EcartsPanel({
  variabilite,
}: {
  data: DPERecord[];
  variabilite: Variabilite[];
}) {
  const varData = useMemo(
    () =>
      DPE_ORDER.map((cls) => {
        const v = variabilite.find((x) => x.classe_dpe === cls);
        return {
          classe: cls,
          ecart: v ? Math.round(v["ecart_moyen_%"]) : 0,
        };
      }),
    [variabilite]
  );

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={varData}>
        <XAxis dataKey="classe" />
        <YAxis />
        <Tooltip {...tooltipProps} />
        <Bar dataKey="ecart" radius={[6, 6, 0, 0]} isAnimationActive>
          {varData.map((entry) => (
            <Cell
              key={entry.classe}
              fill={getDPEColorHex(entry.classe)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ──────────────────────────────────────────────
// PANEL GAINS
// ──────────────────────────────────────────────
function GainsPanel({ gains }: { gains: GainParClasse[] }) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={gains}>
        <XAxis dataKey="transition" />
        <YAxis />
        <Tooltip {...tooltipProps} />
        <Bar
          dataKey="gain_euros_65m2"
          fill="#34d399"
          radius={[6, 6, 0, 0]}
          isAnimationActive
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ──────────────────────────────────────────────
// MAIN
// ──────────────────────────────────────────────
export default function KPIDetailPanel({
  panel,
  data,
  gains,
  variabilite,
}: Props) {
  if (!panel) return null;

  return (
    <div className="border-b border-white/5 bg-card/40 backdrop-blur-md px-4 py-4 animate-in fade-in duration-300">
      {panel === "addresses" && <AddressesPanel data={data} />}
      {panel === "ecarts" && (
        <EcartsPanel data={data} variabilite={variabilite} />
      )}
      {panel === "gains" && <GainsPanel gains={gains} />}
    </div>
  );
}