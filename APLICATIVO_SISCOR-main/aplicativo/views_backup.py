import re
import random
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required  
from django.utils import timezone
from datetime import datetime, timedelta
from datetime import datetime
import logging
import requests  #IMPORT ADICIONADO
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

def teste_sem_login(request):
    """Teste sem login"""
    from django.http import HttpResponse
    return HttpResponse('<h1>FUNCIONOU! SEM LOGIN!</h1>')

# ============================================
# VIEWS DE PÁGINAS
# ============================================

def waze_dashboard_view(request):
    """Dashboard principal do mapa"""
    return render(request, 'mapa_novo/waze_dashboard.html')

# ============================================
# APIs - SIRENES
# ============================================

@never_cache
def sirene_api(request):
    """
    API de Sirenes - Retorna todas as sirenes com seus últimos dados
    """
    try:
        lista_estacoes = []
        sirenes = Sirene.objects.all()

        for sirene in sirenes:
            try:
                # Pegar último dado da sirene
                dados = DadosSirene.objects.filter(estacao_id=sirene.id).latest('id')

                lista_estacoes.append({
                    "id": sirene.id,
                    "fonte": sirene.fonte if hasattr(sirene, 'fonte') else "COR",
                    "lat": float(sirene.lat) if sirene.lat else -22.9068,
                    "lng": float(sirene.lon) if sirene.lon else -43.1729,
                    "nome": sirene.nome,
                    "cidade": sirene.municipio if hasattr(sirene, 'municipio') else "Rio de Janeiro",
                    "status": dados.status if hasattr(dados, 'status') else "ativa",
                    "tipo": dados.tipo if hasattr(dados, 'tipo') else "alta",
                    "prioridade": dados.tipo if hasattr(dados, 'tipo') else "alta"
                })
            except DadosSirene.DoesNotExist:
                # Se não tem dados, adiciona com valores padrão
                lista_estacoes.append({
                    "id": sirene.id,
                    "fonte": sirene.fonte if hasattr(sirene, 'fonte') else "COR",
                    "lat": float(sirene.lat) if sirene.lat else -22.9068,
                    "lng": float(sirene.lon) if sirene.lon else -43.1729,
                    "nome": sirene.nome,
                    "cidade": sirene.municipio if hasattr(sirene, 'municipio') else "Rio de Janeiro",
                    "status": "inativa",
                    "tipo": "baixa",
                    "prioridade": "baixa"
                })

        # Ordenar por tipo (prioridade)
        lista_ordenada = sorted(lista_estacoes, key=lambda k: k['tipo'], reverse=True)

        return JsonResponse({
            'success': True,
            'count': len(lista_ordenada),
            'data': lista_ordenada
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


# ============================================
# APIs - ESTÁGIOS DE MOBILIDADE
# ============================================

@never_cache
def estagio_api(request):
    """
    API de Estágios de Mobilidade
    Retorna o estágio atual da cidade
    """
    try:
        av = Estagio.objects.latest('id')

        # Extrair número do texto "Nível X"
        estagio_texto = av.esta or 'Nível 1'
        match = re.search(r'(\d+)', estagio_texto)
        nivel = int(match.group(1)) if match else 1

        # Mapeamento de cores por nível
        cores_map = {
            1: '#228d46',  # Verde - Normalidade
            2: '#f5c520',  # Amarelo - Atenção
            3: '#ef8c3f',  # Laranja - Alerta
            4: '#d0262d',  # Vermelho - Alerta Máximo
            5: '#5f2f7e'   # Roxo - Crise
        }

        nomes_map = {
            1: 'Normalidade',
            2: 'Atenção',
            3: 'Alerta',
            4: 'Alerta Máximo',
            5: 'Crise'
        }

        return JsonResponse({
            'success': True,
            'estagio': estagio_texto,
            'estagio_id': nivel,
            'nivel': nivel,
            'cor': cores_map.get(nivel, '#228d46'),
            'nome': nomes_map.get(nivel, 'Normalidade'),
            'mensagem': av.men if hasattr(av, 'men') else '',
            'inicio': av.data_i.isoformat() if hasattr(av, 'data_i') and av.data_i else None,
            'data_atualizacao': datetime.now().isoformat()
        })

    except Estagio.DoesNotExist:
        return JsonResponse({
            'success': True,
            'estagio': 'Nível 1',
            'estagio_id': 1,
            'nivel': 1,
            'cor': '#228d46',
            'nome': 'Normalidade',
            'mensagem': 'Sistema operando normalmente',
            'inicio': None,
            'data_atualizacao': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def estagio_api_app(request):
    """API de estágio para app mobile (formato simplificado)"""
    try:
        av = Estagio.objects.latest('id')
        estagio = av.esta.upper()
        return HttpResponse(estagio)
    except:
        return HttpResponse("NORMALIDADE")


# ============================================
# APIs - CHUVA/METEOROLOGIA
# ============================================

@cache_page(60 * 5)  # Cache de 5 minutos
def chuva_api(request):
    """
    API de Dados de Chuva
    Retorna último consolidado de chuva
    """
    try:
        consolidado = ChuvaConsolidado.objects.latest('id')

        return JsonResponse({
            'success': True,
            'data': {
                'id': consolidado.id,
                'valor': str(consolidado) if consolidado else 'N/A',
                'data_atualizacao': datetime.now().isoformat()
            }
        })
    except ChuvaConsolidado.DoesNotExist:
        return JsonResponse({
            'success': True,
            'data': {
                'valor': 'Sem dados',
                'data_atualizacao': datetime.now().isoformat()
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================
# APIs - EVENTOS
# ============================================

@never_cache
def api_eventos(request):
    """API de eventos da cidade"""
    try:
        eventos = Evento.objects.all()[:50]  # Últimos 50 eventos

        data = []
        for evento in eventos:
            data.append({
                'id': evento.id,
                'nome': evento.nome if hasattr(evento, 'nome') else 'Evento',
                'tipo': evento.tipo if hasattr(evento, 'tipo') else 'geral',
                'lat': float(evento.lat) if hasattr(evento, 'lat') and evento.lat else -22.9068,
                'lng': float(evento.lon) if hasattr(evento, 'lon') and evento.lon else -43.1729,
                'data': evento.data.isoformat() if hasattr(evento, 'data') and evento.data else None,
                'prioridade': evento.prioridade if hasattr(evento, 'prioridade') else 'media',
                'local': evento.local if hasattr(evento, 'local') else ''
            })

        return JsonResponse({
            'success': True,
            'count': len(data),
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


# ============================================
# APIs - OCORRÊNCIAS
# ============================================

@csrf_exempt
def api_ocorrencias(request):
    """
    API de ocorrências - APENAS DO DIA ATUAL
    """
    try:
        from django.utils import timezone  # ← Importar do Django
        
        # FILTRAR APENAS OCORRÊNCIAS DE HOJE
        hoje = timezone.now().date()  # ← Usar timezone do Django
        ocorrencias = Ocorrencias.objects.filter(
            data__date=hoje  # Filtra pela data de hoje
        ).order_by('-data')  # Mais recentes primeiro
        
        total = ocorrencias.count()
        
        data = []
        for ocorrencia in ocorrencias:
            data.append({
                'id': ocorrencia.id,
                'id_c': ocorrencia.id_c,
                'incidente': ocorrencia.incidente,
                'location': ocorrencia.location,
                'lat': float(ocorrencia.lat) if ocorrencia.lat else None,
                'lon': float(ocorrencia.lon) if ocorrencia.lon else None,
                'prio': ocorrencia.prio,
                'status': ocorrencia.status,
                'data': ocorrencia.data.isoformat() if ocorrencia.data else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'count': total,
            'filtro': 'hoje',
            'data_filtro': hoje.isoformat()
        })
        
    except Exception as e:
        logger.error(f'Erro ao buscar ocorrências: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)

# ============================================
# APIs - OUTRAS (Placeholder para expansão futura)
# ============================================

def api_escolas(request):
    """API de escolas (placeholder)"""
    return JsonResponse({'success': True, 'count': 0, 'data': []})

def api_hospitais(request):
    """API de hospitais (placeholder)"""
    return JsonResponse({'success': True, 'count': 0, 'data': []})


def waze_dashboard_completo(request):
    """Dashboard completo com todas as estatísticas"""
    context = {
        'tamanho_4': 0,
        'pc': 0,
        'color_pc': '228d46',
        'hist': 0,
        'unz': [],
        'qt_unz': 0,
        'baixo_v': 0,
        'medio_v': 0,
        'alto_v': 0,
        'lista_estacoes_plv': [],
        'jams_linha': [],
        'escolas': [],
        'hospitais': [],
        'eventos': [],
        'ocorrencias': [],
        'sirenes': [],
        'abrigos': [],
        'alagamentos': [],
        'bens': [],
        'chuva': [],
        'lista_pontos': [],
        'sensores': []
    }

    return render(request, 'mapa_novo/waze_dashboard.html', context)

def cor_dashboard_view(request):
    """Dashboard com design COR profissional"""
    return render(request, 'mapa_novo/cor_dashboard.html')


@api_view(['GET'])
def pluviometros_view(request):
    """API de Pluviômetros - Estações de Chuva"""
    try:
        data = []
        estacoes = EstacaoPlv.objects.all()

        for estacao in estacoes:
            if estacao.lat and estacao.lon:
                ultimo = DadosPlv.objects.filter(estacao=estacao).order_by('-data').first()

                if ultimo:
                    # Tratar data (pode ser string ou datetime)
                    data_formatada = 'N/A'
                    if ultimo.data:
                        if isinstance(ultimo.data, str):
                            data_formatada = ultimo.data
                        else:
                            data_formatada = ultimo.data.strftime('%d/%m/%Y %H:%M')

                    data.append({
                        'id': estacao.id,
                        'nome': estacao.nome,
                        'lat': float(estacao.lat),
                        'lng': float(estacao.lon),
                        'chuva_1h': float(ultimo.chuva_1 or 0),
                        'chuva_4h': float(ultimo.chuva_4 or 0),
                        'chuva_24h': float(ultimo.chuva_24 or 0),
                        'chuva_96h': float(ultimo.chuva_96 or 0),
                        'data': data_formatada,
                        'status': 'ativa'
                    })

        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })

    except Exception as e:
        import traceback
        print(f'ERRO: {e}')
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


@api_view(['GET'])
def estacoes_vento_view(request):
    """API de Estações de Vento"""
    try:
        data = []
        estacoes = EstacaoMet.objects.all()

        for estacao in estacoes:
            if estacao.lat and estacao.lon:
                ultimo = DadosMet.objects.filter(estacao=estacao).order_by('-data').first()

                if ultimo:
                    data.append({
                        'id': estacao.id,
                        'nome': estacao.nome,
                        'lat': float(estacao.lat),
                        'lng': float(estacao.lon),
                        'temperatura': float(ultimo.temp or 0),
                        'umidade': float(ultimo.umd or 0),
                        'direcao': str(ultimo.dire) if ultimo.dire else 'N/A',
                        'velocidade': float(ultimo.vel or 0),
                        'data': str(ultimo.data) if ultimo.data else 'N/A',
                        'status': 'ativa'
                    })

        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })

    except Exception as e:
        import traceback
        print(f'ERRO: {e}')
        print(traceback.format_exc())
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


@api_view(['GET'])
def escolas_view(request):
    """API de Escolas Municipais"""
    print('DEBUG: escolas_view foi chamada!')
    escolas_list = list(EscolasMunicipais.objects.all())
    print(f'DEBUG: Encontradas {len(escolas_list)} escolas')

    data = []
    for escola in escolas_list:
        print(f'DEBUG: Processando {escola.nome} - x={escola.x}, y={escola.y}')
        data.append({
            'id': escola.id,
            'nome': escola.nome,
            'lat': float(escola.y),
            'lng': float(escola.x),
            'endereco': str(escola.endereco or 'N/A'),
            'bairro': str(escola.bairro or 'N/A'),
            'telefone': str(escola.telefone or 'N/A'),
            'tipo': 'escola_municipal'
        })

    print(f'DEBUG: Retornando {len(data)} escolas')
    return Response({'success': True, 'data': data, 'count': len(data)})


@api_view(['GET'])
def bens_tombados_view(request):
    """API de Bens Tombados"""
    try:
        data = []
        bens = BensProtegidos.objects.all()

        for bem in bens:
            if bem.y and bem.x:
                data.append({
                    'id': bem.id,
                    'nome': bem.np or 'Bem Tombado',
                    'lat': float(bem.y),
                    'lng': float(bem.x),
                    'rua': bem.rua or 'N/A',
                    'grau': bem.grau_de_pr or 'N/A',
                    'tipo': 'bem_tombado'
                })

        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e), 'data': []}, status=500)


@api_view(['GET'])
def api_estagio(request):
    """API de estágio - formato novo"""
    try:
        # Buscar último estágio
        ultimo = Estagio.objects.filter(
            data_f__isnull=True
        ).order_by('-data_i').first()

        if not ultimo:
            ultimo = Estagio.objects.order_by('-data_i').first()

        if ultimo:
            # Extrair número do estágio
            estagio_texto = ultimo.esta or 'Nível 1'
            match = re.search(r'(\d+)', estagio_texto)
            nivel = int(match.group(1)) if match else 1

            # Mapear cores
            cores_map = {
                1: '#228d46',
                2: '#f5c520',
                3: '#ef8c3f',
                4: '#d0262d',
                5: '#5f2f7e'
            }

            descricoes_map = {
                1: 'Normalidade',
                2: 'Atenção',
                3: 'Alerta',
                4: 'Alerta Máximo',
                5: 'Crise'
            }

            return Response({
                'success': True,
                'data': {
                    'nivel': nivel,
                    'nome': estagio_texto,
                    'cor': cores_map.get(nivel, '#228d46'),
                    'descricao': descricoes_map.get(nivel, 'Normalidade')
                },
                'estagio': estagio_texto,
                'cor': cores_map.get(nivel, '#228d46'),
                'estagio_id': ultimo.id,
                'inicio': ultimo.data_i,
                'data_atualizacao': timezone.now()
            })

        # Se não tem estágio, retornar padrão
        return Response({
            'success': True,
            'data': {
                'nivel': 1,
                'nome': 'Nível 1',
                'cor': '#228d46',
                'descricao': 'Normalidade'
            },
            'estagio': 'Nível 1',
            'cor': '#228d46',
            'data_atualizacao': timezone.now()
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def inserir_ocorrencia_mobile(request):
    """
    Endpoint compatível com o sistema antigo
    Recebe via GET: ?lat=X&lon=Y&descricao=Z&tipo=W
    """
    try:
        ocorrencia = Ocorrencias.objects.create(
            incidente=request.GET.get('descricao', 'Ocorrência via mobile'),
            lat=request.GET.get('lat'),
            lon=request.GET.get('lon'),
            tipo_forma=request.GET.get('tipo', 'Outros'),
            prio=request.GET.get('prioridade', 'media'),
            bairro=request.GET.get('bairro', ''),
            status='Em andamento',
            data=timezone.now()
        )

        return Response({
            'success': True,
            'message': 'Ocorrência registrada',
            'id': ocorrencia.id
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)

@never_cache
def calor_api(request):
    """
    API de Alerta de Calor
    Retorna o alerta de calor atual
    """
    try:
        # Buscar último alerta ativo (sem data_f)
        alerta = Calor.objects.filter(data_f__isnull=True).latest('id')
        
        # Se não encontrar, buscar o último registro
        if not alerta:
            alerta = Calor.objects.latest('id')
        
        # Extrair número do texto "Nível X"
        nivel_texto = alerta.alive or 'Nível 0'
        match = re.search(r'(\d+)', nivel_texto)
        nivel = int(match.group(1)) if match else 0
        
        # Mapeamento de cores por nível
        cores_map = {
            0: '#228d46',  # Verde - Normal
            1: '#f5c520',  # Amarelo - Observação
            2: '#ef8c3f',  # Laranja - Atenção
            3: '#d0262d',  # Vermelho - Alerta
        }
        
        nomes_map = {
            0: 'Normal',
            1: 'Observação',
            2: 'Atenção',
            3: 'Alerta',
        }
        
        return JsonResponse({
            'success': True,
            'nivel': nivel,
            'nome': nomes_map.get(nivel, 'Normal'),
            'cor': cores_map.get(nivel, '#228d46'),
            'texto': nivel_texto,
            'data_inicio': alerta.data_i.isoformat() if alerta.data_i else None,
            'data_atualizacao': datetime.now().isoformat()
        })
        
    except Calor.DoesNotExist:
        return JsonResponse({
            'success': True,
            'nivel': 0,
            'nome': 'Normal',
            'cor': '#228d46',
            'texto': 'Nível 0',
            'data_inicio': None,
            'data_atualizacao': datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_estagio_atual(request):
    """Retorna o estágio operacional calculado dinamicamente"""
    try:
        # Calcular inline
        CORES = {
            1: {'cor': '#228d46', 'nome': 'Nível 1', 'descricao': 'Normalidade'},
            2: {'cor': '#f5c520', 'nome': 'Nível 2', 'descricao': 'Atenção'},
            3: {'cor': '#ef8c3f', 'nome': 'Nível 3', 'descricao': 'Alerta'},
            4: {'cor': '#d0262d', 'nome': 'Nível 4', 'descricao': 'Alerta Máximo'},
            5: {'cor': '#5f2f7e', 'nome': 'Nível 5', 'descricao': 'Crise'}
        }

        # Nível Ocorrências
        abertas = Ocorrencias.objects.count()
        if abertas >= 50:
            nivel_ocorrencias = 5
        elif abertas >= 30:
            nivel_ocorrencias = 4
        elif abertas >= 15:
            nivel_ocorrencias = 3
        elif abertas >= 5:
            nivel_ocorrencias = 2
        else:
            nivel_ocorrencias = 1

        # Nível Tempo (simplificado)
        nivel_tempo = 1

        # Nível Eventos
        nivel_eventos = 1

        # Nível geral
        nivel_geral = int((nivel_ocorrencias + nivel_tempo + nivel_eventos) / 3)

        resultado = {
            'nivel': nivel_geral,
            'cor': CORES[nivel_geral]['cor'],
            'nome': CORES[nivel_geral]['nome'],
            'descricao': CORES[nivel_geral]['descricao'],
            'detalhes': {
                'tempo': {'nivel': nivel_tempo, **CORES[nivel_tempo]},
                'ocorrencias': {'nivel': nivel_ocorrencias, **CORES[nivel_ocorrencias], 'total': abertas},
                'eventos': {'nivel': nivel_eventos, **CORES[nivel_eventos]}
            }
        }

        return Response({
            'success': True,
            'data': resultado
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def waze_data_view(request):
    """Busca dados do Waze (alertas e congestionamentos)"""
    try:
        import requests
        
        url = "https://www.waze.com/row-partnerhub-api/partners/14420996249/waze-feeds/c5c19146-e0f9-44a7-9815-3862c8a6ed67?format=1"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return Response({
                'success': False,
                'error': 'Erro ao buscar dados do Waze'
            }, status=500)
        
        data = response.json()
        
        # Processar alertas
        alertas_processados = []
        for alert in data.get('alerts', [])[:100]:  # Limitar a 100 para performance
            tipo_map = {
                'HAZARD': 'Perigo',
                'ACCIDENT': 'Acidente',
                'JAM': 'Congestionamento',
                'WEATHERHAZARD': 'Condição Climática',
                'ROAD_CLOSED': 'Via Fechada'
            }
            
            subtipo_map = {
                'HAZARD_ON_ROAD_POT_HOLE': 'Buraco',
                'HAZARD_ON_ROAD_OBJECT': 'Objeto na Pista',
                'HAZARD_ON_ROAD': 'Perigo na Pista',
                'HAZARD_ON_SHOULDER': 'Perigo no Acostamento',
                'HAZARD_WEATHER': 'Clima',
                'HAZARD_ON_ROAD_ICE': 'Pista Escorregadia',
                'HAZARD_ON_ROAD_CONSTRUCTION': 'Obra',
                'HAZARD_ON_ROAD_CAR_STOPPED': 'Veículo Parado',
                'HAZARD_ON_ROAD_TRAFFIC_LIGHT_FAULT': 'Semáforo com Defeito'
            }
            
            alertas_processados.append({
                'id': alert.get('uuid'),
                'tipo': tipo_map.get(alert.get('type'), alert.get('type')),
                'subtipo': subtipo_map.get(alert.get('subtype'), alert.get('subtype', '')),
                'lat': alert.get('location', {}).get('y'),
                'lng': alert.get('location', {}).get('x'),
                'rua': alert.get('street', 'Via não identificada'),
                'cidade': alert.get('city', 'Rio de Janeiro'),
                'confianca': alert.get('confidence', 0),
                'confiabilidade': alert.get('reliability', 0),
                'data': alert.get('pubMillis')
            })
        
        # Processar congestionamentos
        jams_processados = []
        for jam in data.get('jams', [])[:50]:  # Limitar a 50
            # Pegar primeiro e último ponto da linha
            line = jam.get('line', [])
            if len(line) > 0:
                inicio = line[0]
                fim = line[-1]
                
                # Calcular ponto central
                centro_lat = (inicio['y'] + fim['y']) / 2
                centro_lng = (inicio['x'] + fim['x']) / 2
                
                nivel_map = {
                    0: 'Livre',
                    1: 'Leve',
                    2: 'Moderado', 
                    3: 'Pesado',
                    4: 'Parado',
                    5: 'Muito Lento'
                }
                
                jams_processados.append({
                    'id': jam.get('uuid'),
                    'rua': jam.get('street', 'Via não identificada'),
                    'cidade': jam.get('city', 'Rio de Janeiro'),
                    'nivel': jam.get('level', 0),
                    'nivel_texto': nivel_map.get(jam.get('level', 0), 'Desconhecido'),
                    'velocidade': round(jam.get('speedKMH', 0), 1),
                    'comprimento': jam.get('length', 0),
                    'atraso': jam.get('delay', 0),
                    'lat': centro_lat,
                    'lng': centro_lng,
                    'linha': line,  # Pontos para desenhar linha no mapa
                    'data': jam.get('pubMillis')
                })
        
        return Response({
            'success': True,
            'alertas': alertas_processados,
            'congestionamentos': jams_processados,
            'total_alertas': len(data.get('alerts', [])),
            'total_jams': len(data.get('jams', [])),
            'atualizacao': data.get('endTime')
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
        
@api_view(['GET'])
def api_ocorrencias(request):
    """API de ocorrências"""
    try:
        ocorrencias = Ocorrencias.objects.filter(
            lat__isnull=False,
            lon__isnull=False
        ).exclude(
            lat=0,
            lon=0
        ).order_by('-data')[:100]
        
        data = []
        for o in ocorrencias:
            data.append({
                'id': o.id,
                'tipo': o.incidente or 'Ocorrência',
                'descricao': o.location or 'Sem descrição',
                'location': o.location or '',
                'lat': float(o.lat) if o.lat else None,
                'lng': float(o.lon) if o.lon else None,
                'prioridade': o.prio or 'MÉDIA',
                'status': o.status or 'Em andamento',
                'data_criacao': o.data.isoformat() if o.data else None
            })
        
        return Response({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def api_cameras(request):
    """API de câmeras de monitoramento"""
    try:
        from aplicativo.models import Cameras
        
        # Parâmetros
        bairro = request.GET.get('bairro', None)
        status = request.GET.get('status', None)
        search = request.GET.get('search', None)
        
        # Query
        cameras = Cameras.objects.all()
        
        # Filtros
        if bairro:
            cameras = cameras.filter(bairro__icontains=bairro)
        
        if status:
            cameras = cameras.filter(status__iexact=status)
        
        if search:
            cameras = cameras.filter(nome__icontains=search)
        
        # Serializar
        data = []
        bairros_set = set()
        
        for cam in cameras.order_by('id_c'):
            try:
                lat = float(cam.lat) if cam.lat else None
                lon = float(cam.lon) if cam.lon else None
                
                if lat and lon and lat != 0 and lon != 0:
                    data.append({
                        'id': cam.id,
                        'id_c': cam.id_c,
                        'nome': cam.nome or f'Câmera {cam.id_c}',
                        'bairro': cam.bairro or 'Sem bairro',
                        'lat': lat,
                        'lng': lon,
                        'status': cam.status,
                        'url_stream': f'https://dev.tixxi.rio/outvideo2/?CODE={cam.id_c}&KEY=B0914'
                    })
                    bairros_set.add(cam.bairro or 'Sem bairro')
            except:
                continue
        
        return Response({
            'success': True,
            'data': data,
            'count': len(data),
            'bairros': sorted(list(bairros_set))
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def api_sirenes(request):
    """API de sirenes"""
    try:
        from aplicativo.models import Sirene
        
        sirenes = Sirene.objects.all()
        data = []
        
        for s in sirenes:
            try:
                data.append({
                    'id': s.id,
                    'nome': s.nome or f'Sirene {s.id}',
                    'endereco': s.endereco if hasattr(s, 'endereco') else '',
                    'bairro': s.bairro if hasattr(s, 'bairro') else '',
                    'lat': float(s.lat) if s.lat else None,
                    'lng': float(s.lon) if s.lon else None,
                    'status': s.status if hasattr(s, 'status') else 'inativa',
                    'prioridade': s.prioridade if hasattr(s, 'prioridade') else 'média'
                })
            except:
                continue
        
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def api_pluviometros(request):
    """API de pluviômetros"""
    try:
        from aplicativo.models import EstacaoPlv
        
        pluviometros = EstacaoPlv.objects.all()
        data = []
        
        for p in pluviometros:
            try:
                data.append({
                    'id': p.id,
                    'nome': p.nome if hasattr(p, 'nome') else f'Pluviômetro {p.id}',
                    'lat': float(p.lat) if hasattr(p, 'lat') and p.lat else None,
                    'lng': float(p.lon) if hasattr(p, 'lon') and p.lon else None,
                    'chuva_1h': float(p.chuva_1h) if hasattr(p, 'chuva_1h') and p.chuva_1h else 0,
                    'chuva_4h': float(p.chuva_4h) if hasattr(p, 'chuva_4h') and p.chuva_4h else 0,
                    'chuva_24h': float(p.chuva_24h) if hasattr(p, 'chuva_24h') and p.chuva_24h else 0,
                    'chuva_96h': float(p.chuva_96h) if hasattr(p, 'chuva_96h') and p.chuva_96h else 0,
                    'data': p.data.strftime('%d/%m/%Y %H:%M') if hasattr(p, 'data') and p.data else 'N/A'
                })
            except:
                continue
        
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def api_ventos(request):
    """API de estações meteorológicas"""
    try:
        from aplicativo.models import EstacaoMet
        
        estacoes = EstacaoMet.objects.all()
        data = []
        
        for e in estacoes:
            try:
                data.append({
                    'id': e.id,
                    'nome': e.nome if hasattr(e, 'nome') else f'Estação {e.id}',
                    'lat': float(e.lat) if hasattr(e, 'lat') and e.lat else None,
                    'lng': float(e.lon) if hasattr(e, 'lon') and e.lon else None,
                    'velocidade': float(e.velocidade) if hasattr(e, 'velocidade') and e.velocidade else 0,
                    'direcao': e.direcao if hasattr(e, 'direcao') else 'N/A',
                    'temperatura': float(e.temperatura) if hasattr(e, 'temperatura') and e.temperatura else 0,
                    'umidade': float(e.umidade) if hasattr(e, 'umidade') and e.umidade else 0,
                    'data': e.data.strftime('%d/%m/%Y %H:%M') if hasattr(e, 'data') and e.data else 'N/A'
                })
            except:
                continue
        
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


# ===== VIEWS DE METEOROLOGIA =====

def meteorologia_dashboard_view(request):
    """Dashboard de Meteorologia"""
    return render(request, 'mapa_novo/meteorologia_dashboard.html')


@api_view(['GET'])
def api_previsao_tempo(request):
    """API de previsão do tempo (dados simulados por enquanto)"""
    try:
        # Dados de previsão para próximos 5 dias
        previsao = [
            {
                'dia': 'Segunda',
                'data': '28/10',
                'temp_min': 22,
                'temp_max': 28,
                'condicao': 'Parcialmente nublado',
                'icone': 'cloud-sun',
                'chuva_prob': 30,
                'umidade': 65
            },
            {
                'dia': 'Terça',
                'data': '29/10',
                'temp_min': 21,
                'temp_max': 27,
                'condicao': 'Chuva leve',
                'icone': 'cloud-drizzle',
                'chuva_prob': 70,
                'umidade': 75
            },
            {
                'dia': 'Quarta',
                'data': '30/10',
                'temp_min': 20,
                'temp_max': 26,
                'condicao': 'Nublado',
                'icone': 'cloud',
                'chuva_prob': 50,
                'umidade': 70
            },
            {
                'dia': 'Quinta',
                'data': '31/10',
                'temp_min': 23,
                'temp_max': 29,
                'condicao': 'Ensolarado',
                'icone': 'sun',
                'chuva_prob': 10,
                'umidade': 55
            },
            {
                'dia': 'Sexta',
                'data': '01/11',
                'temp_min': 24,
                'temp_max': 30,
                'condicao': 'Ensolarado',
                'icone': 'sun',
                'chuva_prob': 5,
                'umidade': 50
            }
        ]
        
        return Response({
            'success': True,
            'data': previsao
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_historico_chuva(request):
    """API de histórico de chuva - últimas 24 horas"""
    try:
        from aplicativo.models import DadosPlv
        from datetime import datetime, timedelta
        
        # Pegar dados das últimas 24 horas
        data_limite = datetime.now() - timedelta(hours=24)
        
        dados = DadosPlv.objects.filter(
            data__gte=data_limite
        ).order_by('data')[:100]
        
        historico = []
        for d in dados:
            historico.append({
                'hora': d.data.strftime('%H:%M') if d.data else 'N/A',
                'chuva_1h': float(d.chuva_1 or 0),
                'estacao': d.estacao.nome if hasattr(d, 'estacao') else 'N/A'
            })
        
        return Response({
            'success': True,
            'data': historico
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)


@api_view(['GET'])
def api_alertas_meteorologicos(request):
    """API de alertas meteorológicos ativos"""
    try:
        from aplicativo.models import EstacaoPlv, DadosPlv
        
        alertas = []
        
        # Verificar estações com chuva forte
        estacoes = EstacaoPlv.objects.all()
        
        for estacao in estacoes:
            ultimo = DadosPlv.objects.filter(estacao=estacao).order_by('-data').first()
            
            if ultimo:
                chuva_1h = float(ultimo.chuva_1 or 0)
                
                if chuva_1h >= 25:
                    alertas.append({
                        'tipo': 'Chuva Forte',
                        'nivel': 'alto',
                        'estacao': estacao.nome,
                        'valor': chuva_1h,
                        'mensagem': f'Chuva forte de {chuva_1h}mm em {estacao.nome}',
                        'icone': 'cloud-rain-heavy'
                    })
                elif chuva_1h >= 10:
                    alertas.append({
                        'tipo': 'Chuva Moderada',
                        'nivel': 'medio',
                        'estacao': estacao.nome,
                        'valor': chuva_1h,
                        'mensagem': f'Chuva moderada de {chuva_1h}mm em {estacao.nome}',
                        'icone': 'cloud-rain'
                    })
        
        return Response({
            'success': True,
            'data': alertas,
            'count': len(alertas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e),
            'data': []
        }, status=500)

# ===== VIEWS DE MOBILIDADE URBANA =====

def mobilidade_dashboard_view(request):
    return render(request, 'mapa_novo/mobilidade_dashboard.html')  # ← NOME REAL DO ARQUIVO


@api_view(['GET'])
def api_brt_linhas(request):
    """API de linhas de BRT"""
    try:
        # Dados das principais linhas de BRT do Rio
        linhas = [
            {
                'id': 1,
                'nome': 'TransOeste',
                'cor': '#0066cc',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 59,
                'extensao': '56 km',
                'tempo_medio': '85 min',
                'intervalo': '5-10 min'
            },
            {
                'id': 2,
                'nome': 'TransCarioca',
                'cor': '#ff6600',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 45,
                'extensao': '39 km',
                'tempo_medio': '60 min',
                'intervalo': '4-8 min'
            },
            {
                'id': 3,
                'nome': 'TransOlímpica',
                'cor': '#00cc66',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 18,
                'extensao': '26 km',
                'tempo_medio': '35 min',
                'intervalo': '6-12 min'
            },
            {
                'id': 4,
                'nome': 'TransBrasil',
                'cor': '#cc0000',
                'status': 'Em Obras',
                'status_code': 'obras',
                'estacoes': 28,
                'extensao': '32 km',
                'tempo_medio': 'N/A',
                'intervalo': 'N/A'
            }
        ]
        
        return Response({
            'success': True,
            'data': linhas,
            'count': len(linhas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_metro_linhas(request):
    """API de linhas de Metrô"""
    try:
        linhas = [
            {
                'id': 1,
                'numero': '1',
                'nome': 'Linha 1 (Laranja)',
                'cor': '#ff6600',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 19,
                'extensao': '19,8 km',
                'intervalo': '3-5 min',
                'origem': 'Uruguai',
                'destino': 'General Osório'
            },
            {
                'id': 2,
                'numero': '2',
                'nome': 'Linha 2 (Verde)',
                'cor': '#00aa00',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 18,
                'extensao': '22,8 km',
                'intervalo': '4-6 min',
                'origem': 'Pavuna',
                'destino': 'Botafogo'
            },
            {
                'id': 3,
                'numero': '4',
                'nome': 'Linha 4 (Amarela)',
                'cor': '#ffcc00',
                'status': 'Operação Normal',
                'status_code': 'normal',
                'estacoes': 6,
                'extensao': '16 km',
                'intervalo': '5-8 min',
                'origem': 'Ipanema',
                'destino': 'Jardim Oceânico'
            }
        ]
        
        return Response({
            'success': True,
            'data': linhas,
            'count': len(linhas)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_bike_rio(request):
    """API de estações Bike Rio"""
    try:
        # Dados simulados de estações Bike Rio
        estacoes = [
            {
                'id': 1,
                'nome': 'Copacabana - Posto 5',
                'bairro': 'Copacabana',
                'bikes_disponiveis': 12,
                'vagas_disponiveis': 8,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9876,
                'lng': -43.1902
            },
            {
                'id': 2,
                'nome': 'Ipanema - Posto 9',
                'bairro': 'Ipanema',
                'bikes_disponiveis': 5,
                'vagas_disponiveis': 15,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9833,
                'lng': -43.2043
            },
            {
                'id': 3,
                'nome': 'Leblon - Posto 12',
                'bairro': 'Leblon',
                'bikes_disponiveis': 0,
                'vagas_disponiveis': 18,
                'total_vagas': 18,
                'status': 'Sem Bikes',
                'lat': -22.9844,
                'lng': -43.2200
            },
            {
                'id': 4,
                'nome': 'Botafogo - Metrô',
                'bairro': 'Botafogo',
                'bikes_disponiveis': 18,
                'vagas_disponiveis': 2,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9519,
                'lng': -43.1822
            },
            {
                'id': 5,
                'nome': 'Centro - Praça XV',
                'bairro': 'Centro',
                'bikes_disponiveis': 7,
                'vagas_disponiveis': 13,
                'total_vagas': 20,
                'status': 'Operando',
                'lat': -22.9035,
                'lng': -43.1737
            }
        ]
        
        return Response({
            'success': True,
            'data': estacoes,
            'count': len(estacoes),
            'total_bikes': sum(e['bikes_disponiveis'] for e in estacoes),
            'total_vagas': sum(e['total_vagas'] for e in estacoes)
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def api_transito_status(request):
    """API de status geral do trânsito"""
    try:
        # Status simulado baseado em horário
        from datetime import datetime
        
        hora_atual = datetime.now().hour
        
        # Definir status baseado no horário
        if (7 <= hora_atual <= 9) or (17 <= hora_atual <= 19):
            nivel = 3  # Intenso
            descricao = 'Trânsito Intenso'
            cor = '#ef4444'
        elif (10 <= hora_atual <= 16) or (20 <= hora_atual <= 22):
            nivel = 2  # Moderado
            descricao = 'Trânsito Moderado'
            cor = '#f59e0b'
        else:
            nivel = 1  # Leve
            descricao = 'Trânsito Leve'
            cor = '#10b981'
        
        return Response({
            'success': True,
            'data': {
                'nivel': nivel,
                'descricao': descricao,
                'cor': cor,
                'hora': hora_atual,
                'lentidao_km': nivel * 15,  # km de lentidão
                'velocidade_media': 45 - (nivel * 10)  # km/h
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
        
        
def waze_alerts_api(request):
    """
    API compatível com o frontend - redireciona para waze_data_view
    """
    try:
        import requests
        
        # Usar a URL oficial do parceiro Waze do Rio
        url = "https://www.waze.com/row-partnerhub-api/partners/14420996249/waze-feeds/c5c19146-e0f9-44a7-9815-3862c8a6ed67?format=1"
        
        print('🚗 Buscando dados do Waze...')
        print(f'📡 URL: {url}')
        
        response = requests.get(url, timeout=15)
        
        print(f'✅ Status: {response.status_code}')
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': f'Waze API retornou status {response.status_code}',
                'data': []
            })
        
        data = response.json()
        
        print(f'📦 Dados recebidos: {len(data.get("alerts", []))} alertas, {len(data.get("jams", []))} congestionamentos')
        
        # Processar alertas
        alerts = []
        
        for alert in data.get('alerts', []):
            alerts.append({
                'id': alert.get('uuid', ''),
                'type': alert.get('type', 'UNKNOWN'),
                'subtype': alert.get('subtype', ''),
                'location': {
                    'x': alert.get('location', {}).get('x'),
                    'y': alert.get('location', {}).get('y')
                },
                'street': alert.get('street', ''),
                'city': alert.get('city', ''),
                'reportDescription': alert.get('reportDescription', ''),
                'reliability': alert.get('reliability', 0),
                'confidence': alert.get('confidence', 0),
                'nThumbsUp': alert.get('nThumbsUp', 0),
                'pubMillis': alert.get('pubMillis', 0)
            })
        
        # Processar congestionamentos
        for jam in data.get('jams', []):
            line = jam.get('line', [])
            if line and len(line) > 0:
                mid_point = line[len(line) // 2]
                alerts.append({
                    'id': jam.get('uuid', ''),
                    'type': 'JAM',
                    'subtype': f"Nível {jam.get('level', 0)}",
                    'location': {
                        'x': mid_point.get('x'),
                        'y': mid_point.get('y')
                    },
                    'street': jam.get('street', ''),
                    'city': jam.get('city', ''),
                    'reportDescription': f"Congestionamento - Velocidade: {jam.get('speedKMH', 0)} km/h",
                    'reliability': jam.get('reliability', 0),
                    'confidence': 10,
                    'nThumbsUp': 0,
                    'pubMillis': jam.get('pubMillis', 0)
                })
        
        print(f'✅ Total de alertas processados: {len(alerts)}')
        
        return JsonResponse({
            'success': True,
            'data': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.exceptions.Timeout:
        print('❌ Timeout!')
        return JsonResponse({
            'success': False,
            'error': 'Timeout ao conectar com Waze',
            'data': []
        })
    except Exception as e:
        print(f'❌ Erro: {str(e)}')
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'data': []
        })


@csrf_exempt
def chuva_api(request):
    """API de dados de chuva/pluviômetros"""
    try:
        # TODO: Substituir por dados reais do banco
        # Por enquanto, dados de exemplo
        
        pluviometros = [
            {
                'id': 1,
                'nome': 'Alto da Boa Vista',
                'lat': -22.9667,
                'lng': -43.2833,
                'chuva_15min': 12.5,
                'chuva_1h': 25.3,
                'chuva_24h': 45.8
            },
            {
                'id': 2,
                'nome': 'Tijuca',
                'lat': -22.9333,
                'lng': -43.2333,
                'chuva_15min': 8.2,
                'chuva_1h': 18.7,
                'chuva_24h': 32.4
            },
            {
                'id': 3,
                'nome': 'Copacabana',
                'lat': -22.9711,
                'lng': -43.1822,
                'chuva_15min': 2.1,
                'chuva_1h': 5.3,
                'chuva_24h': 12.7
            },
            {
                'id': 4,
                'nome': 'Barra da Tijuca',
                'lat': -23.0050,
                'lng': -43.3650,
                'chuva_15min': 0.5,
                'chuva_1h': 1.2,
                'chuva_24h': 3.8
            },
            {
                'id': 5,
                'nome': 'Jacarepaguá',
                'lat': -22.9211,
                'lng': -43.3628,
                'chuva_15min': 15.8,
                'chuva_1h': 32.4,
                'chuva_24h': 56.9
            },
            {
                'id': 6,
                'nome': 'Centro',
                'lat': -22.9068,
                'lng': -43.1729,
                'chuva_15min': 6.3,
                'chuva_1h': 14.5,
                'chuva_24h': 28.2
            },
        ]
        
        # Estatísticas gerais
        stats = {
            'temperatura_media': 25.3,
            'umidade_media': 68,
            'chuva_24h': sum(p['chuva_24h'] for p in pluviometros) / len(pluviometros),
            'vento_velocidade': 15
        }
        
        return JsonResponse({
            'success': True,
            'data': pluviometros,
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def alertas_api(request):
    """API de alertas meteorológicos"""
    try:
        # TODO: Substituir por dados reais do banco
        # Por enquanto, dados de exemplo
        
        alertas = [
            {
                'id': 1,
                'tipo': 'chuva_forte',
                'severidade': 'alta',
                'titulo': 'Chuva Forte',
                'mensagem': 'Chuva forte prevista para as próximas horas',
                'regiao': 'Zona Norte',
                'lat': -22.9333,
                'lng': -43.2333
            },
            {
                'id': 2,
                'tipo': 'alagamento',
                'severidade': 'media',
                'titulo': 'Risco de Alagamento',
                'mensagem': 'Pontos de alagamento reportados',
                'regiao': 'Zona Sul',
                'lat': -22.9711,
                'lng': -43.1822
            }
        ]
        
        return JsonResponse({
            'success': True,
            'alertas': alertas,
            'total': len(alertas),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'alertas': []
        }, status=500)


@csrf_exempt
def estagio_api(request):
    """API de estágio operacional"""
    try:
        estagios = ['Normalidade', 'Atenção', 'Alerta', 'Crise', 'Mobilização']
        
        return JsonResponse({
            'success': True,
            'estagio': 'Atenção',
            'nivel': 2,
            'descricao': 'Chuva moderada em algumas regiões',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        

        
        
@csrf_exempt
def chuva_api(request):
    """API de dados de chuva/pluviômetros"""
    import random
    
    # 30 pluviômetros cobrindo toda a cidade do Rio
    pluviometros = [
        # ZONA NORTE
        {'id': 1, 'nome': 'Tijuca', 'lat': -22.9333, 'lng': -43.2333, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 2, 'nome': 'Maracanã', 'lat': -22.9122, 'lng': -43.2302, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 3, 'nome': 'São Cristóvão', 'lat': -22.8994, 'lng': -43.2228, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 4, 'nome': 'Méier', 'lat': -22.9025, 'lng': -43.2789, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        {'id': 5, 'nome': 'Vila Isabel', 'lat': -22.9164, 'lng': -43.2456, 
         'chuva_15min': random.uniform(0, 15), 'chuva_1h': random.uniform(5, 30), 'chuva_24h': random.uniform(10, 50)},
        
        # ZONA SUL
        {'id': 6, 'nome': 'Copacabana', 'lat': -22.9711, 'lng': -43.1822, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 7, 'nome': 'Ipanema', 'lat': -22.9838, 'lng': -43.2096, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 8, 'nome': 'Leblon', 'lat': -22.9844, 'lng': -43.2175, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 9, 'nome': 'Botafogo', 'lat': -22.9519, 'lng': -43.1828, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 10, 'nome': 'Lagoa', 'lat': -22.9711, 'lng': -43.2053, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        {'id': 11, 'nome': 'Gávea', 'lat': -22.9797, 'lng': -43.2344, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 20), 'chuva_24h': random.uniform(5, 35)},
        
        # CENTRO
        {'id': 12, 'nome': 'Centro', 'lat': -22.9068, 'lng': -43.1729, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        {'id': 13, 'nome': 'Praça XV', 'lat': -22.9033, 'lng': -43.1752, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        {'id': 14, 'nome': 'Lapa', 'lat': -22.9133, 'lng': -43.1786, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(3, 25), 'chuva_24h': random.uniform(8, 40)},
        
        # ZONA OESTE
        {'id': 15, 'nome': 'Barra da Tijuca', 'lat': -23.0050, 'lng': -43.3650, 
         'chuva_15min': random.uniform(0, 8), 'chuva_1h': random.uniform(1, 15), 'chuva_24h': random.uniform(3, 30)},
        {'id': 16, 'nome': 'Recreio', 'lat': -23.0197, 'lng': -43.4597, 
         'chuva_15min': random.uniform(0, 8), 'chuva_1h': random.uniform(1, 15), 'chuva_24h': random.uniform(3, 30)},
        {'id': 17, 'nome': 'Jacarepaguá', 'lat': -22.9211, 'lng': -43.3628, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(5, 28), 'chuva_24h': random.uniform(10, 55)},
        {'id': 18, 'nome': 'Cidade de Deus', 'lat': -22.9456, 'lng': -43.3592, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(5, 28), 'chuva_24h': random.uniform(10, 55)},
        {'id': 19, 'nome': 'Campo Grande', 'lat': -22.9009, 'lng': -43.5615, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 22), 'chuva_24h': random.uniform(8, 45)},
        {'id': 20, 'nome': 'Bangu', 'lat': -22.8719, 'lng': -43.4664, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 22), 'chuva_24h': random.uniform(8, 45)},
        
        # REGIÕES MONTANHOSAS (mais chuva)
        {'id': 21, 'nome': 'Alto da Boa Vista', 'lat': -22.9667, 'lng': -43.2833, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 22, 'nome': 'Floresta da Tijuca', 'lat': -22.9442, 'lng': -43.2633, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 23, 'nome': 'Vista Chinesa', 'lat': -22.9583, 'lng': -43.2361, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        {'id': 24, 'nome': 'Corcovado', 'lat': -22.9519, 'lng': -43.2106, 
         'chuva_15min': random.uniform(5, 25), 'chuva_1h': random.uniform(15, 45), 'chuva_24h': random.uniform(30, 80)},
        
        # ILHA DO GOVERNADOR
        {'id': 25, 'nome': 'Ilha do Governador', 'lat': -22.8147, 'lng': -43.2108, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 18), 'chuva_24h': random.uniform(5, 35)},
        {'id': 26, 'nome': 'Galeão', 'lat': -22.8094, 'lng': -43.2436, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(2, 18), 'chuva_24h': random.uniform(5, 35)},
        
        # SUBÚRBIOS
        {'id': 27, 'nome': 'Penha', 'lat': -22.8436, 'lng': -43.2775, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 28, 'nome': 'Pavuna', 'lat': -22.8117, 'lng': -43.3539, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 29, 'nome': 'Irajá', 'lat': -22.8328, 'lng': -43.3264, 
         'chuva_15min': random.uniform(0, 12), 'chuva_1h': random.uniform(4, 24), 'chuva_24h': random.uniform(10, 48)},
        {'id': 30, 'nome': 'Santa Cruz', 'lat': -22.9197, 'lng': -43.6836, 
         'chuva_15min': random.uniform(0, 10), 'chuva_1h': random.uniform(3, 20), 'chuva_24h': random.uniform(7, 42)},
    ]
    
    stats = {
        'temperatura_media': round(random.uniform(22, 28), 1),
        'umidade_media': random.randint(60, 85),
        'chuva_24h': round(sum(p['chuva_24h'] for p in pluviometros) / len(pluviometros), 1),
        'vento_velocidade': random.randint(10, 25)
    }
    
    return JsonResponse({
        'success': True,
        'data': pluviometros,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })

@csrf_exempt
def alertas_api(request):
    """API de alertas"""
    alertas = [
        {'id': 1, 'tipo': 'chuva_forte', 'severidade': 'alta', 
         'titulo': 'Chuva Forte', 'mensagem': 'Chuva forte prevista',
         'regiao': 'Zona Norte', 'lat': -22.9333, 'lng': -43.2333},
        {'id': 2, 'tipo': 'alagamento', 'severidade': 'media',
         'titulo': 'Risco de Alagamento', 'mensagem': 'Pontos de alagamento',
         'regiao': 'Zona Sul', 'lat': -22.9711, 'lng': -43.1822}
    ]
    
    return JsonResponse({
        'success': True,
        'alertas': alertas,
        'total': len(alertas),
        'timestamp': datetime.now().isoformat()
    })


 #VIDEO MONITORAMENTO - SEM LOGIN
def videomonitoramento(request):
    return render(request, 'mapa_novo/videomonitoramento.html')

# API DE CAMERAS - SEM LOGIN
@csrf_exempt
def cameras_api_local(request):
    import requests
    try:
        response = requests.get('https://aplicativo.cocr.com.br/cameras_api', timeout=10)
        return JsonResponse(response.json(), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def chuva_api(request):
    pluviometros = [
        {'id': 1, 'nome': 'Alto da Boa Vista', 'lat': -22.9667, 'lng': -43.2833, 
         'chuva_15min': 12.5, 'chuva_1h': 25.3, 'chuva_24h': 45.8},
        {'id': 2, 'nome': 'Tijuca', 'lat': -22.9333, 'lng': -43.2333, 
         'chuva_15min': 8.2, 'chuva_1h': 18.7, 'chuva_24h': 32.4},
    ]
    return JsonResponse({'success': True, 'data': pluviometros, 
        'stats': {'temperatura_media': 25.3, 'umidade_media': 68, 'chuva_24h': 29.1, 'vento_velocidade': 15}})

@csrf_exempt
def alertas_api(request):
    alertas = [{'id': 1, 'tipo': 'chuva_forte', 'titulo': 'Chuva Forte', 
                'mensagem': 'Chuva forte prevista', 'lat': -22.9333, 'lng': -43.2333}]
    return JsonResponse({'success': True, 'alertas': alertas, 'total': 1})


# VIDEO - SEM LOGIN - DEFINITIVO
def video_dashboard(request):
    return render(request, 'mapa_novo/videomonitoramento.html')

def api_cameras_proxy(request):
    import requests
    try:
        r = requests.get('https://aplicativo.cocr.com.br/cameras_api', timeout=10)
        return JsonResponse(r.json(), safe=False)
    except:
        return JsonResponse({'error': 'API offline'}, status=500)
    


logger = logging.getLogger(__name__)

@csrf_exempt
def estagio_proxy(request):
    """
    Proxy para API externa de estágio (API retorna só número)
    """
    try:
        logger.info('Buscando estágio da API externa...')
        
        response = requests.get(
            'http://aplicativo.cocr.com.br/estagio_api_app',
            timeout=10
        )
        
        # Verificar se deu erro
        if response.status_code != 200:
            logger.error(f'API retornou status {response.status_code}')
            return JsonResponse({
                'cor': '#10b981',
                'estagio': 'Estágio 1',
                'mensagem': '',
                'mensagem2': '',
                'id': 1,
                'inicio': timezone.now().isoformat(),
                'fallback': True
            })
        
        # API retorna só o número (ex: "1")
        numero_estagio = int(response.text.strip())
        
        # Mapeamento de cores por nível
        cores = {
            1: '#10b981',  # Verde
            2: '#fbbf24',  # Amarelo
            3: '#f97316',  # Laranja
            4: '#ef4444',  # Vermelho
            5: '#dc2626'   # Vermelho escuro
        }
        
        # Construir resposta completa
        data = {
            'cor': cores.get(numero_estagio, '#10b981'),
            'estagio': f'Estágio {numero_estagio}',
            'mensagem': '',
            'mensagem2': '',
            'id': numero_estagio,
            'inicio': timezone.now().isoformat()
        }
        
        logger.info(f'Estágio recebido: {numero_estagio}')
        return JsonResponse(data)
        
    except requests.exceptions.Timeout:
        logger.error('Timeout ao buscar API externa')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'API temporariamente indisponível',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        })
        
    except ValueError as e:
        logger.error(f'Erro ao converter número do estágio: {str(e)}')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Formato inválido da API',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        }, status=500)
        
    except Exception as e:
        logger.error(f'Erro ao buscar estágio: {str(e)}')
        return JsonResponse({
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Erro ao buscar estágio',
            'mensagem2': '',
            'id': 1,
            'inicio': timezone.now().isoformat(),
            'fallback': True
        }, status=500)
        
        # Se API retornar erro 500
        if response.status_code != 200:
            logger.error(f'API externa retornou status {response.status_code}')
            # Retornar valores padrão
            return JsonResponse({
                'cor': '#10b981',
                'estagio': 'Estágio 1',
                'mensagem': '',
                'mensagem2': '',
                'id': 1,
                'inicio': '2025-11-09T18:00:00Z',
                'fallback': True  # Indica que é valor padrão
            })
        
        data = response.json()
        logger.info(f'Estágio recebido: {data.get("estagio")}')
        
        return JsonResponse(data)
        
    except requests.exceptions.Timeout:
        logger.error('Timeout ao buscar API externa')
        return JsonResponse({
            'error': 'Timeout',
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'API temporariamente indisponível',
            'mensagem2': '',
            'id': 1,
            'inicio': '2025-11-09T18:00:00Z',
            'fallback': True
        })
        
    except Exception as e:
        logger.error(f'Erro ao buscar estágio: {str(e)}')
        return JsonResponse({
            'error': str(e),
            'cor': '#10b981',
            'estagio': 'Estágio 1',
            'mensagem': 'Erro ao buscar estágio',
            'mensagem2': '',
            'id': 1,
            'inicio': '2025-11-09T18:00:00Z',
            'fallback': True
        }, status=500)

