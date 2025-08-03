"""API FastAPI principal para o sistema de análise de crédito."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import get_settings
from .graph.credit_analysis_graph import credit_analysis_graph
from .models.schemas import CreditAnalysisRequest, CreditAnalysisResponse

# Configurar settings
settings = get_settings()

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)

# Criar aplicação FastAPI
app = FastAPI(
    title="Orquestra de Agentes - Análise de Crédito",
    description="Sistema multi-agente para análise de risco de crédito de PMEs brasileiras",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logger.add(
    "logs/api.log",
    rotation="1 day",
    retention="7 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da aplicação."""
    logger.info("Iniciando Orquestra de Agentes API")
    
    # Verificar configurações críticas
    if not settings.openai_api_key and not settings.anthropic_api_key:
        logger.warning("Nenhuma API key de LLM configurada")
    
    # Criar diretórios necessários
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs(settings.vector_store_path, exist_ok=True)
    
    logger.info("API inicializada com sucesso")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento da aplicação."""
    logger.info("Encerrando Orquestra de Agentes API")


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Endpoint raiz com informações da API."""
    return {
        "message": "Orquestra de Agentes - Sistema de Análise de Crédito",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/analyze-credit", response_model=CreditAnalysisResponse)
@limiter.limit(f"{settings.rate_limit_requests}/hour")
async def analyze_credit(
    request,  # Necessário para rate limiting
    cnpj: str = Form(..., description="CNPJ da empresa (14 dígitos)"),
    requested_amount: Optional[float] = Form(None, description="Valor de crédito solicitado"),
    purpose: Optional[str] = Form(None, description="Finalidade do crédito"),
    files: List[UploadFile] = File(default=[], description="Documentos financeiros")
):
    """
    Analisa risco de crédito para uma empresa.
    
    Aceita CNPJ e documentos financeiros, retorna análise completa.
    """
    try:
        # Validar CNPJ
        cnpj_clean = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj_clean) != 14:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ deve ter 14 dígitos"
            )
        
        # Gerar ID único da solicitação
        request_id = str(uuid.uuid4())
        
        logger.info(f"Nova solicitação de análise: {request_id} para CNPJ {cnpj_clean}")
        
        # Processar arquivos uploadados
        documents = []
        for file in files:
            # Validar tipo de arquivo
            if not any(file.filename.lower().endswith(ext) for ext in settings.allowed_file_types):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tipo de arquivo não suportado: {file.filename}"
                )
            
            # Validar tamanho
            file_content = await file.read()
            if len(file_content) > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Arquivo muito grande: {file.filename}"
                )
            
            documents.append({
                'filename': file.filename,
                'content': file_content,
                'uploaded_at': datetime.now().isoformat()
            })
        
        logger.info(f"Processando {len(documents)} documentos para {request_id}")
        
        # Executar análise usando o grafo
        final_state = await credit_analysis_graph.analyze_credit(
            cnpj=cnpj_clean,
            documents=documents,
            request_id=request_id
        )
        
        # Construir resposta
        response = CreditAnalysisResponse(
            request_id=request_id,
            cnpj=cnpj_clean,
            company_data=final_state.company_data,
            web_search_results=final_state.web_search_results,
            document_analysis=final_state.document_analysis,
            risk_analysis=final_state.risk_analysis,
            quality_validation=final_state.quality_validation,
            processing_status="completed",
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        logger.info(f"Análise concluída para {request_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na análise de crédito: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor durante análise"
        )


@app.get("/graph-info")
async def get_graph_info():
    """Retorna informações sobre o grafo de processamento."""
    return {
        "description": "Grafo de análise de crédito usando LangGraph",
        "agents": [
            "DataGatherer - Coleta dados públicos",
            "DocumentAnalyst - Análise de documentos com RAG",
            "RiskAnalyst - Análise consolidada de risco",
            "QualityAssurance - Validação e controle de qualidade"
        ],
        "flow": credit_analysis_graph.get_graph_visualization()
    }


@app.get("/config")
async def get_config():
    """Retorna configurações públicas da aplicação."""
    return {
        "llm_provider": settings.llm_provider,
        "environment": settings.environment,
        "max_file_size_mb": settings.max_file_size // (1024 * 1024),
        "allowed_file_types": settings.allowed_file_types,
        "rate_limit": f"{settings.rate_limit_requests} requests/hour"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas."""
    logger.error(f"Erro não tratado: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor"}
    )


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=settings.environment == "development"
    )