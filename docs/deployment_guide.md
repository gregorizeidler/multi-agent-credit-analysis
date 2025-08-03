# Guia de Deploy - Orquestra de Agentes

Este guia detalha como fazer deploy da Orquestra de Agentes em diferentes ambientes.

## 🚀 Deploy Local (Desenvolvimento)

### Pré-requisitos

- Python 3.11+
- Docker & Docker Compose
- Git

### Setup Rápido

```bash
# 1. Clone o repositório
git clone <repo-url>
cd orquestra-agentes-financeiros

# 2. Execute o script de setup
./scripts/setup.sh

# 3. Configure API keys
cp env.example .env
# Edite .env com suas chaves

# 4. Inicie com Docker
docker-compose up --build
```

### Verificação

```bash
# Health check
curl http://localhost:8000/health

# Documentação
open http://localhost:8000/docs
```

## 🌐 Deploy em Produção

### 1. Preparação do Ambiente

#### Ubuntu/Debian

```bash
# Instalar dependências
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Configurar Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

#### CentOS/RHEL

```bash
# Instalar Docker
sudo yum install -y docker docker-compose git
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. Configuração de Produção

```bash
# Clone do repositório
git clone <repo-url>
cd orquestra-agentes-financeiros

# Configurar ambiente de produção
cp env.example .env.prod
```

#### Arquivo .env.prod

```bash
# API Keys (OBRIGATÓRIO)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...

# Configurações de Produção
ENVIRONMENT=production
LOG_LEVEL=INFO
LLM_PROVIDER=openai

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Rate Limiting (mais restritivo em produção)
RATE_LIMIT_REQUESTS=50
RATE_LIMIT_WINDOW=3600

# Segurança
MAX_FILE_SIZE=5242880  # 5MB em produção
```

### 3. Deploy com Docker Compose

```bash
# Build e deploy
docker-compose --env-file .env.prod up -d --build

# Verificar status
docker-compose ps
docker-compose logs -f orquestra-api
```

## ☁️ Deploy em Cloud

### AWS (EC2 + ECS)

#### 1. Configuração da Instância EC2

```bash
# Instância recomendada: t3.medium ou superior
# 2 vCPUs, 4GB RAM, 20GB storage

# Configurar Security Group
# - Porta 22 (SSH) - apenas seu IP
# - Porta 8000 (API) - conforme necessário
# - Porta 443 (HTTPS) - se usar SSL
```

#### 2. Deploy na EC2

```bash
# Conectar via SSH
ssh -i keypair.pem ubuntu@ec2-instance-ip

# Instalar dependências
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git

# Deploy da aplicação
git clone <repo-url>
cd orquestra-agentes-financeiros
cp env.example .env.prod
# Configurar .env.prod

# Iniciar aplicação
docker-compose --env-file .env.prod up -d
```

#### 3. ECS Task Definition

```json
{
  "family": "orquestra-agentes",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "orquestra-api",
      "image": "orquestra-agentes:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."},
        {"name": "ANTHROPIC_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/orquestra-agentes",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Platform (Cloud Run)

#### 1. Build da Imagem

```bash
# Tag para GCR
docker tag orquestra-agentes:latest gcr.io/PROJECT_ID/orquestra-agentes

# Push para registry
docker push gcr.io/PROJECT_ID/orquestra-agentes
```

#### 2. Deploy no Cloud Run

```bash
gcloud run deploy orquestra-agentes \
  --image gcr.io/PROJECT_ID/orquestra-agentes \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars LOG_LEVEL=INFO \
  --memory 2Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10
```

### Azure (Container Instances)

```bash
# Criar Resource Group
az group create --name OrquestraAgentes --location eastus

# Deploy container
az container create \
  --resource-group OrquestraAgentes \
  --name orquestra-api \
  --image orquestra-agentes:latest \
  --cpu 1 \
  --memory 2 \
  --restart-policy Always \
  --ports 8000 \
  --environment-variables \
    ENVIRONMENT=production \
    LOG_LEVEL=INFO \
  --secure-environment-variables \
    OPENAI_API_KEY=$OPENAI_API_KEY \
    ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

## 🔒 Configurações de Segurança

### 1. HTTPS/SSL

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Variáveis de Ambiente Seguras

```bash
# Usar sistemas de gerenciamento de secrets
# AWS Secrets Manager
# Azure Key Vault  
# Google Secret Manager
# HashiCorp Vault

# Exemplo com AWS Secrets Manager
aws secretsmanager create-secret \
  --name orquestra/api-keys \
  --secret-string '{"OPENAI_API_KEY":"sk-...","ANTHROPIC_API_KEY":"sk-ant-..."}'
```

### 3. Firewall e Rate Limiting

```bash
# iptables (Linux)
sudo iptables -A INPUT -p tcp --dport 8000 -m limit --limit 100/hour -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP

# UFW (Ubuntu)
sudo ufw allow from 10.0.0.0/8 to any port 8000
```

## 📊 Monitoramento e Observabilidade

### 1. Health Checks

```bash
# Configurar health check automático
#!/bin/bash
while true; do
  if ! curl -f http://localhost:8000/health; then
    echo "API down, restarting..."
    docker-compose restart orquestra-api
  fi
  sleep 30
done
```

### 2. Logs Centralizados

#### ELK Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  elasticsearch:
    image: elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    
  logstash:
    image: logstash:7.14.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      
  kibana:
    image: kibana:7.14.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### 3. Métricas com Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'orquestra-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## 🚀 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t orquestra-agentes:${{ github.sha }} .
        
      - name: Deploy to server
        run: |
          echo "$SSH_KEY" | tr -d '\r' | ssh-add - > /dev/null
          ssh user@server "
            cd /app/orquestra-agentes &&
            git pull &&
            docker-compose down &&
            docker-compose up -d --build
          "
        env:
          SSH_KEY: ${{ secrets.SSH_KEY }}
```

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia

```bash
# Verificar logs
docker-compose logs orquestra-api

# Problemas de memória
docker stats

# Verificar configuração
docker-compose config
```

#### 2. API retorna 500

```bash
# Verificar logs da aplicação
docker-compose logs -f orquestra-api

# Verificar configuração de ambiente
docker-compose exec orquestra-api env | grep -E "(OPENAI|ANTHROPIC)"
```

#### 3. Performance baixa

```bash
# Verificar recursos
htop
df -h
free -m

# Otimizar Docker
docker system prune -f
```

### Comandos Úteis

```bash
# Restart completo
docker-compose down && docker-compose up -d

# Ver logs em tempo real
docker-compose logs -f --tail=100

# Backup de dados
docker-compose exec orquestra-api tar -czf backup.tar.gz /app/data

# Update da aplicação
git pull && docker-compose up -d --build
```

## 📋 Checklist de Deploy

- [ ] **Ambiente preparado** (Docker, dependências)
- [ ] **API keys configuradas** (.env.prod)
- [ ] **Firewall configurado** (portas necessárias)
- [ ] **SSL/HTTPS configurado** (se necessário)
- [ ] **Health checks funcionando**
- [ ] **Logs centralizados** (se necessário)
- [ ] **Backup configurado** (dados importantes)
- [ ] **Monitoramento ativo** (uptime, métricas)
- [ ] **Documentação atualizada** (URLs, credenciais)

---

Para suporte adicional, consulte os logs ou abra uma issue no repositório.