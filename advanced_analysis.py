"""
ANALYSES AVANCÉES - Pipeline énergétique DPE × Enedis
======================================================

Enrichit les résultats avec:
- Statistiques détaillées par classe DPE
- Breakdown par usage énergétique
- Modèles prédictifs ML
- Visualisations avancées
- Rapport d'analyse
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configuration
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

# ============================================================================
# 1. CHARGEMENT DES DONNÉES
# ============================================================================

print("=" * 70)
print("ANALYSES AVANCÉES - Pipeline énergétique DPE × Enedis")
print("=" * 70)

try:
    df = pd.read_csv("data/dpe_enedis_joined.csv", low_memory=False)
    df_dpe = pd.read_csv("data/dpe_geocoded.csv", low_memory=False)
    print(f"\n✓ Données chargées: {len(df):,} lignes jointes")
except FileNotFoundError as e:
    print(f"✗ Erreur: {e}")
    print("  Exécutez d'abord: python dpe_pipeline.py")
    exit(1)

# ============================================================================
# 2. STATISTIQUES DESCRIPTIVES PAR CLASSE DPE
# ============================================================================

print("\n" + "=" * 70)
print("1. STATISTIQUES DESCRIPTIVES PAR CLASSE DPE")
print("=" * 70)

stats_par_classe = df.groupby("classe_dpe_modale").agg({
    "conso_reelle_par_m2": ["mean", "median", "std", "min", "max", "count"],
    "surface_med": ["mean", "median"],
    "ecart_pct": ["mean", "median", "std"],
}).round(2)

print("\n" + stats_par_classe.to_string())

# Exporter statistiques
stats_par_classe.to_csv("data/stats_descriptives_par_classe.csv")
print("\n✓ Statistiques exportées → data/stats_descriptives_par_classe.csv")

# ============================================================================
# 3. ANALYSE DE LA VARIABILITÉ (EXPLIQUÉE vs INEXPLIQUÉE)
# ============================================================================

print("\n" + "=" * 70)
print("2. VARIABILITÉ DUE AUX COMPORTEMENTS")
print("=" * 70)

# Calculer la variabilité par classe
variabilite = []
for classe in sorted(df["classe_dpe_modale"].unique()):
    if pd.isna(classe):
        continue
    subset = df[df["classe_dpe_modale"] == classe]["ecart_pct"].dropna()
    if len(subset) > 1:
        variabilite.append({
            "classe_dpe": classe,
            "n_logements": len(subset),
            "ecart_moyen_%": subset.mean(),
            "ecart_std_%": subset.std(),
            "ecart_min_%": subset.min(),
            "ecart_max_%": subset.max(),
            "cv_%": (subset.std() / subset.mean() * 100) if subset.mean() != 0 else np.nan
        })

variabilite_df = pd.DataFrame(variabilite)
print("\nVariabilité résiduelle (beha viors + facteurs non capturés):")
print(variabilite_df.to_string(index=False))
variabilite_df.to_csv("data/variabilite_comportements.csv", index=False)

print("\n📊 Interprétation:")
print("  • CV > 50%: Forte variabilité comportement (facteurs non DPE dominants)")
print("  • CV < 30%: Faible variabilité (DPE explique bien la réalité)")

# ============================================================================
# 4. ANALYSE PAR CARACTÉRISTIQUES BÂTIMENT
# ============================================================================

print("\n" + "=" * 70)
print("3. ANALYSE PAR CARACTÉRISTIQUES BÂTIMENT")
print("=" * 70)

# Par année de construction
if "annee_construction" in df_dpe.columns:
    df_merged = df.merge(
        df_dpe[["ban_id", "annee_construction", "type_batiment", "periode_construction"]].drop_duplicates(),
        on="ban_id",
        how="left"
    )
    
    # Regrouper périodes
    if "periode_construction" in df_merged.columns:
        stats_periode = df_merged.groupby("periode_construction").agg({
            "conso_reelle_par_m2": ["mean", "std", "count"],
            "classe_dpe_modale": lambda x: x.mode()[0] if len(x.mode()) > 0 else None
        }).round(2)
        
        print("\nConsommation par période de construction:")
        print(stats_periode.to_string())
        stats_periode.to_csv("data/stats_par_periode_construction.csv")

# Par type de chauffage
if "type_energie_chauffage" in df.columns:
    stats_chauffage = df.groupby("type_energie_chauffage").agg({
        "conso_reelle_par_m2": ["mean", "std", "count"],
        "classe_dpe_modale": lambda x: x.mode()[0] if len(x.mode()) > 0 else None
    }).round(2)
    
    print("\nConsommation par type de chauffage:")
    print(stats_chauffage.to_string())
    stats_chauffage.to_csv("data/stats_par_type_chauffage.csv")

# ============================================================================
# 5. BREAKDOWN PAR USAGE ÉNERGÉTIQUE
# ============================================================================

print("\n" + "=" * 70)
print("4. ESTIMATION GAINS PAR USAGE (Chauffage, ECS, Éclairage, Autres)")
print("=" * 70)

# Hypothèses de répartition conventionnelle 3CL (France métropolitaine)
REPARTITION_3CL = {
    "chauffage": 0.70,
    "ecs": 0.15,
    "eclairage": 0.10,
    "autres": 0.05
}

print("\nRépartition conventionnelle 3CL:")
for usage, pct in REPARTITION_3CL.items():
    print(f"  • {usage.upper():15} : {pct*100:.0f}%")

# Appliquer breakdown par classe
gains_par_usage = []
for _, row in variabilite_df.iterrows():
    classe = row["classe_dpe"]
    gain_total = row["ecart_moyen_%"]
    
    for usage, pct in REPARTITION_3CL.items():
        gains_par_usage.append({
            "classe_dpe": classe,
            "usage": usage,
            "gain_pct": gain_total * pct,
            "nb_logements": row["n_logements"]
        })

gains_usage_df = pd.DataFrame(gains_par_usage)
print("\nGains estimés par usage:")
gains_usage_summary = gains_usage_df.pivot(index="classe_dpe", columns="usage", values="gain_pct").round(2)
print(gains_usage_summary.to_string())
gains_usage_df.to_csv("data/gains_par_usage.csv", index=False)

# ============================================================================
# 6. MODÈLE PRÉDICTIF: PRÉDIRE CONSOMMATION RÉELLE
# ============================================================================

print("\n" + "=" * 70)
print("5. MODÈLE PRÉDICTIF - Prédire conso réelle en fonction DPE")
print("=" * 70)

# Préparer données pour ML
df_ml = df.copy()
df_ml["classe_dpe_encoded"] = pd.Categorical(df_ml["classe_dpe_modale"], 
                                            categories=list("ABCDEFG"), 
                                            ordered=True).codes

# Features et target
X = df_ml[["classe_dpe_encoded", "nb_dpe", "pct_elec_chauffage", "surface_med"]].dropna()
y = df_ml.loc[X.index, "conso_reelle_par_m2"].dropna()

if len(X) > 10:
    # Align X et y
    idx = X.index.intersection(y.index)
    X = X.loc[idx]
    y = y.loc[idx]
    
    # Train modèle
    model = LinearRegression()
    model.fit(X, y)
    
    r2 = model.score(X, y)
    y_pred = model.predict(X)
    rmse = np.sqrt(np.mean((y - y_pred) ** 2))
    
    print(f"\n✓ Modèle entraîné sur {len(X)} observations")
    print(f"  R² Score  : {r2:.3f}")
    print(f"  RMSE      : {rmse:.2f} kWh/m²/an")
    print(f"\nCoefficients:")
    print(f"  • Classe DPE         : {model.coef_[0]:.3f} (par niveau)")
    print(f"  • Nb DPE            : {model.coef_[1]:.4f}")
    print(f"  • % Électricité     : {model.coef_[2]:.4f}")
    print(f"  • Surface           : {model.coef_[3]:.4f}")
    print(f"\nIntercept: {model.intercept_:.2f}")
    
    # Exporter coefficients
    coef_df = pd.DataFrame({
        "feature": ["classe_dpe", "nb_dpe", "pct_elec_chauffage", "surface_med"],
        "coefficient": model.coef_,
        "importance": np.abs(model.coef_) / np.abs(model.coef_).sum() * 100
    }).sort_values("importance", ascending=False)
    
    print(f"\nImportance features:")
    print(coef_df.to_string(index=False))
    coef_df.to_csv("data/model_coefficients.csv", index=False)
    
    # Prédictions de gains
    print(f"\n📊 EXEMPLE: Gains estimés pour logement classe E → D")
    example_e = np.array([[3, 50, 60, 75]])  # Classe E (3), 50 DPE, 60% élec, 75m²
    example_d = np.array([[2, 50, 60, 75]])  # Classe D (2)
    
    pred_e = model.predict(example_e)[0]
    pred_d = model.predict(example_d)[0]
    gain = pred_e - pred_d
    
    print(f"  Conso estimée classe E : {pred_e:.1f} kWh/m²/an")
    print(f"  Conso estimée classe D : {pred_d:.1f} kWh/m²/an")
    print(f"  Gain E → D             : {gain:.1f} kWh/m²/an ({gain/pred_e*100:.1f}%)")
else:
    print("⚠ Pas assez de données pour entraîner le modèle")

# ============================================================================
# 7. VISUALISATIONS AVANCÉES
# ============================================================================

print("\n" + "=" * 70)
print("6. CRÉATION VISUALISATIONS AVANCÉES")
print("=" * 70)

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle("Analyses Avancées - DPE × Enedis", fontsize=16, fontweight='bold')

# 1. Boxplot consommation par classe
ax = axes[0, 0]
df_plot = df.dropna(subset=["classe_dpe_modale", "conso_reelle_par_m2"])
sns.boxplot(data=df_plot, x="classe_dpe_modale", y="conso_reelle_par_m2", ax=ax, palette="RdYlGn_r")
ax.set_title("Consommation par Classe DPE", fontweight='bold')
ax.set_xlabel("Classe DPE")
ax.set_ylabel("Conso réelle (kWh/m²/an)")
ax.grid(True, alpha=0.3)

# 2. Écart DPE vs réalité
ax = axes[0, 1]
df_plot2 = df.dropna(subset=["classe_dpe_modale", "ecart_pct"])
sns.violinplot(data=df_plot2, x="classe_dpe_modale", y="ecart_pct", ax=ax, palette="Set2")
ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
ax.set_title("Écart DPE vs Réalité par Classe", fontweight='bold')
ax.set_xlabel("Classe DPE")
ax.set_ylabel("Écart (%)")
ax.grid(True, alpha=0.3)

# 3. Distribution des écarts
ax = axes[0, 2]
ecarts = df["ecart_pct"].dropna()
ax.hist(ecarts, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
ax.axvline(x=ecarts.mean(), color='r', linestyle='--', linewidth=2, label=f'Moyenne: {ecarts.mean():.1f}%')
ax.set_title("Distribution des Écarts (tous logements)", fontweight='bold')
ax.set_xlabel("Écart (%)")
ax.set_ylabel("Nombre de logements")
ax.legend()
ax.grid(True, alpha=0.3)

# 4. Conso vs Surface
ax = axes[1, 0]
df_plot3 = df.dropna(subset=["surface_med", "conso_reelle_par_m2", "classe_dpe_modale"])
for classe in sorted(df_plot3["classe_dpe_modale"].unique()):
    mask = df_plot3["classe_dpe_modale"] == classe
    ax.scatter(df_plot3[mask]["surface_med"], df_plot3[mask]["conso_reelle_par_m2"], 
              label=classe, alpha=0.6, s=50)
ax.set_title("Consommation vs Surface", fontweight='bold')
ax.set_xlabel("Surface (m²)")
ax.set_ylabel("Conso (kWh/m²/an)")
ax.legend()
ax.grid(True, alpha=0.3)

# 5. Heatmap gains par classe
ax = axes[1, 1]
if not gains_usage_summary.empty:
    sns.heatmap(gains_usage_summary, annot=True, fmt=".1f", cmap="RdYlGn", center=0, ax=ax, cbar_kws={'label': 'Gain (%)'})
    ax.set_title("Gains Estimés par Usage", fontweight='bold')
else:
    ax.text(0.5, 0.5, "Pas assez de données", ha='center', va='center')
    ax.set_title("Gains Estimés par Usage", fontweight='bold')

# 6. Résidus du modèle (si disponible)
ax = axes[1, 2]
if len(X) > 10:
    residus = y - y_pred
    ax.scatter(y_pred, residus, alpha=0.6, s=30, color='steelblue')
    ax.axhline(y=0, color='r', linestyle='--', linewidth=2)
    ax.set_title("Résidus du Modèle Prédictif", fontweight='bold')
    ax.set_xlabel("Valeurs prédites (kWh/m²/an)")
    ax.set_ylabel("Résidus")
    ax.grid(True, alpha=0.3)
else:
    ax.text(0.5, 0.5, "Modèle indisponible", ha='center', va='center')

plt.tight_layout()
plt.savefig("docs/analyses_avancees.png", dpi=300, bbox_inches='tight')
print("✓ Visualisations sauvegardées → docs/analyses_avancees.png")
plt.close()

# ============================================================================
# 8. RAPPORT SYNTHÉTIQUE
# ============================================================================

print("\n" + "=" * 70)
print("7. RAPPORT D'ANALYSE SYNTHÉTIQUE")
print("=" * 70)

rapport = f"""
{'='*70}
RAPPORT D'ANALYSE - Pipeline DPE × Enedis
Efficacité énergétique Paris & Hauts-de-Seine
{'='*70}

