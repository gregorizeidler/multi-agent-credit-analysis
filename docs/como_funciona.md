# 🎯 Como Funciona a Orquestra de Agentes

Este documento explica de forma detalhada como o sistema de análise de crédito funciona na prática.

## 🔄 **Fluxo Completo: Do CNPJ ao Relatório**

### **1. INPUT: O que entra no sistema**
```
📋 CNPJ da empresa (ex: 11.222.333/0001-81)
📄 Documentos financeiros (PDFs, Word, imagens)
💰 Valor de crédito solicitado (opcional)
🎯 Finalidade do empréstimo (opcional)
```

### **2. PROCESSAMENTO: Como os 4 agentes trabalham**

#### **🔍 Agente 1: DataGatherer (Coletor de Dados)**
```
📞 "Vou buscar tudo sobre essa empresa!"

1. Consulta CNPJ na Receita Federal
   → Razão social, situação cadastral, atividade
   → Data de abertura, capital social
   
2. Busca notícias na web (Tavily)
   → "Empresa X expandindo negócios"
   → "Processo judicial contra Empresa Y"
   
3. Verifica presença online
   → Site oficial, LinkedIn, Reclame Aqui

✅ Resultado: Perfil completo da empresa
```

#### **📄 Agente 2: DocumentAnalyst (Analisador de Documentos)**
```
📊 "Vou extrair todos os números dos documentos!"

1. Processa PDFs e documentos
   → OCR se for imagem escaneada
   → Identifica tipo: Balanço, DRE, Fluxo de Caixa
   
2. Usa RAG (busca semântica) com 12 perguntas:
   → "Qual foi a receita líquida?"
   → "Qual é o lucro operacional?"
   → "Qual o valor do ativo total?"
   
3. Extrai KPIs financeiros
   → ROA, ROE, liquidez, endividamento
   → Margem de lucro, crescimento

✅ Resultado: Indicadores financeiros estruturados
```

#### **⚡ Agente 3: RiskAnalyst (Analista de Risco)**
```
🧠 "Vou analisar tudo e dar minha recomendação!"

1. Consolida informações dos agentes anteriores
   → Dados públicos + KPIs financeiros
   
2. Calcula scores ponderados:
   → 70% Score Financeiro (baseado em KPIs)
   → 30% Score Não-Financeiro (notícias, processos)
   
3. Aplica thresholds calibrados para PMEs brasileiras:
   → ROA > 15% = Excelente
   → Endividamento < 0.5 = Baixo risco
   
4. Gera análise com LLM:
   → Texto explicativo em português
   → Recomendação: APROVAR/REVISAR/RECUSAR

✅ Resultado: Análise completa + recomendação
```

#### **🛡️ Agente 4: QualityAssurance (Controle de Qualidade)**
```
🔍 "Vou verificar se tudo faz sentido!"

1. Executa 8 verificações de consistência:
   → CNPJ bate entre fontes?
   → Score alto mas recomendação de rejeição? ❌
   → Fatores listados têm evidências nos dados?
   
2. Valida lógica de recomendação:
   → Score 8.5 + recomendação APROVAR ✅
   → Score 2.0 + recomendação APROVAR ❌
   
3. Se encontrar inconsistências:
   → Gera feedback específico
   → Manda de volta pro RiskAnalyst corrigir
   
4. Se tudo OK:
   → Aprova o relatório final

✅ Resultado: Relatório validado e consistente
```

## 🎭 **Orquestração com LangGraph**

O **LangGraph** é o "maestro" que coordena tudo:

```
📊 Estado Compartilhado (AgentState)
├── request_id: "abc-123"
├── cnpj: "11222333000181" 
├── documents: [balanco.pdf, dre.pdf]
├── company_data: {...}
├── web_search_results: [...]
├── risk_analysis: {...}
└── processing_notes: ["DataGatherer: OK", "DocumentAnalyst: 3 KPIs extraídos"]

🔄 Fluxo Condicional:
DataGatherer → DocumentAnalyst → RiskAnalyst → QualityAssurance
                                        ↑              ↓
                                   [Feedback] ← [Rejeitado]
                                   
                                   [Aprovado] → [FIM]
```

## 🔧 **Tecnologias em Ação**

### **RAG (Retrieval-Augmented Generation)**
```python
# Como funciona a extração de KPIs:

1. Documento PDF → Chunks de texto
2. Chunks → Embeddings (vetores)
3. Embeddings → Vector Store (FAISS)
4. Pergunta: "Qual a receita líquida?" → Embedding
5. Busca semântica → Chunks mais relevantes
6. LLM analisa chunks → Extrai valor exato
```

### **APIs Brasileiras Integradas**
```python
# Fallback automático entre APIs:
try:
    dados = ReceitaWS.consultar(cnpj)
except:
    dados = BrasilAPI.consultar(cnpj)  # Backup
```

### **Sistema Anti-Alucinação**
```python
# Validação cruzada:
if relatorio.diz("receita: 2M") and kpis.receita != 2000000:
    return "INCONSISTÊNCIA DETECTADA - REPROCESSAR"
```

## 🎯 **Exemplo Prático**

