# 🏘️ Pipeline DPE × Enedis - Analyse Énergétique Paris & Hauts-de-Seine

## 📋 Vue d'ensemble du projet

Ce projet analyse l'**efficacité énergétique des bâtiments** en combinant deux sources de données majeures:
- **DPE (Diagnostic de Performance Énergétique)**: estimations théoriques des performances énergétiques
- **Enedis**: consommation électrique réelle mesurée

**Objectif**: Répondre à deux questions clés:
1. **Où sont les opportunités de rénovation énergétique?** (Quels quartiers consomment le plus?)
2. **Les estimations DPE reflètent-elles la réalité?** (Écart entre théorie et pratique)

**Zone d'étude**: Paris (75) & Hauts-de-Seine (92) | **Période**: 2018-2024

---

## 🎯 Principes data du projet

### 1. **Géocodage comme clé de jointure**
Problème: Les DPE et Enedis utilisent des adresses différentes (formats non standardisés).
Solution: Utiliser l'**API BAN (Base Adresse Nationale)** pour normaliser et géocoder tous les adresses vers des coordonnées (lat/lon) + `ban_id` unique.

### 2. **Jointure par agrégation**
- **Enedis**: format long (1 ligne = 1 adresse × 1 année)
- **DPE**: format court (1 ligne = 1 logement diagnostiqué)
→ Agrégation DPE par adresse (classe modale, surface médiane, % chauffage électrique)
→ Jointure sur `ban_id`

### 3. **Filtrage sur qualité**
- **Score BAN ≥ 0.7**: Garder seulement les adresses bien géocodées
- **Classes DPE A-G**: Exclure les données invalides
- **Enedis ≥ 0.7**: Filtrer les petits consommateurs (erreurs de lecture)

### 4. **Robustesse aux données manquantes**
DPE n'existe que pour **0.4% des adresses Enedis** (obligatoire seulement en cas de vente/location)
→ Pipeline conçu pour fonctionner même avec peu de couverture

---

## 🔄 Architecture du pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 1: Chargement Enedis                                  │
│ → Charger CSV Enedis (522,907 lignes)                       │
│ → Nettoyer et normaliser colonnes (conso, année, etc)       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 2: Téléchargement DPE via API ADEME                   │
│ → Paginer les résultats (10k par page)                      │
│ → Filtrer par code postal (75, 92)                          │
│ → Cacher les résultats localement (727 DPE)                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 3: Normalisation DPE                                  │
│ → Renommer colonnes API vers noms stables                   │
│ → Valider classes DPE (A-G) et exclure invalides            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 4: Géocodage BAN (avec cache)                         │
│ → Chunking par 5k adresses (évite timeouts)                 │
│ → Retry avec backoff exponentiel                            │
│ → Filtre score ≥ 0.7                                        │
│ → Cache local (enedis_geocoded.csv, dpe_geocoded.csv)       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 5: Jointure Enedis × DPE                              │
│ → Agrégation DPE par ban_id (classe modale, surface med)    │
│ → Inner join sur ban_id                                     │
│ → 2,310 lignes résultantes (338 adresses uniques)           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 6: Calcul des métriques                               │
│ → Conso par m² (normalisation taille)                       │
│ → Écart DPE vs réalité (en %)                               │
│ → Gains potentiels par classe de rénovation                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ÉTAPE 7: Export visualisations                              │
│ → Carte Plotly animée (années 2018-2024)                    │
│ → Export docs/index.html pour GitHub Pages                  │
│ → CSV pour Kepler.gl                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Données utilisées

### **Enedis** (`data/enedis_conso.csv`)
| Colonne | Description |
|---------|-------------|
| `adresse` | Adresse complète (format Enedis) |
| `annee` | Année de la mesure |
| `conso_kwh` | Consommation électrique annuelle (kWh) |
| `code_postal` | Code postal (75, 92) |
| `type_client` | Résidentiel/Professionnel |

**Volume**: 522,907 lignes | **Période**: 2018-2024

