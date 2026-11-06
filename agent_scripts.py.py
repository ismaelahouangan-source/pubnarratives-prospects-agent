import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from google import genai

# ==============================================================================
# CONFIGURATION & VARIABLES D'ENVIRONNEMENT
# ==============================================================================
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
CSV_PATH = os.environ.get("PROSPECTS_CSV", "annuaire_prospects.csv")

INDEX_START = int(os.environ.get("INDEX_START", "1"))
INDEX_END = int(os.environ.get("INDEX_END", "100"))

OUTPUT_DIR = "scripts_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not API_KEY:
    raise ValueError("Variable d'environnement GEMINI_API_KEY manquante.")

client = genai.Client(api_key=API_KEY)

# ==============================================================================
# EXTRACTION DU CONTENU DE L'OFFRE (SCRAPING)
# ==============================================================================
def extraire_texte_url(url: str) -> str:
    """Extrait le texte de la page produit via Jina Reader ou BeautifulSoup."""
    if not isinstance(url, str) or not url.startswith("http"):
        return ""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. Tentative via Jina Reader
    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(jina_url, headers=headers, timeout=12)
        if resp.status_code == 200 and len(resp.text) > 150:
            return resp.text[:4000]
    except Exception:
        pass

    # 2. Fallback classique BeautifulSoup
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        titre = soup.find('title').get_text().strip() if soup.find('title') else ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc['content'].strip() if meta_desc and 'content' in meta_desc.attrs else ""
        paras = " ".join([p.get_text().strip() for p in soup.find_all('p')[:12]])
        return f"TITRE: {titre}\nDESCRIPTION: {desc}\nCONTENU: {paras}"[:3500]
    except Exception as e:
        return f"Extraction limitée de la page : {str(e)}"

# ==============================================================================
# GÉNÉRATION STORYBRAND & STORYBOARD RYTHMIQUE (PUBNARRATIVES)
# ==============================================================================
def generer_script_prospect(ligne: dict) -> str:
    nom_marque = ligne.get("Nom de la marque / entreprise", "Marque")
    niche = ligne.get("Niche", "")
    produit = ligne.get("Produit / Service phare à modéliser en vidéo", "")
    accroche = ligne.get("Angle d'accroche StoryBrand (Acte I)", "")
    url = ligne.get("URL publique de l'offre", "")

    print(f" Scraping de l'offre pour : {nom_marque} ({url})...")
    contexte_page = extraire_texte_url(url)

    brief_source = f"""
    ENTREPRISE : {nom_marque}
    NICHE : {niche}
    PRODUIT / OFFRE CIBLE : {produit}
    ACCROCHE RECOMMANDÉE (ACTE I) : {accroche}
    DONNÉES EXTRAITES DE LA PAGE :
    {contexte_page}
    """

    system_prompt = """
    Tu es un Directeur de Création et Monteur Vidéo publicitaire d'élite chez PubNarratives.
    Tu maîtrises parfaitement le framework StoryBrand (Donald Miller) et le montage rythmique (Karen Pearlman, 'Cutting Rhythms').
    
    TON OBJECTIF :
    Produire un script publicitaire vertical (9:16) ultra-percutant, conçu pour briser la glace en prospection froide (Cold DM Instagram).
    
    RÈGLES STORYBRAND (SB7) :
    - Le prospect/client final est le héros (il vit une frustration concrète au quotidien).
    - Problème interne appuyé dès les 3 premières secondes (Acte I).
    - La marque intervient comme Guide empathique et compétent avec une démonstration visuelle nette (Acte II).
    - Résolution limpide et appel à l'action court (Acte III).
    
    RÈGLES DU MONTAGE RYTHMIQUE (PEARLMAN) :
    - Découpe en 7 à 9 plans rythmés (durée 45s à 60s au total).
    - Spécifie les collisions ou linkages visuels.
    """

    user_prompt = f"""
    BRIEF DU PROSPECT :
    {brief_source}

    Rédige le dossier de production complet au format exact suivant :
    =======================================================
    1. BRANDSCRIPT SB7 (Héros, Frustration Interne, Marque Guide, Solution, Victoire)
    =======================================================
    2. SCRIPT VOIX OFF GLOBAL (45-60s, ~110-130 mots, oralisé et percutant)
    =======================================================
    3. STORYBOARD RYTHMIQUE PLAN PAR PLAN
    Pour chaque plan :
       - PLAN N° [Timecode : ex. 00s-03s] | DURÉE : [ex. 3s]
       - RÔLE RYTHMIQUE : [Tension / Collision / Respiration / Révélation / Climax]
       - VOIX OFF : [Phrase exacte prononcée]
       - PHRASÉ DE TRAJECTOIRE : [COLLISION d'énergie OU LIAISON (Linkage)]
       - B-ROLL / RECHERCHE VIDÉO : [5 à 7 mots-clés en anglais]
       - PROMPT VIDÉO IA (Anglais) : [Description cinématique 9:16 photoréaliste]
       - SOUND DESIGN : [SFX, transition, ASMR ou montée sonore]
    =======================================================
    4. ACCROCHE DIRECTE DM INSTAGRAM (1 court message personnalisé prêt à envoyer en DM Instagram pour proposer ce test vidéo).
    """

    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=f"{system_prompt}\n\n{user_prompt}"
    )
    return resp.text

# ==============================================================================
# EXECUTION DU BATCH
# ==============================================================================
def main():
    if CSV_PATH.endswith(".xlsx"):
        df = pd.read_excel(CSV_PATH)
    else:
        df = pd.read_csv(CSV_PATH)

    total_lignes = len(df)
    debut = max(1, INDEX_START)
    fin = min(total_lignes, INDEX_END)

    print(f" Démarrage de l'agent PubNarratives. Traitement des prospects {debut} à {fin} sur {total_lignes}...")

    for idx in range(debut - 1, fin):
        ligne = df.iloc[idx].to_dict()
        num = ligne.get("N°", idx + 1)
        nom_marque = re.sub(r'[^\w\-_\. ]', '_', str(ligne.get("Nom de la marque / entreprise", f"Prospect_{num}"))).strip()
        
        nom_fichier = f"{int(num):03d}_{nom_marque}.txt"
        chemin_fichier = os.path.join(OUTPUT_DIR, nom_fichier)

        if os.path.exists(chemin_fichier):
            print(f"⏭️ Prospect déjà généré : {nom_fichier}")
            continue

        print(f"\n▶️ Génération [{num}/{fin}] : {nom_marque}...")
        try:
            script_complet = generer_script_prospect(ligne)
            with open(chemin_fichier, "w", encoding="utf-8") as f:
                f.write(script_complet)
            print(f" Fichier sauvegardé : {nom_fichier}")
        except Exception as e:
            print(f"❌ Erreur sur {nom_marque} : {e}")

        # Pause de temporisation pour respecter les quotas d'API
        time.sleep(2)

    print(f"\n🎉 Lot {debut}-{fin} terminé avec succès dans '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    main()