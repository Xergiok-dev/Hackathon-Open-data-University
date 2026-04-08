"""
=============================================================================
HACKATHON OPEN DATA UNIVERSITY — Diagnostics de Performance Énergétique
=============================================================================

OBJECTIF :
    Croiser les données de consommation électrique réelle (Enedis, 2018-2024)
    avec les classes DPE (ADEME, depuis juillet 2021) pour :
    1. Quantifier le gain réel en kWh/an entre chaque classe DPE
    2. Mesurer l'écart entre consommation estimée (DPE) et mesurée (Enedis)
    3. Produire une carte temporelle animée (2018→2024) par adresse

CE QU'ON PEUT OBTENIR COMME RÉSULTATS :
    - Carte animée GitHub Pages : points colorés par classe DPE, taille
      proportionnelle à la conso réelle, slider 2018→2024
    - Boxplots : distribution des consos réelles par classe (A→G)
    - Tableau de gains : passage F→E = X kWh/an/m², E→D = Y kWh/an/m², etc.
    - Écart DPE estimé vs réel : zones sur-estimées vs sous-estimées
    - Heatmap des "mauvais élèves" : adresses où l'écart estimé/réel est maximal

SOURCES DE DONNÉES :
    - Enedis : https://data.enedis.fr/explore/dataset/consommation-annuelle-residentielle-par-adresse
      → Format réel : CSV virgule, unité MWh, années en lignes (colonne "Année")
      → "Code Département" est un float64 (ex: 75.0) → on compare avec des ints
    - ADEME DPE : https://data.ademe.fr/datasets/dpe03existant
      → Récupéré via l'API (pas de téléchargement du fichier 10Go)
      → ID correct de l'API : dpe03existant (pas dpe-v2-logements-existants)

STRATÉGIE DE JOINTURE :
    Ni Enedis ni le DPE ne partagent de clé commune. On passe les deux
    datasets par l'API BAN (Base Adresse Nationale) pour normaliser les
    adresses et obtenir un identifiant géographique commun (ban_id).

    On filtre sur 1 ou 2 départements pour rester sous ~50k lignes de
    chaque côté → jointure rapide, carte lisible, rendu pro en présentation.

BUGS CORRIGÉS :
    - "Code Département" est float64 → DEPARTEMENTS doit être une liste d'ints
    - L'API ADEME dpe-v2-logements-existants est morte → nouvel ID : dpe03existant
    - Noms de colonnes DPE détectés dynamiquement depuis l'API au premier appel
    - Filtre département côté Python (plus fiable que le filtre API ADEME)

=============================================================================
"""

import pandas as pd
import requests
import time
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
from pathlib import Path

# =============================================================================
# 0. CONFIGURATION — MODIFIER ICI SELON VOS BESOINS
# =============================================================================

# IMPORTANT : ints, pas strings !
# La colonne "Code Département" dans Enedis est de type float64 (75.0, 92.0)
# → isin(["75", "92"]) ne matcherait jamais → on utilise isin([75, 92])
DEPARTEMENTS = [75, 92]

# Seuil de confiance de l'API BAN : entre 0 et 1
# 0.7 = bon compromis qualité/quantité (on garde ~80% des adresses)
BAN_SCORE_MIN = 0.7

# Chemin vers le fichier Enedis téléchargé depuis data.enedis.fr
PATH_ENEDIS = Path("data/enedis_conso.csv")

# Fichiers intermédiaires (générés automatiquement par le pipeline)
PATH_DPE_CACHE  = Path("data/dpe_75_92.csv")        # DPE brut téléchargé via API
PATH_DPE_GEO    = Path("data/dpe_geocoded.csv")     # DPE + coordonnées GPS
PATH_ENEDIS_GEO = Path("data/enedis_geocoded.csv")  # Enedis + coordonnées GPS
PATH_OUTPUT     = Path("data/dpe_enedis_joined.csv")  # Résultat final jointure


# =============================================================================
# 1. CHARGEMENT ENEDIS
# =============================================================================