### **DPE API ADEME** (API `/datasets/dpe03existant`)
Après normalisation:
| Colonne | Description |
|---------|-------------|
| `classe_consommation_energie` | Classe A-G |
| `adresse_ban` | Adresse normalisée BAN |
| `surface_habitable_logement` | m² du logement |
| `conso_5_usages_par_m2_ef` | Consommation estimée par m² |
| `type_energie_chauffage` | Type chauffage (gaz, électrique, etc) |

**Volume**: 727 DPE après filtrage | **Couverture**: 0.4% des adresses Enedis

### **Géocodage BAN** (API `/search/csv/`)
| Colonne | Description |
|---------|-------------|
| `lat`, `lon` | Coordonnées GPS |
| `score` | Score de confiance géocodage (0-1) |
| `ban_id` | Identifiant unique BAN |

---

## 🔧 Techniques pipeline

### **1. Chunking pour géocodage à grande échelle**
- Divise 77k adresses en chunks de 5k
- Évite les timeouts et erreurs IncompleteRead
- Retry avec backoff (1s → 2s → 4s)

```python
CHUNK_SIZE = 5000
for chunk_idx in range(n_chunks):
    chunk = adresses[start:start+CHUNK_SIZE]
    result = API_CALL(chunk)  # POST /search/csv/
    retry_on_error(attempt=0, max_retries=3)
```

### **2. Jointure par agrégation**
Problème: Plusieurs DPE par adresse (différentes années)
Solution: Agrégation par `ban_id` avant jointure
```python
dpe_agg = dpe.groupby("ban_id").agg({
    "classe_consommation_energie": lambda x: x.mode()[0],  # classe modale
    "surface_habitable_logement":  "median",
    "conso_5_usages_par_m2_ef":    "median",
})
df_joined = enedis.merge(dpe_agg, on="ban_id", how="inner")
```

### **3. Cache multi-niveaux**
Évite relancer les longs traitements:
- **Étape 2**: Cache DPE API (data/dpe_75_92.csv)
- **Étape 4**: Cache géocodage (enedis_geocoded.csv, dpe_geocoded.csv)
→ Relance = 5s vs 30min premier lancement

### **4. Normalisation colonnes**
API ADEME changeante → Mapper noms variables:
```python
rename_map = {
    "Etiquette_DPE": "classe_consommation_energie",
    "Surface_habitable_logement": "surface_habitable_logement",
    # ...différents formats possibles
}
```

---

## 📈 Résultats & Insights

### **Couverture de données**
```
Enedis total:           522,907 adresses
Enedis dans 75/92:      77,069 adresses
DPE géocodé:            559 adresses (0.7%)
Adresses jointes:       338 adresses (0.4%)
Lignes résultantes:     2,310 (années 2018-2024)
```

### **Distribution DPE**
Parmi les 338 adresses jointes:
- **Classe D**: Majorité (logements années 1970-1990)
- **Classes E-G**: Petite portion (anciens immeubles)
- **Classes A-B**: Très rare (rénovations récentes)

### **Gains potentiels (hypothèse)**
Gain estimé en kWh/m²/an entre classes:
```
G → F : ~50-80 kWh/m²/an  →  ~650-1040 €/an (65m²)
F → E : ~30-50 kWh/m²/an  →  ~390-650  €/an
E → D : ~20-35 kWh/m²/an  →  ~260-455  €/an
D → C : ~15-25 kWh/m²/an  →  ~195-325  €/an
```
(Hypothèse: 0.20 €/kWh électrique)

---

## 🚀 Installation & utilisation

### **Prérequis**
```bash
Python 3.10+
pip or conda
```

### **Setup**
```bash
# 1. Clone ou télécharge le projet
cd hackahton

# 2. Crée l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installe les dépendances
pip install -r requirements.txt
```

### **Lancer le pipeline COMPLET**

**Option 1: Pipeline principal SEULEMENT**
```bash
python dpe_pipeline.py
```
**Durée:** ~30 min (1er lancement), ~5 min après

**Option 2: Pipeline + Analyses avancées**
```bash
python dpe_pipeline.py
python advanced_analysis.py
```
**Durée:** ~45 min total
**Génère:** Statistiques ML, prédictions, graphiques

