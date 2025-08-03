"""Cliente para APIs de consulta de CNPJ."""

import asyncio
from datetime import datetime
from typing import Optional

import aiohttp
from loguru import logger

from ..models.schemas import CompanyData


class CNPJApiClient:
    """Cliente para consulta de dados de CNPJ via APIs públicas."""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
        
    async def get_company_data(self, cnpj: str) -> Optional[CompanyData]:
        """
        Busca dados da empresa via CNPJ.
        
        Usa múltiplas APIs como fallback para garantir disponibilidade.
        """
        cnpj_clean = self._clean_cnpj(cnpj)
        
        # Lista de APIs para tentar
        apis = [
            self._get_from_receitaws,
            self._get_from_brasilapi,
        ]
        
        for api_func in apis:
            try:
                result = await api_func(cnpj_clean)
                if result:
                    logger.info(f"Dados obtidos com sucesso para CNPJ {cnpj_clean}")
                    return result
            except Exception as e:
                logger.warning(f"Erro ao consultar API {api_func.__name__}: {e}")
                continue
        
        logger.error(f"Não foi possível obter dados para CNPJ {cnpj_clean}")
        return None
    
    def _clean_cnpj(self, cnpj: str) -> str:
        """Remove formatação do CNPJ."""
        return ''.join(filter(str.isdigit, cnpj))
    
    async def _get_from_receitaws(self, cnpj: str) -> Optional[CompanyData]:
        """Consulta via ReceitaWS API."""
        url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_receitaws_response(data)
                
        return None
    
    async def _get_from_brasilapi(self, cnpj: str) -> Optional[CompanyData]:
        """Consulta via Brasil API."""
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_brasilapi_response(data)
                
        return None
    
    def _parse_receitaws_response(self, data: dict) -> Optional[CompanyData]:
        """Converte resposta da ReceitaWS para modelo interno."""
        if data.get('status') == 'ERROR':
            return None
            
        try:
            registration_date = None
            if data.get('abertura'):
                registration_date = datetime.strptime(data['abertura'], '%d/%m/%Y')
            
            capital = None
            if data.get('capital_social'):
                capital_str = data['capital_social'].replace('.', '').replace(',', '.')
                try:
                    capital = float(capital_str)
                except ValueError:
                    pass
            
            address = {
                'street': data.get('logradouro'),
                'number': data.get('numero'),
                'neighborhood': data.get('bairro'),
                'city': data.get('municipio'),
                'state': data.get('uf'),
                'zip_code': data.get('cep'),
            }
            
            return CompanyData(
                cnpj=data.get('cnpj', ''),
                corporate_name=data.get('nome', ''),
                trade_name=data.get('fantasia'),
                legal_nature=data.get('natureza_juridica'),
                main_activity=data.get('atividade_principal', [{}])[0].get('text') if data.get('atividade_principal') else None,
                registration_date=registration_date,
                capital=capital,
                address=address,
                legal_situation=data.get('situacao'),
                special_situation=data.get('situacao_especial'),
            )
        except Exception as e:
            logger.error(f"Erro ao processar resposta ReceitaWS: {e}")
            return None
    
    def _parse_brasilapi_response(self, data: dict) -> Optional[CompanyData]:
        """Converte resposta da Brasil API para modelo interno."""
        try:
            registration_date = None
            if data.get('data_inicio_atividade'):
                registration_date = datetime.strptime(data['data_inicio_atividade'], '%Y-%m-%d')
            
            capital = data.get('capital_social')
            if isinstance(capital, str):
                try:
                    capital = float(capital)
                except ValueError:
                    capital = None
            
            address = {
                'street': data.get('logradouro'),
                'number': data.get('numero'),
                'neighborhood': data.get('bairro'),
                'city': data.get('municipio'),
                'state': data.get('uf'),
                'zip_code': data.get('cep'),
            }
            
            return CompanyData(
                cnpj=data.get('cnpj', ''),
                corporate_name=data.get('razao_social', ''),
                trade_name=data.get('nome_fantasia'),
                legal_nature=data.get('natureza_juridica'),
                main_activity=data.get('cnae_fiscal_descricao'),
                registration_date=registration_date,
                capital=capital,
                address=address,
                legal_situation=data.get('descricao_situacao_cadastral'),
                special_situation=data.get('situacao_especial'),
            )
        except Exception as e:
            logger.error(f"Erro ao processar resposta Brasil API: {e}")
            return None


# Singleton instance
cnpj_client = CNPJApiClient()