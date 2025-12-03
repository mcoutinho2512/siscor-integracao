"""Limpa caracteres invisíveis do views.py"""

with open('aplicativo/views.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Remover BOM e caracteres invisíveis
content = content.replace('\ufeff', '')
content = content.replace('\u00bb', '')
content = content.replace('\u00bf', '')

# Salvar limpo
with open('aplicativo/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Arquivo limpo!')