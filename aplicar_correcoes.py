# -*- coding: utf-8 -*-
"""
SISCOR - Script de Correções Fase 1
Execute na pasta raiz do projeto: python aplicar_correcoes.py
"""

import os
import re
import shutil

# Cores para terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'

def print_ok(msg):
    print(f"{Cores.VERDE}✅ {msg}{Cores.RESET}")

def print_erro(msg):
    print(f"{Cores.VERMELHO}❌ {msg}{Cores.RESET}")

def print_info(msg):
    print(f"{Cores.AZUL}ℹ️  {msg}{Cores.RESET}")

def print_titulo(msg):
    print(f"\n{Cores.NEGRITO}{Cores.AMARELO}{'='*50}")
    print(f"   {msg}")
    print(f"{'='*50}{Cores.RESET}\n")


# ===========================================
# CORREÇÃO 1: views.py
# ===========================================
NOVO_CABECALHO_VIEWS = '''# -*- coding: utf-8 -*-
"""
SISCOR - Views
Sistema Integrado do Centro de Operações Rio
"""

import re
import random
import base64
import logging
import urllib3
import requests
from functools import lru_cache
from datetime import datetime, timedelta

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    Sirene,
    DadosSirene,
    Estagio,
    ChuvaConsolidado,
    Evento,
    Ocorrencias,
    EstacaoPlv,
    DadosPlv,
    EstacaoMet,
    DadosMet,
    EscolasMunicipais,
    BensProtegidos,
    Calor
)

# Configuração do Logger
logger = logging.getLogger(__name__)

'''


def corrigir_views():
    """Corrige o arquivo views.py"""
    arquivo = "aplicativo/views.py"
    
    if not os.path.exists(arquivo):
        print_erro(f"Arquivo não encontrado: {arquivo}")
        return False
    
    # Backup
    backup = arquivo + ".backup_fase1"
    shutil.copy2(arquivo, backup)
    print_ok(f"Backup criado: {backup}")
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        conteudo = f.read()
    
    # Encontrar fim dos imports
    padrao = r'^from \.models import \([^)]+\)\s*'
    match = re.search(padrao, conteudo, re.MULTILINE | re.DOTALL)
    
    if match:
        resto = conteudo[match.end():]
    else:
        match2 = re.search(r'^def ', conteudo, re.MULTILINE)
        if match2:
            resto = conteudo[match2.start():]
        else:
            print_erro("Estrutura do arquivo não reconhecida")
            return False
    
    # Remover decorators duplicados
    original_count = resto.count("@login_required")
    resto = re.sub(
        r"@login_required\(login_url=['\"]login['\"]\)\s*\n@login_required\(login_url=['\"]login['\"]\)",
        "@login_required(login_url='login')",
        resto
    )
    removidos = original_count - resto.count("@login_required")
    
    # Montar e salvar
    novo = NOVO_CABECALHO_VIEWS + resto
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(novo)
    
    print_ok("Imports reorganizados")
    print_ok("Logger configurado")
    print_ok(f"{removidos} decorators duplicados removidos")
    
    return True


def criar_env():
    """Cria arquivo .env se não existir"""
    if os.path.exists('.env'):
        print_info(".env já existe, pulando...")
        return True
    
    conteudo = '''# ===========================================
# SISCOR - Variáveis de Ambiente
# ===========================================
# NUNCA faça commit deste arquivo no Git!

# Django
DEBUG=True
SECRET_KEY=sua-chave-secreta-super-segura-mude-isso-em-producao

# Hosts permitidos (separados por vírgula)
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados PostgreSQL (produção)
# DATABASE_URL=postgres://usuario:senha@localhost:5432/siscor
'''
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print_ok("Arquivo .env criado")
    return True