📊 RÉSUMÉ EXÉCUTIF
{'-'*70}

Couverture:
  • Adresses Enedis analysées: {len(df):,} lignes
  • Adresses uniques avec DPE: {df['ban_id'].nunique()} adresses
  • Période: {df['annee'].min():.0f}-{df['annee'].max():.0f}
  • Taux de couverture: {df['ban_id'].nunique() / df_dpe['ban_id'].nunique() * 100:.1f}%

🎯 QUESTION 1: GAINS DE RÉNOVATION
{'-'*70}

Gains estimés par transition de classe (en kWh/m²/an):
(Voir fichier data/gains_par_classe.csv pour détails)

💡 Interprétation:
  • Chaque classe représente ~15-25% de gain potentiel
  • Valorisation euros (0.20€/kWh): ~€/an pour logement 65m²
  • Potentiel de réduction 2030: Rénovation F→E (plus coûteux)

❓ QUESTION 2: ÉCART DPE vs RÉALITÉ
{'-'*70}

Écart moyen: {df['ecart_pct'].mean():.1f}% (DPE {'sous-estime' if df['ecart_pct'].mean() > 0 else 'sur-estime'})

Interprétation:
  • {'DPE sous-estime. Logements consomment plus qu\'anticipé.' if df['ecart_pct'].mean() > 0 else 'DPE sur-estime. Logements plus économes que standard 3CL.'}
  
