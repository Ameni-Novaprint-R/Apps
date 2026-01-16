# Explication : Comment est affichée la valeur "OFFSET FEUILLES (SM742) 228.329"

## 📊 FLUX COMPLET DE LA DONNÉE

### ÉTAPE 1 : Base de données SQL Server
```
Table: GP_FICHES_TRAVAIL
- ID = 415695
- ID_COMMANDE = (ID de la commande 2025050176)
- ID_POSTE = (ID du poste SM742)
- CtPrevDev = 228.32916259765625

Table: GP_POSTES
- ID = (ID du poste SM742)
- Nom = "SM742"
- ID_SERVICE = (ID du service OFFSET FEUILLES)

Table: GP_SERVICES
- ID = (ID du service OFFSET FEUILLES)
- Nom = "OFFSET FEUILLES"
```

### ÉTAPE 2 : Requête SQL dans db.py (ligne ~1882-1895)
```sql
SELECT 
    FT.ID AS ID_FICHE_TRAVAIL,           -- 415695
    S.Nom AS Nom_GP_SERVICES,            -- "OFFSET FEUILLES"
    FT.CtPrevDev AS CoutCtPrevDev,       -- 228.32916259765625
    P.Nom AS Nom_Poste                    -- "SM742"
FROM GP_FICHES_TRAVAIL FT
INNER JOIN COMMANDES C ON C.ID = FT.ID_COMMANDE
INNER JOIN GP_POSTES P ON P.ID = FT.ID_POSTE
INNER JOIN GP_SERVICES S ON S.ID = P.ID_SERVICE
WHERE LTRIM(RTRIM(C.Numero)) = '2025050176'
```

**Résultat de la requête :**
- ID_FICHE_TRAVAIL = 415695
- Nom_GP_SERVICES = "OFFSET FEUILLES"
- CoutCtPrevDev = 228.32916259765625 (float)
- Nom_Poste = "SM742"

### ÉTAPE 3 : Traitement Python dans db.py (ligne ~1900-1928)
```python
# Pour chaque ligne retournée par la requête SQL
for row in rows:
    # 1. Récupérer la valeur brute
    cout_value = float(row.CoutCtPrevDev)  # 228.32916259765625
    
    # 2. Arrondir à 3 décimales
    cout_value = round(cout_value, 3)  # 228.329
    
    # 3. Créer un identifiant unique
    service_id = f"{row.Nom_GP_SERVICES}_{row.ID_FICHE_TRAVAIL}"
    # service_id = "OFFSET FEUILLES_415695"
    
    # 4. Construire le dictionnaire Python
    result.append({
        "id": "OFFSET FEUILLES_415695",
        "id_fiche_travail": 415695,
        "nom": "OFFSET FEUILLES",
        "nom_poste": "SM742",
        "cout": 228.329  # float arrondi à 3 décimales
    })
```

### ÉTAPE 4 : Route Flask dans routes/projet19_routes.py (ligne ~109-136)
```python
@projet19_bp.route('/api/postes/<numero>', methods=['GET'])
def api_get_postes(numero):
    # 1. Appeler la fonction Python
    services = get_services_by_numero_commande(numero)
    # services = [
    #     {
    #         "id": "OFFSET FEUILLES_415695",
    #         "nom": "OFFSET FEUILLES",
    #         "cout": 228.329,
    #         "id_fiche_travail": 415695,
    #         "nom_poste": "SM742"
    #     },
    #     ... autres services ...
    # ]
    
    # 2. Convertir en dictionnaire Python standard (sérialisable JSON)
    services_dict = []
    for service in services:
        service_dict = {
            "id": str(service.get('id', '')),                    # "OFFSET FEUILLES_415695"
            "nom": str(service.get('nom', '')),                  # "OFFSET FEUILLES"
            "cout": float(service.get('cout', 0.0)),             # 228.329
            "id_fiche_travail": int(service.get('id_fiche_travail')) if ... else None,  # 415695
            "nom_poste": str(service.get('nom_poste')) if ... else None  # "SM742"
        }
        services_dict.append(service_dict)
    
    # 3. Retourner en JSON
    return jsonify({
        "postes": services_dict
    })
```

**Réponse HTTP JSON :**
```json
{
  "postes": [
    {
      "id": "OFFSET FEUILLES_415695",
      "nom": "OFFSET FEUILLES",
      "cout": 228.329,
      "id_fiche_travail": 415695,
      "nom_poste": "SM742"
    }
  ]
}
```

### ÉTAPE 5 : Frontend JavaScript - Chargement (templates/projet19.html ligne ~1839-1853)
```javascript
// 1. Faire la requête HTTP
fetch('/projet19/api/postes/2025050176')
    .then(response => response.json())
    .then(data => {
        // data = {
        //     postes: [
        //         {
        //             id: "OFFSET FEUILLES_415695",
        //             nom: "OFFSET FEUILLES",
        //             cout: 228.329,
        //             id_fiche_travail: 415695,
        //             nom_poste: "SM742"
        //         }
        //     ]
        // }
        
        // 2. Appeler la fonction de traitement
        loadServiceCosts(numero, data.postes);
    });
```

