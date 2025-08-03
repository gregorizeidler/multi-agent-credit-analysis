"""Ferramentas de busca na web para coleta de informações adicionais."""

import asyncio
import os
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger
from tavily import TavilyClient

from ..models.schemas import WebSearchResult


class WebSearchTool:
    """Ferramenta de busca na web usando Tavily e scraping direto."""
    
    def __init__(self):
        self.tavily_client = None
        if os.getenv("TAVILY_API_KEY"):
            self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def search_company_news(self, cnpj: str, company_name: str) -> List[WebSearchResult]:
        """Busca notícias sobre a empresa."""
        queries = [
            f'"{company_name}" CNPJ {cnpj} notícias',
            f'"{company_name}" {cnpj} processos jurídicos',
            f'"{company_name}" site:jusbrasil.com.br',
        ]
        
        results = []
        for query in queries:
            search_results = await self._search_with_tavily(query, "news")
            results.extend(search_results)
        
        # Remove duplicatas baseado na URL
        seen_urls = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        return unique_results[:10]  # Limita a 10 resultados
    
    async def search_legal_issues(self, cnpj: str, company_name: str) -> List[WebSearchResult]:
        """Busca informações sobre processos judiciais."""
        queries = [
            f'"{company_name}" CNPJ {cnpj} processo judicial',
            f'{cnpj} site:jusbrasil.com.br',
            f'"{company_name}" execução fiscal',
            f'"{company_name}" falência recuperação judicial',
        ]
        
        results = []
        for query in queries:
            search_results = await self._search_with_tavily(query, "legal")
            results.extend(search_results)
        
        return results[:5]  # Foca nos resultados mais relevantes
    
    async def search_company_presence(self, cnpj: str, company_name: str) -> List[WebSearchResult]:
        """Busca presença online da empresa."""
        queries = [
            f'"{company_name}" site oficial',
            f'"{company_name}" linkedin',
            f'"{company_name}" reclame aqui',
        ]
        
        results = []
        for query in queries:
            search_results = await self._search_with_tavily(query, "presence")
            results.extend(search_results)
        
        return results[:5]
    
    async def _search_with_tavily(self, query: str, search_type: str) -> List[WebSearchResult]:
        """Realiza busca usando Tavily API."""
        if not self.tavily_client:
            logger.warning("Tavily API key não configurada, pulando busca")
            return []
        
        try:
            response = self.tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=5,
                include_domains=["jusbrasil.com.br", "g1.globo.com", "folha.uol.com.br", "estadao.com.br"] if search_type == "legal" else None
            )
            
            results = []
            for item in response.get("results", []):
                result = WebSearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", "")[:1000],  # Limita o conteúdo
                    relevance_score=item.get("score", 0.0),
                    search_type=search_type
                )
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Erro na busca Tavily para '{query}': {e}")
            return []
    
    async def _scrape_page(self, url: str) -> Optional[str]:
        """Faz scraping de uma página específica."""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove scripts e styles
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Pega o texto principal
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = '\n'.join(chunk for chunk in chunks if chunk)
                        
                        return text[:2000]  # Limita o texto
                    
        except Exception as e:
            logger.error(f"Erro ao fazer scraping de {url}: {e}")
            
        return None


# Singleton instance
web_search_tool = WebSearchTool()