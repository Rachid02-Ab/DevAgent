# 🤖 DevAgent — Agent LLM Python Auto-Réparateur

**DevAgent** est un agent intelligent basé sur un LLM (Large Language Models -Mistral-) qui :
- Génère du code Python à partir d’une simple instruction en langage naturel
- Exécute automatiquement le code généré
- Corrige les erreurs si nécessaire, jusqu’à obtenir un résultat fonctionnel ✅

> ⚙️ Le projet est basé sur **Langchain**, **Streamlit**, **Mistral LLM**, et un environnement Python REPL.

---

## 🚀 Démo rapide
![Demo GIF](demo/agent-demo-code.gif)

## Améliorations apportées au code

Le code original présentait plusieurs problèmes qui ont été corrigés :

1. **Division par zéro** : La fonction `calculer_salaire_moyen` ne vérifiait pas si la liste des employés était vide, risquant une erreur de division par zéro.

2. **Méthode vs attribut** : Utilisation incorrecte de `e.age_retraite` comme attribut alors qu'il s'agit d'une méthode (`e.age_retraite()`).

3. **Variable non définie** : Dans `employe_plus_ancien`, la variable `ancien` n'était pas définie si la liste était vide.

Ces corrections ont amélioré la robustesse et la fiabilité du code.


## 🧠 Fonctionnalités

- 💬 **Entrée en langage naturel**  
  Permet à l'utilisateur de fournir des instructions en langage naturel pour générer, exécuter ou corriger du code Python automatiquement.

- 🤖 **Génération de code avec Mistral (mistral-large-latest)**  
  Utilisation du modèle Mistral pour générer du code Python détaillé et documenté à partir des instructions en langage naturel de l'utilisateur.

- ⚙️ **Exécution Python sécurisée**  
  Exécution sécurisée du code généré dans un environnement contrôlé pour éviter tout risque de mauvaise manipulation ou d'erreurs potentielles.

- 🛠 **Correction automatique des erreurs**  
  Si des erreurs sont détectées dans le code généré, l'agent peut proposer une correction et exécuter à nouveau le code.

- 🔁 **3 tentatives maximum par tâche**  
  L'agent peut tenter de corriger les erreurs jusqu'à trois fois avant d'arrêter le processus.

- 🧾 **Export du journal d’exécution (logs) (.txt)**  
  Les utilisateurs peuvent exporter un fichier texte contenant les journaux détaillés de l'exécution du code, utile pour le suivi ou le débogage.

- 🔍 **Diff entre versions de code en cas de correction**  
  Un comparatif des différentes versions du code généré ou corrigé est fourni pour voir les modifications apportées à chaque étape.

- 🧠 **Mode explicatif (commentaires ligne par ligne)**  
  Le code généré est toujours accompagné de commentaires détaillés expliquant la logique derrière chaque fonction, paramètre et variable.



## 🧩 Langchain

**Langchain** est utilisé pour créer un graph d’états avec trois nœuds principaux qui gèrent l'exécution du flux de travail :

- **generate_code** : Génération du code Python à partir d'une instruction en langage naturel.
- **execute_code** : Exécution du code généré dans un environnement sécurisé.
- **fix_code** : Correction automatique des erreurs dans le code.

L'agent vérifie l’état de sortie (succès ou erreur) avant de continuer l'exécution. Voici un aperçu de la logique de l'agent :

- L'agent commence par générer du code.
- Si une erreur est détectée lors de l'exécution, il tente de corriger le code.
- Si la correction échoue après trois tentatives, l'agent termine l'exécution.

### Technologies utilisées avec Langchain :

- **Mistral (mistral-large-latest)** : Un modèle de génération de code en langage naturel, utilisé pour produire du code Python bien structuré et commenté.
- **Langchain** : Un framework permettant de définir des workflows d'agent en utilisant des graphes d'états. Il permet d'organiser les tâches (générer, exécuter, corriger) dans un flux logique.
- **Langgraph** : Permet de gérer les transitions entre les nœuds du workflow et de gérer l'état de l'agent tout au long du processus.
- **Python Executor (python_execution_tool)** : Exécute le code Python dans un environnement sécurisé et gère les erreurs d'exécution.

## 🔧 Architecture de l'Agent via FastAPI

L'agent est accessible via une API FastAPI qui permet de recevoir des requêtes HTTP et de renvoyer les résultats sous forme de réponses JSON.