### **Input:**
```bash
CNPJ: 11.222.333/0001-81
Arquivo: balanco_2023.pdf
Valor: R$ 500.000
```

### **Processamento (2 minutos):**
```
🔍 DataGatherer:
   ✅ Empresa: "Tech Solutions LTDA"  
   ✅ Situação: ATIVA
   ✅ 3 anos de operação
   ✅ 2 notícias positivas encontradas

📄 DocumentAnalyst:
   ✅ PDF processado: Balanço Patrimonial
   ✅ KPIs extraídos: ROA=18%, ROE=25%, Liquidez=2.3
   ✅ Confiança: 89%

⚡ RiskAnalyst:
   ✅ Score Financeiro: 8.2/10 (ROA excelente)
   ✅ Score Não-Financeiro: 7.8/10 (empresa estabelecida)
   ✅ Score Geral: 8.0/10
   ✅ Recomendação: APROVAR

🛡️ QualityAssurance:
   ✅ 8/8 verificações aprovadas
   ✅ Lógica consistente
   ✅ Relatório APROVADO
```

### **Output:**
```json
{
  "recommendation": "APPROVE",
  "overall_risk_score": 8.0,
  "analysis": "Empresa apresenta excelentes indicadores financeiros com ROA de 18%, bem acima da média do setor. Liquidez adequada e baixo endividamento. Histórico de 3 anos sem intercorrências. Recomendamos APROVAÇÃO do crédito de R$ 500.000.",
  "confidence": 0.89
}
```

## 🚀 **Vantagens do Sistema**

### **1. Velocidade**
- Manual: 2-5 dias ⏰
- Automatizado: < 2 minutos ⚡

### **2. Consistência**  
- Manual: Varia por analista 📊
- Automatizado: Critérios padronizados 🎯

### **3. Escalabilidade**
- Manual: 1 analista = 5-10 análises/dia 👤
- Automatizado: 100+ análises/hora 🤖

### **4. Qualidade**
- Manual: Suscetível a erros humanos ❌
- Automatizado: 8 verificações automáticas ✅

## 🏛️ **Como o Sistema Busca na Receita Federal**

### **Processo de Consulta CNPJ**

#### **1. APIs Brasileiras Utilizadas**

O sistema usa **múltiplas APIs** com fallback automático:

```python
# src/tools/cnpj_api.py

class CNPJApiClient:
    async def get_company_data(self, cnpj: str):
        # Lista de APIs para tentar (fallback automático)
        apis = [
            self._get_from_receitaws,    # API 1: ReceitaWS
            self._get_from_brasilapi,    # API 2: Brasil API
        ]
        
        # Tenta cada API até conseguir dados
        for api_func in apis:
            try:
                result = await api_func(cnpj_clean)
                if result:
                    return result  # ✅ Sucesso!
            except Exception as e:
                continue  # ❌ Falhou, tenta próxima
                
        return None  # Nenhuma API funcionou
```

#### **2. ReceitaWS (API Principal)**

```python
async def _get_from_receitaws(self, cnpj: str):
    # URL da API pública da ReceitaWS
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_receitaws_response(data)
```

**Exemplo de resposta da ReceitaWS:**
```json
{
  "cnpj": "11.222.333/0001-81",
  "nome": "TECH SOLUTIONS LTDA",
  "fantasia": "TechSol",
  "situacao": "ATIVA",
  "abertura": "01/01/2020",
  "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
  "atividade_principal": [
    {
      "code": "62.01-5-00",
      "text": "Desenvolvimento de programas de computador sob encomenda"
    }
  ],
  "capital_social": "100.000,00",
  "logradouro": "RUA DAS FLORES",
  "numero": "123",
  "bairro": "CENTRO",
  "municipio": "SAO PAULO",
  "uf": "SP",
  "cep": "01234-567"
}
```

#### **3. Brasil API (Backup)**

```python
async def _get_from_brasilapi(self, cnpj: str):
    # URL da Brasil API (backup)
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_brasilapi_response(data)
```

### **Fluxo Completo de Busca**

#### **Passo a Passo:**

```python
# 1. LIMPEZA DO CNPJ
cnpj_input = "11.222.333/0001-81"
cnpj_clean = "11222333000181"  # Remove pontos e traços

# 2. PRIMEIRA TENTATIVA - ReceitaWS
try:
    response = GET https://www.receitaws.com.br/v1/cnpj/11222333000181
    if success:
        dados = parse_receitaws_data(response)
        return dados ✅
except:
    # Continua para próxima API

# 3. SEGUNDA TENTATIVA - Brasil API  
try:
    response = GET https://brasilapi.com.br/api/cnpj/v1/11222333000181
    if success:
        dados = parse_brasilapi_data(response)
        return dados ✅
except:
    # Nenhuma API funcionou

# 4. RETORNA ERRO
return None ❌
```

### **Processamento dos Dados**

#### **Conversão para Modelo Interno:**