### ÉTAPE 6 : Frontend JavaScript - Traitement (ligne ~1864-1882)
```javascript
function loadServiceCosts(numero, services) {
    // services = [
    //     {
    //         id: "OFFSET FEUILLES_415695",
    //         nom: "OFFSET FEUILLES",
    //         cout: 228.329,
    //         id_fiche_travail: 415695,
    //         nom_poste: "SM742"
    //     }
    // ]
    
    popupServicesData = {};
    
    services.forEach(service => {
        // 1. Récupérer l'ID unique
        const serviceId = service.id;  // "OFFSET FEUILLES_415695"
        
        // 2. Récupérer le nom
        const serviceName = service.nom;  // "OFFSET FEUILLES"
        
        // 3. Parser le coût (convertir string en nombre si nécessaire)
        let cout = parseFloat(service.cout);  // 228.329
        
        // 4. Stocker dans popupServicesData
        popupServicesData[serviceId] = {
            id: "OFFSET FEUILLES_415695",
            nom: "OFFSET FEUILLES",
            nom_poste: "SM742",
            id_fiche_travail: 415695,
            checked: false,
            cout: 228.329  // nombre JavaScript
        };
    });
    
    // 5. Appeler la fonction d'affichage
    renderServicesList();
}
```

### ÉTAPE 7 : Frontend JavaScript - Affichage (ligne ~1919-1960)
```javascript
function renderServicesList() {
    let html = '';
    
    // 1. Trier les services par nom puis par ID
    const sortedServices = Object.values(popupServicesData).sort(...);
    
    sortedServices.forEach(serviceData => {
        // serviceData = {
        //     id: "OFFSET FEUILLES_415695",
        //     nom: "OFFSET FEUILLES",
        //     nom_poste: "SM742",
        //     cout: 228.329
        // }
        
        // 2. Construire le nom d'affichage
        let displayName = serviceData.nom;  // "OFFSET FEUILLES"
        if (serviceData.nom_poste) {
            displayName += ` (${serviceData.nom_poste})`;  // "OFFSET FEUILLES (SM742)"
        }
        
        // 3. Générer le HTML
        html += `
            <div class="service-item">
                <input type="checkbox" 
                       class="service-checkbox" 
                       data-service-id="${serviceData.id}"
                       data-service-name="${serviceData.nom}">
                <span class="service-name">${displayName}</span>
                <span class="service-cout">${serviceData.cout.toFixed(3)}</span>
            </div>
        `;
        // serviceData.cout.toFixed(3) = 228.329.toFixed(3) = "228.329"
    });
    
    // 4. Insérer le HTML dans la page
    servicesList.innerHTML = html;
}
```

**HTML généré :**
```html
<div class="service-item">
    <input type="checkbox" 
           class="service-checkbox" 
           data-service-id="OFFSET FEUILLES_415695"
           data-service-name="OFFSET FEUILLES">
    <span class="service-name">OFFSET FEUILLES (SM742)</span>
    <span class="service-cout">228.329</span>
</div>
```

### ÉTAPE 8 : Affichage dans le navigateur

Le navigateur interprète le HTML et affiche :
```
☐ OFFSET FEUILLES (SM742)    228.329
```

## 📝 RÉSUMÉ DU FLUX

1. **Base de données** : `GP_FICHES_TRAVAIL.CtPrevDev = 228.32916259765625`
2. **SQL** : Requête JOIN pour récupérer service + poste + coût
3. **Python db.py** : Arrondi à 3 décimales → `228.329`
4. **Python routes** : Conversion en dict JSON-sérialisable
5. **HTTP JSON** : `{"cout": 228.329, "nom_poste": "SM742"}`
6. **JavaScript fetch** : Parse le JSON → objet JavaScript
7. **JavaScript traitement** : Stocke dans `popupServicesData`
8. **JavaScript affichage** : Génère HTML avec `toFixed(3)` → `"228.329"`
9. **Navigateur** : Affiche "OFFSET FEUILLES (SM742) 228.329"

## 🔍 POINTS CLÉS

- **Valeur source** : `CtPrevDev` dans `GP_FICHES_TRAVAIL`
- **Arrondi** : `round(cout_value, 3)` en Python → 3 décimales
- **Affichage nom** : `nom + " (" + nom_poste + ")"` → "OFFSET FEUILLES (SM742)"
- **Affichage coût** : `cout.toFixed(3)` en JavaScript → "228.329"
- **ID unique** : `nom_service + "_" + id_fiche_travail` → "OFFSET FEUILLES_415695"