**Option 3: Pipeline + Analyses + Exploration interactive**
```bash
python dpe_pipeline.py
python advanced_analysis.py
python explore_data.py
```
**Durée:** ~50 min total
**Génère:** Cartes Plotly interactives HTML

### **Résultats produits**

**Après `dpe_pipeline.py`:**
```
data/
├── enedis_geocoded.csv             # Enedis + coordonnées
├── dpe_geocoded.csv                # DPE + coordonnées
├── dpe_enedis_joined.csv           # DONNÉES FINALES (2,310 lignes)
├── gains_par_classe.csv            # Gains rénovation
├── dpe_kepler.csv                  # Format optimisé Kepler.gl
└── METADATA.json                   # Métadonnées

docs/
└── index.html                      # Carte Plotly animée
```

**Après `advanced_analysis.py`:**
```
data/
├── stats_descriptives_par_classe.csv    # Min/max/médiane/std
├── variabilite_comportements.csv        # Écart-types résidus
├── gains_par_usage.csv                  # Breakdown chauffage/ECS/éclairage
├── model_coefficients.csv               # Coefficients ML
└── rapport_analyse.txt                  # Rapport synthétique complet

docs/
└── analyses_avancees.png               # 6 graphiques PNG
```

**Après `explore_data.py`:**
```
docs/
├── 01_carte_classes_dpe.html           # Carte classes A-G
├── 02_carte_consommation.html          # Heatmap consommation
├── 03_carte_ecarts.html                # Écarts DPE vs réalité
├── 04_distribution_par_classe.html     # Boxplots par classe
├── 05_evolution_temporelle.html        # Tendance 2018-2024
└── analyses_avancees.png               # Graphiques synthétiques

data/
└── top_20_adresses_conso.csv           # Top consommateurs
```

### **Visualiser les résultats**

**Option 1: Cartes locales (HTML)**
```bash
# Ouvre dans navigateur:
cd docs/
# Double-clique sur: 01_carte_classes_dpe.html
# Ou ouvre directement: file:///path/hackahton/docs/01_carte_classes_dpe.html
```

**Option 2: Kepler.gl cloud**
1. Allez sur https://kepler.gl
2. Drag & drop `data/dpe_enedis_joined.csv` ou `data/dpe_kepler.csv`
3. Customisez les couches et couleurs
4. Partagez via le lien public

**Option 3: Rapport texte complet**
```bash
# Lire le rapport d'analyse:
cat data/rapport_analyse.txt
# Ou ouvrir dans éditeur: data/rapport_analyse.txt
```

**Option 4: Exploration Python**
```bash
python explore_data.py
# Génère statistiques + cartes interactives
```

---

## ⚡ Démarrage rapide

### **Les 3 façons de lancer le projet**

**🟢 Mode RAPIDE (5 min) - Juste les données finales**
```bash
python dpe_pipeline.py
# ✓ Crée: dpe_enedis_joined.csv + 1 carte HTML
```

**🟡 Mode STANDARD (45 min) - Données + Analyses (RECOMMANDÉ)**
```bash
python dpe_pipeline.py
python advanced_analysis.py
python explore_data.py
# ✓ Crée: Tous les fichiers CSV + 5 cartes HTML + 6 graphiques PNG + rapport TXT
```

**🔵 Mode MANUEL (Python interactif)**
```python
import pandas as pd
df = pd.read_csv("data/dpe_enedis_joined.csv")
print(f"Nombre de lignes: {len(df)}")
print(df[['classe_dpe_modale', 'conso_kwh', 'lat', 'lon']].head(10))
df.to_json("export.json", orient="records", force_ascii=False)
```

### **Uploader directement à Kepler.gl**
1. Ouvrez https://kepler.gl
2. Drag & drop `data/dpe_enedis_joined.csv`
3. Colorez par `classe_dpe_modale` (classe DPE)
4. Filtrez par année si besoin

---

## 📁 Structure du projet

