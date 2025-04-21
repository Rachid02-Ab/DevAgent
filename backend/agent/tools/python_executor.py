from langchain_experimental.tools import PythonREPLTool

class SafePythonREPLTool(PythonREPLTool):
    def run(self, query: str) -> str:
        try:
            # Nettoyage de l'entrée et sortie
            clean_query = query.encode('utf-8', errors='replace').decode('utf-8')
            result = super().run(clean_query)
            return str(result).encode('utf-8', errors='replace').decode('utf-8')
        except Exception as e:
            return f"[ERREUR] {str(e).encode('utf-8', errors='replace').decode('utf-8')}"

python_execution_tool = SafePythonREPLTool()