def load_enedis(path: Path) -> pd.DataFrame:
    """
    Charge le dataset Enedis et filtre sur les départements voulus.

    FORMAT RÉEL DU FICHIER (vérifié sur les données) :
    - Séparateur : virgule (pas point-virgule)
    - Unité : MWh (pas kWh !) → on convertit × 1000
    - Les années sont en LIGNES (colonne "Année"), pas en colonnes séparées
    - "Code Département" est de type float64 : 75.0, 92.0, etc.
      → DEPARTEMENTS doit être une liste d'ints pour que isin() fonctionne

    Colonnes utilisées :
    - "Année"                                           : 2018 à 2024
    - "Adresse"                                         : adresse complète
    - "Nombre de logements"                             : nb de PDL à l'adresse
    - "Consommation annuelle totale de l'adresse (MWh)" : conso totale en MWh
    - "Code Département"                                : float (75.0, 92.0...)
    """
    print(f"[Enedis] Chargement de {path}...")
    df = pd.read_csv(path, sep=",", low_memory=False)
    df.columns = df.columns.str.strip()

    # "Code Département" est float64 → on compare avec des ints
    # isin(["75", "92"]) ne matcherait jamais 75.0
    df = df[df["Code Département"].isin(DEPARTEMENTS)].copy()

    # Garder uniquement les lignes résidentielles
    df = df[df["Segment de client"] == "RESIDENTIEL"].copy()

    # Conversion MWh → kWh
    df["conso_totale_kwh"] = (
        df["Consommation annuelle totale de l'adresse (MWh)"] * 1000
    )

    # Conso moyenne par logement à cette adresse
    df["conso_par_logement_kwh"] = (
        df["conso_totale_kwh"] / df["Nombre de logements"]
    )

    # Renommage pour simplifier la suite du pipeline
    df = df.rename(columns={
        "Année":               "annee",
        "Adresse":             "adresse",
        "Nombre de logements": "nb_logements",
        "Code Département":    "dept",
        "Code IRIS":           "code_iris",
        "Nom Commune":         "nom_commune",
    })

    df = df[[
        "annee", "adresse", "nb_logements", "dept",
        "conso_totale_kwh", "conso_par_logement_kwh",
        "code_iris", "nom_commune",
    ]].copy()

    print(f"[Enedis] {len(df):,} lignes chargées pour départements {DEPARTEMENTS}")
    print(f"         Années disponibles  : {sorted(df['annee'].unique())}")
    print(f"         Adresses uniques    : {df['adresse'].nunique():,}")
    return df


# =============================================================================
# 2. TÉLÉCHARGEMENT DPE VIA L'API ADEME
# =============================================================================

def _detect_column(row: dict, candidates: list) -> str:
    """
    Trouve le premier nom de colonne candidat présent dans un dict.
    Utile car les noms de colonnes ADEME varient selon la version de l'API.
    Si aucun candidat ne matche, retourne le premier candidat par défaut
    et affiche un warning pour qu'on puisse corriger.
    """
    for c in candidates:
        if c in row:
            return c
    print(f"  [WARN] Aucune colonne trouvée parmi {candidates}")
    print(f"         Colonnes disponibles : {list(row.keys())}")
    return candidates[0]  # fallback