```
hackahton/
├── dpe_pipeline.py                 # Script principal pipeline (7 étapes)
├── advanced_analysis.py            # Analyses ML + statistiques avancées
├── explore_data.py                 # Exploration interactive + cartes Plotly
├── requirements.txt                # Dépendances Python
├── README.md                       # Cette documentation
├── .gitignore                      # Fichiers à ne pas pusher
│
├── data/
│   ├── enedis_conso.csv            # Source: Enedis 522k lignes
│   ├── dpe_75_92.csv               # Cache: DPE API ADEME
│   ├── enedis_geocoded.csv         # Enedis + lat/lon/ban_id
│   ├── dpe_geocoded.csv            # DPE + lat/lon/ban_id
│   ├── dpe_enedis_joined.csv       # ⭐ RÉSULTAT FINAL (2310 lignes)
│   ├── gains_par_classe.csv        # Gains rénovation E→D, F→E...
│   ├── dpe_kepler.csv              # Format Kepler.gl optimisé
│   ├── METADATA.json               # Métadonnées data.gouv.fr
│   │
│   ├── stats_descriptives_par_classe.csv
│   ├── variabilite_comportements.csv
│   ├── gains_par_usage.csv
│   ├── model_coefficients.csv
│   ├── rapport_analyse.txt
│   └── top_20_adresses_conso.csv
│
└── docs/
    ├── index.html                  # Carte animée (pipeline principal)
    ├── 01_carte_classes_dpe.html   # Carte classes A-G interactives
    ├── 02_carte_consommation.html  # Heatmap consommation
    ├── 03_carte_ecarts.html        # Écarts DPE vs réalité
    ├── 04_distribution_par_classe.html
    ├── 05_evolution_temporelle.html
    └── analyses_avancees.png       # 6 graphiques synthétiques
```

### **Fichiers clés**

| Fichier | Contenu | Taille | Utilité |
|---------|---------|--------|---------|
| `dpe_enedis_joined.csv` | 2,310 lignes jointes | ~2-5 MB | **Données principales à analyser** |
| `gains_par_classe.csv` | Gains E→D, F→E... | <1 KB | Réponse à Q1 (gains rénovation) |
| `rapport_analyse.txt` | Rapport complet | ~10 KB | Documentation complète |
| `01-05_*.html` | Cartes interactives | ~500 KB | Visualisations Kepler.gl-style |
| `model_coefficients.csv` | Régression ML | <1 KB | Modèle prédictif DPE |

---

## 🛠️ Scripts disponibles

### **1. `dpe_pipeline.py` - Pipeline principal** ⭐

**Qu'est-ce qu'il fait:**
- Charge 522k adresses Enedis
- Télécharge 727 DPE via API ADEME
- Géocode 77k adresses via API BAN (avec chunking + retry)
- **Jointure final:** 2,310 lignes (338 adresses uniques)
- Calcule gains rénovation et écarts DPE vs réalité
- Crée carte Plotly animée (2018-2024)

**Durée:** ~30 min (1er lancement), ~5 min après (cache)

**Résultats:**
```
✓ data/dpe_enedis_joined.csv (données finales)
✓ data/gains_par_classe.csv
✓ docs/index.html (carte animée)
```

**Lancer:**
```bash
python dpe_pipeline.py
```

---

### **2. `advanced_analysis.py` - Analyses statistiques & ML** 📊

**Qu'est-ce qu'il fait:**
- Statistiques descriptives par classe DPE
- Analyse de la variabilité (comportements + facteurs non-DPE)
- Breakdown des gains par usage (chauffage 70%, ECS 15%, éclairage 10%)
- **Modèle prédictif:** Régression linéaire (DPE → conso réelle)
- Crée 6 graphiques avancés (boxplots, heatmaps, résidus)
- Génère rapport synthétique complet

**Durée:** ~15 min

**Résultats:**
```
✓ data/stats_descriptives_par_classe.csv
✓ data/variabilite_comportements.csv
✓ data/gains_par_usage.csv
✓ data/model_coefficients.csv
✓ data/rapport_analyse.txt (rapport complet)
✓ docs/analyses_avancees.png (6 graphiques)
```

**Lancer après pipeline:**
```bash
python advanced_analysis.py
```

---

### **3. `explore_data.py` - Visualisations interactives Plotly** 🗺️

