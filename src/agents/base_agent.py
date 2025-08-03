"""Classe base para todos os agentes."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from loguru import logger

from ..models.schemas import AgentState


class BaseAgent(ABC):
    """Classe base para todos os agentes do sistema."""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = self._initialize_llm()
        logger.info(f"Agente {self.name} inicializado")
    
    def _initialize_llm(self):
        """Inicializa o modelo de linguagem baseado na configuração."""
        provider = os.getenv("LLM_PROVIDER", "openai").lower()
        
        if provider == "anthropic":
            return ChatAnthropic(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=0.1
            )
        else:  # Default para OpenAI
            return ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1
            )
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Executa a lógica principal do agente.
        
        Args:
            state: Estado atual do processamento
            
        Returns:
            Estado atualizado após processamento
        """
        pass
    
    def add_processing_note(self, state: AgentState, note: str) -> None:
        """Adiciona uma nota de processamento ao estado."""
        state.processing_notes.append(f"[{self.name}] {note}")
        logger.info(f"{self.name}: {note}")
    
    def should_retry(self, state: AgentState) -> bool:
        """Verifica se deve tentar novamente em caso de erro."""
        return state.retry_count < state.max_retries
    
    def increment_retry(self, state: AgentState) -> None:
        """Incrementa o contador de tentativas."""
        state.retry_count += 1
        self.add_processing_note(state, f"Tentativa {state.retry_count}/{state.max_retries}")
    
    async def handle_error(self, state: AgentState, error: Exception) -> AgentState:
        """Trata erros durante a execução."""
        error_msg = f"Erro no agente {self.name}: {str(error)}"
        logger.error(error_msg)
        self.add_processing_note(state, error_msg)
        
        if self.should_retry(state):
            self.increment_retry(state)
            logger.info(f"Tentando novamente... ({state.retry_count}/{state.max_retries})")
            return await self.execute(state)
        else:
            logger.error(f"Máximo de tentativas excedido para agente {self.name}")
            raise error