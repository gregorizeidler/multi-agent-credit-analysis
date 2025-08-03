"""Agente responsável por análise de risco consolidada."""

from typing import List, Optional

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from ..models.schemas import AgentState, RiskAnalysis, RiskDecision
from .base_agent import BaseAgent


class RiskAnalystAgent(BaseAgent):
    """
    Agente especializado em análise de risco de crédito.
    
    Responsabilidades:
    - Consolidar informações de todos os agentes anteriores
    - Analisar saúde financeira baseada em KPIs
    - Avaliar riscos não-financeiros (notícias, processos)
    - Produzir recomendação estruturada (Aprovar/Revisar/Recusar)
    """
    
    def __init__(self):
        super().__init__("RiskAnalyst")
        
        # Critérios de análise
        self.financial_thresholds = {
            'excellent': {'roa': 15, 'roe': 20, 'debt_to_equity': 0.5},
            'good': {'roa': 10, 'roe': 15, 'debt_to_equity': 1.0},
            'acceptable': {'roa': 5, 'roe': 10, 'debt_to_equity': 2.0},
            'poor': {'roa': 0, 'roe': 0, 'debt_to_equity': 3.0}
        }
    
    async def execute(self, state: AgentState) -> AgentState:
        """Executa a análise de risco consolidada."""
        try:
            self.add_processing_note(state, "Iniciando análise de risco consolidada")
            
            # Analisar saúde financeira
            financial_score, financial_factors = self._analyze_financial_health(state)
            
            # Analisar riscos não-financeiros
            non_financial_score, non_financial_factors = self._analyze_non_financial_risks(state)
            
            # Calcular score geral
            overall_score = (financial_score * 0.7) + (non_financial_score * 0.3)
            
            # Determinar recomendação
            recommendation = self._determine_recommendation(overall_score, financial_score, non_financial_score)
            
            # Gerar análise textual usando LLM
            analysis_text = await self._generate_detailed_analysis(state, financial_score, non_financial_score)
            
            # Calcular confiança
            confidence = self._calculate_confidence_level(state)
            
            # Criar análise de risco
            risk_analysis = RiskAnalysis(
                financial_health_score=financial_score,
                non_financial_risk_score=non_financial_score,
                overall_risk_score=overall_score,
                positive_factors=financial_factors['positive'] + non_financial_factors['positive'],
                negative_factors=financial_factors['negative'] + non_financial_factors['negative'],
                recommendation=recommendation,
                analysis_text=analysis_text,
                confidence_level=confidence
            )
            
            state.risk_analysis = risk_analysis
            self.add_processing_note(state, f"Análise concluída: {recommendation.value} (score: {overall_score:.1f})")
            
            return state
            
        except Exception as e:
            return await self.handle_error(state, e)
    
    def _analyze_financial_health(self, state: AgentState) -> tuple[float, dict]:
        """Analisa a saúde financeira baseada nos KPIs."""
        score = 5.0  # Score neutro
        positive_factors = []
        negative_factors = []
        
        if not state.document_analysis:
            negative_factors.append("Nenhum documento financeiro analisado")
            return 3.0, {'positive': positive_factors, 'negative': negative_factors}
        
        # Agregar todos os KPIs
        all_kpis = []
        for doc_analysis in state.document_analysis:
            all_kpis.extend(doc_analysis.financial_kpis)
        
        if not all_kpis:
            negative_factors.append("Nenhum KPI financeiro extraído")
            return 3.0, {'positive': positive_factors, 'negative': negative_factors}
        
        # Analisar KPIs mais recentes (assumindo que o último é o mais atual)
        latest_kpi = all_kpis[-1]
        
        # Análise de rentabilidade
        if latest_kpi.roa is not None:
            if latest_kpi.roa >= self.financial_thresholds['excellent']['roa']:
                score += 1.5
                positive_factors.append(f"Excelente ROA: {latest_kpi.roa}%")
            elif latest_kpi.roa >= self.financial_thresholds['good']['roa']:
                score += 1.0
                positive_factors.append(f"Bom ROA: {latest_kpi.roa}%")
            elif latest_kpi.roa >= self.financial_thresholds['acceptable']['roa']:
                score += 0.5
                positive_factors.append(f"ROA aceitável: {latest_kpi.roa}%")
            else:
                score -= 1.0
                negative_factors.append(f"ROA baixo: {latest_kpi.roa}%")
        
        # Análise de endividamento
        if latest_kpi.debt_to_equity is not None:
            if latest_kpi.debt_to_equity <= self.financial_thresholds['excellent']['debt_to_equity']:
                score += 1.0
                positive_factors.append(f"Baixo endividamento: {latest_kpi.debt_to_equity}")
            elif latest_kpi.debt_to_equity <= self.financial_thresholds['good']['debt_to_equity']:
                score += 0.5
                positive_factors.append(f"Endividamento controlado: {latest_kpi.debt_to_equity}")
            elif latest_kpi.debt_to_equity <= self.financial_thresholds['acceptable']['debt_to_equity']:
                # Score neutro
                pass
            else:
                score -= 1.5
                negative_factors.append(f"Alto endividamento: {latest_kpi.debt_to_equity}")
        
        # Análise de liquidez
        if latest_kpi.current_assets and latest_kpi.current_liabilities:
            current_ratio = latest_kpi.current_assets / latest_kpi.current_liabilities
            if current_ratio >= 1.5:
                score += 0.8
                positive_factors.append(f"Boa liquidez corrente: {current_ratio:.2f}")
            elif current_ratio >= 1.0:
                score += 0.3
                positive_factors.append(f"Liquidez adequada: {current_ratio:.2f}")
            else:
                score -= 1.0
                negative_factors.append(f"Liquidez insuficiente: {current_ratio:.2f}")
        
        # Análise de lucratividade
        if latest_kpi.net_profit and latest_kpi.revenue:
            margin = (latest_kpi.net_profit / latest_kpi.revenue) * 100
            if margin >= 10:
                score += 1.0
                positive_factors.append(f"Alta margem líquida: {margin:.1f}%")
            elif margin >= 5:
                score += 0.5
                positive_factors.append(f"Margem líquida adequada: {margin:.1f}%")
            elif margin < 0:
                score -= 1.5
                negative_factors.append(f"Empresa com prejuízo: {margin:.1f}%")
        
        # Limitar score entre 0 e 10
        score = max(0, min(10, score))
        
        return score, {'positive': positive_factors, 'negative': negative_factors}
    
    def _analyze_non_financial_risks(self, state: AgentState) -> tuple[float, dict]:
        """Analisa riscos não-financeiros baseados em dados públicos."""
        score = 7.0  # Score padrão (baixo risco)
        positive_factors = []
        negative_factors = []
        
        # Análise de dados cadastrais
        if state.company_data:
            company = state.company_data
            
            # Situação cadastral
            if company.legal_situation and 'ativa' in company.legal_situation.lower():
                positive_factors.append("Empresa com situação cadastral ativa")
            else:
                score -= 2.0
                negative_factors.append(f"Situação cadastral irregular: {company.legal_situation}")
            
            # Tempo de operação
            if company.registration_date:
                from datetime import datetime
                years_operating = (datetime.now() - company.registration_date).days / 365
                if years_operating >= 5:
                    score += 1.0
                    positive_factors.append(f"Empresa estabelecida: {years_operating:.1f} anos de operação")
                elif years_operating >= 2:
                    positive_factors.append(f"Empresa com {years_operating:.1f} anos de operação")
                else:
                    score -= 0.5
                    negative_factors.append(f"Empresa recente: {years_operating:.1f} anos")
        
        # Análise de resultados web
        legal_issues = 0
        negative_news = 0
        positive_mentions = 0
        
        for result in state.web_search_results:
            content_lower = result.content.lower()
            
            # Identificar questões legais
            legal_keywords = ['processo', 'execução', 'falência', 'recuperação judicial', 'dívida']
            if any(keyword in content_lower for keyword in legal_keywords):
                legal_issues += 1
            
            # Identificar notícias negativas
            negative_keywords = ['fraude', 'irregularidade', 'multa', 'penalidade', 'investigação']
            if any(keyword in content_lower for keyword in negative_keywords):
                negative_news += 1
            
            # Identificar menções positivas
            positive_keywords = ['prêmio', 'expansão', 'crescimento', 'inovação', 'sucesso']
            if any(keyword in content_lower for keyword in positive_keywords):
                positive_mentions += 1
        
        # Penalizar questões legais
        if legal_issues > 0:
            score -= min(legal_issues * 1.5, 3.0)
            negative_factors.append(f"Encontrados {legal_issues} indicadores de questões legais")
        
        # Penalizar notícias negativas
        if negative_news > 0:
            score -= min(negative_news * 1.0, 2.0)
            negative_factors.append(f"Encontradas {negative_news} menções negativas na mídia")
        
        # Premiar menções positivas
        if positive_mentions > 0:
            score += min(positive_mentions * 0.5, 1.0)
            positive_factors.append(f"Encontradas {positive_mentions} menções positivas")
        
        # Limitar score entre 0 e 10
        score = max(0, min(10, score))
        
        return score, {'positive': positive_factors, 'negative': negative_factors}
    
    def _determine_recommendation(self, overall_score: float, financial_score: float, non_financial_score: float) -> RiskDecision:
        """Determina a recomendação final baseada nos scores."""
        
        # Regras críticas (qualquer uma pode gerar recusa)
        if financial_score <= 2.0:
            return RiskDecision.REJECT
        
        if non_financial_score <= 3.0:
            return RiskDecision.REJECT
        
        # Regras baseadas no score geral
        if overall_score >= 7.5:
            return RiskDecision.APPROVE
        elif overall_score >= 5.5:
            return RiskDecision.REVIEW
        else:
            return RiskDecision.REJECT
    
    async def _generate_detailed_analysis(self, state: AgentState, financial_score: float, non_financial_score: float) -> str:
        """Gera análise textual detalhada usando LLM."""
        
        # Preparar contexto
        company_info = ""
        if state.company_data:
            company_info = f"""
Dados da Empresa:
- Razão Social: {state.company_data.corporate_name}
- CNPJ: {state.cnpj}
- Atividade Principal: {state.company_data.main_activity or 'Não informado'}
- Situação: {state.company_data.legal_situation or 'Não informado'}
"""
        
        financial_info = ""
        if state.document_analysis and state.document_analysis[0].financial_kpis:
            kpi = state.document_analysis[0].financial_kpis[0]
            financial_info = f"""
Indicadores Financeiros:
- Receita: {f'R$ {kpi.revenue:,.2f}' if kpi.revenue else 'Não informado'}
- Lucro Líquido: {f'R$ {kpi.net_profit:,.2f}' if kpi.net_profit else 'Não informado'}
- ROA: {f'{kpi.roa}%' if kpi.roa else 'Não calculado'}
- Endividamento: {f'{kpi.debt_to_equity}' if kpi.debt_to_equity else 'Não calculado'}
"""
        
        web_info = f"Resultados de busca web: {len(state.web_search_results)} fontes analisadas"
        
        system_prompt = """Você é um analista de risco sênior especializado em crédito para PMEs brasileiras.
        
Sua tarefa é escrever uma análise de risco clara e profissional baseada nos dados fornecidos.

A análise deve:
1. Resumir os principais pontos financeiros e não-financeiros
2. Explicar os fatores de risco identificados
3. Justificar a recomendação com base nos dados
4. Ser escrita em português claro e profissional
5. Ter entre 200-400 palavras

Foque nos aspectos mais relevantes para a decisão de crédito."""
        
        user_prompt = f"""Analise os seguintes dados e produza um relatório de análise de risco:

{company_info}

{financial_info}

{web_info}

Scores calculados:
- Saúde Financeira: {financial_score:.1f}/10
- Risco Não-Financeiro: {non_financial_score:.1f}/10

Produza uma análise detalhada explicando estes scores e os fatores que levaram à recomendação."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar análise textual: {e}")
            return f"Análise automática: Score financeiro {financial_score:.1f}/10, Score não-financeiro {non_financial_score:.1f}/10. Recomendação baseada nos indicadores calculados."
    
    def _calculate_confidence_level(self, state: AgentState) -> float:
        """Calcula o nível de confiança da análise."""
        confidence = 0.0
        
        # Confiança baseada em dados da empresa
        if state.company_data:
            confidence += 0.2
        
        # Confiança baseada em documentos
        if state.document_analysis:
            doc_confidence = sum(doc.confidence_score for doc in state.document_analysis) / len(state.document_analysis)
            confidence += doc_confidence * 0.5
        
        # Confiança baseada em dados web
        if state.web_search_results:
            confidence += min(len(state.web_search_results) / 10, 0.2)
        
        # Confiança baseada em KPIs extraídos
        total_kpis = sum(len(doc.financial_kpis) for doc in state.document_analysis)
        if total_kpis > 0:
            confidence += min(total_kpis / 5, 0.1)
        
        return min(confidence, 1.0)