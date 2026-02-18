-- Script pour supprimer les lignes de WEB_TRAITEMENTS avec ID entre 1 et 180
-- ATTENTION: Cette opération est irréversible !

-- Vérifier d'abord combien de lignes seront supprimées
SELECT COUNT(*) as Nombre_de_lignes_a_supprimer
FROM WEB_TRAITEMENTS
WHERE ID >= 1 AND ID <= 180;

-- Afficher les lignes qui seront supprimées (pour vérification)
SELECT ID, Numero_COMMANDES, Nom_GP_SERVICES, DteDeb, DteFin
FROM WEB_TRAITEMENTS
WHERE ID >= 1 AND ID <= 180
ORDER BY ID;

-- DÉCOMMENTER LA LIGNE CI-DESSOUS POUR EXÉCUTER LA SUPPRESSION
-- DELETE FROM WEB_TRAITEMENTS WHERE ID >= 1 AND ID <= 180;
