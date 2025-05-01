import pytest
from fastapi.testclient import TestClient
from main import app
from schemas import CodeRequest

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 404  # Assuming no root endpoint

def test_run_endpoint_success():
    """Test successful code generation"""
    test_request = {
        "instruction": "Fonction qui retourne 'Hello World'"
    }
    response = client.post("/run", json=test_request)
    
    assert response.status_code == 200
    assert "code" in response.json()
    assert "output" in response.json()
    assert "Hello World" in response.json()["output"] or "hello world" in response.json()["output"].lower()

def test_run_endpoint_empty_instruction():
    """Test with empty instruction"""
    response = client.post("/run", json={"instruction": ""})
    assert response.status_code == 422  # Unprocessable Entity

def test_run_endpoint_invalid_payload():
    """Test with invalid payload"""
    response = client.post("/run", json={"wrong_key": "test"})
    assert response.status_code == 422

@pytest.mark.parametrize("instruction", [
    "Fonction qui divise par zéro",
    "Import os; os.system('rm -rf /')",
    "Invalid Python code"
])
def test_run_endpoint_error_handling(instruction):
    """Test error handling with problematic instructions"""
    response = client.post("/run", json={"instruction": instruction})
    assert response.status_code == 200  # The endpoint should return 200 even if code fails
    assert "ERREUR" in response.json()["output"] or "Error" in response.json()["output"]

def test_code_response_model():
    """Test the CodeResponse model"""
    from schemas import CodeResponse
    test_data = {
        "code": "print('test')",
        "output": "test",
        "full_result": "print('test')\n\n# Résultat:\ntest"
    }
    response = CodeResponse(**test_data)
    
    assert response.code == test_data["code"]
    assert response.output == test_data["output"]
    assert response.full_result == test_data["full_result"]

def test_max_attempts_handling(monkeypatch):
    """Test that the agent stops after max attempts"""
    import main
    import config
    
    # Patch max attempts to 1 for testing
    monkeypatch.setattr(config.settings, "MAX_ATTEMPTS", 1)
    
    response = client.post("/run", json={"instruction": "Code with intentional error"})
    assert response.status_code == 200
    assert response.json()["attempts"] == 1

def test_special_characters_handling():
    """Test handling of special characters in input"""
    test_request = {
        "instruction": "Fonction avec caractères spéciaux éàç"
    }
    response = client.post("/run", json=test_request)
    
    assert response.status_code == 200
    assert "code" in response.json()