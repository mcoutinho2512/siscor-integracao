# -*- coding: utf-8 -*-
"""
SISCOR - Script de Correções Fase 2
Corrige bugs funcionais: funções duplicadas, IntegerField, API Keys

Execute na pasta raiz do projeto: python aplicar_fase2.py
"""

import os
import re
import shutil
from datetime import datetime

# Cores para terminal
class Cores:
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    AZUL = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    NEGRITO = '\033[1m'

def print_ok(msg):
    print(f"{Cores.VERDE}✅ {msg}{Cores.RESET}")

def print_erro(msg):
    print(f"{Cores.VERMELHO}❌ {msg}{Cores.RESET}")

def print_info(msg):
    print(f"{Cores.AZUL}ℹ️  {msg}{Cores.RESET}")

def print_aviso(msg):
    print(f"{Cores.AMARELO}⚠️  {msg}{Cores.RESET}")

def print_titulo(msg):
    print(f"\n{Cores.NEGRITO}{Cores.CYAN}{'='*60}")
    print(f"   {msg}")
    print(f"{'='*60}{Cores.RESET}\n")


def backup_arquivo(arquivo):
    """Cria backup do arquivo"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{arquivo}.backup_fase2_{timestamp}"
    shutil.copy2(arquivo, backup)
    return backup


def encontrar_funcoes(conteudo):
    """
    Encontra todas as funções e suas posições no arquivo.
    Retorna dict: {nome_funcao: [(inicio, fim, decorators), ...]}
    """
    linhas = conteudo.split('\n')
    funcoes = {}
    i = 0
    
    while i < len(linhas):
        linha = linhas[i]
        
        # Procurar por definição de função
        match = re.match(r'^def\s+(\w+)\s*\(', linha)
        if match:
            nome_func = match.group(1)
            inicio_func = i
            
            # Voltar para pegar decorators
            decorators_inicio = i
            j = i - 1
            while j >= 0 and (linhas[j].strip().startswith('@') or linhas[j].strip() == ''):
                if linhas[j].strip().startswith('@'):
                    decorators_inicio = j
                j -= 1
            
            # Avançar para encontrar fim da função
            # Uma função termina quando encontramos outra def no mesmo nível de indentação
            # ou um decorator seguido de def, ou fim do arquivo
            fim_func = i + 1
            while fim_func < len(linhas):
                linha_atual = linhas[fim_func]
                
                # Se encontrar nova definição de função ou decorator de função
                if re.match(r'^def\s+\w+\s*\(', linha_atual):
                    break
                if linha_atual.strip().startswith('@') and fim_func + 1 < len(linhas):
                    proxima = linhas[fim_func + 1]
                    if re.match(r'^def\s+\w+\s*\(', proxima) or proxima.strip().startswith('@'):
                        break
                fim_func += 1
            
            # Guardar informação da função
            if nome_func not in funcoes:
                funcoes[nome_func] = []
            funcoes[nome_func].append((decorators_inicio, fim_func))
            
            i = fim_func
        else:
            i += 1
    
    return funcoes


def remover_funcoes_duplicadas(conteudo):
    """Remove funções duplicadas, mantendo a primeira ocorrência"""
    funcoes = encontrar_funcoes(conteudo)
    linhas = conteudo.split('\n')
    
    # Encontrar linhas a remover (duplicatas)
    linhas_remover = set()
    duplicatas_encontradas = []
    
    for nome, ocorrencias in funcoes.items():
        if len(ocorrencias) > 1:
            duplicatas_encontradas.append(f"{nome} ({len(ocorrencias)}x)")
            # Manter primeira, remover as outras
            for inicio, fim in ocorrencias[1:]:
                for i in range(inicio, fim):
                    linhas_remover.add(i)
    
    # Criar novo conteúdo sem as linhas removidas
    novas_linhas = []
    for i, linha in enumerate(linhas):
        if i not in linhas_remover:
            novas_linhas.append(linha)
    
    return '\n'.join(novas_linhas), duplicatas_encontradas


def corrigir_views():
    """Corrige o arquivo views.py"""
    arquivo = "aplicativo/views.py"
    
    if not os.path.exists(arquivo):
        print_erro(f"Arquivo não encontrado: {arquivo}")
        return False, []
    
    # Backup
    backup = backup_arquivo(arquivo)
    print_ok(f"Backup criado: {backup}")
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        conteudo = f.read()
    
    # 1. Remover funções duplicadas
    conteudo, duplicatas = remover_funcoes_duplicadas(conteudo)
    
    # 2. Corrigir variável 'hoje' não definida na api_ocorrencias
    # Procurar por 'data_filtro': hoje.isoformat() e corrigir
    conteudo = re.sub(
        r"'data_filtro':\s*hoje\.isoformat\(\)",
        "'data_filtro': timezone.now().date().isoformat()",
        conteudo
    )
    
    # Salvar
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    return True, duplicatas


def corrigir_models():
    """Corrige o arquivo models.py"""
    arquivo = "aplicativo/models.py"
    
    if not os.path.exists(arquivo):
        print_erro(f"Arquivo não encontrado: {arquivo}")
        return False
    
    # Backup
    backup = backup_arquivo(arquivo)
    print_ok(f"Backup criado: {backup}")
    
    # Ler arquivo
    with open(arquivo, 'r', encoding='utf-8-sig') as f:
        conteudo = f.read()
    
    correcoes = 0
    
    # 1. Corrigir IntegerField com max_length
    # Padrão: IntegerField("...", max_length=250)
    padrao_int = r'(IntegerField\([^)]*)(,\s*max_length\s*=\s*\d+)([^)]*\))'
    matches = re.findall(padrao_int, conteudo)
    if matches:
        conteudo = re.sub(padrao_int, r'\1\3', conteudo)
        correcoes += len(matches)
        print_ok(f"{len(matches)} IntegerField com max_length corrigidos")
    
    # 2. Remover Google Maps API Key hardcoded
    # Linha 661: api_key="AIzaSyBke5pvPpmPU9EGo1iJj4cCm0dgpeTM-bc"
    api_google_pattern = r'api_key\s*=\s*["\']AIza[^"\']+["\']'
    if re.search(api_google_pattern, conteudo):
        conteudo = re.sub(
            api_google_pattern,
            'api_key=os.environ.get("GOOGLE_MAPS_API_KEY", "")',
            conteudo
        )
        correcoes += 1
        print_ok("Google Maps API Key movida para variável de ambiente")
    
    # 3. Remover FCM API Key hardcoded (linha ~2905)
    # Está comentado mas vamos garantir que não seja usado
    fcm_pattern = r'api_key\s*=\s*["\']AAAA[^"\']+["\']'
    if re.search(fcm_pattern, conteudo):
        conteudo = re.sub(
            fcm_pattern,
            'api_key=os.environ.get("FCM_API_KEY", "")',
            conteudo
        )
        correcoes += 1
        print_ok("FCM API Key movida para variável de ambiente")
    
    # 4. Adicionar import os se necessário
    if 'os.environ' in conteudo and 'import os' not in conteudo:
        conteudo = 'import os\n' + conteudo
        print_ok("Import 'os' adicionado ao models.py")
    
    # Salvar
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    return True


def atualizar_env():
    """Atualiza o arquivo .env com as novas variáveis"""
    arquivo = ".env"
    
    novas_vars = """
