import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000/run"  # Modifier si tu déploies l'API ailleurs

# Configuration de la page
st.set_page_config(
    page_title="DevAgent Client", 
    page_icon="🤖",
    layout="wide"
)

# Style CSS personnalisé
st.markdown("""
    <style>
    .stTextArea [data-baseweb=textarea] {
        height: 150px;
    }
    .success-box {
        padding: 15px;
        background-color: #e6f7e6;
        border-radius: 5px;
        border-left: 5px solid #2e7d32;
        margin: 10px 0;
    }
    .error-box {
        padding: 15px;
        background-color: #ffebee;
        border-radius: 5px;
        border-left: 5px solid #c62828;
        margin: 10px 0;
    }
    .info-box {
        padding: 15px;
        background-color: #e3f2fd;
        border-radius: 5px;
        border-left: 5px solid #1565c0;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 DevAgent – Interface distante")
st.caption("Un assistant intelligent pour générer et exécuter du code Python")

# Barre latérale pour les paramètres
with st.sidebar:
    st.header("⚙️ Paramètres")
    execution_mode = st.radio(
        "Mode d'exécution",
        ["Automatique", "Manuel"],
        help="Choisissez si le code s'exécute automatiquement ou après validation"
    )
    debug_mode = st.checkbox("Mode debug", help="Afficher les informations de débogage")
    api_url = st.text_input("URL de l'API", API_URL, help="Modifier l'URL du endpoint API si nécessaire")

# Section principale
tab1, tab2 = st.tabs(["📝 Nouvelle tâche", "📚 Historique"])

with tab1:
    with st.form("formulaire"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            instruction = st.text_area(
                "📝 Tâche à coder", 
                placeholder="Ex: Crée une fonction qui trie une liste",
                help="Décrivez clairement la fonctionnalité souhaitée"
            )
        
        with col2:
            st.markdown("**Options avancées**")
            timeout = st.number_input("Timeout (s)", min_value=1, max_value=60, value=10)
            language = st.selectbox("Langage", ["Python", "JavaScript"], disabled=True)
        
        submitted = st.form_submit_button("🚀 Lancer DevAgent", use_container_width=True)

    if submitted and instruction:
        with st.spinner("🧠 L'agent travaille sur votre demande..."):
            try:
                start_time = datetime.now()
                response = requests.post(
                    api_url, 
                    json={"instruction": instruction},
                )
                response.raise_for_status()
                data = response.json()
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Affichage des résultats
                st.markdown(f"""
                <div class="success-box">
                    ✅ Tâche complétée en {processing_time:.2f} secondes
                </div>
                """, unsafe_allow_html=True)
                
                # Onglets pour les résultats
                result_tab1, result_tab2, result_tab3 = st.tabs(["📄 Code", "🔍 Résultat", "📊 Détails"])
                
                with result_tab1:
                    st.code(data["code"], language="python")
                    
                    # Boutons d'actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.download_button(
                            "📥 Télécharger le script", 
                            data["full_result"], 
                            file_name="result.py", 
                            mime="text/x-python",
                            use_container_width=True
                        )
                    with col2:
                        if st.button("📋 Copier dans le presse-papier", use_container_width=True):
                            st.session_state.clipboard = data["code"]
                            st.toast("Code copié dans le presse-papier!", icon="📋")
                    with col3:
                        if execution_mode == "Manuel" and st.button("▶️ Exécuter le code", use_container_width=True):
                            with st.spinner("Exécution en cours..."):
                                # Ici vous pourriez ajouter l'exécution locale du code
                                pass
                
                with result_tab2:
                    st.code(data["output"], language="markdown")
                
                with result_tab3:
                    if debug_mode:
                        st.json(data)
                    else:
                        st.warning("Activez le mode debug dans la barre latérale pour voir les détails techniques")
                
                # Sauvegarde dans l'historique
                if "history" not in st.session_state:
                    st.session_state.history = []
                
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "instruction": instruction,
                    "code": data["code"],
                    "output": data["output"]
                })
                
            except requests.exceptions.RequestException as e:
                st.markdown(f"""
                <div class="error-box">
                    ❌ Erreur de connexion: {str(e)}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                    ❌ Erreur inattendue: {str(e)}
                </div>
                """, unsafe_allow_html=True)

with tab2:
    if "history" not in st.session_state or not st.session_state.history:
        st.info("Aucun historique disponible. Exécutez des tâches pour les voir apparaître ici.")
    else:
        st.markdown("## 📚 Historique des tâches")
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"🗓 {item['timestamp']} - {item['instruction'][:50]}..."):
                st.markdown(f"**Tâche:** {item['instruction']}")
                st.code(item["code"], language="python")
                st.markdown("**Résultat:**")
                st.code(item["output"], language="markdown")
                
                if st.button(f"♻️ Réexécuter #{len(st.session_state.history)-i}", key=f"replay_{i}"):
                    st.session_state.replay_instruction = item["instruction"]
                    st.rerun()

# Gestion de la réexécution depuis l'historique
if "replay_instruction" in st.session_state:
    instruction = st.session_state.replay_instruction
    del st.session_state.replay_instruction
    st.rerun()