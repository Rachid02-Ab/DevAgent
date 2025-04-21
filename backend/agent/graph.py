import re
from typing import TypedDict, Callable, Optional, Dict, Literal
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig

from .tools.python_executor import python_execution_tool
from .llm import get_mistral_llm
from ..config import settings

class AgentState(TypedDict):
    """État de l'agent pendant l'exécution du graphe"""
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
    
    Règles:
    - Retourne uniquement le code sans explications
    - Ajoute des commentaires clairs si nécessaire
    - Respecte les bonnes pratiques PEP 8
    - Gère les cas d'erreur potentiels
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)], config=config)
        code = force_utf8(response.content)
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
    """Tente de corriger le code en fonction des erreurs d'exécution"""
    llm = get_mistral_llm()
    
    prompt = f"""
    Code avec erreur:
    {state['code']}
    
    Erreur rencontrée:
    {state['output']}
    
    Instructions:
    - Corrige le code en conservant la fonctionnalité originale
    - Explique brièvement les corrections (en commentaires)
    - Gère tous les cas d'erreur possibles
    """
    
    try:
        fixed_code = llm.invoke([HumanMessage(content=prompt)], config=config).content
        fixed_code = force_utf8(fixed_code)
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