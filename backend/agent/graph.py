import re
from typing import TypedDict, Callable, Optional, Dict, Literal
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig

from .tools.python_executor import python_execution_tool
from .llm import get_mistral_llm
from config import settings

class AgentState(TypedDict):
    instruction: str
    code: str
    output: str
    attempts: int
    status: Literal["generating", "executing", "fixing", "completed", "failed"]

def force_utf8(text: str) -> str:
    """Normalise le texte en UTF-8 et gère les erreurs de décodage"""
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    return text.encode('utf-8', errors='replace').decode('utf-8')

def check_success(state: AgentState) -> str:
    """Détermine si l'exécution a réussi ou besoin de correction"""
    output = force_utf8(str(state["output"]))
    
    error_patterns = [
        r"\[ERREUR\]",
        r"Traceback \(most recent call last\)",
        r"Error:",
        r"Exception:",
        r"SyntaxError:",
    ]
    
    if any(re.search(pattern, output) for pattern in error_patterns):
        return "fix_code" if state.get("attempts", 0) < settings.MAX_ATTEMPTS else END
    return END

def generate_code(state: AgentState, config: Optional[RunnableConfig] = None) -> AgentState:
    """Génère du code à partir d'une instruction en langage naturel"""
    llm = get_mistral_llm()
    instruction = force_utf8(state['instruction'])
    
    prompt = f"""
    Tu es un expert Python. Génère du code pour accomplir la tâche suivante.
    Tâche: {instruction}
    
    Instructions pour la génération du code:
    
    1. Structure du code:
       - Commence par une docstring explicative
       - Organise le code de manière logique
       - Utilise des noms de variables descriptifs
    
    2. Documentation:
       - Ajoute des commentaires détaillés pour expliquer:
         * Le but de chaque fonction/classe
         * Les paramètres et leur utilisation
         * Les valeurs de retour
         * Les cas particuliers et limitations
    
    3. Gestion des erreurs:
       - Implémente une gestion d'erreurs robuste
       - Ajoute des messages d'erreur explicatifs
       - Vérifie les entrées utilisateur
    
    4. Format de réponse:
    ```python
    # === DESCRIPTION ===
    # Explication détaillée de la solution
    
    # === CODE ===
    [Le code ici avec commentaires détaillés]
    ```
    
    5. Bonnes pratiques:
       - Suis les conventions PEP 8
       - Utilise des types hints quand c'est pertinent
       - Assure la lisibilité et la maintenabilité
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)], config=config)
        code = force_utf8(response.content)
        
        # Extraction du code uniquement
        if "# === CODE ===" in code:
            code_parts = code.split("# === CODE ===")
            code = code_parts[1].strip()
            
        status = "generating"
    except Exception as e:
        code = f"# Erreur lors de la génération: {force_utf8(str(e))}"
        status = "failed"
    
    return {**state, "code": code, "status": status}

def execute_code(state: AgentState, config: Optional[RunnableConfig] = None) -> AgentState:
    """Exécute le code généré dans un environnement sécurisé"""
    try:
        result = str(python_execution_tool.run(state["code"]))
        result = force_utf8(result)
        status = "executing"
    except Exception as e:
        result = f"[ERREUR] {force_utf8(str(e))}"
        status = "failed"
    
    return {**state, "output": result, "status": status}

def fix_code(state: AgentState, config: Optional[RunnableConfig] = None) -> AgentState:
    llm = get_mistral_llm()
    
    prompt = f"""
    Code avec erreur:
    {state['code']}
    
    Erreur rencontrée:
    {state['output']}
    
    Instructions:
    1. Analyse détaillée de l'erreur:
       - Explique la cause principale de l'erreur
       - Identifie les lignes problématiques
       - Décris l'impact sur le fonctionnement du code
    
    2. Correction du code:
       - Propose une solution détaillée
       - Ajoute des commentaires explicatifs pour chaque correction
       - Implémente des vérifications pour éviter des erreurs similaires
    
    3. Format de réponse:
    ```python
    # === ANALYSE DE L'ERREUR ===
    # Explication détaillée de l'erreur et de sa cause
    
    # === CODE CORRIGÉ ===
    # Solution implémentée avec commentaires
    [Le code corrigé ici]
    ```
    
    4. Bonnes pratiques:
       - Assure-toi que le code suit PEP 8
       - Ajoute de la gestion d'erreurs appropriée
       - Maintiens la lisibilité du code
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)], config=config)
        fixed_code = force_utf8(response.content)
        
        # Extraction du code corrigé uniquement (ignore l'analyse)
        if "# === CODE CORRIGÉ ===" in fixed_code:
            code_parts = fixed_code.split("# === CODE CORRIGÉ ===")
            fixed_code = code_parts[1].strip()
        
        status = "fixing"
    except Exception as e:
        fixed_code = f"# Erreur lors de la correction: {force_utf8(str(e))}"
        status = "failed"
    
    return {
        **state, 
        "code": fixed_code, 
        "attempts": state.get("attempts", 0) + 1,
        "status": status
    }

def build_devagent_graph() -> StateGraph:
    """Construit le graphe d'exécution de l'agent"""
    workflow = StateGraph(AgentState)
    
    # Définition des nœuds
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("execute_code", execute_code)
    workflow.add_node("fix_code", fix_code)
    
    # Configuration du flux
    workflow.set_entry_point("generate_code")
    workflow.add_edge("generate_code", "execute_code")
    
    # Branche conditionnelle après exécution
    workflow.add_conditional_edges(
        "execute_code",
        check_success,
        {"fix_code": "fix_code", END: END}
    )
    
    workflow.add_edge("fix_code", "execute_code")
    
    return workflow.compile()

def run_dev_agent(
    instruction: str,
    config: Optional[RunnableConfig] = None
) -> Dict[str, str]:
    """Exécute le pipeline complet de l'agent"""
    workflow = build_devagent_graph()
    initial_state = {
        "instruction": force_utf8(instruction),
        "code": "",
        "output": "",
        "attempts": 0,
        "status": "generating"
    }
    
    result = workflow.invoke(initial_state, config=config)
    
    return {
        "code": result["code"],
        "output": result["output"],
        "full_result": f"{result['code']}\n\n# Résultat d'exécution:\n{result['output']}",
        "status": result["status"],
        "attempts": result["attempts"]
    }