from fastapi import FastAPI, HTTPException
from .schemas import CodeRequest, CodeResponse
from agent.graph import run_dev_agent

app = FastAPI(
    title="DevAgent API",
    description="Génère, exécute et corrige du code Python automatiquement avec Mistral + LangGraph",
    version="1.0.0"
)

@app.post("/run", response_model=CodeResponse)
def generate_code(request: CodeRequest):
    try:
        result = run_dev_agent(request.instruction)

        return CodeResponse(
            code=result["code"].strip(),
            output=result["output"].strip(),
            full_result=result["full_result"].strip()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur : {str(e)}")
