"""Configurações compartilhadas para testes."""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.config import get_settings
from src.main import app
from src.models.schemas import AgentState


@pytest.fixture
def test_settings():
    """Configurações para ambiente de teste."""
    settings = get_settings()
    settings.environment = "test"
    settings.log_level = "DEBUG"
    settings.vector_store_path = tempfile.mkdtemp()
    return settings


@pytest.fixture
def client() -> Generator:
    """Cliente de teste para a API."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_cnpj() -> str:
    """CNPJ de exemplo para testes."""
    return "11222333000181"  # CNPJ fictício válido


@pytest.fixture
def sample_agent_state(sample_cnpj) -> AgentState:
    """Estado de agente de exemplo para testes."""
    return AgentState(
        request_id="test-123",
        cnpj=sample_cnpj,
        documents=[
            {
                "filename": "test_balance.pdf",
                "content": b"Mock PDF content",
                "uploaded_at": "2024-01-01T00:00:00"
            }
        ]
    )


@pytest.fixture
def mock_pdf_content() -> bytes:
    """Conteúdo mockado de PDF para testes."""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"


@pytest.fixture
def mock_company_data() -> dict:
    """Dados de empresa mockados para testes."""
    return {
        "cnpj": "11222333000181",
        "corporate_name": "Empresa Teste LTDA",
        "trade_name": "Teste Corp",
        "legal_nature": "Sociedade Limitada",
        "main_activity": "Atividades de consultoria",
        "legal_situation": "ATIVA"
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuração do ambiente de teste."""
    # Definir variáveis de ambiente de teste
    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Criar diretórios necessários
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    yield
    
    # Cleanup se necessário
    pass