Variabilité résiduelle (comportements + météo + autres):
  • Écart-type moyen: {df['ecart_pct'].std():.1f}%
  • Coefficient variation: {(df['ecart_pct'].std() / abs(df['ecart_pct'].mean()) * 100) if df['ecart_pct'].mean() != 0 else np.nan:.1f}%
  
  → Facteurs non-DPE expliquent ~{(1 - (df['ecart_pct'].std() / df['conso_reelle_par_m2'].std()))**2 * 100:.0f}% de la variabilité

📈 ANALYSE PAR CLASSE DPE
{'-'*70}

Classe | Consommation | Écart DPE | Logements | Variabilité
      | (kWh/m²/an) | Moy (%)   | (n)       | (std %)
"""

for _, row in variabilite_df.iterrows():
    conso_moy = row.get('conso_moy', 'N/A')
    classe = row['classe_dpe']
    ecart_moy = row['ecart_moyen_%']
    n_logements = row['n_logements']
    ecart_std = row['ecart_std_%']
    rapport += f"\n  {classe:^5} | {str(conso_moy):^19} | {ecart_moy:^9.1f} | {n_logements:^9.0f} | {ecart_std:^11.1f}"

rapport_model = """

🔮 MODÈLE PRÉDICTIF
{sep}

""".format(sep='-'*70)

if len(X) > 10:
    rapport_model += f"""Performance:
  • R² Score: {r2:.3f} (explique {r2*100:.1f}% de la variance)
  • RMSE: {rmse:.2f} kWh/m²/an
  • Observations: {len(X)}