def fetch_and_save_dpe() -> pd.DataFrame:
    """
    Télécharge les DPE depuis l'API ADEME et sauvegarde en CSV local.

    POURQUOI L'API ET PAS LE FICHIER COMPLET :
    Le fichier DPE complet fait ~10Go. L'API permet de ne récupérer que
    les logements des départements qui nous intéressent (~50-100k lignes).

    ID CORRECT DE L'API : dpe03existant
    (l'ancien ID dpe-v2-logements-existants renvoie 404 depuis 2024)

    PAGINATION : l'API utilise un curseur "after" (pas un numéro de page).
    On boucle jusqu'à ce qu'il n'y ait plus de "next" dans la réponse.

    FILTRE DÉPARTEMENT : on filtre côté Python sur le code postal plutôt
    que via le paramètre API, car le filtre ADEME est peu fiable sur les
    colonnes avec caractères spéciaux dans le nom.
    """
    # Si déjà téléchargé, on recharge depuis le cache
    if PATH_DPE_CACHE.exists():
        print(f"[CACHE] DPE déjà téléchargé → {PATH_DPE_CACHE}")
        df = pd.read_csv(PATH_DPE_CACHE, low_memory=False)
        print(f"        {len(df):,} logements chargés")
        return df

    BASE_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines"

    # Préfixes de codes postaux à garder (ex: 75 → "75xxx", 92 → "92xxx")
    prefixes = [str(d) for d in DEPARTEMENTS]

    all_rows = []
    after = None
    page = 0
    col_cp = None  # détecté dynamiquement à la première page

    print(f"[DPE API] Téléchargement pour départements {DEPARTEMENTS}...")
    print(f"          (peut prendre 5-15 min selon le volume)")

    while True:
        params = {"size": 10000}
        if after:
            params["after"] = after

        try:
            r = requests.get(BASE_URL, params=params, timeout=60)
        except requests.RequestException as e:
            print(f"  Erreur réseau page {page} : {e}, on réessaie dans 5s...")
            time.sleep(5)
            continue

        if r.status_code == 404:
            print(f"404 — URL : {r.url}")
            print("Vérifier l'ID du dataset sur https://data.ademe.fr/datasets/dpe03existant")
            break

        if r.status_code != 200:
            print(f"  Erreur {r.status_code} page {page}, arrêt.")
            break

        data = r.json()
        rows = data.get("results", [])
        if not rows:
            break

        # À la première page : détecter les bons noms de colonnes
        if page == 0:
            col_cp = _detect_column(rows[0], [
                "Code_postal_(BAN)", "Code_postal_BAN",
                "code_postal_ban",   "Code postal (BAN)",
            ])
            col_etiquette = _detect_column(rows[0], [
                "Etiquette_DPE", "Étiquette_DPE", "etiquette_dpe",
                "classe_consommation_energie",
            ])
            print(f"  Colonnes détectées → CP: '{col_cp}', Étiquette: '{col_etiquette}'")

        # Filtrage côté Python sur le code postal
        rows_dept = [
            row for row in rows
            if any(str(row.get(col_cp, "")).startswith(p) for p in prefixes)
        ]
        all_rows.extend(rows_dept)

        after = data.get("next")
        page += 1

        if page % 10 == 0:
            print(f"  Page {page} — {len(all_rows):,} DPE filtrés au total")

        if not after:
            break

    df = pd.DataFrame(all_rows)
    PATH_DPE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PATH_DPE_CACHE, index=False)
    print(f"[DPE] {len(df):,} logements sauvegardés → {PATH_DPE_CACHE}")
    return df