```python
def _parse_receitaws_response(self, data):
    # Converte data de abertura
    registration_date = datetime.strptime(data['abertura'], '%d/%m/%Y')
    
    # Converte capital social (remove formatação brasileira)
    capital_str = data['capital_social']  # "100.000,00"
    capital = float(capital_str.replace('.', '').replace(',', '.'))  # 100000.0
    
    # Monta endereço completo
    address = {
        'street': data.get('logradouro'),
        'number': data.get('numero'), 
        'neighborhood': data.get('bairro'),
        'city': data.get('municipio'),
        'state': data.get('uf'),
        'zip_code': data.get('cep')
    }
    
    # Retorna objeto estruturado
    return CompanyData(
        cnpj=data.get('cnpj'),
        corporate_name=data.get('nome'),
        trade_name=data.get('fantasia'),
        legal_nature=data.get('natureza_juridica'),
        main_activity=data.get('atividade_principal')[0].get('text'),
        registration_date=registration_date,
        capital=capital,
        address=address,
        legal_situation=data.get('situacao'),
        special_situation=data.get('situacao_especial')
    )
```

### **Como é Usado no DataGatherer Agent**

```python
# src/agents/data_gatherer.py

class DataGathererAgent:
    async def execute(self, state: AgentState):
        # 1. Busca dados da Receita Federal
        company_data = await cnpj_client.get_company_data(state.cnpj)
        
        if company_data:
            state.company_data = company_data
            self.add_processing_note(state, 
                f"✅ Dados obtidos: {company_data.corporate_name}")
        else:
            self.add_processing_note(state, 
                "❌ Não foi possível obter dados da Receita Federal")
```

### **Recursos de Robustez**

#### **1. Timeout e Retry**
```python
# Timeout de 30 segundos
self.timeout = aiohttp.ClientTimeout(total=30)

# Se primeira API falhar, tenta a segunda automaticamente
```

#### **2. Validação de Dados**
```python
# Verifica se resposta é válida
if data.get('status') == 'ERROR':
    return None

# Valida CNPJ
if len(cnpj_clean) != 14:
    raise ValueError("CNPJ deve ter 14 dígitos")
```

#### **3. Error Handling**
```python
try:
    result = await api_call()
except aiohttp.ClientTimeout:
    logger.warning("Timeout na API da Receita Federal")
except aiohttp.ClientError:
    logger.warning("Erro de conexão com API")
except Exception as e:
    logger.error(f"Erro inesperado: {e}")
```

### **Exemplo Prático de Consulta CNPJ**

#### **Input:**
```
CNPJ: 11.222.333/0001-81
```

#### **Processamento:**
```
🔍 DataGatherer executando...

1️⃣ Limpando CNPJ: "11222333000181"

2️⃣ Tentando ReceitaWS...
   GET https://www.receitaws.com.br/v1/cnpj/11222333000181
   ✅ Status: 200 OK

3️⃣ Processando resposta...
   📋 Nome: "TECH SOLUTIONS LTDA"
   📍 Situação: "ATIVA" 
   📅 Abertura: 01/01/2020
   💰 Capital: R$ 100.000,00
   🏢 Atividade: "Desenvolvimento de software"

4️⃣ Salvando no estado compartilhado...
   ✅ state.company_data = CompanyData(...)
```

#### **Output Estruturado:**
```python
CompanyData(
    cnpj="11222333000181",
    corporate_name="TECH SOLUTIONS LTDA",
    trade_name="TechSol",
    legal_situation="ATIVA",
    main_activity="Desenvolvimento de programas de computador",
    registration_date=datetime(2020, 1, 1),
    capital=100000.0,
    address={
        "street": "RUA DAS FLORES",
        "city": "SAO PAULO", 
        "state": "SP"
    }
)
```

### **Vantagens da Implementação**

#### **1. Redundância**
- Se ReceitaWS cair → Brasil API assume automaticamente
- Sistema nunca para por falha de uma API

#### **2. Performance**
- Requests assíncronos (não bloqueia)
- Timeout configurável (30s)
- Cache interno possível

#### **3. Robustez**
- Validação rigorosa de CNPJ
- Tratamento de todos os tipos de erro
- Logs detalhados para debug

#### **4. Padrão Brasileiro**
- Formatação correta de datas (DD/MM/YYYY)
- Conversão de valores monetários (1.000,00 → 1000.0)
- Endereços completos com CEP

## 🎯 **Por que é Revolucionário**

Este sistema demonstra:

1. **AI Aplicada**: Não é só "chatbot", é solução real de negócio
2. **Arquitetura Complexa**: Multi-agente, RAG, orquestração
3. **Mercado Brasileiro**: APIs nacionais, documentos em português
4. **Production-Ready**: Docker, testes, CI/CD, monitoring
5. **Valor Mensurável**: ROI claro para bancos e fintechs

---

**🎉 Em resumo:** Transformamos um processo manual de dias em uma análise automática de minutos, mantendo (ou superando) a qualidade e consistência de analistas humanos, usando as tecnologias mais avançadas de AI disponíveis hoje!

O sistema consulta APIs públicas oficiais da Receita Federal de forma robusta e assíncrona, com fallback automático e tratamento completo de erros, garantindo que sempre tenha os dados mais atualizados das empresas brasileiras!