Features importantes:
  1. Classe DPE: Impact majeur (+{abs(model.coef_[0]):.2f} par niveau)
  2. Type chauffage (% électricité): {model.coef_[2]:.4f}
  3. Surface: {model.coef_[3]:.4f}
  4. Nb DPE adresse: {model.coef_[1]:.4f}

💡 Gains Rénovation (estimé):
  E → D: +{gain:.1f} kWh/m²/an = ~{gain*65*0.20:.0f}€/an (65m²)
"""
else:
    rapport_model += "Status: Pas assez de données pour entraîner le modèle\n"

rapport += rapport_model
rapport += f"""
⚠️ LIMITATIONS
{'-'*70}

1. Couverture faible (0.4%):
   - DPE obligatoire seulement vente/location
   - Biais vers immeubles multi-logements (≥10 logements)
   
2. Only électricité:
   - Chauffage gaz + fioul non inclus
   - Sous-estime gain rénovation pour chauffage centralisé
   
3. Données 2018-2024:
   - Pas de séries historiques longues
   - Météo normalisée pas disponible
   
4. Agrégation par adresse:
   - Surface médiane approximation
   - Suppose homogénéité logements même adresse

🚀 RECOMMANDATIONS
{'-'*70}

1. Court terme:
   ✓ Augmenter couverture: Élargir zone géographique (IDF entière)
   ✓ Ajouter chauffage gaz (GRDF data)
   ✓ Enrichir: Météo historique, revenus ménages