def normalize_dpe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise les noms de colonnes DPE pour le reste du pipeline.

    L'API ADEME peut retourner des noms de colonnes légèrement différents
    selon la version. On mappe vers des noms stables utilisés dans la suite.

    Mapping appliqué :
    - Etiquette_DPE / etiquette_dpe           → classe_consommation_energie
    - Adresse_(BAN) / Adresse_BAN             → adresse_ban
    - Code_postal_(BAN)                        → code_postal_ban
    - Conso_5_usages_par_m²_é_prim            → conso_5_usages_par_m2
    - Surface_habitable_logement              → surface_habitable_logement
    - Type_énergie_principale_chauffage       → type_energie_chauffage
    - Année_construction                      → annee_construction
    """
    rename_map = {}

    # Étiquette DPE → classe_consommation_energie
    for c in ["Etiquette_DPE", "Étiquette_DPE", "etiquette_dpe"]:
        if c in df.columns:
            rename_map[c] = "classe_consommation_energie"
            break

    # Adresse BAN → adresse_ban
    for c in ["Adresse_(BAN)", "Adresse_BAN", "adresse_ban"]:
        if c in df.columns:
            rename_map[c] = "adresse_ban"
            break

    # Code postal → code_postal_ban
    for c in ["Code_postal_(BAN)", "Code_postal_BAN", "code_postal_ban"]:
        if c in df.columns:
            rename_map[c] = "code_postal_ban"
            break

    # Consommation estimée par m² → conso_5_usages_par_m2
    for c in ["Conso_5_usages_par_m²_é_prim", "Conso_5_usages_par_m2_e_prim",
              "conso_5_usages_par_m2", "Conso_5_usages/m²_é_prim"]:
        if c in df.columns:
            rename_map[c] = "conso_5_usages_par_m2"
            break

    # Surface → surface_habitable_logement (peut déjà être au bon nom)
    for c in ["Surface_habitable_logement", "surface_habitable_logement"]:
        if c in df.columns and c != "surface_habitable_logement":
            rename_map[c] = "surface_habitable_logement"
            break

    # Type d'énergie chauffage → type_energie_chauffage
    for c in ["Type_énergie_principale_chauffage", "Type_energie_principale_chauffage",
              "type_energie_principale_chauffage"]:
        if c in df.columns:
            rename_map[c] = "type_energie_chauffage"
            break

    # Année de construction → annee_construction
    for c in ["Année_construction", "Annee_construction", "annee_construction"]:
        if c in df.columns:
            rename_map[c] = "annee_construction"
            break

    df = df.rename(columns=rename_map)

    # Ne garder que les classes valides A à G
    if "classe_consommation_energie" in df.columns:
        df = df[df["classe_consommation_energie"].isin(list("ABCDEFG"))].copy()
    else:
        print("[WARN] Colonne 'classe_consommation_energie' introuvable après renommage !")
        print(f"       Colonnes disponibles : {df.columns.tolist()}")

    # Conso estimée totale = surface × conso par m²
    if "conso_5_usages_par_m2" in df.columns and "surface_habitable_logement" in df.columns:
        df["conso_estimee_kwh_an"] = (
            pd.to_numeric(df["conso_5_usages_par_m2"], errors="coerce") *
            pd.to_numeric(df["surface_habitable_logement"], errors="coerce")
        )

    print(f"[DPE] Après normalisation : {len(df):,} logements avec classe valide")
    return df


# =============================================================================
# 3. GÉOCODAGE VIA L'API BAN
# =============================================================================

def geocode_batch(df: pd.DataFrame, col_adresse: str, label: str) -> pd.DataFrame:
    """
    Géocode en masse un DataFrame via l'API BAN (endpoint /csv/).

    STRATÉGIE AMÉLIORÉE :
    - Traite par chunks de 5000 adresses pour éviter timeouts/IncompleteRead
    - Retry avec exponential backoff sur chaque chunk
    - Filtre sur score >= BAN_SCORE_MIN pour qualité

    Performance :
    - 77k adresses en ~10-15 chunks = ~5-10 minutes (vs ~7h ligne par ligne)
    """
    print(f"[BAN] Géocodage de {len(df):,} adresses ({label})...")

    # Dédupliquer les adresses avant d'envoyer
    adresses_uniques = df[[col_adresse]].drop_duplicates().reset_index(drop=True)
    all_results = []
    
    # Traiter par chunks pour éviter IncompleteRead
    CHUNK_SIZE = 5000
    n_chunks = (len(adresses_uniques) + CHUNK_SIZE - 1) // CHUNK_SIZE
    
    for chunk_idx in range(n_chunks):
        start_idx = chunk_idx * CHUNK_SIZE
        end_idx = min((chunk_idx + 1) * CHUNK_SIZE, len(adresses_uniques))
        chunk = adresses_uniques.iloc[start_idx:end_idx]
        
        print(f"[BAN] Chunk {chunk_idx + 1}/{n_chunks} ({len(chunk):,} adresses)...")
        
        tmp_csv_str = chunk.rename(
            columns={col_adresse: "adresse"}
        ).to_csv(index=False)
        
        # Retry avec backoff exponentiel
        max_retries = 3
        for attempt in range(max_retries):
            try:
                r = requests.post(
                    "https://api-adresse.data.gouv.fr/search/csv/",
                    files={"data": ("adresses.csv", tmp_csv_str.encode("utf-8"), "text/csv")},
                    data={"columns": "adresse"},
                    timeout=120,
                )
                r.raise_for_status()

                result = pd.read_csv(StringIO(r.text))
                
                # Debug: vérifier les colonnes reçues
                if chunk_idx == 0:
                    print(f"[BAN DEBUG] Colonnes reçues du chunk 1: {list(result.columns)}")
                
                # Renommer les colonnes (lat/lon ne sont PAS préfixés avec result_)
                result = result.rename(columns={
                    "latitude":         "lat",
                    "longitude":        "lon",
                    "result_score":     "score",
                    "result_id":        "ban_id",
                })

                # Filtrer sur score minimum
                if "score" not in result.columns:
                    print(f"[BAN ERROR] Colonnes après renommage: {list(result.columns)}")
                    raise ValueError(f"Colonne 'score' absente. Colonnes: {list(result.columns)}")
                    
                result = result[result["score"] >= BAN_SCORE_MIN].copy()
                print(f"      → {len(result):,} adresses géocodées (score ≥ {BAN_SCORE_MIN})")
                
                all_results.append(result)
                break  # Succès, sortir de la boucle de retry
                
            except Exception as e:
                wait_time = 2 ** attempt
                if attempt < max_retries - 1:
                    print(f"      ⚠ Tentative {attempt + 1} échouée: {type(e).__name__}")
                    print(f"      ⏳ Retry dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"      ✗ Chunk échoué après {max_retries} tentatives")
    
    # Concaténer tous les résultats
    if all_results:
        result_df = pd.concat(all_results, ignore_index=True)
        
        print(f"[BAN DEBUG] Après concat - colonnes disponibles: {list(result_df.columns)}")
        
        # Vérifier que les colonnes requises existent
        required = ["adresse", "lat", "lon", "score", "ban_id"]
        missing = [col for col in required if col not in result_df.columns]
        if missing:
            print(f"[BAN ERROR] Colonnes manquantes après concat: {missing}")
            print(f"[BAN DEBUG] Colonnes actuelles: {list(result_df.columns)}")
            raise ValueError(f"Colonnes manquantes: {missing}")
        
        result_df = result_df[required].drop_duplicates()
        
        print(f"[BAN] Total: {len(result_df):,} adresses géocodées avec succès")
        
        # Jointure sur l'adresse texte
        return df.merge(
            result_df,
            left_on=col_adresse,
            right_on="adresse",
            how="left",
        )
    else:
        print(f"[BAN] ERREUR: Aucun résultat obtenu après chunking")
        # Ajouter des colonnes vides pour continuité
        return df.assign(lat=None, lon=None, score=None, ban_id=None)


# =============================================================================
# 4. JOINTURE ENEDIS × DPE
# =============================================================================

def join_enedis_dpe(df_enedis: pd.DataFrame, df_dpe: pd.DataFrame) -> pd.DataFrame:
    """
    Joint les deux datasets sur le ban_id (clé géographique commune).

    LOGIQUE :
    - Enedis : format long, 1 ligne par adresse × année
    - DPE    : 1 ligne par logement individuel
      → on agrège d'abord les DPE par adresse (ban_id) :
        classe modale, conso estimée médiane, surface médiane

    Chaque ligne Enedis hérite ensuite des métadonnées DPE de son adresse.

    COUVERTURE ATTENDUE :
    10-30% des adresses Enedis auront un DPE (obligatoire seulement en cas
    de vente/location). Sur ~50k adresses, on espère 5k-15k avec DPE.
    C'est suffisant pour la carte animée et les analyses statistiques.
    """
    # Agrégation DPE par adresse (ban_id)
    # Syntaxe pandas: new_col=(col, func)
    dpe_agg = df_dpe.groupby("ban_id", as_index=False).agg(
        classe_dpe_modale = ("classe_consommation_energie",
                            lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0]),
        nb_dpe            = ("classe_consommation_energie", "count"),
        surface_med       = ("surface_habitable_logement", "median"),
        pct_elec_chauffage = ("type_energie_chauffage",
                             lambda x: (x.astype(str).str.lower()
                                       .str.contains("élec|elec")).mean() * 100),
    )
    
    # Ajouter conso_5_usages_par_m2_ef si disponible
    if "conso_5_usages_par_m2_ef" in df_dpe.columns:
        conso_agg = df_dpe.groupby("ban_id", as_index=False).agg(
            conso_5_usages_par_m2_med = ("conso_5_usages_par_m2_ef", "median")
        )
        dpe_agg = dpe_agg.merge(conso_agg, on="ban_id")

    print(f"[JOIN] DPE agrégé: {len(dpe_agg):,} adresses avec DPE")
    
    # Jointure : chaque ligne Enedis (année) hérite des infos DPE de l'adresse
    df_joined = df_enedis.merge(dpe_agg, on="ban_id", how="inner")

    nb_adresses = df_joined["adresse"].nunique()
    nb_total    = df_enedis["adresse"].nunique()
    print(f"[JOIN] {len(df_joined):,} lignes résultantes")
    print(f"       {nb_adresses:,} adresses uniques avec DPE")
    print(f"       Couverture : {nb_adresses / nb_total * 100:.1f}%")
    return df_joined


# =============================================================================
# 5. CALCUL DES MÉTRIQUES
# =============================================================================

def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les métriques clés pour répondre aux deux questions du brief :

    QUESTION 1 : "Combien gagne-t-on en passant d'une classe à l'autre ?"
    → conso_reelle_par_m2 permet de comparer logements de tailles différentes

    QUESTION 2 : "Les estimations DPE reflètent-elles la réalité ?"
    → ecart_pct mesure l'écart en % entre DPE estimé et Enedis mesuré
      Positif = DPE sous-estime (logement plus énergivore qu'annoncé)
      Négatif = DPE sur-estime (occupants plus économes que le standard 3CL)
    """
    # Normalisation par m² pour comparer des logements de tailles différentes
    df["conso_reelle_par_m2"] = (
        df["conso_par_logement_kwh"] / df["surface_med"]
    )

    # Écart entre estimation DPE et consommation réelle mesurée par Enedis
    # Note: on utilise conso_5_usages_par_m2_med si disponible, sinon on estime
    if "conso_5_usages_par_m2_med" in df.columns:
        df["conso_estimee_med"] = df["conso_5_usages_par_m2_med"] * df["surface_med"]
    else:
        print("[WARN] conso_5_usages_par_m2_med non disponible, écart non calculé")
        df["conso_estimee_med"] = None
    
    df["ecart_estime_vs_reel"] = (
        df["conso_estimee_med"] - df["conso_par_logement_kwh"]
    )
    df["ecart_pct"] = (
        df["ecart_estime_vs_reel"] / df["conso_par_logement_kwh"] * 100
    ).round(1)

    return df


