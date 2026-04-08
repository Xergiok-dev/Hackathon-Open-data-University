"""
EXPLORATION INTERACTIVE - DPE × Enedis
=======================================
Visualise les données fusionnées avec Plotly
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

print("=" * 70)
print("EXPLORATION DONNÉES FUSIONNÉES")
print("=" * 70)

# Charger données
df = pd.read_csv("data/dpe_enedis_joined.csv", low_memory=False)

print(f"\n✓ Données chargées: {len(df):,} lignes")
print(f"  Colonnes ({len(df.columns)}): {', '.join(df.columns[:8])}...")

# ============================================================================
# 1. STATISTIQUES GLOBALES
# ============================================================================

print("\n" + "=" * 70)
print("1. STATISTIQUES GLOBALES")
print("=" * 70)

print(f"""
📍 Couverture géographique:
  • Adresses uniques: {df['ban_id'].nunique():,}
  • Années: {df['annee'].min():.0f}-{df['annee'].max():.0f}
  • Classes DPE: {df['classe_dpe_modale'].nunique()} (A-G)

⚡ Consommation électrique:
  • Moyenne: {df['conso_par_logement_kwh'].mean():.0f} kWh/an/logement
  • Par m²: {df['conso_reelle_par_m2'].mean():.1f} kWh/m²/an (médiane: {df['conso_reelle_par_m2'].median():.1f})
  • Range: {df['conso_reelle_par_m2'].min():.1f} - {df['conso_reelle_par_m2'].max():.1f} kWh/m²/an

🏠 Logements:
  • Surface médiane: {df['surface_med'].median():.0f} m²
  • % Chauffage électrique: {df['pct_elec_chauffage'].mean():.1f}%

📊 Écarts DPE vs réalité:
  • Moyen: {df['ecart_pct'].mean():.1f}%
  • Médian: {df['ecart_pct'].median():.1f}%
  • Écart-type: {df['ecart_pct'].std():.1f}%
