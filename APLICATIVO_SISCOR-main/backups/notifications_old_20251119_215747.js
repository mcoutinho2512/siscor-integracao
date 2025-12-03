/**
 * notifications.js - Sistema de Notificações em Tempo Real
 */

class NotificationsSystem {
    constructor() {
        this.panel = document.getElementById('notifications-panel');
        this.toggle = document.getElementById('notifications-toggle');
        this.list = document.getElementById('notifications-list');
        this.badge = document.getElementById('notification-count');
        this.notifications = [];
        this.unreadCount = 0;
        this.readIds = new Set(this.loadReadIds());
        this.lastNotificationIds = new Set();

        this.init();
    }

    init() {
        // Toggle painel
        if (this.toggle) {
            this.toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.togglePanel();
            });
        }

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (this.panel && !this.panel.contains(e.target) && !this.toggle.contains(e.target)) {
                this.panel.classList.remove('active');
            }
        });

        // Filtros
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.filterNotifications(e.target.dataset.filter));
        });

        // Marcar todas como lidas
        const markAllBtn = document.getElementById('mark-all-read');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => this.markAllRead());
        }

        // Carregar notificações imediatamente
        this.loadNotifications();

        // Atualizar a cada 30 segundos
        setInterval(() => this.loadNotifications(), 30000);

        console.log('✅ Sistema de notificações inicializado');
    }

    togglePanel() {
        if (!this.panel) return;

        this.panel.classList.toggle('active');

        // Quando abre o painel, marca visíveis como lidas
        if (this.panel.classList.contains('active')) {
            setTimeout(() => this.markVisibleAsRead(), 500);
        }
    }

    loadReadIds() {
        try {
            const saved = localStorage.getItem('readNotifications');
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.warn('⚠️ Erro ao carregar notificações lidas');
            return [];
        }
    }

    saveReadIds() {
        try {
            localStorage.setItem('readNotifications', JSON.stringify([...this.readIds]));
        } catch (e) {
            console.warn('⚠️ Erro ao salvar notificações lidas');
        }
    }

    async loadNotifications() {
        try {
            const [ocorrenciasRes, sirenesRes] = await Promise.all([
                fetch('/api/ocorrencias/'),
                fetch('/api/sirenes/')
            ]);

            const ocorrencias = await ocorrenciasRes.json();
            const sirenes = await sirenesRes.json();

            const newNotifications = [];
            const currentIds = new Set();

            // Adicionar ocorrências
            if (ocorrencias.success && ocorrencias.data) {
                ocorrencias.data.slice(0, 20).forEach(o => {
                    const id = `ocorrencia-${o.id}`;
                    currentIds.add(id);

                    newNotifications.push({
                        id: id,
                        type: 'ocorrencia',
                        title: o.tipo || 'Ocorrência',
                        content: o.descricao || o.location,
                        location: o.location,
                        priority: o.prioridade,
                        timestamp: new Date(o.data_criacao || new Date()),
                        time: this.getRelativeTime(o.data_criacao || new Date()),
                        unread: !this.readIds.has(id)
                    });
                });
            }

            // Adicionar sirenes ativas
            if (sirenes.success && sirenes.data) {
                const ativas = sirenes.data.filter(s => s.status === 'ativa');
                ativas.slice(0, 10).forEach(s => {
                    const id = `sirene-${s.id}`;
                    currentIds.add(id);

                    newNotifications.push({
                        id: id,
                        type: 'sirene',
                        title: 'Sirene Ativada',
                        content: s.nome,
                        location: s.endereco,
                        priority: 'ALTA',
                        timestamp: new Date(),
                        time: 'Agora',
                        unread: !this.readIds.has(id)
                    });
                });
            }

            // Detectar novas notificações
            const hasNewNotifications = [...currentIds].some(id => !this.lastNotificationIds.has(id));

            if (hasNewNotifications && this.lastNotificationIds.size > 0) {
                this.showNewNotificationAlert();
            }

            this.lastNotificationIds = currentIds;
            this.notifications = newNotifications.sort((a, b) => b.timestamp - a.timestamp);
            this.unreadCount = this.notifications.filter(n => n.unread).length;

            this.updateCounter();
            this.renderNotifications();

        } catch (error) {
            console.error('Erro ao carregar notificações:', error);
        }
    }

    showNewNotificationAlert() {
        // Animar o botão
        if (this.toggle) {
            this.toggle.classList.add('has-notifications');

            // Tocar som (opcional)
            // const audio = new Audio('/static/sounds/notification.mp3');
            // audio.play().catch(() => {});
        }

        console.log('🔔 Nova notificação recebida!');
    }

    markVisibleAsRead() {
        let changed = false;

        this.notifications.forEach(n => {
            if (n.unread) {
                this.readIds.add(n.id);
                n.unread = false;
                changed = true;
            }
        });

        if (changed) {
            this.saveReadIds();
            this.unreadCount = 0;
            this.updateCounter();
            this.renderNotifications();
            console.log('✅ Notificações visíveis marcadas como lidas');
        }
    }

    renderNotifications(filter = 'all') {
        if (!this.list) return;

        let filtered = this.notifications;

        if (filter === 'criticas') {
            filtered = this.notifications.filter(n =>
                n.priority === 'ALTA' || n.priority === 'MUITO ALTA'
            );
        } else if (filter !== 'all') {
            filtered = this.notifications.filter(n =>
                n.type === filter || n.type === filter.slice(0, -1)
            );
        }

        if (filtered.length === 0) {
            this.list.innerHTML = `
                <div class="notifications-empty">
                    <i class="bi bi-bell-slash"></i>
                    <p>Nenhuma notificação</p>
                </div>
            `;
            return;
        }

        this.list.innerHTML = filtered.map(n => this.renderNotification(n)).join('');
    }

    renderNotification(n) {
        const icon = n.type === 'sirene' ? 'megaphone-fill' : 'exclamation-triangle-fill';
        const typeClass = n.type === 'sirene' ? 'sirene' :
            (n.priority === 'ALTA' || n.priority === 'MUITO ALTA') ? 'critica' : '';

        return `
            <div class="notification-item ${n.unread ? 'unread' : ''} ${typeClass}" data-id="${n.id}">
                <div class="notification-header">
                    <div class="notification-type">
                        <i class="bi bi-${icon}"></i>
                        ${n.title}
                    </div>
                    <div class="notification-time">${n.time}</div>
                </div>
                <div class="notification-content">${n.content}</div>
                ${n.location ? `<div class="notification-location"><i class="bi bi-geo-alt"></i> ${n.location}</div>` : ''}
            </div>
        `;
    }

    filterNotifications(filter) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });

        this.renderNotifications(filter);
    }

    markAllRead() {
        this.notifications.forEach(n => {
            n.unread = false;
            this.readIds.add(n.id);
        });

        this.saveReadIds();
        this.unreadCount = 0;
        this.updateCounter();
        this.renderNotifications();

        console.log('✅ Todas notificações marcadas como lidas');
    }

    updateCounter() {
        console.log('🔄 updateCounter chamado, unreadCount:', this.unreadCount);

        // Procurar badge novamente para garantir
        this.badge = document.getElementById('notification-count');

        if (!this.badge) {
            console.error('❌ Badge não encontrado!');
            return;
        }

        console.log('✅ Badge encontrado:', this.badge);

        if (this.unreadCount > 0) {
            this.badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            this.badge.classList.remove('hidden');
            this.badge.style.display = 'flex';
            console.log('📊 Badge atualizado para:', this.badge.textContent);
        } else {
            this.badge.textContent = '0';
            this.badge.classList.add('hidden');
            this.badge.style.display = 'none';
            console.log('✅ Badge escondido (0 notificações)');
        }

        // Atualizar classe do botão
        if (this.toggle) {
            if (this.unreadCount > 0) {
                this.toggle.classList.add('has-notifications');
            } else {
                this.toggle.classList.remove('has-notifications');
            }
        }
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = Math.floor((now - new Date(date)) / 1000);

        if (diff < 60) return 'Agora';
        if (diff < 3600) return Math.floor(diff / 60) + ' min atrás';
        if (diff < 86400) return Math.floor(diff / 3600) + 'h atrás';
        return Math.floor(diff / 86400) + 'd atrás';
    }
}

// Inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.notificationsSystem = new NotificationsSystem();
    });
} else {
    window.notificationsSystem = new NotificationsSystem();
}

console.log('✅ notifications.js carregado');