import re
from typing import TypedDict, Callable, Optional
from langchain_core.messages import HumanMessage
from langchain.chat_models import ChatOpenAI
from langgraph.graph import END, StateGraph
from agent.tools.python_executor import python_execution_tool


def force_utf8(text: str) -> str:
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')
    return text.encode('utf-8', errors='replace').decode('utf-8')


class AgentState(TypedDict):
    instruction: str
    code: str
    output: str
    attempts: int


def get_mistral_llm():
    return ChatOpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key="onYcoSEMsQRVRfrt7WfjQrwrMcKJ8HzE",
        model="mistral-large-latest",
        openai_api_base="https://api.mistral.ai/v1",
    )


def check_success(state: AgentState) -> str:
    output = force_utf8(str(state["output"]))
    if any(err in output for err in ["[ERREUR]", "Traceback", "Error", "Exception"]):
        return "fix_code" if state.get("attempts", 0) < 3 else END
    return END


def generate_code(state: AgentState, callback: Optional[Callable] = None, explain_mode: bool = False) -> AgentState:
    llm = get_mistral_llm()
    instruction = force_utf8(state['instruction'])
    prompt = force_utf8(f"Crée un script Python pour: {instruction}")

    if explain_mode:
        prompt += "\n\nAjoute des commentaires ligne par ligne pour expliquer chaque partie du code."

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        code = force_utf8(response.content)
    except Exception as e:
        code = f"# Erreur: {force_utf8(str(e))}"

    if callback:
        callback("generation", code)

    return {**state, "code": code}


def execute_code(state: AgentState, callback: Optional[Callable] = None) -> AgentState:
    try:
        result = str(python_execution_tool.run(state["code"]))
        result = force_utf8(result)
        if callback:
            callback("execution", result)
        return {**state, "output": result}
    except Exception as e:
        error_msg = f"[ERREUR] {force_utf8(str(e))}"
        if callback:
            callback("execution", error_msg, is_error=True)
        return {**state, "output": error_msg}


def fix_code(state: AgentState, callback: Optional[Callable] = None) -> AgentState:
    llm = get_mistral_llm()
    prompt = force_utf8(f"""
Code avec erreur:
{state['code']}

Erreur:
{state['output']}

Corrige le code en conservant la même fonctionnalité.
Retourne uniquement le code corrigé sans commentaires.
""")
    try:
        fixed_code = llm.invoke([HumanMessage(content=prompt)]).content
        fixed_code = force_utf8(fixed_code)
    except Exception as e:
        fixed_code = f"# Erreur lors de la correction: {force_utf8(str(e))}"

    if callback:
        callback("correction", fixed_code)

    return {**state, "code": fixed_code, "attempts": state.get("attempts", 0) + 1}


def build_devagent_graph(callback: Optional[Callable] = None, explain_mode: bool = False, step_by_step: bool = False):
    builder = StateGraph(AgentState)

    builder.add_node("generate_code", lambda state: generate_code(state, callback, explain_mode))
    builder.add_node("execute_code", lambda state: execute_code(state, callback))
    builder.add_node("fix_code", lambda state: fix_code(state, callback))

    builder.set_entry_point("generate_code")
    builder.add_edge("generate_code", "execute_code")
    builder.add_conditional_edges("execute_code", check_success, {
        "fix_code": "fix_code",
        END: END
    })
    builder.add_edge("fix_code", "execute_code")

    return builder.compile()


def run_dev_agent(instruction: str, callback: Optional[Callable] = None, explain_mode: bool = False, step_by_step: bool = False) -> str:
    instruction = force_utf8(instruction)
    graph = build_devagent_graph(callback, explain_mode, step_by_step)
    result = graph.invoke({
        "instruction": instruction,
        "attempts": 1,
        "code": "",
        "output": ""
    })
    return force_utf8(f"{result['code']}\n\n# Résultat d'exécution :\n{result['output']}")
