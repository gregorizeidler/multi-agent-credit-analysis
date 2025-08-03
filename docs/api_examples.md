# Exemplos de Uso da API

Este documento contém exemplos práticos de como usar a API da Orquestra de Agentes.

## 🚀 Início Rápido

### 1. Health Check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

### 2. Informações da API

```bash
curl http://localhost:8000/
```

### 3. Configurações

```bash
curl http://localhost:8000/config
```

## 📋 Análise de Crédito

### Exemplo Básico (Apenas CNPJ)

```bash
curl -X POST "http://localhost:8000/analyze-credit" \
  -H "Content-Type: multipart/form-data" \
  -F "cnpj=11222333000181"
```

### Exemplo com Documentos

```bash
curl -X POST "http://localhost:8000/analyze-credit" \
  -H "Content-Type: multipart/form-data" \
  -F "cnpj=11222333000181" \
  -F "requested_amount=100000" \
  -F "purpose=Capital de giro" \
  -F "files=@balanco_2023.pdf" \
  -F "files=@dre_2023.pdf"
```

### Exemplo com Python

```python
import requests

# Preparar arquivos
files = [
    ('files', ('balanco.pdf', open('balanco.pdf', 'rb'), 'application/pdf')),
    ('files', ('dre.pdf', open('dre.pdf', 'rb'), 'application/pdf'))
]

# Dados do formulário
data = {
    'cnpj': '11222333000181',
    'requested_amount': 100000,
    'purpose': 'Expansão de negócio'
}

# Fazer requisição
response = requests.post(
    'http://localhost:8000/analyze-credit',
    data=data,
    files=files
)

# Processar resposta
if response.status_code == 200:
    result = response.json()
    print(f"Recomendação: {result['risk_analysis']['recommendation']}")
    print(f"Score: {result['risk_analysis']['overall_risk_score']}")
else:
    print(f"Erro: {response.status_code}")
    print(response.json())
```

### Exemplo com JavaScript

```javascript
const formData = new FormData();
formData.append('cnpj', '11222333000181');
formData.append('requested_amount', '100000');
formData.append('purpose', 'Capital de giro');

// Adicionar arquivos
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
    formData.append('files', file);
}

fetch('http://localhost:8000/analyze-credit', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Análise concluída:', data);
    displayResults(data);
})
.catch(error => {
    console.error('Erro:', error);
});
```

## 📊 Estrutura da Resposta

### Resposta Completa

```json
{
  "request_id": "uuid-4-string",
  "cnpj": "11222333000181",
  "company_data": {
    "cnpj": "11222333000181",
    "corporate_name": "Empresa Exemplo LTDA",
    "trade_name": "Exemplo Corp",
    "legal_situation": "ATIVA",
    "main_activity": "Atividades de consultoria",
    "registration_date": "2020-01-01T00:00:00",
    "capital": 100000.0
  },
  "web_search_results": [
    {
      "url": "https://example.com/news",
      "title": "Empresa em crescimento",
      "content": "Conteúdo da notícia...",
      "relevance_score": 0.95,
      "search_type": "news"
    }
  ],
  "document_analysis": [
    {
      "document_type": "balance_sheet",
      "financial_kpis": [
        {
          "revenue": 8500000.0,
          "net_profit": 750000.0,
          "total_assets": 4300000.0,
          "equity": 2300000.0,
          "roa": 17.44,
          "roe": 32.61,
          "debt_to_equity": 0.87,
          "period": "2023"
        }
      ],
      "confidence_score": 0.89,
      "processing_notes": []
    }
  ],
  "risk_analysis": {
    "financial_health_score": 8.2,
    "non_financial_risk_score": 7.8,
    "overall_risk_score": 8.08,
    "positive_factors": [
      "Excelente ROA: 17.4%",
      "Empresa estabelecida: 4.0 anos de operação",
      "Boa liquidez corrente: 2.08"
    ],
    "negative_factors": [
      "Endividamento moderado: 0.87"
    ],
    "recommendation": "approve",
    "analysis_text": "Análise detalhada da empresa...",
    "confidence_level": 0.85
  },
  "quality_validation": {
    "status": "approved",
    "consistency_checks": {
      "company_data_available": true,
      "cnpj_consistency": true,
      "recommendation_logic_consistent": true,
      "scores_in_valid_range": true
    },
    "validation_notes": [
      "Verificações de qualidade: 8/8 aprovadas",
      "Lógica de recomendação consistente com scores calculados"
    ]
  },
  "processing_status": "completed",
  "created_at": "2024-01-01T12:00:00",
  "completed_at": "2024-01-01T12:01:30"
}
```

## ⚠️ Tratamento de Erros

### Erro de Validação (400)

```json
{
  "detail": "CNPJ deve ter 14 dígitos"
}
```

### Erro de Arquivo (400)

```json
{
  "detail": "Tipo de arquivo não suportado: documento.txt"
}
```

### Erro Interno (500)

```json
{
  "detail": "Erro interno do servidor durante análise"
}
```

### Rate Limit (429)

```json
{
  "detail": "Rate limit exceeded: 100 requests per hour"
}
```

## 📝 Formatos de Arquivo Suportados

- **PDF** (.pdf) - Documentos financeiros
- **Word** (.docx) - Relatórios em Word
- **Imagens** (.png, .jpg, .jpeg, .tiff) - Documentos escaneados

### Limites

- **Tamanho máximo**: 10MB por arquivo
- **Total de arquivos**: Sem limite (respeitando rate limit)
- **Rate limit**: 100 requests/hora por IP

## 🔧 Configuração de Cliente

### Headers Recomendados

```http
Content-Type: multipart/form-data
User-Agent: MeuApp/1.0
```

### Timeout

- **Conexão**: 30 segundos
- **Leitura**: 120 segundos (análise pode demorar)

### Retry Policy

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "POST"],
        backoff_factor=1
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

# Uso
session = create_session()
response = session.post(url, data=data, files=files, timeout=120)
```

## 📊 Monitoramento

### Métricas Importantes

- **Response Time**: Tempo de resposta da análise
- **Success Rate**: Taxa de sucesso das análises
- **Error Rate**: Taxa de erros por tipo
- **Throughput**: Análises por hora

### Logs

Os logs podem ser acessados via Docker:

```bash
docker-compose logs -f orquestra-api
```

## 🎯 Casos de Uso

### 1. Análise Rápida (Sem Documentos)

Para triagem inicial baseada apenas em dados públicos:

```bash
curl -X POST "http://localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181"
```

### 2. Análise Completa (Com Documentos)

Para decisão final de crédito:

```bash
curl -X POST "http://localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181" \
  -F "files=@balanco.pdf" \
  -F "files=@dre.pdf" \
  -F "files=@fluxo_caixa.pdf"
```

### 3. Análise Específica (Com Contexto)

Para crédito direcionado:

```bash
curl -X POST "http://localhost:8000/analyze-credit" \
  -F "cnpj=11222333000181" \
  -F "requested_amount=500000" \
  -F "purpose=Compra de equipamentos" \
  -F "files=@documentos.pdf"
```

---

Para mais exemplos, consulte os notebooks Jupyter na pasta `notebooks/`.