# Nouvelle version interactive avec exécution pas-à-pas et mode explicatif

import streamlit as st
from agent.devagent_graph import run_dev_agent
import difflib
import time
from io import StringIO
import datetime

st.set_page_config(page_title="DevAgent", page_icon="🤖", layout="centered")

# --- Initialisation des variables de session ---
if "logs" not in st.session_state:
    st.session_state.logs = []
if "previous_code" not in st.session_state:
    st.session_state.previous_code = ""
if "execution_log" not in st.session_state:
    st.session_state.execution_log = []

# --- Header ---
st.markdown("""
# 🤖 DevAgent
**Agent LLM qui génère, exécute et corrige du code Python automatiquement.**
""")

# --- Instructions utilisateur ---
with st.expander("ℹ️ Comment ça marche ?", expanded=False):
    st.markdown("""
1. Entrez une tâche en langage naturel (ex: *Crée une fonction qui calcule la factorielle*)
2. L'agent génère le code avec **Mistral**
3. Il exécute le code automatiquement
4. En cas d'erreur, il le corrige et réessaie jusqu'à succès ✅
    """)

# --- Formulaire utilisateur ---
with st.form("code_gen_form"):
    instruction = st.text_area(
        "💬 Quelle tâche souhaitez-vous automatiser en Python ?",
        placeholder="Ex: Crée une fonction pour calculer le PGCD",
        height=120
    )
    explain_mode = st.checkbox("🧠 Activer le mode explicatif (commentaires ligne par ligne)")
    step_by_step = st.checkbox("👣 Mode pas-à-pas (exécution et debug interactif)")
    submitted = st.form_submit_button("🚀 Lancer DevAgent")

# --- Callback pour chaque étape ---
def extract_error_line(error_msg: str):
    import re
    match = re.search(r'line (\d+)', error_msg)
    return int(match.group(1)) if match else None

def display_callback(step, content, is_error=False):
    content = content.strip()
    st.session_state.execution_log.append(f"[{step.upper()}]\n{content}\n")

    if step == "generation":
        lines = content.strip().splitlines()
        st.markdown("### 📄 Code généré ligne par ligne :")
        for i, line in enumerate(lines, 1):
            st.code(f"{i:02d}: {line}", language="python")
            time.sleep(0.2)
        st.session_state.previous_code = content

    elif step == "execution":
        if is_error:
            st.error("❌ Erreur détectée pendant l'exécution !")
            st.markdown("Voici l'erreur retournée :")
            st.code(content, language="python")
            error_line = extract_error_line(content)
            if error_line:
                st.markdown(f"🛑 Erreur détectée à la ligne **{error_line}** du code")
        else:
            st.success("✅ Exécution réussie")
            st.markdown("Sortie de l'exécution :")
            st.code(content, language="python")

    elif step == "correction":
        st.warning("🔧 Correction automatique appliquée")
        st.code(content, language="python")

        diff = difflib.unified_diff(
            st.session_state.previous_code.splitlines(),
            content.splitlines(),
            lineterm="",
            fromfile="Avant correction",
            tofile="Après correction"
        )
        st.markdown("#### 🔍 Différence avec la version précédente :")
        st.code("\n".join(diff), language="diff")
        st.session_state.previous_code = content

    time.sleep(1)

# --- Traitement principal ---
if submitted and instruction:
    st.session_state.logs.clear()
    st.session_state.execution_log.clear()
    with st.spinner("🤖 DevAgent travaille sur votre demande..."):
        result = run_dev_agent(
            instruction,
            callback=display_callback,
            explain_mode=explain_mode,
            step_by_step=step_by_step
        )

    st.success("✅ Agent terminé ! Résultat final :")
    st.markdown("### 🧪 Résultat d'exécution")
    st.code(result, language="python")

    # --- Téléchargement du script final ---
    st.download_button(
        label="📥 Télécharger le script Python",
        data=result,
        file_name="devagent_result.py",
        mime="text/x-python"
    )

    # --- Téléchargement du journal d'exécution ---
    log_text = "\n---\n".join(st.session_state.execution_log)
    log_name = f"devagent_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    st.download_button(
        label="📄 Télécharger le journal d'exécution",
        data=log_text,
        file_name=log_name,
        mime="text/plain"
    )

# --- Footer ---
st.markdown("---")
st.caption("✨ Projet IA agentique – LangGraph + Streamlit + Mistral • by Rachid Abounnaim")
