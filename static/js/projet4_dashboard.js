// Configuration globale
const config = {
    apiBaseUrl: '/projet4/api',
    refreshInterval: 300000 // 5 minutes
};

// Fonction pour formater la date
function formatDate(dateString) {
    if (!dateString) return 'Non spécifié';
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Date invalide';
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('Erreur de formatage de la date:', error);
        return 'Date invalide';
    }
}

// Fonction pour charger les actions
async function loadActions() {
    try {
        const response = await fetch(`${config.apiBaseUrl}/actions/a_venir`);
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des actions');
        }
        const actions = await response.json();
        displayActions(actions);
    } catch (error) {
        console.error('Erreur:', error);
        const tbody = document.querySelector('#actionsTable tbody');
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Erreur lors du chargement des actions</td></tr>';
    }
}

// Fonction pour afficher les actions
function displayActions(actions) {
    const tbody = document.querySelector('#actionsTable tbody');
    tbody.innerHTML = '';

    if (!actions || actions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Aucune action à afficher</td></tr>';
        return;
    }

    actions.forEach(action => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${formatDate(action.date_echeance)}</td>
            <td>${action.description || 'Non spécifié'}</td>
            <td>${action.raison_sociale || 'Non spécifié'}</td>
            <td>${formatDate(action.date_visite)}</td>
            <td>${action.visiteur || 'Non spécifié'}</td>
            <td>
                <span class="badge ${getPriorityClass(action.priorite)}">
                    ${action.priorite || 'Non spécifié'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editAction(${action.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteAction(${action.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Fonction pour obtenir la classe CSS en fonction de la priorité
function getPriorityClass(priority) {
    switch (priority?.toLowerCase()) {
        case 'haute':
            return 'bg-danger';
        case 'moyenne':
            return 'bg-warning';
        case 'basse':
            return 'bg-info';
        default:
            return 'bg-secondary';
    }
}

// Fonction pour rafraîchir les actions
function refreshActions() {
    loadActions();
}

// Fonction pour supprimer une action
async function deleteAction(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette action ?')) {
        return;
    }

    try {
        const response = await fetch(`${config.apiBaseUrl}/actions/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Erreur lors de la suppression de l\'action');
        }

        // Recharger les actions après la suppression
        loadActions();
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la suppression de l\'action');
    }
}

// Fonction pour éditer une action
function editAction(id) {
    // À implémenter : redirection vers la page d'édition
    console.log('Éditer action:', id);
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Événements
    document.getElementById('btn_refresh').addEventListener('click', refreshActions);

    // Chargement initial
    loadActions();

    // Rafraîchissement automatique
    setInterval(refreshActions, config.refreshInterval);
}); 