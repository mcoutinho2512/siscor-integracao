# 🏙️ SISCOR - Sistema Integrado do Centro de Operações Rio

Sistema de monitoramento e gestão operacional da cidade do Rio de Janeiro.

## 📋 Sobre

O SISCOR é uma aplicação Django que integra diversas fontes de dados para monitoramento em tempo real da cidade, incluindo:

- 🚨 **Sirenes de Alerta** - Sistema de alertas da Defesa Civil
- 🌧️ **Meteorologia** - Pluviômetros, estações meteorológicas, alertas de chuva
- 🚗 **Mobilidade** - Integração Waze, BRT, Metrô, SuperVia, Bike Rio
- 📹 **Videomonitoramento** - Sistema de câmeras da cidade
- ⚠️ **Ocorrências** - Registro e acompanhamento de incidentes
- 📊 **Matriz Decisória** - Dashboard para tomada de decisões

## 🛠️ Tecnologias

- **Backend:** Django 4.x + Django REST Framework
- **Frontend:** Leaflet.js + Bootstrap + jQuery
- **Banco:** SQLite (desenvolvimento) / PostgreSQL (produção)

## 🚀 Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/siscor.git
cd siscor

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Rodar servidor
python manage.py runserver
```

## 📁 Estrutura

```
siscor/
├── aplicativo/          # App principal
│   ├── models.py        # Modelos de dados
│   ├── views.py         # Views e APIs
│   ├── urls.py          # Rotas
│   ├── static/          # Arquivos estáticos
│   └── templates/       # Templates HTML
├── core/                # App core (base)
├── sitecor/             # Configurações Django
├── manage.py
└── requirements.txt
```

## 🔗 Principais Endpoints

| Endpoint | Descrição |
|----------|-----------|
| `/` | Login |
| `/cor/` | Dashboard COR |
| `/waze-dashboard/` | Dashboard Waze |
| `/mobilidade/` | Dashboard Mobilidade |
| `/meteorologia/` | Dashboard Meteorologia |
| `/videomonitoramento/` | Câmeras |
| `/api/sirenes/` | API Sirenes |
| `/api/estagio/` | API Estágio Operacional |
| `/api/ocorrencias/` | API Ocorrências |

## 👤 Autor

Centro de Operações Rio - Prefeitura do Rio de Janeiro

## 📄 Licença

Uso interno - Prefeitura do Rio de Janeiro