def corrigir_settings():
    """Atualiza settings.py para usar variáveis de ambiente"""
    arquivo = "sitecor/settings.py"
    
    if not os.path.exists(arquivo):
        print_erro(f"Arquivo não encontrado: {arquivo}")
        return False
    
    # Backup
    backup = arquivo + ".backup_fase1"
    shutil.copy2(arquivo, backup)
    print_ok(f"Backup criado: {backup}")
    
    # Ler
    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        conteudo = f.read()
    
    # Adicionar import do os no início se não existir
    if 'import os' not in conteudo:
        conteudo = 'import os\n' + conteudo
        print_ok("Import 'os' adicionado")
    
    # Substituir SECRET_KEY hardcoded
    conteudo = re.sub(
        r"SECRET_KEY\s*=\s*['\"].*?['\"]",
        "SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-MUDE-EM-PRODUCAO')",
        conteudo
    )
    print_ok("SECRET_KEY agora usa variável de ambiente")
    
    # Substituir DEBUG
    conteudo = re.sub(
        r"DEBUG\s*=\s*True",
        "DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')",
        conteudo
    )
    print_ok("DEBUG agora usa variável de ambiente")
    
    # Substituir ALLOWED_HOSTS
    conteudo = re.sub(
        r"ALLOWED_HOSTS\s*=\s*\[\]",
        "ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')",
        conteudo
    )
    print_ok("ALLOWED_HOSTS agora usa variável de ambiente")
    
    # Corrigir timezone
    conteudo = re.sub(
        r"TIME_ZONE\s*=\s*['\"]UTC['\"]",
        "TIME_ZONE = 'America/Sao_Paulo'",
        conteudo
    )
    print_ok("Timezone corrigido para America/Sao_Paulo")
    
    # Corrigir language
    conteudo = re.sub(
        r"LANGUAGE_CODE\s*=\s*['\"]en-us['\"]",
        "LANGUAGE_CODE = 'pt-br'",
        conteudo
    )
    print_ok("Idioma corrigido para pt-br")
    
    # Adicionar LOGGING se não existir
    if 'LOGGING' not in conteudo:
        logging_config = '''

# ===========================================
# LOGGING
# ===========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'aplicativo': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
'''
        conteudo += logging_config
        print_ok("Configuração de LOGGING adicionada")
    
    # Salvar
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    return True


def atualizar_requirements():
    """Atualiza requirements.txt"""
    arquivo = "requirements.txt"
    
    # Backup
    if os.path.exists(arquivo):
        backup = arquivo + ".backup_fase1"
        shutil.copy2(arquivo, backup)
        print_ok(f"Backup criado: {backup}")
    
    conteudo = '''# ===========================================
# SISCOR - Dependências Python
# ===========================================
# Instale com: pip install -r requirements.txt

# Django e REST
Django>=4.2,<5.0
djangorestframework>=3.14.0

# Variáveis de ambiente
python-dotenv>=1.0.0

# Geolocalização
django-geojson>=4.0.0
django-location-field>=2.7.0
geopy>=2.4.0

# APIs e HTTP
requests>=2.31.0
urllib3>=2.0.0

# Datas
python-dateutil>=2.8.2
pytz>=2023.3

# Traduções
deep-translator>=1.11.0

# Firebase (notificações push)
pyfcm>=2.0.0

# Imagens
Pillow>=10.0.0
'''
    
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print_ok("requirements.txt atualizado")
    return True


def main():
    print_titulo("SISCOR - Aplicando Correções Fase 1")
    
    # Verificar se está na pasta certa
    if not os.path.exists("manage.py"):
        print_erro("Execute este script na pasta raiz do projeto (onde está o manage.py)")
        return
    
    erros = 0
    
    # 1. Corrigir views.py
    print_info("Corrigindo views.py...")
    if not corrigir_views():
        erros += 1
    
    # 2. Criar .env
    print_info("\nCriando .env...")
    if not criar_env():
        erros += 1
    
    # 3. Corrigir settings.py
    print_info("\nCorrigindo settings.py...")
    if not corrigir_settings():
        erros += 1
    
    # 4. Atualizar requirements
    print_info("\nAtualizando requirements.txt...")
    if not atualizar_requirements():
        erros += 1
    
    # Resultado
    print_titulo("Resultado")
    
    if erros == 0:
        print_ok("Todas as correções aplicadas com sucesso!")
        print("")
        print_info("Próximos passos:")
        print("   1. pip install python-dotenv")
        print("   2. Edite o arquivo .env com suas configurações")
        print("   3. python manage.py runserver")
        print("")
        print_info("Para commitar as alterações:")
        print("   git add .")
        print('   git commit -m "🔧 Fase 1: Correções de bugs e segurança"')
        print("   git push")
    else:
        print_erro(f"{erros} erro(s) encontrado(s)")


if __name__ == "__main__":
    main()