def compute_gains_par_classe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le gain en kWh/an/m² et en euros entre chaque paire de classes DPE.

    Utilise l'année la plus récente disponible comme référence.
    Valorise le gain en euros avec l'hypothèse 0.20 €/kWh.
    Calcule aussi pour un logement de 65m² (taille médiane France).

    RÉSULTAT ATTENDU (ordre de grandeur) :
    G → F : ~50-80 kWh/m²/an  →  ~650-1040 €/an pour 65m²
    F → E : ~30-50 kWh/m²/an  →  ~390-650  €/an pour 65m²
    E → D : ~20-35 kWh/m²/an  →  ~260-455  €/an pour 65m²
    D → C : ~15-25 kWh/m²/an  →  ~195-325  €/an pour 65m²
    """
    annee_ref = df["annee"].max()
    df_ref = df[df["annee"] == annee_ref].copy()

    # Agrégation simple - utiliser dict[col] = func format
    stats = df_ref.groupby("classe_dpe_modale", as_index=False).agg({
        "conso_reelle_par_m2": "median",
        "ban_id":               "count",
    }).rename(columns={
        "conso_reelle_par_m2": "conso_mediane_kwh_m2",
        "ban_id": "nb_adresses"
    })
    
    # Optionnel : ajouter ecart_pct s'il existe
    if "ecart_pct" in df_ref.columns and df_ref["ecart_pct"].notna().any():
        ecart_stats = df_ref.groupby("classe_dpe_modale", as_index=False).agg({
            "ecart_pct": "median"
        }).rename(columns={"ecart_pct": "ecart_median_pct"})
        stats = stats.merge(ecart_stats, on="classe_dpe_modale")
    
    # Filtrer sur classes valides A-G
    stats = stats[stats["classe_dpe_modale"].isin(list("ABCDEFG"))].copy()

    gains = []
    classes = sorted(stats["classe_dpe_modale"].tolist())
    
    for i in range(len(classes) - 1):
        classe_basse = classes[i]       # ex : E (plus économe)
        classe_haute = classes[i + 1]   # ex : F (plus énergivore)
        
        row_basse = stats[stats["classe_dpe_modale"] == classe_basse]
        row_haute = stats[stats["classe_dpe_modale"] == classe_haute]
        
        if len(row_basse) > 0 and len(row_haute) > 0:
            conso_basse = row_basse["conso_mediane_kwh_m2"].values[0]
            conso_haute = row_haute["conso_mediane_kwh_m2"].values[0]
            
            gain_kwh_m2  = conso_haute - conso_basse
            gain_euros_m2 = gain_kwh_m2 * 0.20  # hypothèse 0.20 €/kWh
            
            gains.append({
                "transition":       f"{classe_haute} → {classe_basse}",
                "gain_kwh_m2_an":   round(gain_kwh_m2, 1),
                "gain_euros_m2_an": round(gain_euros_m2, 2),
                "gain_euros_65m2":  round(gain_euros_m2 * 65, 0),
            })

    if gains:
        gains_df = pd.DataFrame(gains)
        print(f"\n[GAINS] Gains estimés — référence année {annee_ref} :")
        print(gains_df.to_string(index=False))
    else:
        print(f"\n[GAINS] Pas assez de données pour calculer les gains par classe")
        gains_df = pd.DataFrame()
    
    return gains_df


# =============================================================================
# 6. VISUALISATION — CARTE TEMPORELLE ANIMÉE
# =============================================================================

def build_animated_map(df: pd.DataFrame) -> go.Figure:
    """
    Construit la carte temporelle animée pour GitHub Pages.

    - 1 point par adresse × année
    - Couleur   : classe DPE (palette officielle A=vert → G=rouge)
    - Taille    : consommation réelle en kWh/an
    - Animation : slider 2018 → 2024 (7 frames)

    CE QU'ON VOIT :
    - Les zones qui "refroidissent" entre 2018 et 2024 = rénovations effectives
    - Les pics de conso sur années chaudes (2022) = logements mal isolés sensibles
    - Concentration géographique des passoires F/G (souvent centres-villes anciens)

    DÉPLOIEMENT : fichier HTML autonome (~5-8 Mo) → docs/index.html → GitHub Pages
    """
    # Palette de couleurs DPE officielle française
    couleurs_dpe = {
        "A": "#009900",   # Vert foncé
        "B": "#33CC00",   # Vert clair
        "C": "#99CC00",   # Jaune-vert
        "D": "#FFCC00",   # Jaune
        "E": "#FF9900",   # Orange
        "F": "#FF3300",   # Rouge-orange
        "G": "#CC0000",   # Rouge foncé
    }

    df_map = df.dropna(subset=["lat", "lon", "conso_par_logement_kwh"]).copy()

    # Tooltip avec toutes les infos au survol
    df_map["hover"] = (
        "Adresse : "           + df_map["adresse"].astype(str)           + "<br>" +
        "Classe DPE : "        + df_map["classe_dpe_modale"].astype(str) + "<br>" +
        "Conso réelle : "      + df_map["conso_par_logement_kwh"].round(0)
                                     .apply(lambda x: f"{x:,.0f} kWh/an")   + "<br>" +
        "Conso DPE estimée : " + df_map["conso_estimee_med"].round(0)
                                     .apply(lambda x: f"{x:,.0f} kWh/an")   + "<br>" +
        "Écart : "             + df_map["ecart_pct"].apply(lambda x: f"{x:+.0f}%") + "<br>" +
        "Surface médiane : "   + df_map["surface_med"].round(0)
                                     .apply(lambda s: f"{s:.0f} m²")        + "<br>" +
        "Logements : "         + df_map["nb_logements"].astype(str)
    )

    fig = px.scatter_mapbox(
        df_map,
        lat="lat",
        lon="lon",
        color="classe_dpe_modale",
        color_discrete_map=couleurs_dpe,
        size="conso_par_logement_kwh",
        size_max=15,
        animation_frame="annee",        # ← slider temporel 2018 → 2024
        hover_name="hover",
        mapbox_style="carto-positron",  # fond sobre et lisible
        zoom=11,
        center={
            "lat": df_map["lat"].median(),
            "lon": df_map["lon"].median(),
        },
        title=(
            "Consommation électrique réelle par adresse (2018-2024)<br>"
            "<sup>Source : Enedis × ADEME DPE — Hackathon ODU 2025</sup>"
        ),
        labels={"classe_dpe_modale": "Classe DPE"},
        category_orders={"classe_dpe_modale": list("ABCDEFG")},
    )

    fig.update_layout(
        margin={"r": 0, "t": 60, "l": 0, "b": 0},
        height=700,
        legend=dict(
            title="Classe DPE",
            orientation="v",
            x=0.01, y=0.99,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="lightgrey",
            borderwidth=1,
        ),
        # Vitesse d'animation : 1500ms par frame = lisible en présentation
        updatemenus=[{
            "buttons": [{
                "args": [None, {"frame": {"duration": 1500, "redraw": True},
                                "fromcurrent": True}],
                "label": "▶ Play",
                "method": "animate",
            }],
            "type": "buttons",
            "x": 0.1,
            "y": 0,
        }],
    )

    return fig


def export_for_github_pages(fig: go.Figure, output_path: str = "docs/index.html"):
    """
    Exporte la carte en HTML autonome pour GitHub Pages.

    DÉPLOIEMENT EN 3 ÉTAPES :
    1. Commiter docs/index.html sur GitHub
    2. Settings > Pages > Source = "main branch /docs folder"
    3. URL : https://[username].github.io/[repo-name]/

    Le HTML inclut Plotly.js en inline → pas besoin de backend.
    Taille : ~5-8 Mo selon le nombre de points.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        output_path,
        include_plotlyjs=True,
        full_html=True,
        config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d"],
            "toImageButtonOptions": {"format": "png", "filename": "carte_dpe"},
        },
    )
    taille = Path(output_path).stat().st_size / 1e6
    print(f"[EXPORT] Carte exportée → {output_path} ({taille:.1f} Mo)")


