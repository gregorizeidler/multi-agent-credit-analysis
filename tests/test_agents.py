"""Testes para os agentes do sistema."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.schemas import AgentState, CompanyData, DocumentType, RiskDecision


class TestDataGathererAgent:
    """Testes para o agente coletor de dados."""
    
    @pytest.fixture
    def data_gatherer(self):
        from src.agents.data_gatherer import DataGathererAgent
        return DataGathererAgent()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, data_gatherer, sample_agent_state, mock_company_data):
        """Testa execução bem-sucedida do data gatherer."""
        with patch("src.tools.cnpj_api.cnpj_client.get_company_data") as mock_cnpj, \
             patch("src.tools.web_search.web_search_tool.search_company_news") as mock_news, \
             patch("src.tools.web_search.web_search_tool.search_legal_issues") as mock_legal, \
             patch("src.tools.web_search.web_search_tool.search_company_presence") as mock_presence:
            
            # Configurar mocks
            mock_cnpj.return_value = CompanyData(**mock_company_data)
            mock_news.return_value = []
            mock_legal.return_value = []
            mock_presence.return_value = []
            
            # Executar
            result = await data_gatherer.execute(sample_agent_state)
            
            # Verificar
            assert result.company_data is not None
            assert result.company_data.cnpj == mock_company_data["cnpj"]
            assert len(result.processing_notes) > 0
    
    @pytest.mark.asyncio
    async def test_execute_cnpj_api_failure(self, data_gatherer, sample_agent_state):
        """Testa execução quando API de CNPJ falha."""
        with patch("src.tools.cnpj_api.cnpj_client.get_company_data") as mock_cnpj:
            mock_cnpj.return_value = None
            
            result = await data_gatherer.execute(sample_agent_state)
            
            assert result.company_data is None
            assert any("não foi possível" in note.lower() for note in result.processing_notes)


class TestDocumentAnalystAgent:
    """Testes para o agente analisador de documentos."""
    
    @pytest.fixture
    def document_analyst(self):
        with patch("src.tools.vector_store.create_vector_store"):
            from src.agents.document_analyst import DocumentAnalystAgent
            return DocumentAnalystAgent()
    
    @pytest.mark.asyncio
    async def test_execute_no_documents(self, document_analyst, sample_cnpj):
        """Testa execução sem documentos."""
        state = AgentState(request_id="test", cnpj=sample_cnpj, documents=[])
        
        result = await document_analyst.execute(state)
        
        assert len(result.document_analysis) == 0
        assert any("nenhum documento" in note.lower() for note in result.processing_notes)
    
    @pytest.mark.asyncio
    async def test_analyze_document_success(self, document_analyst, mock_pdf_content):
        """Testa análise bem-sucedida de documento."""
        with patch("src.tools.document_processor.document_processor.process_document") as mock_process:
            mock_process.return_value = ("Sample financial text", DocumentType.BALANCE_SHEET)
            
            doc_info = {
                "filename": "test.pdf",
                "content": mock_pdf_content,
                "uploaded_at": "2024-01-01T00:00:00"
            }
            
            result = await document_analyst._analyze_document(doc_info)
            
            assert result is not None
            assert result.document_type == DocumentType.BALANCE_SHEET
            assert result.confidence_score > 0


class TestRiskAnalystAgent:
    """Testes para o agente analista de risco."""
    
    @pytest.fixture
    def risk_analyst(self):
        from src.agents.risk_analyst import RiskAnalystAgent
        return RiskAnalystAgent()
    
    @pytest.mark.asyncio
    async def test_execute_no_data(self, risk_analyst, sample_cnpj):
        """Testa execução sem dados."""
        state = AgentState(request_id="test", cnpj=sample_cnpj)
        
        with patch.object(risk_analyst, '_generate_detailed_analysis') as mock_analysis:
            mock_analysis.return_value = "Análise sem dados disponíveis"
            
            result = await risk_analyst.execute(state)
            
            assert result.risk_analysis is not None
            assert result.risk_analysis.recommendation in [RiskDecision.REJECT, RiskDecision.REVIEW]
    
    def test_analyze_financial_health_no_documents(self, risk_analyst, sample_agent_state):
        """Testa análise financeira sem documentos."""
        score, factors = risk_analyst._analyze_financial_health(sample_agent_state)
        
        assert score <= 5.0  # Score neutro ou baixo
        assert len(factors['negative']) > 0
    
    def test_determine_recommendation_logic(self, risk_analyst):
        """Testa lógica de determinação de recomendação."""
        # Score alto deve resultar em aprovação
        recommendation = risk_analyst._determine_recommendation(8.0, 7.0, 8.0)
        assert recommendation == RiskDecision.APPROVE
        
        # Score baixo deve resultar em rejeição
        recommendation = risk_analyst._determine_recommendation(3.0, 2.0, 4.0)
        assert recommendation == RiskDecision.REJECT
        
        # Score médio deve resultar em revisão
        recommendation = risk_analyst._determine_recommendation(6.0, 6.0, 6.0)
        assert recommendation == RiskDecision.REVIEW


class TestQualityAssuranceAgent:
    """Testes para o agente de controle de qualidade."""
    
    @pytest.fixture
    def qa_agent(self):
        from src.agents.quality_assurance import QualityAssuranceAgent
        return QualityAssuranceAgent()
    
    @pytest.mark.asyncio
    async def test_execute_no_risk_analysis(self, qa_agent, sample_agent_state):
        """Testa execução sem análise de risco."""
        result = await qa_agent.execute(sample_agent_state)
        
        assert result.quality_validation is None
        assert any("nenhuma análise" in note.lower() for note in result.processing_notes)
    
    def test_consistency_checks(self, qa_agent, sample_agent_state):
        """Testa verificações de consistência."""
        # Adicionar dados mockados
        sample_agent_state.company_data = CompanyData(
            cnpj=sample_agent_state.cnpj,
            corporate_name="Test Company"
        )
        
        from src.models.schemas import RiskAnalysis, RiskDecision
        sample_agent_state.risk_analysis = RiskAnalysis(
            financial_health_score=7.0,
            non_financial_risk_score=8.0,
            overall_risk_score=7.5,
            positive_factors=[],
            negative_factors=[],
            recommendation=RiskDecision.APPROVE,
            analysis_text="Análise de teste para empresa com CNPJ " + sample_agent_state.cnpj,
            confidence_level=0.8
        )
        
        checks = qa_agent._perform_consistency_checks(sample_agent_state)
        
        assert checks['company_data_available'] is True
        assert checks['risk_analysis_present'] is True
        assert checks['scores_in_valid_range'] is True
        assert checks['recommendation_logic_consistent'] is True
    
    def test_recommendation_logic_consistency(self, qa_agent, sample_agent_state):
        """Testa verificação de consistência da lógica de recomendação."""
        from src.models.schemas import RiskAnalysis, RiskDecision
        
        # Caso inconsistente: score alto mas recomendação de rejeição
        sample_agent_state.risk_analysis = RiskAnalysis(
            financial_health_score=8.0,
            non_financial_risk_score=9.0,
            overall_risk_score=8.5,
            positive_factors=[],
            negative_factors=[],
            recommendation=RiskDecision.REJECT,  # Inconsistente com score alto
            analysis_text="Test analysis",
            confidence_level=0.8
        )
        
        result = qa_agent._check_recommendation_logic(sample_agent_state)
        assert result is False  # Deve detectar inconsistência