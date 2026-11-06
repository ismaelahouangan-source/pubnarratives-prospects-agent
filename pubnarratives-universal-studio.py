import streamlit as st
import requests
from bs4 import BeautifulSoup
from google import genai
import pypdf
import io

# ==============================================================================
# CONFIGURATION DE LA PAGE & STYLISATION (THÈME CLAIR PUBNARRATIVES)
# ==============================================================================
st.set_page_config(
    page_title="PubNarratives Studio | Générateur Narratif & Rythmique",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .main {
        background-color: #FDFBF7;
        color: #1C1917;
    }
    .stButton>button {
        background-color: #D97706;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.6rem 1.2rem;
    }
    .stButton>button:hover {
        background-color: #B45309;
        color: white;
    }
    .badge-universal {
        background-color: #EFEAE1;
        color: #845309;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FONCTIONS D'EXTRACTION MULTI-SOURCES
# ==============================================================================
def extraire_texte_url(url: str) -> str:
    """Extrait le texte propre depuis une URL via Jina Reader ou BeautifulSoup."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, headers=headers, timeout=10)
        if response.status_code == 200 and len(response.text) > 150:
            return response.text[:4500]
    except Exception:
        pass

    try:
        res = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(res.text, 'html.parser')
        titre = soup.find('title').get_text() if soup.find('title') else ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else ""
        paragraphes = " ".join([p.get_text().strip() for p in soup.find_all('p')[:10]])
        return f"TITRE: {titre}\nDESCRIPTION: {description}\nCONTENU: {paragraphes}"[:4000]
    except Exception as e:
        return f"Erreur lors de l'extraction de l'URL : {str(e)}"

def extraire_texte_fichier(fichier_uploade) -> str:
    """Extrait le texte brut depuis un fichier PDF ou TXT."""
    try:
        nom = fichier_uploade.name.lower()
        if nom.endswith(".txt"):
            return fichier_uploade.read().decode("utf-8")[:4500]
        elif nom.endswith(".pdf"):
            lecteur = pypdf.PdfReader(io.BytesIO(fichier_uploade.read()))
            texte_complet = []
            for page in lecteur.pages[:10]:
                extrait = page.extract_text()
                if extrait:
                    texte_complet.append(extrait)
            return "\n".join(texte_complet)[:4500]
    except Exception as e:
        return f"Erreur lors de la lecture du fichier : {str(e)}"
    return ""

# ==============================================================================
# MOTEUR DE GÉNÉRATION NARRATIVE UNIVERSELLE (GEMINI)
# ==============================================================================
def orchestrer_production_universelle(api_key: str, model_name: str, brief_source: str, type_objectif: str):
    system_prompt = f"""
    Tu es un Directeur de Création et Monteur Vidéo publicitaire et narratif d'élite.
    Tu maîtrises parfaitement le framework StoryBrand (Donald Miller) et la théorie du montage rythmique (Karen Pearlman, 'Cutting Rhythms').
    
    TON OBJECTIF :
    Prendre le brief, le texte ou la ressource fournie et le transformer en un script et un storyboard vidéo vertical (format 9:16) ultra-dynamique, captivant et clair.
    
    CE N'EST PAS NÉCESSAIREMENT DE LA VENTE DIRECTE :
    Le contenu peut être de la sensibilisation, de l'éducation, de l'inspiration, un manifeste de marque, une histoire vécue ou une réflexion percutante.
    OBJECTIF VISÉ PAR L'UTILISATEUR : {type_objectif}
    
    RÈGLES STORYBRAND (SB7) UNIVERSELLES :
    - Le spectateur/héros est au centre de l'histoire (il a une aspiration ou fait face à un défi/blocage).
    - Le problème doit toucher une dimension INTERNE (ce que le spectateur ressent : doute, confusion, isolement, surcharge, stagnation).
    - L'émetteur (la marque, l'auteur, le narrateur, l'idée centrale) intervient comme le GUIDE : avec empathie et compétence.
    - Il y a un chemin clair (un déclic, un plan, une perspective) et une transformation (du doute vers la clarté/victoire).
    
    RÈGLES DU MONTAGE RYTHMIQUE (KAREN PEARLMAN) :
    - Ne fais pas des plans uniformes. Le rythme est fait de pulsations, d'accélérations et de respirations.
    - Pour chaque cut, définis le 'Phrasé de trajectoire' :
        * COLLISION : choc visuel, rupture d'échelle, changement d'axe brutal pour susciter une prise de conscience ou une tension.
        * LINKAGE : liaison fluide d'un mouvement qui traverse la coupe (match on action) pour entraîner le regard.
    - Découpe en 7 à 10 plans rythmés (durée de 1.5s à 4.5s par plan, durée totale 45 à 60s).
    """

    user_prompt = f"""
    MATIÈRE BRUTE / BRIEF SOURCE À TRAITER :
    \"\"\"{brief_source}\"\"\"

    LIVRABLE EXIGÉ AU FORMAT PRÉCIS SUIVANT :
    =======================================================
    1. BRANDSCRIPT SB7 UNIVERSEL (Synthèse : Héros, Problème Interne, Guide, Déclic/Plan, Transformation)
    =======================================================
    2. SCRIPT VOIX OFF GLOBAL (Format 45s-60s, ~110-130 mots français, prêt pour lecture orale rythmée)
    =======================================================
    3. STORYBOARD RYTHMIQUE (Découpage plan par plan)
    Pour chaque plan :
       - PLAN N° [Timecode : ex. 00s-02s] | DURÉE : [ex. 2s]
       - RÔLE RYTHMIQUE : [Tension / Choc / Respiration / Révélation / Climax]
       - VOIX OFF : [Extrait exact du script prononcé à ce moment]
       - PHRASÉ DE TRAJECTOIRE : [COLLISION d'énergie OU LIAISON cinétique (Linkage)]
       - STOCK FOOTAGE B-ROLL : [5 à 7 mots-clés de recherche vidéo en anglais]
       - PROMPT VIDÉO IA (Anglais) : [Description cinématique 9:16 ultra-détaillée : sujet, cadrage, mouvement, éclairage]
       - SOUND DESIGN : [SFX, transition sonore, ASMR, silence ou montée en intensité]
    =======================================================
    4. DIRECTION ARTISTIQUE AUDIO & ÉNERGIE (Tempo BPM conseillé, couleur musicale, tonalité de la voix)
    """

    client = genai.Client(api_key=api_key)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    response = client.models.generate_content(
        model=model_name,
        contents=full_prompt
    )
    return response.text

# ==============================================================================
# INTERFACE UTILISATEUR
# ==============================================================================
def main():
    st.markdown('<span class="badge-universal">Moteur Universel de Contenu Narratif</span>', unsafe_allow_html=True)
    st.title("⚡ PubNarratives Studio : Script & Storyboard")
    st.markdown("Transformez n'importe quelle source (URL, brief PDF/TXT, note rédigée) en une vidéo narrative percutante et rythmée.")
    st.divider()

    cle_secrete = ""
    if "GEMINI_API_KEY" in st.secrets:
        cle_secrete = st.secrets["GEMINI_API_KEY"]

    with st.sidebar:
        st.header("🔑 Configuration")
        api_key_input = st.text_input(
            "Clé API Gemini",
            value=cle_secrete,
            type="password",
            placeholder="AIzaSy...",
            help="Récupérée automatiquement depuis st.secrets si configurée."
        )
        
        if cle_secrete and api_key_input == cle_secrete:
            st.success("✅ Clé API active via st.secrets")
            
        model_name = st.selectbox(
            "Modèle Gemini Actif",
            ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"],
            index=0
        )

        type_objectif = st.selectbox(
            "Intention du contenu",
            [
                "Persuasion & Vente de produit/service",
                "Sensibilisation & Storytelling émotionnel",
                "Éducation & Déclic philosophique",
                "Manifeste de marque / Vision",
                "Personal Branding & Post LinkedIn/Reel"
            ]
        )

    st.subheader("📥 Source du contenu")
    tab_texte, tab_url, tab_fichier = st.tabs(["📝 Texte libre / Brief", "🔗 URL de page web", "📄 Fichier (PDF ou TXT)"])
    
    brief_final = ""

    with tab_texte:
        texte_libre = st.text_area(
            "Collez votre texte, vos idées ou votre ébauche de scénario :",
            height=200,
            placeholder="Ex : Je veux raconter l'histoire d'un créateur qui a peur de se lancer..."
        )
        if texte_libre:
            brief_final = texte_libre

    with tab_url:
        url_input = st.text_input(
            "Collez le lien d'un article, d'une page de service ou d'un produit :",
            placeholder="https://exemple.com/article-ou-page"
        )
        if url_input:
            if st.button("🔍 Prévisualiser l'extraction du lien"):
                with st.spinner("Extraction en cours..."):
                    brief_final = extraire_texte_url(url_input)
                    st.text_area("Texte extrait :", value=brief_final, height=150)

    with tab_fichier:
        fichier_upload = st.file_uploader(
            "Importez un brief en fichier (.pdf ou .txt) :",
            type=["pdf", "txt"]
        )
        if fichier_upload:
            brief_final = extraire_texte_fichier(fichier_upload)
            st.success(f"Fichier '{fichier_upload.name}' chargé avec succès.")
            st.text_area("Extrait du fichier :", value=brief_final[:800] + "...", height=120)

    st.markdown("---")
    
    if st.button("🚀 Générer le Script & le Découpage Rythmique", use_container_width=True):
        api_key_finale = api_key_input.strip()
        
        if not api_key_finale:
            st.error("⚠️ Veuillez renseigner votre clé API Gemini.")
            return

        if not brief_final and url_input:
            with st.spinner("Extraction de l'URL en cours..."):
                brief_final = extraire_texte_url(url_input)

        if not brief_final or len(brief_final.strip()) < 15:
            st.warning("⚠️ Veuillez fournir une matière première (texte, URL valide ou fichier chargé).")
            return

        with st.status("🛠️ Composition narrative en cours...", expanded=True) as status:
            st.write("1. Analyse du matériau et structuration StoryBrand universelle...")
            st.write(f"2. Découpage cinétique selon Karen Pearlman via {model_name}...")
            
            try:
                resultat = orchestrer_production_universelle(
                    api_key=api_key_finale,
                    model_name=model_name,
                    brief_source=brief_final,
                    type_objectif=type_objectif
                )
                status.update(label="✅ Master narratif généré avec succès !", state="complete", expanded=False)
                
                st.subheader("🎬 Livrable Narratif & Storyboard")
                st.markdown(resultat)

                st.download_button(
                    label="💾 Télécharger le dossier complet (.txt)",
                    data=resultat,
                    file_name="PubNarratives_Universal_Script.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            except Exception as e:
                status.update(label="❌ Erreur de génération", state="error")
                st.error(f"Erreur API Gemini : {str(e)}")

if __name__ == "__main__":
    main()
