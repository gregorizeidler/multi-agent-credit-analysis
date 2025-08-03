"""Agente responsável por coletar dados públicos sobre a empresa."""

from typing import List

from loguru import logger

from ..models.schemas import AgentState, CompanyData, WebSearchResult
from ..tools.cnpj_api import cnpj_client
from ..tools.web_search import web_search_tool
from .base_agent import BaseAgent


class DataGathererAgent(BaseAgent):
    """
    Agente especializado em coleta de dados públicos.
    
    Responsabilidades:
    - Consultar dados da Receita Federal via CNPJ
    - Buscar notícias e informações na web
    - Identificar processos judiciais
    - Avaliar presença online da empresa
    """
    
    def __init__(self):
        super().__init__("DataGatherer")
    
    async def execute(self, state: AgentState) -> AgentState:
        """Executa a coleta de dados públicos."""
        try:
            self.add_processing_note(state, f"Iniciando coleta de dados para CNPJ {state.cnpj}")
            
            # 1. Buscar dados da Receita Federal
            company_data = await self._get_company_data(state.cnpj)
            if company_data:
                state.company_data = company_data
                self.add_processing_note(state, "Dados da Receita Federal coletados com sucesso")
            else:
                self.add_processing_note(state, "Não foi possível obter dados da Receita Federal")
            
            # 2. Buscar informações na web
            if company_data:
                web_results = await self._search_web_information(state.cnpj, company_data)
                state.web_search_results.extend(web_results)
                self.add_processing_note(state, f"Coletados {len(web_results)} resultados de busca web")
            
            self.add_processing_note(state, "Coleta de dados concluída")
            return state
            
        except Exception as e:
            return await self.handle_error(state, e)
    
    async def _get_company_data(self, cnpj: str) -> CompanyData:
        """Obtém dados da empresa via APIs da Receita Federal."""
        try:
            company_data = await cnpj_client.get_company_data(cnpj)
            return company_data
        except Exception as e:
            logger.error(f"Erro ao buscar dados do CNPJ {cnpj}: {e}")
            raise
    
    async def _search_web_information(self, cnpj: str, company_data: CompanyData) -> List[WebSearchResult]:
        """Busca informações adicionais na web."""
        company_name = company_data.corporate_name or company_data.trade_name or ""
        
        if not company_name:
            logger.warning("Nome da empresa não disponível para busca web")
            return []
        
        all_results = []
        
        try:
            # Buscar notícias
            news_results = await web_search_tool.search_company_news(cnpj, company_name)
            all_results.extend(news_results)
            
            # Buscar questões legais
            legal_results = await web_search_tool.search_legal_issues(cnpj, company_name)
            all_results.extend(legal_results)
            
            # Buscar presença online
            presence_results = await web_search_tool.search_company_presence(cnpj, company_name)
            all_results.extend(presence_results)
            
            logger.info(f"Total de {len(all_results)} resultados web coletados")
            
        except Exception as e:
            logger.error(f"Erro na busca web: {e}")
            # Não propaga o erro para não parar o processamento
        
        return all_results