// Configuration
const CONFIG = {
    API_BASE_URL: '/projet4',
    DEBUG_MODE: true
};

// =============================================
// Module de gestion des sociétés
// =============================================
const SocieteManager = {
    // Charger les détails d'une société
    async loadDetails(id) {
        if (!id) {
            console.error('ID de société manquant');
            return;
        }

        try {
            if (CONFIG.DEBUG_MODE) console.log(`Chargement des détails de la société ${id}`);
            
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/societes/${id}`);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            
            const societe = await response.json();
            if (CONFIG.DEBUG_MODE) {
                console.log('Détails de la société:', societe);
                console.log('Importance reçue:', societe.importance);
            }
            
            // Mise à jour des champs du formulaire
            document.getElementById('id_societe').value = societe.id;
            document.getElementById('raison_sociale').value = societe.raison_sociale;
            document.getElementById('ville').value = societe.ville || '';
            document.getElementById('pays_select').value = societe.id_pays || '';
            document.getElementById('telephone').value = societe.telephone || '';
            document.getElementById('fax').value = societe.fax || '';
            document.getElementById('email').value = societe.email || '';
            document.getElementById('id_categorie').value = societe.id_categorie || '';
            
            // Gestion de l'importance
            const importanceMap = {
                'Faible': '1',
                'Moyen': '2',
                'Important': '3',
                'Très important': '4',
                'Stratégique': '5'
            };
            
            let importanceId = '';
            if (societe.importance) {
                importanceId = importanceMap[societe.importance] || societe.importance;
                if (CONFIG.DEBUG_MODE) {
                    console.log('Importance convertie:', importanceId);
                }
            }
            
            const importanceEl = document.getElementById('importance');
            if (importanceEl) importanceEl.value = importanceId;
            if (CONFIG.DEBUG_MODE) {
                console.log('Valeur finale dans le select:', importanceEl ? importanceEl.value : '');
            }
            
            // Charger les contacts de la société
            ContactManager.loadContacts(id);
        } catch (error) {
            console.error('Erreur lors du chargement des détails:', error);
            alert('Erreur lors du chargement des détails de la société');
        }
    },

    // Fonction de filtrage
    async filterCompanies(query) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/societes?filter=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Erreur lors du filtrage:', error);
            return [];
        }
    },

    // Fonction de debounce pour limiter les appels
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Fonction de filtrage avec debounce
    performFilter: function(query) {
        const debouncedFilter = this.debounce(async (query) => {
            try {
                const societes = await this.filterCompanies(query);
                this.displaySearchResults(societes);
            } catch (error) {
                console.error('Erreur lors du filtrage:', error);
            }
        }, 300);
        
        debouncedFilter(query);
    },

    // Afficher les résultats de filtrage
    displaySearchResults(societes) {
        const tbody = document.getElementById('searchResults').querySelector('tbody');
        tbody.innerHTML = '';

        societes.forEach(societe => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${societe.raison_sociale}</td>
                <td>${societe.ville || ''}</td>
                <td>${societe.pays || ''}</td>
                <td>
                    <button type="button" class="btn btn-primary btn-sm" onclick="SocieteManager.selectCompany(${societe.id})">
                        <i class="fas fa-check"></i> Sélectionner
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    },

    // Sélectionner une société
    async selectCompany(id) {
        await this.loadDetails(id);
        const modalEl = document.getElementById('searchModal');
        if (modalEl) bootstrap.Modal.getOrCreateInstance(modalEl).show();
    },

    init() {
        // Vérifier si les gestionnaires d'événements sont déjà attachés
        if (this._initialized) return;
        this._initialized = true;

        // Gestion du bouton de filtrage
        const searchButton = document.getElementById('btn_search_company');
        if (searchButton) {
            searchButton.addEventListener('click', () => {
                const modalEl = document.getElementById('searchModal');
                if (modalEl) bootstrap.Modal.getOrCreateInstance(modalEl).show();
                // Déclencher le filtrage immédiatement à l'ouverture
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.value = '';
                    this.performFilter('');
                }
            });
        }

        // Gestion du filtrage
        const searchBtn = document.getElementById('btnSearch');
        const searchInput = document.getElementById('searchInput');
        
        if (searchBtn && searchInput) {
            // Gestionnaire pour le clic
            searchBtn.addEventListener('click', () => {
                const query = searchInput.value.trim();
                this.performFilter(query);
            });

            // Gestionnaire pour la touche Entrée
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const query = searchInput.value.trim();
                    this.performFilter(query);
                }
            });

            // Gestionnaire pour la saisie
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                this.performFilter(query);
            });
        }
    },

    searchCompanies: function(query) {
        const url = new URL('/projet4/api/societes', window.location.origin);
        url.searchParams.append('filter', query);
        
        return fetch(url)
            .then(response => response.json())
            .then(data => {
                return data;
            })
            .catch(error => {
                console.error('Erreur lors de la recherche:', error);
                return [];
            });
    }
};

// =============================================
// Module de gestion des contacts
// =============================================
const ContactManager = {
    // Charger les contacts d'une société
    async loadContacts(idSociete) {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/contacts?id_societe=${idSociete}`);
            const contacts = await response.json();
            
            const contactSelector = document.getElementById('contact_selector');
            contactSelector.innerHTML = '<option value="">Sélectionnez un contact</option>';
            contacts.forEach(contact => {
                const option = document.createElement('option');
                option.value = contact.id;
                option.textContent = `${contact.nom} ${contact.prenom} - ${contact.fonction || 'Sans fonction'}`;
                contactSelector.appendChild(option);
            });
            
            document.getElementById('contact_select_wrapper').style.display = 'block';

            // Ajout de l'événement de sélection du contact
            contactSelector.addEventListener('change', function() {
                const selectedContact = contacts.find(c => c.id === parseInt(this.value));
                if (selectedContact) {
                    document.getElementById('id_personne').value = selectedContact.id;
                    document.getElementById('contact_nom').value = selectedContact.nom || '';
                    document.getElementById('contact_prenom').value = selectedContact.prenom || '';
                    document.getElementById('contact_email').value = selectedContact.email || '';
                    document.getElementById('contact_telephone').value = selectedContact.telephone || '';
                    
                    // Mise à jour de la fonction
                    const fonctionSelect = document.getElementById('contact_fonction');
                    if (selectedContact.id_fonction) {
                        fonctionSelect.value = selectedContact.id_fonction;
                    } else {
                        fonctionSelect.value = '';
                    }
                }
            });
        } catch (error) {
            console.error('Erreur lors du chargement des contacts:', error);
        }
    },

    // Mettre à jour les champs du contact
    updateContactFields(contact) {
        document.getElementById('id_personne').value = contact.id;
        document.getElementById('contact_nom').value = contact.nom || '';
        document.getElementById('contact_prenom').value = contact.prenom || '';
        
        // Mise à jour de la fonction
        const fonctionSelect = document.getElementById('contact_fonction');
        if (contact.fonction) {
            // Trouver l'option correspondant à la fonction
            const options = Array.from(fonctionSelect.options);
            const matchingOption = options.find(opt => opt.text === contact.fonction);
            if (matchingOption) {
                fonctionSelect.value = matchingOption.value;
            }
        }
        
        document.getElementById('contact_email').value = contact.email || '';
        document.getElementById('contact_telephone').value = contact.telephone || '';
    },

    async loadSelectOptions() {
        try {
            // Charger les pays
            const paysResponse = await fetch(`${CONFIG.API_BASE_URL}/api/pays`);
            if (!paysResponse.ok) throw new Error(`Erreur HTTP: ${paysResponse.status}`);
            const pays = await paysResponse.json();
            
            const paysSelect = document.getElementById('pays_select');
            paysSelect.innerHTML = '<option value="">Sélectionnez un pays</option>';
            pays.forEach(pays => {
                const option = document.createElement('option');
                option.value = pays.id;
                option.textContent = pays.nom;
                paysSelect.appendChild(option);
            });

            // Charger les catégories
            const categoriesResponse = await fetch(`${CONFIG.API_BASE_URL}/api/categories`);
            if (!categoriesResponse.ok) throw new Error(`Erreur HTTP: ${categoriesResponse.status}`);
            const categories = await categoriesResponse.json();
            const categoriesSelect = document.getElementById('id_categorie');
            categories.forEach(categorie => {
                const option = document.createElement('option');
                option.value = categorie.id;
                option.textContent = categorie.nom;
                categoriesSelect.appendChild(option);
            });

            // Charger les fonctions
            console.log('Tentative de chargement des fonctions...');
            const fonctionsResponse = await fetch(`${CONFIG.API_BASE_URL}/api/fonctions`);
            console.log('Statut de la réponse:', fonctionsResponse.status);
            if (!fonctionsResponse.ok) {
                console.error('Erreur lors du chargement des fonctions:', fonctionsResponse.statusText);
                throw new Error(`Erreur HTTP: ${fonctionsResponse.status}`);
            }
            const fonctions = await fonctionsResponse.json();
            console.log('Fonctions reçues:', fonctions);
            
            // Mettre à jour le select de fonction
            const fonctionSelect = document.getElementById('contact_fonction');
            if (fonctionSelect) {
                console.log('Mise à jour du select contact_fonction');
                fonctionSelect.innerHTML = '<option value="">Sélectionnez une fonction</option>';
                fonctions.forEach(fonction => {
                    const option = document.createElement('option');
                    option.value = fonction.id;
                    option.textContent = fonction.nom;
                    fonctionSelect.appendChild(option);
                });
                console.log('Select mis à jour avec succès');
            } else {
                console.error('Select contact_fonction non trouvé');
            }
        } catch (error) {
            console.error('Erreur lors du chargement des options:', error);
        }
    },

    // Gérer l'ajout d'un nouveau contact
    async addNewContact() {
        const idSociete = document.getElementById('id_societe').value;
        if (!idSociete) {
            alert('Veuillez d\'abord sélectionner une société');
            return;
        }

        // Récupérer les données du formulaire
        const formData = {
            id_societe: idSociete,
            nom: document.getElementById('contact_nom').value,
            prenom: document.getElementById('contact_prenom').value,
            telephone: document.getElementById('contact_telephone').value,
            email: document.getElementById('contact_email').value,
            id_fonction: document.getElementById('contact_fonction').value
        };

        // Validation des données
        if (!formData.nom) {
            alert('Le nom du contact est obligatoire');
            return;
        }

        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/contacts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const result = await response.json();
            
            // Mise à jour de l'interface
            document.getElementById('id_personne').value = result.id_personne;
            alert('Contact ajouté avec succès');
            
            // Recharger les contacts
            this.loadContacts(idSociete);
        } catch (error) {
            console.error('Erreur lors de l\'ajout du contact:', error);
            alert('Erreur lors de l\'ajout du contact');
        }
    },

    async loadPredefinedActions() {
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/api/actions`);
            const actions = await response.json();
            
            document.querySelectorAll('.action-select').forEach(select => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Sélectionnez une action</option>';
                actions.forEach(action => {
                    const option = document.createElement('option');
                    option.value = action.id;
                    option.textContent = action.nom;
                    select.appendChild(option);
                });
                select.value = currentValue;
            });
        } catch (error) {
            console.error('Erreur lors du chargement des actions prédéfinies:', error);
        }
    },

    // Créer un nouvel élément d'action
    createActionElement() {
        const newAction = document.createElement('div');
        newAction.className = 'action-item priority-high';
        newAction.innerHTML = `
            <button type="button" class="btn btn-danger btn-sm btn-remove-action">
                <i class="fas fa-times"></i>
            </button>
            <div class="form-group">
                <label>Description de l'Action</label>
                <div class="input-group">
                    <select class="form-control action-select" name="action_select[]" required>
                        <option value="">Sélectionnez une action</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Date d'échéance</label>
                <input type="date" class="form-control" name="date_echeance[]">
            </div>
            <div class="form-group">
                <label>Rappel</label>
                <select class="form-control" name="rappel[]">
                    <option value="">Aucun rappel</option>
                    <option value="1">1 jour avant</option>
                    <option value="3">3 jours avant</option>
                    <option value="7">1 semaine avant</option>
                    <option value="14">2 semaines avant</option>
                    <option value="30">1 mois avant</option>
                </select>
            </div>
            <div class="form-group">
                <label>Priorité</label>
                <select class="form-control" name="action_priority[]">
                    <option value="high">Haute</option>
                    <option value="medium">Moyenne</option>
                    <option value="low">Basse</option>
                </select>
            </div>
        `;
        return newAction;
    }
};

// =============================================
// Module de gestion des listes déroulantes
// =============================================
const SelectManager = {
    // Charger les options des listes déroulantes
    async loadOptions() {
        try {
            // Charger les pays
            const paysResponse = await fetch(`${CONFIG.API_BASE_URL}/api/pays`);
            if (!paysResponse.ok) {
                throw new Error(`Erreur HTTP: ${paysResponse.status}`);
            }
            const pays = await paysResponse.json();
            
            const paysSelect = document.getElementById('pays_select');
            paysSelect.innerHTML = '<option value="">Sélectionnez un pays</option>';
            pays.forEach(pays => {
                const option = document.createElement('option');
                option.value = pays.id;
                option.textContent = pays.nom;
                paysSelect.appendChild(option);
            });

            // Charger les catégories
            const categoriesResponse = await fetch(`${CONFIG.API_BASE_URL}/api/categories`);
            if (!categoriesResponse.ok) {
                throw new Error(`Erreur HTTP: ${categoriesResponse.status}`);
            }
            const categories = await categoriesResponse.json();
            const categoriesSelect = document.getElementById('id_categorie');
            categories.forEach(categorie => {
                const option = document.createElement('option');
                option.value = categorie.id;
                option.textContent = categorie.nom;
                categoriesSelect.appendChild(option);
            });

            // Charger les fonctions
            const fonctionsResponse = await fetch(`${CONFIG.API_BASE_URL}/api/fonctions`);
            if (!fonctionsResponse.ok) {
                throw new Error(`Erreur HTTP: ${fonctionsResponse.status}`);
            }
            const fonctions = await fonctionsResponse.json();
            
            // Mettre à jour le select de fonction
            const fonctionSelect = document.getElementById('contact_fonction');
            if (fonctionSelect) {
                fonctionSelect.innerHTML = '<option value="">Sélectionnez une fonction</option>';
                fonctions.forEach(fonction => {
                    const option = document.createElement('option');
                    option.value = fonction.id;
                    option.textContent = fonction.nom;
                    fonctionSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erreur lors du chargement des options:', error);
            alert('Erreur lors du chargement des options. Veuillez rafraîchir la page.');
        }
    }
};

// =============================================
// Initialisation
// =============================================
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des tooltips
    document.querySelectorAll('[title]').forEach(element => {
        new bootstrap.Tooltip(element);
    });

    // Charger les options des listes déroulantes
    SelectManager.loadOptions();

    // Initialiser la gestion des sociétés
    SocieteManager.init();

    // Charger les actions prédéfinies au démarrage
    ContactManager.loadPredefinedActions();

    // Gestion des boutons de mise à jour
    document.getElementById('btn_update_client').addEventListener('click', function() {
        const idSociete = document.getElementById('id_societe').value;
        if (idSociete) {
            updateClientInfo(idSociete);
        } else {
            alert('Veuillez d\'abord sélectionner une société');
        }
    });

    // Gestionnaire pour le bouton "Ajouter un contact"
    document.getElementById('btn_add_new_contact').addEventListener('click', function() {
        const idSociete = document.getElementById('id_societe').value;
        if (!idSociete) {
            alert('Veuillez d\'abord sélectionner une société');
            return;
        }

        // Réinitialiser les champs du formulaire
        document.getElementById('contact_nom').value = '';
        document.getElementById('contact_prenom').value = '';
        document.getElementById('contact_fonction').value = '';
        document.getElementById('contact_email').value = '';
        document.getElementById('contact_telephone').value = '';
        document.getElementById('id_personne').value = '';

        // Afficher le formulaire de contact
        document.getElementById('contact_select_wrapper').style.display = 'none';
        document.getElementById('contact_nom').closest('.form-group').style.display = 'block';
        document.getElementById('contact_prenom').closest('.form-group').style.display = 'block';
        document.getElementById('contact_fonction').closest('.form-group').style.display = 'block';
        document.getElementById('contact_email').closest('.form-group').style.display = 'block';
        document.getElementById('contact_telephone').closest('.form-group').style.display = 'block';
    });

    // Gestionnaire pour le bouton "Mettre à jour" le contact
    document.getElementById('btn_update_contact').addEventListener('click', function() {
        const idPersonne = document.getElementById('id_personne').value;
        if (idPersonne) {
            updateContactInfo(idPersonne);
        } else {
            alert('Veuillez d\'abord sélectionner un contact');
        }
    });

    // Gestion des actions
    const addActionBtn = document.getElementById('addAction');
    const actionsContainer = document.getElementById('actions-container');

    addActionBtn.addEventListener('click', function() {
        const newAction = ContactManager.createActionElement();
        actionsContainer.appendChild(newAction);
        ContactManager.loadPredefinedActions();
    });

    // Gestion de la suppression des actions
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-remove-action')) {
            e.target.closest('.action-item').remove();
        }
    });

    // Mise à jour de la classe de priorité
    document.addEventListener('change', function(e) {
        if (e.target.name === 'action_priority[]') {
            const actionItem = e.target.closest('.action-item');
            actionItem.className = `action-item priority-${e.target.value}`;
        }
    });
});

async function updateContactInfo(idPersonne) {
    try {
        // Récupérer les données du formulaire
        const formData = {
            nom: document.getElementById('contact_nom').value,
            prenom: document.getElementById('contact_prenom').value,
            telephone: document.getElementById('contact_telephone').value,
            email: document.getElementById('contact_email').value,
            id_fonction: document.getElementById('contact_fonction').value
        };

        console.log('Données de mise à jour:', formData);

        // Envoyer les données mises à jour au serveur
        const response = await fetch(`${CONFIG.API_BASE_URL}/api/contacts/${idPersonne}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        console.log('Réponse du serveur:', response.status);

        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }

        const result = await response.json();
        console.log('Résultat de la mise à jour:', result);

        if (result.success) {
            alert('Informations contact mises à jour avec succès');
        } else {
            throw new Error(result.error || 'Erreur lors de la mise à jour');
        }
    } catch (error) {
        console.error('Erreur lors de la mise à jour des informations contact:', error);
        alert('Erreur lors de la mise à jour des informations contact');
    }
}

async function loadPredefinedActions() {
    try {
        const response = await fetch('/projet4/api/actions');
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des actions');
        }
        const actions = await response.json();
        
        // Mettre à jour tous les selects d'actions
        document.querySelectorAll('.action-select').forEach(select => {
            const currentValue = select.value;
            select.innerHTML = '<option value="">Sélectionnez une action</option>';
            actions.forEach(action => {
                const option = document.createElement('option');
                option.value = action.id;
                option.textContent = action.nom;
                select.appendChild(option);
            });
            select.value = currentValue;
        });
    } catch (error) {
        console.error('Erreur lors du chargement des actions prédéfinies:', error);
    }
} 