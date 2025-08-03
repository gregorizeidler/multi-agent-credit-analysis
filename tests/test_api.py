"""Testes para a API FastAPI."""

import io
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Testes para endpoints de health e informações."""
    
    def test_health_check(self, client: TestClient):
        """Testa endpoint de health check."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client: TestClient):
        """Testa endpoint raiz."""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    def test_graph_info(self, client: TestClient):
        """Testa endpoint de informações do grafo."""
        response = client.get("/graph-info")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "description" in data
        assert "agents" in data
        assert len(data["agents"]) == 4  # 4 agentes
    
    def test_config_endpoint(self, client: TestClient):
        """Testa endpoint de configurações."""
        response = client.get("/config")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "llm_provider" in data
        assert "environment" in data
        assert "max_file_size_mb" in data


class TestCreditAnalysis:
    """Testes para análise de crédito."""
    
    def test_analyze_credit_invalid_cnpj(self, client: TestClient):
        """Testa análise com CNPJ inválido."""
        response = client.post(
            "/analyze-credit",
            data={"cnpj": "123"}  # CNPJ muito curto
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "14 dígitos" in response.json()["detail"]
    
    def test_analyze_credit_no_files(self, client: TestClient, sample_cnpj: str):
        """Testa análise sem arquivos."""
        with patch("src.graph.credit_analysis_graph.credit_analysis_graph.analyze_credit") as mock_analyze:
            # Mock do resultado da análise
            from src.models.schemas import AgentState
            mock_state = AgentState(
                request_id="test-123",
                cnpj=sample_cnpj,
                documents=[]
            )
            mock_analyze.return_value = mock_state
            
            response = client.post(
                "/analyze-credit",
                data={"cnpj": sample_cnpj}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["cnpj"] == sample_cnpj
            assert data["processing_status"] == "completed"
    
    def test_analyze_credit_with_pdf(self, client: TestClient, sample_cnpj: str):
        """Testa análise com arquivo PDF."""
        # Criar arquivo PDF mockado
        pdf_content = b"%PDF-1.4\nMock PDF content for testing"
        pdf_file = io.BytesIO(pdf_content)
        
        with patch("src.graph.credit_analysis_graph.credit_analysis_graph.analyze_credit") as mock_analyze:
            from src.models.schemas import AgentState
            mock_state = AgentState(
                request_id="test-123",
                cnpj=sample_cnpj,
                documents=[{"filename": "test.pdf", "content": pdf_content}]
            )
            mock_analyze.return_value = mock_state
            
            response = client.post(
                "/analyze-credit",
                data={"cnpj": sample_cnpj},
                files={"files": ("test.pdf", pdf_file, "application/pdf")}
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["cnpj"] == sample_cnpj
    
    def test_analyze_credit_invalid_file_type(self, client: TestClient, sample_cnpj: str):
        """Testa análise com tipo de arquivo inválido."""
        txt_file = io.BytesIO(b"Plain text content")
        
        response = client.post(
            "/analyze-credit",
            data={"cnpj": sample_cnpj},
            files={"files": ("test.txt", txt_file, "text/plain")}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "não suportado" in response.json()["detail"]
    
    def test_analyze_credit_large_file(self, client: TestClient, sample_cnpj: str):
        """Testa análise com arquivo muito grande."""
        # Criar arquivo maior que o limite (10MB + 1 byte)
        large_content = b"x" * (10 * 1024 * 1024 + 1)
        large_file = io.BytesIO(large_content)
        
        response = client.post(
            "/analyze-credit",
            data={"cnpj": sample_cnpj},
            files={"files": ("large.pdf", large_file, "application/pdf")}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "muito grande" in response.json()["detail"]
    
    @patch("src.graph.credit_analysis_graph.credit_analysis_graph.analyze_credit")
    def test_analyze_credit_internal_error(self, mock_analyze, client: TestClient, sample_cnpj: str):
        """Testa tratamento de erro interno."""
        mock_analyze.side_effect = Exception("Erro simulado")
        
        response = client.post(
            "/analyze-credit",
            data={"cnpj": sample_cnpj}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Erro interno" in response.json()["detail"]


class TestRateLimiting:
    """Testes para rate limiting."""
    
    @pytest.mark.skip(reason="Rate limiting difícil de testar em ambiente de teste")
    def test_rate_limit_exceeded(self, client: TestClient, sample_cnpj: str):
        """Testa se rate limiting funciona."""
        # Este teste seria implementado com configuração específica
        # para rate limiting mais baixo em ambiente de teste
        pass