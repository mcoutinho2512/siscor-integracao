"""
coleta_sirenes_debug.py - Debug da API de Sirenes
"""

import requests
from datetime import datetime
from xml.etree import ElementTree

print('=' * 60)
print('🔍 DEBUG DA API DE SIRENES')
print('=' * 60)

# Testar API
timestamp = datetime.now().timestamp()
url = f"http://websirene.rio.rj.gov.br/xml/sirenes.xml?nocache={timestamp}"

print(f'\n📡 URL: {url}')

try:
    response = requests.get(url, timeout=15)
    
    print(f'✅ Status Code: {response.status_code}')
    print(f'✅ Content-Type: {response.headers.get("Content-Type")}')
    print(f'✅ Tamanho: {len(response.content)} bytes')
    
    print('\n' + '=' * 60)
    print('📄 CONTEÚDO DA RESPOSTA:')
    print('=' * 60)
    print(response.text[:2000])  # Primeiros 2000 caracteres
    print('...')
    
    # Tentar parsear XML
    print('\n' + '=' * 60)
    print('🔧 TENTANDO PARSEAR XML:')
    print('=' * 60)
    
    try:
        root = ElementTree.fromstring(response.content)
        print(f'✅ Root tag: {root.tag}')
        print(f'✅ Número de elementos: {len(root)}')
        
        if len(root) > 0:
            print('\n📋 ESTRUTURA DO PRIMEIRO ELEMENTO:')
            first = root[0]
            print(f'   Tag: {first.tag}')
            for child in first:
                print(f'   - {child.tag}: {child.text}')
        else:
            print('⚠️  XML vazio!')
            
    except Exception as e:
        print(f'❌ Erro ao parsear XML: {e}')
    
except requests.exceptions.Timeout:
    print('❌ Timeout!')
except Exception as e:
    print(f'❌ Erro: {e}')

print('\n' + '=' * 60)