// =============================================================================
// SISCOR - Melhorias de UI/UX (Fase 6)
// =============================================================================

(function() {
    'use strict';

    // -------------------------------------------------------------------------
    // SISTEMA DE TOAST NOTIFICATIONS
    // -------------------------------------------------------------------------
    window.SISCORToast = {
        container: null,

        init: function() {
            if (!this.container) {
                this.container = document.createElement('div');
                this.container.className = 'toast-container';
                document.body.appendChild(this.container);
            }
        },

        show: function(message, type = 'info', duration = 4000) {
            this.init();

            const toast = document.createElement('div');
            toast.className = 'toast ' + type;

            const icons = {
                success: 'bi-check-circle-fill',
                warning: 'bi-exclamation-triangle-fill',
                error: 'bi-x-circle-fill',
                info: 'bi-info-circle-fill'
            };

            toast.innerHTML = 
                '<i class="bi ' + icons[type] + '"></i>' +
                '<span>' + message + '</span>' +
                '<button class="toast-close" onclick="this.parentElement.remove()">' +
                    '<i class="bi bi-x"></i>' +
                '</button>';

            this.container.appendChild(toast);

            // Auto-remove
            setTimeout(function() {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(function() { toast.remove(); }, 300);
            }, duration);
        },

        success: function(msg) { this.show(msg, 'success'); },
        warning: function(msg) { this.show(msg, 'warning'); },
        error: function(msg) { this.show(msg, 'error'); },
        info: function(msg) { this.show(msg, 'info'); }
    };

    // -------------------------------------------------------------------------
    // LOADING STATES
    // -------------------------------------------------------------------------
    window.SISCORLoading = {
        showCard: function(cardElement) {
            if (cardElement) {
                cardElement.classList.add('loading');
            }
        },

        hideCard: function(cardElement) {
            if (cardElement) {
                cardElement.classList.remove('loading');
            }
        },

        showAll: function() {
            document.querySelectorAll('.cor-status-card').forEach(function(card) {
                card.classList.add('loading');
            });
        },

        hideAll: function() {
            document.querySelectorAll('.cor-status-card').forEach(function(card) {
                card.classList.remove('loading');
            });
        }
    };

    // -------------------------------------------------------------------------
    // ATUALIZACAO COM FEEDBACK VISUAL
    // -------------------------------------------------------------------------
    window.SISCORUpdate = {
        lastUpdate: null,

        markUpdated: function() {
            this.lastUpdate = new Date();
            
            // Mostrar indicador visual
            document.querySelectorAll('.cor-status-card').forEach(function(card) {
                card.style.animation = 'none';
                card.offsetHeight; // Trigger reflow
                card.style.animation = 'fadeInUp 0.3s ease';
            });

            // Toast opcional
            // SISCORToast.info('Dados atualizados');
        },

        getLastUpdate: function() {
            if (!this.lastUpdate) return 'Nunca';
            
            var diff = Math.floor((new Date() - this.lastUpdate) / 1000);
            if (diff < 60) return 'Agora mesmo';
            if (diff < 3600) return Math.floor(diff / 60) + ' min atras';
            return Math.floor(diff / 3600) + 'h atras';
        }
    };

    // -------------------------------------------------------------------------
    // INICIALIZACAO
    // -------------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[SISCOR] UI/UX improvements loaded');

        // Adicionar classe de animacao aos cards
        document.querySelectorAll('.cor-status-card').forEach(function(card, index) {
            card.style.animationDelay = (index * 0.05) + 's';
        });

        // Adicionar tooltips automaticos
        var tooltips = {
            '[data-card="estagio"]': 'Nivel de alerta operacional da cidade',
            '[data-card="calor"]': 'Indice de calor atual',
            '[data-card="ocorrencias"]': 'Ocorrencias abertas no momento',
            '[data-card="tempo"]': 'Condicoes meteorologicas',
            '[data-card="mobilidade"]': 'Status do transito e transporte',
            '[data-card="eventos"]': 'Eventos programados na cidade'
        };

        for (var selector in tooltips) {
            var element = document.querySelector(selector);
            if (element) {
                element.setAttribute('data-tooltip', tooltips[selector]);
            }
        }

        // Service Worker para PWA (se disponivel)
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js').then(function(reg) {
                console.log('[SISCOR] Service Worker registrado');
            }).catch(function(err) {
                // SW nao disponivel, ignorar
            });
        }
    });

})();