""")

# ============================================================================
# 2. CROISEMENTS DE DONNÉES
# ============================================================================

print("=" * 70)
print("2. CROISY DÉFAILLANCES PAR CLASSE DPE")
print("=" * 70)

croiss = df.groupby('classe_dpe_modale').agg({
    'conso_reelle_par_m2': ['mean', 'median', 'std', 'count'],
    'ecart_pct': 'mean',
    'surface_med': 'mean',
}).round(2)

print("\n" + croiss.to_string())

# ============================================================================
# 3. CRÉER VISUALISATIONS INTERACTIVES
# ============================================================================

print("\n" + "=" * 70)
print("3. CRÉATION VISUALISATIONS INTERACTIVES PLOTLY")
print("=" * 70)

# Préparer données
df_plot = df.dropna(subset=['classe_dpe_modale', 'conso_reelle_par_m2', 'lat', 'lon'])

# 1. CARTE: Classes DPE
print("  → Création 1/5: Carte classes DPE...")
fig1 = px.scatter_mapbox(
    df_plot,
    lat='lat', lon='lon',
    color='classe_dpe_modale',
    hover_data=['adresse', 'annee', 'conso_reelle_par_m2', 'surface_med'],
    title='Classes DPE - Paris & Hauts-de-Seine',
    mapbox_style='open-street-map',
    color_discrete_map={
        'A': '#00b050', 'B': '#70ad47', 'C': '#ffc000',
        'D': '#ff9900', 'E': '#ff6600', 'F': '#ff3333', 'G': '#990000'
    },
    zoom=10,
    center={'lat': 48.85, 'lon': 2.35}
)
fig1.update_layout(height=700, margin={'r': 0, 't': 40, 'l': 0, 'b': 0})
fig1.write_html("docs/01_carte_classes_dpe.html")
print("     ✓ docs/01_carte_classes_dpe.html")

# 2. CARTE: Consommation
print("  → Création 2/5: Carte consommation (heatmap)...")
fig2 = px.scatter_mapbox(
    df_plot,
    lat='lat', lon='lon',
    color='conso_reelle_par_m2',
    hover_data=['adresse', 'classe_dpe_modale', 'surface_med'],
    title='Consommation réelle (kWh/m²/an)',
    mapbox_style='open-street-map',
    color_continuous_scale='RdYlGn_r',
    size_max=15,
    zoom=10,
    center={'lat': 48.85, 'lon': 2.35}
)
fig2.update_layout(height=700, margin={'r': 0, 't': 40, 'l': 0, 'b': 0})
fig2.write_html("docs/02_carte_consommation.html")
print("     ✓ docs/02_carte_consommation.html")

# 3. CARTE: Écarts
print("  → Création 3/5: Carte écarts DPE vs réalité...")
fig3 = px.scatter_mapbox(
    df_plot[df_plot['ecart_pct'].notna()],
    lat='lat', lon='lon',
    color='ecart_pct',
    hover_data=['adresse', 'classe_dpe_modale', 'ecart_pct'],
    title='Écart DPE vs Réalité (%)',
    mapbox_style='open-street-map',
    color_continuous_scale='RdBu',
    color_continuous_midpoint=0,
    size_max=15,
    zoom=10,
    center={'lat': 48.85, 'lon': 2.35}
)
fig3.update_layout(height=700, margin={'r': 0, 't': 40, 'l': 0, 'b': 0})
fig3.write_html("docs/03_carte_ecarts.html")
print("     ✓ docs/03_carte_ecarts.html")

# 4. GRAPHIQUE: Distribution par classe
print("  → Création 4/5: Distribution par classe DPE...")
fig4 = go.Figure()

for classe in sorted(df_plot['classe_dpe_modale'].unique()):
    data = df_plot[df_plot['classe_dpe_modale'] == classe]['conso_reelle_par_m2']
    fig4.add_trace(go.Box(
        y=data,
        name=f"Classe {classe}",
        boxmean='sd'
    ))

fig4.update_layout(
    title='Distribution consommation par classe DPE',
    yaxis_title='Consommation (kWh/m²/an)',
    xaxis_title='Classe DPE',
    height=600
)
fig4.write_html("docs/04_distribution_par_classe.html")
print("     ✓ docs/04_distribution_par_classe.html")

# 5. GRAPHIQUE: Évolution temporelle
print("  → Création 5/5: Évolution temporelle 2018-2024...")
evol = df.groupby(['annee', 'classe_dpe_modale'])['conso_reelle_par_m2'].mean().reset_index()

fig5 = px.line(
    evol,
    x='annee', y='conso_reelle_par_m2',
    color='classe_dpe_modale',
    markers=True,
    title='Évolution consommation par classe DPE (2018-2024)',
    labels={'annee': 'Année', 'conso_reelle_par_m2': 'Conso (kWh/m²/an)'}
)
fig5.update_layout(height=600)
fig5.write_html("docs/05_evolution_temporelle.html")
print("     ✓ docs/05_evolution_temporelle.html")

# ============================================================================
# 4. EXPORT TABLEAU SYNTHÉTIQUE
# ============================================================================

print("\n" + "=" * 70)
print("4. EXPORT TABLEAU SYNTHÉTIQUE")
print("=" * 70)

# Top 20 adresses
top_adresses = df.groupby('adresse').agg({
    'ban_id': 'first',
    'conso_reelle_par_m2': 'mean',
    'classe_dpe_modale': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
    'surface_med': 'first',
    'lat': 'first',
    'lon': 'first'
}).sort_values('conso_reelle_par_m2', ascending=False).head(20)

top_adresses.to_csv("data/top_20_adresses_conso.csv")
print("\n✓ Top 20 adresses (consommation): data/top_20_adresses_conso.csv")
print(top_adresses.to_string())

# ============================================================================
# 5. RÉSUMÉ FICHIERS DISPONIBLES
# ============================================================================

print("\n" + "=" * 70)
print("📁 FICHIERS DISPONIBLES")
print("=" * 70)

fichiers = {
    "DONNÉES PRINCIPALES": [
        ("data/dpe_enedis_joined.csv", "2,310 lignes fusionnées"),
        ("data/gains_par_classe.csv", "Gains rénovation E→D, F→E..."),
    ],
    "ANALYSES STATISTIQUES": [
        ("data/stats_descriptives_par_classe.csv", "Min, max, médiane, std"),
        ("data/variabilite_comportements.csv", "Écart-types résidus"),
        ("data/gains_par_usage.csv", "Breakdown chauffage/ECS/éclairage"),
    ],
    "MODÈLE PRÉDICTIF": [
        ("data/model_coefficients.csv", "Régression linéaire"),
        ("data/rapport_analyse.txt", "Rapport complet PDF-ready"),
    ],
    "VISUALISATIONS INTERACTIVES": [
        ("docs/01_carte_classes_dpe.html", "Carte interactive classes A-G"),
        ("docs/02_carte_consommation.html", "Heatmap consommation"),
        ("docs/03_carte_ecarts.html", "Écarts DPE vs réalité"),
        ("docs/04_distribution_par_classe.html", "Boxplots par classe"),
        ("docs/05_evolution_temporelle.html", "Tendance 2018-2024"),
        ("docs/analyses_avancees.png", "Graphiques PDF-exportables"),
    ]
}

for categorie, fichiers_list in fichiers.items():
    print(f"\n{categorie}:")
    for fichier, desc in fichiers_list:
        print(f"  ✓ {fichier:45} → {desc}")

print("\n" + "=" * 70)
print("✅ PRÊT POUR PRÉSENTATION/DATA.GOUV.FR")
print("=" * 70)

print("""
🎯 PROCHAINES ÉTAPES:
  1. Ouvrir docs/*.html dans navigateur pour voir cartes interactives
  2. Uploader data/dpe_enedis_joined.csv sur Kepler.gl
  3. Push sur GitHub + data.gouv.fr

📊 POUR PRÉSENTATION:
  • Montre les cartes interactives (docs/*.html)
  • Affiche le rapport texte (data/rapport_analyse.txt)
  • Parle de la couverture 0.4% (expected for DPE)
  • Mentionne les gains $/an (kWh/m² × 0.20€ × surface)
""")
