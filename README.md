# 🤖 DevAgent — Agent LLM Python Auto-Réparateur

**DevAgent** est un agent intelligent basé sur des modèles LLM (Large Language Models) qui :
- Génère du code Python à partir d’une simple instruction en langage naturel
- Exécute automatiquement le code généré
- Corrige les erreurs si nécessaire, jusqu’à obtenir un résultat fonctionnel ✅

> ⚙️ Le projet est basé sur **Langchain**, **Streamlit**, **Mistral LLM**, et un environnement Python REPL.

---

## 🚀 Démo rapide

```bash
streamlit run app/streamlit_interface.py
```
## 🧠 Fonctionnalités
- 💬 Entrée en langage naturel

- 🤖 Génération de code avec Mistral (mistral-large-latest)

- ⚙️ Exécution Python sécurisée

- 🛠 Correction automatique des erreurs

- 🔁 3 tentatives maximum par tâche

- 🧾 Export du journal d’exécution(logs) (.txt)

- 🔍 Diff entre versions de code en cas de correction

- 🧠 Mode explicatif (commentaires ligne par ligne)

- 👣 Mode pas-à-pas pour visualiser chaque étape

## 🧩 Langchain
Utilisé pour créer un graph d’états avec 3 nœuds principaux :

- generate_code

- execute_code

- fix_code

- L’agent vérifie l’état de sortie (succès ou erreur) avant de continuer

