"""Modelos Pydantic para o sistema de análise de risco."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Tipos de documentos aceitos."""
    
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    OTHER = "other"


class RiskDecision(str, Enum):
    """Decisões possíveis de risco."""
    
    APPROVE = "approve"
    REVIEW = "review"
    REJECT = "reject"


class QualityStatus(str, Enum):
    """Status da validação de qualidade."""
    
    APPROVED = "approved"
    REJECTED = "rejected"


class CompanyData(BaseModel):
    """Dados públicos da empresa."""
    
    cnpj: str = Field(..., description="CNPJ da empresa")
    corporate_name: str = Field(..., description="Razão social")
    trade_name: Optional[str] = Field(None, description="Nome fantasia")
    legal_nature: Optional[str] = Field(None, description="Natureza jurídica")
    main_activity: Optional[str] = Field(None, description="Atividade principal")
    registration_date: Optional[datetime] = Field(None, description="Data de abertura")
    capital: Optional[float] = Field(None, description="Capital social")
    address: Optional[Dict[str, Any]] = Field(None, description="Endereço completo")
    legal_situation: Optional[str] = Field(None, description="Situação cadastral")
    special_situation: Optional[str] = Field(None, description="Situação especial")


class WebSearchResult(BaseModel):
    """Resultado de busca na web."""
    
    url: str = Field(..., description="URL da fonte")
    title: str = Field(..., description="Título da página")
    content: str = Field(..., description="Conteúdo relevante")
    relevance_score: float = Field(..., description="Score de relevância")
    search_type: str = Field(..., description="Tipo de busca (news, legal, etc)")


class FinancialKPI(BaseModel):
    """Indicadores financeiros extraídos."""
    
    revenue: Optional[float] = Field(None, description="Receita líquida")
    gross_profit: Optional[float] = Field(None, description="Lucro bruto")
    operating_profit: Optional[float] = Field(None, description="Lucro operacional")
    net_profit: Optional[float] = Field(None, description="Lucro líquido")
    total_assets: Optional[float] = Field(None, description="Ativo total")
    total_liabilities: Optional[float] = Field(None, description="Passivo total")
    equity: Optional[float] = Field(None, description="Patrimônio líquido")
    current_assets: Optional[float] = Field(None, description="Ativo circulante")
    current_liabilities: Optional[float] = Field(None, description="Passivo circulante")
    debt_to_equity: Optional[float] = Field(None, description="Endividamento")
    roa: Optional[float] = Field(None, description="ROA")
    roe: Optional[float] = Field(None, description="ROE")
    period: str = Field(..., description="Período de referência")


class DocumentAnalysis(BaseModel):
    """Resultado da análise de documentos."""
    
    document_type: DocumentType
    financial_kpis: List[FinancialKPI]
    extracted_text_sample: str = Field(..., description="Amostra do texto extraído")
    confidence_score: float = Field(..., description="Confiança na extração")
    processing_notes: List[str] = Field(default_factory=list, description="Observações do processamento")


class RiskAnalysis(BaseModel):
    """Análise de risco consolidada."""
    
    financial_health_score: float = Field(..., ge=0, le=10, description="Score de saúde financeira (0-10)")
    non_financial_risk_score: float = Field(..., ge=0, le=10, description="Score de risco não-financeiro (0-10)")
    overall_risk_score: float = Field(..., ge=0, le=10, description="Score geral de risco (0-10)")
    positive_factors: List[str] = Field(default_factory=list, description="Fatores positivos")
    negative_factors: List[str] = Field(default_factory=list, description="Fatores negativos")
    recommendation: RiskDecision = Field(..., description="Recomendação final")
    analysis_text: str = Field(..., description="Análise detalhada em português")
    confidence_level: float = Field(..., ge=0, le=1, description="Nível de confiança")


class QualityValidation(BaseModel):
    """Validação de qualidade."""
    
    status: QualityStatus
    consistency_checks: Dict[str, bool] = Field(..., description="Verificações de consistência")
    feedback: Optional[str] = Field(None, description="Feedback para correção")
    validation_notes: List[str] = Field(default_factory=list)


class CreditAnalysisRequest(BaseModel):
    """Solicitação de análise de crédito."""
    
    cnpj: str = Field(..., pattern=r"^\d{14}$", description="CNPJ (14 dígitos)")
    documents: List[Dict[str, Union[str, bytes]]] = Field(
        default_factory=list, 
        description="Lista de documentos (filename, content)"
    )
    requested_credit_amount: Optional[float] = Field(None, description="Valor de crédito solicitado")
    purpose: Optional[str] = Field(None, description="Finalidade do crédito")


class CreditAnalysisResponse(BaseModel):
    """Resposta da análise de crédito."""
    
    request_id: str = Field(..., description="ID da solicitação")
    cnpj: str
    company_data: Optional[CompanyData] = None
    web_search_results: List[WebSearchResult] = Field(default_factory=list)
    document_analysis: List[DocumentAnalysis] = Field(default_factory=list)
    risk_analysis: Optional[RiskAnalysis] = None
    quality_validation: Optional[QualityValidation] = None
    processing_status: str = Field(..., description="Status do processamento")
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AgentState(BaseModel):
    """Estado compartilhado entre agentes no LangGraph."""
    
    request_id: str
    cnpj: str
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    company_data: Optional[CompanyData] = None
    web_search_results: List[WebSearchResult] = Field(default_factory=list)
    document_analysis: List[DocumentAnalysis] = Field(default_factory=list)
    risk_analysis: Optional[RiskAnalysis] = None
    quality_validation: Optional[QualityValidation] = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    processing_notes: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True