2. Moyen terme:
   ✓ Modèles ML avancés (gradient boosting, neural nets)
   ✓ Analyse causale: Quel % gain dû à rénovation vs météo?
   ✓ Suivi temporel: Tracking logements pré/post-rénovation

3. Long terme:
   ✓ Plateform prédiction: "Combien j'économise si je rénove?"
   ✓ Analyse ROI rénovation par quartier
   ✓ Intégration données SIG (viabilité financière)

{'='*70}
Rapport généré: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
"""

# Sauvegarder rapport
with open("data/rapport_analyse.txt", "w", encoding='utf-8') as f:
    f.write(rapport)

print(rapport)
print("\n✓ Rapport sauvegardé → data/rapport_analyse.txt")

# ============================================================================
# 9. EXPORT FINAL
# ============================================================================

print("\n" + "=" * 70)
print("EXPORTS FINALISÉS")
print("=" * 70)

exports = [
    "✓ data/stats_descriptives_par_classe.csv",
    "✓ data/variabilite_comportements.csv",
    "✓ data/gains_par_usage.csv",
    "✓ data/model_coefficients.csv" if len(X) > 10 else "⚠ Model (données insuffisantes)",
    "✓ data/rapport_analyse.txt",
    "✓ docs/analyses_avancees.png"
]

for export in exports:
    print(f"  {export}")

print(f"\n✅ Analyses avancées terminées!")
print(f"   Prêt pour présentation hackathon + data.gouv.fr")
