"""Agente responsável por analisar documentos financeiros usando RAG."""

from typing import Dict, List, Optional

from loguru import logger

from ..models.schemas import AgentState, DocumentAnalysis, DocumentType, FinancialKPI
from ..tools.document_processor import document_processor
from ..tools.vector_store import create_vector_store
from .base_agent import BaseAgent


class DocumentAnalystAgent(BaseAgent):
    """
    Agente especializado em análise de documentos financeiros.
    
    Responsabilidades:
    - Processar documentos (PDF, DOCX, imagens)
    - Extrair texto usando OCR quando necessário
    - Criar pipeline RAG para busca semântica
    - Extrair KPIs financeiros específicos
    """
    
    def __init__(self):
        super().__init__("DocumentAnalyst")
        self.vector_store = create_vector_store()
        
        # Perguntas padrão para extração de KPIs
        self.financial_questions = [
            "Qual foi a receita líquida ou faturamento líquido do período?",
            "Qual foi o lucro bruto da empresa?",
            "Qual foi o lucro operacional ou EBIT?",
            "Qual foi o lucro líquido do período?",
            "Qual é o valor do ativo total da empresa?",
            "Qual é o valor do passivo total?",
            "Qual é o patrimônio líquido da empresa?",
            "Qual é o valor do ativo circulante?",
            "Qual é o valor do passivo circulante?",
            "Qual é o nível de endividamento da empresa?",
            "Qual é o retorno sobre ativos (ROA)?",
            "Qual é o retorno sobre patrimônio (ROE)?",
        ]
    
    async def execute(self, state: AgentState) -> AgentState:
        """Executa a análise de documentos."""
        try:
            self.add_processing_note(state, f"Iniciando análise de {len(state.documents)} documentos")
            
            if not state.documents:
                self.add_processing_note(state, "Nenhum documento fornecido para análise")
                return state
            
            # Limpar vector store anterior
            self.vector_store.clear()
            
            # Processar cada documento
            for doc_info in state.documents:
                analysis = await self._analyze_document(doc_info)
                if analysis:
                    state.document_analysis.append(analysis)
            
            self.add_processing_note(state, f"Análise concluída: {len(state.document_analysis)} documentos processados")
            return state
            
        except Exception as e:
            return await self.handle_error(state, e)
    
    async def _analyze_document(self, doc_info: Dict) -> Optional[DocumentAnalysis]:
        """Analisa um documento específico."""
        try:
            filename = doc_info.get('filename', 'documento')
            content = doc_info.get('content')
            
            if not content:
                logger.warning(f"Conteúdo vazio para documento {filename}")
                return None
            
            # Processar documento
            text, doc_type = await document_processor.process_document(content, filename)
            
            if not text.strip():
                logger.warning(f"Texto vazio extraído de {filename}")
                return None
            
            # Adicionar ao vector store
            metadata = {
                'filename': filename,
                'document_type': doc_type.value,
                'processed_at': str(doc_info.get('uploaded_at', 'unknown'))
            }
            
            self.vector_store.add_document(text, metadata)
            
            # Extrair KPIs financeiros
            kpis = await self._extract_financial_kpis(text, doc_type)
            
            # Calcular score de confiança baseado na qualidade do texto
            confidence_score = self._calculate_confidence_score(text, kpis)
            
            # Notas de processamento
            processing_notes = []
            if len(text) < 500:
                processing_notes.append("Documento pequeno, pode ter informações limitadas")
            if not kpis:
                processing_notes.append("Nenhum KPI financeiro extraído automaticamente")
            
            analysis = DocumentAnalysis(
                document_type=doc_type,
                financial_kpis=kpis,
                extracted_text_sample=text[:500] + "..." if len(text) > 500 else text,
                confidence_score=confidence_score,
                processing_notes=processing_notes
            )
            
            logger.info(f"Documento {filename} analisado: tipo={doc_type}, KPIs={len(kpis)}")
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar documento {doc_info.get('filename')}: {e}")
            return None
    
    async def _extract_financial_kpis(self, text: str, doc_type: DocumentType) -> List[FinancialKPI]:
        """Extrai KPIs financeiros usando RAG e regex."""
        kpis = []
        
        try:
            # 1. Extração via RAG (busca semântica)
            rag_results = self.vector_store.extract_financial_info(self.financial_questions)
            
            # 2. Extração via regex patterns
            regex_data = document_processor.extract_financial_data(text, doc_type)
            
            # 3. Combinar e processar resultados
            combined_data = self._combine_extraction_results(rag_results, regex_data, text)
            
            # 4. Criar KPI se dados encontrados
            if combined_data:
                kpi = FinancialKPI(
                    revenue=combined_data.get('revenue'),
                    gross_profit=combined_data.get('gross_profit'),
                    operating_profit=combined_data.get('operating_profit'),
                    net_profit=combined_data.get('net_profit'),
                    total_assets=combined_data.get('total_assets'),
                    total_liabilities=combined_data.get('total_liabilities'),
                    equity=combined_data.get('equity'),
                    current_assets=combined_data.get('current_assets'),
                    current_liabilities=combined_data.get('current_liabilities'),
                    debt_to_equity=self._calculate_debt_to_equity(combined_data),
                    roa=self._calculate_roa(combined_data),
                    roe=self._calculate_roe(combined_data),
                    period=self._extract_period(text)
                )
                kpis.append(kpi)
            
        except Exception as e:
            logger.error(f"Erro na extração de KPIs: {e}")
        
        return kpis
    
    def _combine_extraction_results(self, rag_results: Dict, regex_data: Dict, text: str) -> Dict:
        """Combina resultados da busca RAG com extração regex."""
        combined = {}
        
        # Mapeamento de perguntas RAG para campos
        question_mapping = {
            "receita líquida": "revenue",
            "lucro bruto": "gross_profit",
            "lucro operacional": "operating_profit",
            "lucro líquido": "net_profit",
            "ativo total": "total_assets",
            "passivo total": "total_liabilities",
            "patrimônio líquido": "equity",
            "ativo circulante": "current_assets",
            "passivo circulante": "current_liabilities",
        }
        
        # Processar resultados RAG
        for question, chunks in rag_results.items():
            for key, field in question_mapping.items():
                if key in question.lower() and chunks:
                    # Tentar extrair valor dos chunks encontrados
                    value = self._extract_number_from_text(chunks[0])
                    if value and field not in combined:
                        combined[field] = value
        
        # Usar dados regex como fallback
        for key, value in regex_data.items():
            if key not in combined and value is not None:
                combined[key] = value
        
        return combined
    
    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """Extrai números do texto usando regex."""
        import re
        
        # Pattern para números com separadores brasileiros
        pattern = r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
        matches = re.findall(pattern, text)
        
        if matches:
            try:
                # Converter formato brasileiro para float
                value_str = matches[0].replace('.', '').replace(',', '.')
                return float(value_str)
            except ValueError:
                pass
        
        return None
    
    def _calculate_debt_to_equity(self, data: Dict) -> Optional[float]:
        """Calcula índice de endividamento."""
        total_liabilities = data.get('total_liabilities')
        equity = data.get('equity')
        
        if total_liabilities and equity and equity != 0:
            return round(total_liabilities / equity, 2)
        
        return None
    
    def _calculate_roa(self, data: Dict) -> Optional[float]:
        """Calcula ROA (Return on Assets)."""
        net_profit = data.get('net_profit')
        total_assets = data.get('total_assets')
        
        if net_profit and total_assets and total_assets != 0:
            return round((net_profit / total_assets) * 100, 2)  # Em percentual
        
        return None
    
    def _calculate_roe(self, data: Dict) -> Optional[float]:
        """Calcula ROE (Return on Equity)."""
        net_profit = data.get('net_profit')
        equity = data.get('equity')
        
        if net_profit and equity and equity != 0:
            return round((net_profit / equity) * 100, 2)  # Em percentual
        
        return None
    
    def _extract_period(self, text: str) -> str:
        """Extrai o período de referência do documento."""
        import re
        
        # Padrões para datas/períodos
        patterns = [
            r'(\d{4})',  # Ano
            r'(\d{1,2}/\d{4})',  # Mês/Ano
            r'(dezembro|novembro|outubro|setembro|agosto|julho|junho|maio|abril|março|fevereiro|janeiro)\s+(?:de\s+)?(\d{4})',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    return f"{matches[0][0]} {matches[0][1]}"
                else:
                    return matches[0]
        
        return "Período não identificado"
    
    def _calculate_confidence_score(self, text: str, kpis: List[FinancialKPI]) -> float:
        """Calcula score de confiança da análise."""
        score = 0.0
        
        # Base score por tamanho do texto
        if len(text) > 2000:
            score += 0.3
        elif len(text) > 1000:
            score += 0.2
        else:
            score += 0.1
        
        # Score por KPIs extraídos
        if kpis:
            kpi = kpis[0]
            extracted_fields = [
                kpi.revenue, kpi.gross_profit, kpi.net_profit,
                kpi.total_assets, kpi.equity
            ]
            non_null_fields = sum(1 for field in extracted_fields if field is not None)
            score += (non_null_fields / len(extracted_fields)) * 0.6
        
        # Score por palavras-chave financeiras
        financial_keywords = ['receita', 'lucro', 'ativo', 'passivo', 'patrimônio', 'balanço']
        keyword_count = sum(1 for keyword in financial_keywords if keyword in text.lower())
        score += min(keyword_count / len(financial_keywords) * 0.1, 0.1)
        
        return min(score, 1.0)  # Máximo 1.0