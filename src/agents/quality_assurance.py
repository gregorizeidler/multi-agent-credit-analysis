"""Agente responsável por validação e controle de qualidade."""

from typing import Dict

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from ..models.schemas import AgentState, QualityStatus, QualityValidation
from .base_agent import BaseAgent


class QualityAssuranceAgent(BaseAgent):
    """
    Agente especializado em validação e controle de qualidade.
    
    Responsabilidades:
    - Validar consistência entre dados brutos e análise final
    - Verificar se a lógica de recomendação está coerente
    - Identificar possíveis "alucinações" ou inconsistências
    - Gerar feedback para correções quando necessário
    """
    
    def __init__(self):
        super().__init__("QualityAssurance")
    
    async def execute(self, state: AgentState) -> AgentState:
        """Executa a validação de qualidade."""
        try:
            self.add_processing_note(state, "Iniciando validação de qualidade")
            
            if not state.risk_analysis:
                self.add_processing_note(state, "Nenhuma análise de risco encontrada para validar")
                return state
            
            # Executar verificações de consistência
            consistency_checks = self._perform_consistency_checks(state)
            
            # Determinar status geral
            status = self._determine_quality_status(consistency_checks)
            
            # Gerar feedback se necessário
            feedback = None
            if status == QualityStatus.REJECTED:
                feedback = await self._generate_feedback(state, consistency_checks)
            
            # Notas de validação
            validation_notes = self._generate_validation_notes(consistency_checks)
            
            # Criar validação
            quality_validation = QualityValidation(
                status=status,
                consistency_checks=consistency_checks,
                feedback=feedback,
                validation_notes=validation_notes
            )
            
            state.quality_validation = quality_validation
            self.add_processing_note(state, f"Validação concluída: {status.value}")
            
            return state
            
        except Exception as e:
            return await self.handle_error(state, e)
    
    def _perform_consistency_checks(self, state: AgentState) -> Dict[str, bool]:
        """Executa verificações de consistência."""
        checks = {}
        
        # 1. Verificar se há dados básicos da empresa
        checks['company_data_available'] = state.company_data is not None
        
        # 2. Verificar consistência de CNPJ
        if state.company_data:
            cnpj_clean = ''.join(filter(str.isdigit, state.cnpj))
            company_cnpj_clean = ''.join(filter(str.isdigit, state.company_data.cnpj))
            checks['cnpj_consistency'] = cnpj_clean == company_cnpj_clean
        else:
            checks['cnpj_consistency'] = False
        
        # 3. Verificar se análise de risco existe
        checks['risk_analysis_present'] = state.risk_analysis is not None
        
        # 4. Verificar se scores estão em faixas válidas
        if state.risk_analysis:
            ra = state.risk_analysis
            checks['scores_in_valid_range'] = (
                0 <= ra.financial_health_score <= 10 and
                0 <= ra.non_financial_risk_score <= 10 and
                0 <= ra.overall_risk_score <= 10
            )
        else:
            checks['scores_in_valid_range'] = False
        
        # 5. Verificar consistência entre scores e recomendação
        checks['recommendation_logic_consistent'] = self._check_recommendation_logic(state)
        
        # 6. Verificar se há evidências para fatores listados
        checks['factors_have_evidence'] = self._check_factors_evidence(state)
        
        # 7. Verificar se análise textual faz sentido
        checks['analysis_text_quality'] = self._check_analysis_text_quality(state)
        
        # 8. Verificar disponibilidade de dados financeiros
        checks['financial_data_available'] = self._check_financial_data_availability(state)
        
        return checks
    
    def _check_recommendation_logic(self, state: AgentState) -> bool:
        """Verifica se a recomendação está logicamente consistente com os scores."""
        if not state.risk_analysis:
            return False
        
        ra = state.risk_analysis
        
        # Regras de consistência
        if ra.overall_risk_score >= 7.5 and ra.recommendation.value != 'approve':
            return False
        
        if ra.overall_risk_score <= 4.0 and ra.recommendation.value != 'reject':
            return False
        
        if ra.financial_health_score <= 2.0 and ra.recommendation.value == 'approve':
            return False
        
        if ra.non_financial_risk_score <= 3.0 and ra.recommendation.value == 'approve':
            return False
        
        return True
    
    def _check_factors_evidence(self, state: AgentState) -> bool:
        """Verifica se os fatores listados têm evidências nos dados coletados."""
        if not state.risk_analysis:
            return False
        
        # Verificar se fatores negativos fazem sentido
        negative_factors = state.risk_analysis.negative_factors
        
        # Se mencionou problemas financeiros, deve haver dados financeiros ruins
        financial_problems_mentioned = any(
            'roa' in factor.lower() or 'endividamento' in factor.lower() or 'liquidez' in factor.lower()
            for factor in negative_factors
        )
        
        if financial_problems_mentioned and not state.document_analysis:
            return False  # Mencionou problemas financeiros sem ter documentos
        
        # Se mencionou questões legais, deve haver evidências na busca web
        legal_issues_mentioned = any(
            'processo' in factor.lower() or 'legal' in factor.lower()
            for factor in negative_factors
        )
        
        if legal_issues_mentioned and not state.web_search_results:
            return False  # Mencionou questões legais sem busca web
        
        return True
    
    def _check_analysis_text_quality(self, state: AgentState) -> bool:
        """Verifica qualidade básica do texto de análise."""
        if not state.risk_analysis or not state.risk_analysis.analysis_text:
            return False
        
        text = state.risk_analysis.analysis_text
        
        # Verificações básicas
        if len(text) < 100:  # Muito curto
            return False
        
        if text.count('.') < 3:  # Deve ter pelo menos algumas frases
            return False
        
        # Deve mencionar a empresa ou CNPJ
        cnpj_mentioned = state.cnpj in text or (
            state.company_data and 
            state.company_data.corporate_name and 
            state.company_data.corporate_name.lower() in text.lower()
        )
        
        return cnpj_mentioned
    
    def _check_financial_data_availability(self, state: AgentState) -> bool:
        """Verifica se há dados financeiros mínimos disponíveis."""
        if not state.document_analysis:
            return False
        
        # Pelo menos um documento deve ter KPIs
        has_kpis = any(
            len(doc.financial_kpis) > 0 
            for doc in state.document_analysis
        )
        
        return has_kpis
    
    def _determine_quality_status(self, checks: Dict[str, bool]) -> QualityStatus:
        """Determina o status geral da qualidade."""
        
        # Verificações críticas que causam rejeição
        critical_checks = [
            'risk_analysis_present',
            'scores_in_valid_range',
            'recommendation_logic_consistent',
        ]
        
        # Se alguma verificação crítica falhou, rejeitar
        for check in critical_checks:
            if not checks.get(check, False):
                return QualityStatus.REJECTED
        
        # Verificações importantes
        important_checks = [
            'company_data_available',
            'cnpj_consistency',
            'factors_have_evidence',
            'analysis_text_quality',
        ]
        
        # Se mais da metade das verificações importantes falharam, rejeitar
        failed_important = sum(1 for check in important_checks if not checks.get(check, False))
        if failed_important > len(important_checks) // 2:
            return QualityStatus.REJECTED
        
        return QualityStatus.APPROVED
    
    async def _generate_feedback(self, state: AgentState, checks: Dict[str, bool]) -> str:
        """Gera feedback para correção dos problemas encontrados."""
        
        failed_checks = [check for check, passed in checks.items() if not passed]
        
        system_prompt = """Você é um revisor de qualidade de análises de risco de crédito.
        
Sua tarefa é gerar feedback construtivo para melhorar uma análise que falhou na validação.

O feedback deve:
1. Ser específico sobre os problemas encontrados
2. Sugerir correções práticas
3. Manter tom profissional e construtivo
4. Ser escrito em português
5. Ser conciso (máximo 200 palavras)"""
        
        user_prompt = f"""Uma análise de risco falhou nas seguintes verificações de qualidade:

Verificações que falharam:
{', '.join(failed_checks)}

Dados disponíveis:
- Dados da empresa: {'Sim' if state.company_data else 'Não'}
- Documentos analisados: {len(state.document_analysis) if state.document_analysis else 0}
- Resultados web: {len(state.web_search_results) if state.web_search_results else 0}
- Análise de risco: {'Sim' if state.risk_analysis else 'Não'}

Gere feedback específico para corrigir estes problemas."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar feedback: {e}")
            return f"Verificações que falharam: {', '.join(failed_checks)}. Favor revisar a análise considerando estes pontos."
    
    def _generate_validation_notes(self, checks: Dict[str, bool]) -> list[str]:
        """Gera notas explicativas sobre a validação."""
        notes = []
        
        passed_count = sum(checks.values())
        total_count = len(checks)
        
        notes.append(f"Verificações de qualidade: {passed_count}/{total_count} aprovadas")
        
        # Adicionar notas específicas para verificações importantes
        if not checks.get('company_data_available', True):
            notes.append("Dados da empresa não disponíveis - pode afetar qualidade da análise")
        
        if not checks.get('financial_data_available', True):
            notes.append("Dados financeiros limitados - análise baseada em informações públicas")
        
        if checks.get('recommendation_logic_consistent', True):
            notes.append("Lógica de recomendação consistente com scores calculados")
        
        if checks.get('analysis_text_quality', True):
            notes.append("Qualidade do texto de análise aprovada")
        
        return notes