# APIs Externas (adicionadas na Fase 2)
GOOGLE_MAPS_API_KEY=sua-chave-google-maps-aqui
FCM_API_KEY=sua-chave-fcm-aqui
"""
    
    if os.path.exists(arquivo):
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        if 'GOOGLE_MAPS_API_KEY' not in conteudo:
            with open(arquivo, 'a', encoding='utf-8') as f:
                f.write(novas_vars)
            print_ok("Novas variáveis adicionadas ao .env")
        else:
            print_info(".env já contém as variáveis necessárias")
    else:
        print_aviso(".env não encontrado, crie manualmente")
    
    return True


def contar_linhas(arquivo):
    """Conta linhas de um arquivo"""
    if os.path.exists(arquivo):
        with open(arquivo, 'r', encoding='utf-8-sig') as f:
            return len(f.readlines())
    return 0


def main():
    print_titulo("SISCOR - Aplicando Correções Fase 2")
    print_info("Correção de Bugs Funcionais")
    print("")
    
    # Verificar se está na pasta certa
    if not os.path.exists("manage.py"):
        print_erro("Execute este script na pasta raiz do projeto (onde está o manage.py)")
        return
    
    erros = 0
    
    # Contar linhas antes
    linhas_views_antes = contar_linhas("aplicativo/views.py")
    linhas_models_antes = contar_linhas("aplicativo/models.py")
    
    # 1. Corrigir views.py
    print_titulo("1. Corrigindo views.py")
    sucesso, duplicatas = corrigir_views()
    if sucesso:
        if duplicatas:
            print_ok(f"Funções duplicadas removidas:")
            for d in duplicatas:
                print(f"      - {d}")
        print_ok("Variável 'hoje' corrigida em api_ocorrencias")
    else:
        erros += 1
    
    # 2. Corrigir models.py
    print_titulo("2. Corrigindo models.py")
    if not corrigir_models():
        erros += 1
    
    # 3. Atualizar .env
    print_titulo("3. Atualizando .env")
    atualizar_env()
    
    # Contar linhas depois
    linhas_views_depois = contar_linhas("aplicativo/views.py")
    linhas_models_depois = contar_linhas("aplicativo/models.py")
    
    # Resultado
    print_titulo("Resultado")
    
    if erros == 0:
        print_ok("Todas as correções da Fase 2 aplicadas com sucesso!")
        print("")
        print_info("Estatísticas:")
        print(f"      views.py: {linhas_views_antes} → {linhas_views_depois} linhas ({linhas_views_antes - linhas_views_depois} removidas)")
        print(f"      models.py: {linhas_models_antes} → {linhas_models_depois} linhas")
        print("")
        print_info("Próximos passos:")
        print("   1. python manage.py runserver")
        print("   2. Testar o sistema no navegador")
        print("   3. Verificar se 'CALOR UNDEFINED' foi corrigido")
        print("")
        print_info("Se tudo estiver OK, faça o commit:")
        print('   git add .')
        print('   git commit -m "🔧 Fase 2: Correção de bugs funcionais"')
        print('   git push')
    else:
        print_erro(f"{erros} erro(s) encontrado(s)")
        print_info("Verifique os backups criados para restaurar se necessário")


if __name__ == "__main__":
    main()
