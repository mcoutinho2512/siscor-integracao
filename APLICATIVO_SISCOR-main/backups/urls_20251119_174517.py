from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from aplicativo import views

urlpatterns = [
    # ============================================
    # AUTENTICAÇÃO - PÁGINA PRINCIPAL
    # ============================================
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ============================================
    # PÁGINAS DO SISTEMA (PROTEGIDAS)
    # ============================================
    path('home/', views.waze_dashboard_view, name='home'),
    path('waze-dashboard/', views.waze_dashboard_view, name='waze_dashboard'),
    path('cor/', views.cor_dashboard_view, name='cor_dashboard'),
    path('mobilidade/', views.mobilidade_dashboard_view, name='mobilidade_dashboard'),
    path('meteorologia/', views.meteorologia_dashboard_view, name='meteorologia_dashboard'),
    path('videomonitoramento/', views.videomonitoramento, name='videomonitoramento'),
    
    # ============================================
    # APIs - Estágios
    # ============================================
    path('api/estagio-externo/', views.estagio_proxy, name='estagio_proxy'),
    path('api/estagio/', views.estagio_api, name='estagio_api'),
    path('api/estagio/app/', views.estagio_api_app, name='estagio_api_app'),
    path('api/estagio-atual/', views.api_estagio_atual, name='api_estagio_atual'),
    path('alertas_api/', views.alertas_api, name='alertas_api_compat'),
    path('estagio_api/', views.estagio_api, name='estagio_api_compat'),
    
    # ============================================
    # APIs - Sirenes
    # ============================================
    path('api/sirenes/', views.sirene_api, name='sirene_api'),
    
    # ============================================
    # APIs - Meteorologia
    # ============================================
    path('api/chuva/', views.chuva_api, name='chuva_api'),
    path('api/alertas/', views.alertas_api, name='api_alertas'),
]

# Arquivos estáticos em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)