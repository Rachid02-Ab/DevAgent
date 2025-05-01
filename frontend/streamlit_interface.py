import streamlit as st
import requests
import subprocess
import sys
from datetime import datetime
from io import StringIO
import contextlib

API_URL = "http://localhost:8000/run"

# Configuration de la page
st.set_page_config(
    page_title="Votre Agent Développeur", 
    page_icon="👨‍💻",
    layout="wide"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    /* Style général */
    .main {
        padding: 2rem;
    }
    
    /* En-tête */
    h1 {
        color: #1E88E5;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Zone de texte */
    .stTextArea [data-baseweb=textarea] {
        height: 150px;
        border-radius: 10px;
        border: 2px solid #E3F2FD;
        font-size: 1.1rem;
    }
    
    /* Boutons */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Boîtes de résultats */
    .success-box {
        padding: 20px;
        background-color: #E8F5E9;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .error-box {
        padding: 20px;
        background-color: #FFEBEE;
        border-radius: 10px;
        border-left: 5px solid #C62828;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .info-box {
        padding: 20px;
        background-color: #E3F2FD;
        border-radius: 10px;
        border-left: 5px solid #1565C0;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 20px;
        background-color: #F5F5F5;
        border-radius: 10px;
        margin-top: 2rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        font-weight: 500;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #F8F9FA;
    }
    </style>
""", unsafe_allow_html=True)

@contextlib.contextmanager
def capture_output():
    new_out = StringIO()
    old_out = sys.stdout
    try:
        sys.stdout = new_out
        yield new_out
    finally:
        sys.stdout = old_out

def execute_locally(code: str):
    """Exécute le code Python localement et capture la sortie"""
    try:
        with capture_output() as out:
            exec(code, {'__name__': '__main__'})
        return out.getvalue(), None
    except Exception as e:
        return None, str(e)

st.title("👨‍💻 Votre Agent Développeur")
st.caption("Votre assistant personnel pour la génération et l'exécution de code Python")

# Barre latérale
with st.sidebar:
    st.header("⚙️ Paramètres")
    execution_mode = st.radio(
        "Mode d'exécution",
        ["Automatique", "Manuel"],
        help="Choisissez si le code s'exécute automatiquement ou après validation"
    )
    debug_mode = st.checkbox("Mode debug", help="Afficher les informations de débogage")
    api_url = st.text_input("URL de l'API", API_URL)
    st.markdown("---")
    st.markdown("**Auteur :** Rachid Abounnaim")

# Section principale
tab1, tab2 = st.tabs(["📝 Nouvelle tâche", "📚 Historique"])

with tab1:
    with st.form("formulaire"):
        instruction = st.text_area(
            "📝 Tâche à coder", 
            placeholder="Ex: Crée une fonction qui trie une liste",
            height=200
        )
        
        submitted = st.form_submit_button("🚀 Lancer l'agent", use_container_width=True)

    if submitted and instruction:
        with st.spinner("🧠 L'agent travaille sur votre demande..."):
            try:
                start_time = datetime.now()
                response = requests.post(api_url, json={"instruction": instruction})
                response.raise_for_status()
                data = response.json()
                processing_time = (datetime.now() - start_time).total_seconds()
                
                st.markdown(f"""
                <div class="success-box">
                    ✅ Tâche complétée en {processing_time:.2f} secondes
                </div>
                """, unsafe_allow_html=True)
                
                # Onglets résultats
                result_tab1, result_tab2, result_tab3 = st.tabs([
                    "📄 Code", 
                    "🔍 Résultat API", 
                    "▶️ Exécution Locale"
                ])
                
                with result_tab1:
                    st.code(data["code"], language="python")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Télécharger", 
                            data["full_result"], 
                            file_name="result.py",
                            use_container_width=True
                        )
                    with col2:
                        if st.button("📋 Copier", use_container_width=True):
                            st.session_state.clipboard = data["code"]
                            st.toast("Code copié!", icon="📋")
                
                with result_tab2:
                    st.code(data["output"], language="markdown")
                
                with result_tab3:
                    if execution_mode == "Automatique" or st.button("Exécuter localement"):
                        output, error = execute_locally(data["code"])
                        if error:
                            st.error(f"Erreur d'exécution:\n{error}")
                        else:
                            st.success("Sortie d'exécution:")
                            st.code(output, language="markdown")
                
                # Sauvegarde historique
                if "history" not in st.session_state:
                    st.session_state.history = []
                
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "instruction": instruction,
                    "code": data["code"],
                    "output": data["output"]
                })
                
            except requests.exceptions.RequestException as e:
                st.error(f"Erreur de connexion: {str(e)}")
            except Exception as e:
                st.error(f"Erreur inattendue: {str(e)}")

with tab2:
    if "history" not in st.session_state or not st.session_state.history:
        st.info("Aucun historique disponible")
    else:
        st.markdown("## 📚 Historique")
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"{item['timestamp']} - {item['instruction'][:50]}..."):
                st.code(item["code"], language="python")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Réexécuter #{i+1}", key=f"replay_{i}"):
                        st.session_state.replay_instruction = item["instruction"]
                        st.rerun()
                with col2:
                    if st.button(f"Supprimer #{i+1}", key=f"delete_{i}"):
                        del st.session_state.history[i]
                        st.rerun()

# Gestion réexécution
if "replay_instruction" in st.session_state:
    instruction = st.session_state.replay_instruction
    del st.session_state.replay_instruction
    st.rerun()

# Footer
st.markdown("---")
st.markdown('<div class="footer">Développé par <strong>Rachid Abounnaim</strong></div>', 
            unsafe_allow_html=True)