# =============================================================================
# 7. PIPELINE PRINCIPAL
# =============================================================================

def run_pipeline():
    """
    Pipeline complet. Ordre d'exécution :
    1. Chargement Enedis (filtré sur DEPARTEMENTS via ints)
    2. Téléchargement DPE via API ADEME (cache local)
    3. Normalisation des noms de colonnes DPE
    4. Géocodage BAN des deux datasets (cache local)
    5. Jointure Enedis × DPE sur ban_id
    6. Calcul des métriques et gains par classe
    7. Export de la carte animée pour GitHub Pages

    TEMPS ESTIMÉ :
    - Étape 1      : ~30s
    - Étapes 2+4   : ~5-15 min au 1er lancement, ~5s ensuite (cache)
    - Étapes 5-7   : ~2 min
    → Total : ~30 min au 1er lancement, ~5 min les fois suivantes
    """

    print("=" * 60)
    print("ÉTAPE 1 — Chargement Enedis")
    print("=" * 60)
    df_enedis = load_enedis(PATH_ENEDIS)

    print("\n" + "=" * 60)
    print("ÉTAPE 2 — Téléchargement DPE via API ADEME")
    print("=" * 60)
    df_dpe = fetch_and_save_dpe()
    df_dpe = normalize_dpe(df_dpe)

    print("\n" + "=" * 60)
    print("ÉTAPE 3 — Géocodage BAN")
    print("=" * 60)

    if PATH_ENEDIS_GEO.exists():
        print("[CACHE] Géocodage Enedis déjà fait")
        df_enedis = pd.read_csv(PATH_ENEDIS_GEO, low_memory=False)
    else:
        df_enedis = geocode_batch(df_enedis, "adresse", "Enedis")
        df_enedis.to_csv(PATH_ENEDIS_GEO, index=False)
        print(f"[CACHE] Sauvegardé → {PATH_ENEDIS_GEO}")

    if PATH_DPE_GEO.exists():
        print("[CACHE] Géocodage DPE déjà fait")
        df_dpe = pd.read_csv(PATH_DPE_GEO, low_memory=False)
    else:
        df_dpe = geocode_batch(df_dpe, "adresse_ban", "DPE")
        df_dpe.to_csv(PATH_DPE_GEO, index=False)
        print(f"[CACHE] Sauvegardé → {PATH_DPE_GEO}")

    print("\n" + "=" * 60)
    print("ÉTAPE 4 — Jointure Enedis × DPE")
    print("=" * 60)
    df_joined = join_enedis_dpe(df_enedis, df_dpe)
    df_joined = compute_metrics(df_joined)
    df_joined.to_csv(PATH_OUTPUT, index=False)
    print(f"[SAVE] Résultat joint sauvegardé → {PATH_OUTPUT}")

    print("\n" + "=" * 60)
    print("ÉTAPE 5 — Gains par classe DPE")
    print("=" * 60)
    gains_df = compute_gains_par_classe(df_joined)
    gains_df.to_csv("data/gains_par_classe.csv", index=False)

    print("\n" + "=" * 60)
    print("ÉTAPE 6 — Carte temporelle animée")
    print("=" * 60)
    fig = build_animated_map(df_joined)
    export_for_github_pages(fig, "docs/index.html")

    print("\n" + "=" * 60)
    print("✓ PIPELINE TERMINÉ")
    print("=" * 60)
    print(f"  Adresses avec DPE + conso : {df_joined['adresse'].nunique():,}")
    print(f"  Années couvertes          : {sorted(df_joined['annee'].unique())}")
    print(f"  Carte GitHub Pages        : docs/index.html")
    print(f"  Données jointes           : {PATH_OUTPUT}")

    return df_joined, gains_df


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    df, gains = run_pipeline()
