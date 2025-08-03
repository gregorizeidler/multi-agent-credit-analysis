"""Grafo LangGraph para orquestração da análise de crédito."""

from typing import Dict, List

from langgraph.graph import END, StateGraph
from loguru import logger

from ..agents.data_gatherer import DataGathererAgent
from ..agents.document_analyst import DocumentAnalystAgent
from ..agents.quality_assurance import QualityAssuranceAgent
from ..agents.risk_analyst import RiskAnalystAgent
from ..models.schemas import AgentState, QualityStatus


class CreditAnalysisGraph:
    """
    Grafo LangGraph que orquestra o processo completo de análise de crédito.
    
    Fluxo:
    1. DataGatherer -> DocumentAnalyst -> RiskAnalyst -> QualityAssurance
    2. Se QA rejeitar, volta para RiskAnalyst (com feedback)
    3. Se QA aprovar, finaliza
    """
    
    def __init__(self):
        self.data_gatherer = DataGathererAgent()
        self.document_analyst = DocumentAnalystAgent()
        self.risk_analyst = RiskAnalystAgent()
        self.quality_assurance = QualityAssuranceAgent()
        
        # Construir o grafo
        self.graph = self._build_graph()
        
        logger.info("Grafo de análise de crédito inicializado")
    
    def _build_graph(self) -> StateGraph:
        """Constrói o grafo de estados usando LangGraph."""
        
        workflow = StateGraph(AgentState)
        
        # Adicionar nós (agentes)
        workflow.add_node("data_gatherer", self._data_gatherer_node)
        workflow.add_node("document_analyst", self._document_analyst_node)
        workflow.add_node("risk_analyst", self._risk_analyst_node)
        workflow.add_node("quality_assurance", self._quality_assurance_node)
        
        # Definir ponto de entrada
        workflow.set_entry_point("data_gatherer")
        
        # Definir arestas (fluxo)
        workflow.add_edge("data_gatherer", "document_analyst")
        workflow.add_edge("document_analyst", "risk_analyst")
        workflow.add_edge("risk_analyst", "quality_assurance")
        
        # Aresta condicional do QA
        workflow.add_conditional_edges(
            "quality_assurance",
            self._should_retry_analysis,
            {
                "retry": "risk_analyst",  # Volta para o analista de risco
                "finish": END             # Termina o processo
            }
        )
        
        return workflow.compile()
    
    async def _data_gatherer_node(self, state: AgentState) -> AgentState:
        """Nó do agente coletor de dados."""
        logger.info("Executando nó: DataGatherer")
        try:
            return await self.data_gatherer.execute(state)
        except Exception as e:
            logger.error(f"Erro no DataGatherer: {e}")
            raise
    
    async def _document_analyst_node(self, state: AgentState) -> AgentState:
        """Nó do agente analisador de documentos."""
        logger.info("Executando nó: DocumentAnalyst")
        try:
            return await self.document_analyst.execute(state)
        except Exception as e:
            logger.error(f"Erro no DocumentAnalyst: {e}")
            raise
    
    async def _risk_analyst_node(self, state: AgentState) -> AgentState:
        """Nó do agente analista de risco."""
        logger.info("Executando nó: RiskAnalyst")
        try:
            # Se há feedback do QA, incluir no contexto
            if state.quality_validation and state.quality_validation.feedback:
                state.processing_notes.append(f"Feedback QA: {state.quality_validation.feedback}")
                # Reset da validação para nova tentativa
                state.quality_validation = None
            
            return await self.risk_analyst.execute(state)
        except Exception as e:
            logger.error(f"Erro no RiskAnalyst: {e}")
            raise
    
    async def _quality_assurance_node(self, state: AgentState) -> AgentState:
        """Nó do agente de controle de qualidade."""
        logger.info("Executando nó: QualityAssurance")
        try:
            return await self.quality_assurance.execute(state)
        except Exception as e:
            logger.error(f"Erro no QualityAssurance: {e}")
            raise
    
    def _should_retry_analysis(self, state: AgentState) -> str:
        """
        Determina se deve tentar novamente a análise.
        
        Returns:
            "retry" se deve tentar novamente, "finish" se pode finalizar
        """
        if not state.quality_validation:
            logger.warning("Validação de qualidade não encontrada, finalizando")
            return "finish"
        
        # Se QA aprovou, finalizar
        if state.quality_validation.status == QualityStatus.APPROVED:
            logger.info("Análise aprovada pelo controle de qualidade")
            return "finish"
        
        # Se ainda há tentativas disponíveis, tentar novamente
        if state.retry_count < state.max_retries:
            logger.info(f"QA rejeitou, tentando novamente ({state.retry_count + 1}/{state.max_retries})")
            return "retry"
        
        # Máximo de tentativas excedido
        logger.warning("Máximo de tentativas excedido, finalizando com status de qualidade rejeitado")
        return "finish"
    
    async def analyze_credit(self, cnpj: str, documents: List[Dict], request_id: str) -> AgentState:
        """
        Executa análise completa de crédito.
        
        Args:
            cnpj: CNPJ da empresa
            documents: Lista de documentos para análise
            request_id: ID único da solicitação
            
        Returns:
            Estado final com todos os resultados
        """
        logger.info(f"Iniciando análise de crédito para CNPJ {cnpj} (request_id: {request_id})")
        
        # Criar estado inicial
        initial_state = AgentState(
            request_id=request_id,
            cnpj=cnpj,
            documents=documents
        )
        
        try:
            # Executar o grafo
            final_state = await self.graph.ainvoke(initial_state)
            
            logger.info(f"Análise concluída para {cnpj}")
            return final_state
            
        except Exception as e:
            logger.error(f"Erro durante análise de crédito para {cnpj}: {e}")
            raise
    
    def get_graph_visualization(self) -> str:
        """Retorna representação textual do grafo para debug."""
        return """
        Fluxo do Grafo de Análise de Crédito:
        
        [START] → DataGatherer → DocumentAnalyst → RiskAnalyst → QualityAssurance
                                                        ↑              ↓
                                                        └── retry ← [REJECTED]
                                                        
                                                    [APPROVED] → [END]
        
        Nós:
        - DataGatherer: Coleta dados públicos via CNPJ
        - DocumentAnalyst: Processa documentos com RAG
        - RiskAnalyst: Análise consolidada de risco
        - QualityAssurance: Validação e controle de qualidade
        
        Arestas Condicionais:
        - QA → retry: Se análise rejeitada e ainda há tentativas
        - QA → finish: Se análise aprovada ou máximo de tentativas
        """


# Instância singleton do grafo
credit_analysis_graph = CreditAnalysisGraph()