**Qu'est-ce qu'il fait:**
- Crée 5 cartes interactives HTML (Plotly)
- Carte 1: Classes DPE (A-G couleurs)
- Carte 2: Heatmap consommation
- Carte 3: Écarts DPE vs réalité
- Graphique 4: Boxplots distribution par classe
- Graphique 5: Évolution temporelle 2018-2024
- Export top 20 adresses consommatrices
- Affiche statistiques globales

**Durée:** ~5 min

**Résultats:**
```
✓ docs/01_carte_classes_dpe.html
✓ docs/02_carte_consommation.html
✓ docs/03_carte_ecarts.html
✓ docs/04_distribution_par_classe.html
✓ docs/05_evolution_temporelle.html
✓ data/top_20_adresses_conso.csv
```

**Lancer après analyses:**
```bash
python explore_data.py
```

---

## ⚡ Raccourcis rapides

### **Tuning performance**

| Paramètre | Valeur | Effet |
|-----------|--------|-------|
| `CHUNK_SIZE` | 5000 | Plus petit = plus stable mais plus lent |
| `BAN_SCORE_MIN` | 0.7 | Plus haut = moins adresses mais plus précis |
| `Timeout API` | 120s | Plus haut = moins d'erreurs mais plus lent |

### **Départements**
Pour ajouter d'autres régions, modifiez dans `dpe_pipeline.py`:
```python
PREFIXES_DEPT = ["75", "92"]  # → ["75", "92", "77", "78"]
```

---

## 📝 Limitations & améliorations

### **Limitations actuelles**
1. **Couverture DPE faible (0.4%)**: DPE obligatoire seulement vente/location
2. **Données vieillissantes**: DPE valide 10 ans, dernière mise à jour 2024
3. **Pas de chauffage gaz**: Pipeline utilise Enedis (électricité seulement)
4. **Écart théorie/réalité**: Beaucoup de facteurs non capturés (comportements, météo)

### **Améliorations possibles**
- Ajouter données **gaz** (GRDF) pour chauffage gaz
- Ajouter **météo historique** pour ajuster les comparaisons
- Modèle de **prédiction** classe DPE par ML (score BAN, surface, année construction)
- **Suivi temporel**: Voir l'amélioration DPE année par année post-rénovation
- **Comparaison inter-quartiers**: Dashboard par arrondissement

---

## 🔍 Méthodologie détaillée

### **Normalisation consommation**

**Problème**: Comparer logements de tailles différentes (50m² vs 200m²)

**Solution**: Normaliser par m²
```python
conso_reelle_par_m2 = conso_par_logement_kwh / surface_med
```

### **Calcul écart DPE vs réalité**

**Formule**:
```
écart_pct = (conso_estimée_DPE - conso_réelle_Enedis) / conso_réelle_Enedis * 100
```

- **Positif**: DPE sous-estime (logement plus énergivore que prévu)
- **Négatif**: DPE sur-estime (logement plus économe que le standard 3CL)

---

## 📞 Support & troubleshooting

### **Erreur: KeyError 'lat', 'lon' not in index**
→ Colonne renommage BAN échouée. Vérifier format API avec `[BAN DEBUG]`

### **Erreur: ChunkedEncodingError**
→ API instable. Retry automatique avec backoff. Si persiste, ↓ CHUNK_SIZE

### **Couverture très faible (~0.4%)**
→ Normal! DPE n'existe que pour ~0.4% des adresses Enedis. Augmenter zone géographique pour plus de données.

### **Kepler.gl: "get is not a function"**
→ Format CSV invalide (NaN, caractères spéciaux). Utiliser `dpe_kepler.csv` au lieu de `dpe_enedis_joined.csv`

---

## 📚 Sources & références

- **API ADEME DPE**: https://data.ademe.fr/datasets/dpe03existant
- **API BAN Géocodage**: https://adresse.data.gouv.fr/api
- **Enedis Data**: Données propriétaires (à fournir)
- **Kepler.gl Viz**: https://kepler.gl

---

## 👨‍💻 Auteur & licence

Hackathon Energy Data Project
MIT Licence - Libre d'utilisation et modification

---

**Dernière mise à jour**: Avril 2026
**Status**: ✅ Production
**Maintenance**: Mise à cache DPE via API manuelle (données changent lentement)
