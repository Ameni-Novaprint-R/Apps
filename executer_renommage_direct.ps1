# Script PowerShell pour exécuter le renommage directement
# Utilise les mêmes mécanismes de connexion que Flask

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "RENOMMAGE DE WEB_DROITS_ACCES EN WEB_ACTIONS" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Importer le module db et exécuter le renommage
$pythonScript = @"
from db import get_db_cursor

try:
    with get_db_cursor() as cursor:
        print('[1/3] Renommage des contraintes...')
        
        # Renommer la clé primaire
        try:
            cursor.execute("EXEC sp_rename 'PK_WEB_DROITS_ACCES', 'PK_WEB_ACTIONS', 'OBJECT'")
            cursor.connection.commit()
            print('  ✓ Clé primaire renommée')
        except Exception as e:
            print(f'  ⚠ Clé primaire: {e}')
        
        # Renommer la contrainte UNIQUE
        try:
            cursor.execute("EXEC sp_rename 'UQ_WEB_DROITS_ACCES_ID_Section_Action', 'UQ_WEB_ACTIONS_ID_Section_Action', 'OBJECT'")
            cursor.connection.commit()
            print('  ✓ Contrainte UNIQUE renommée')
        except Exception as e:
            print(f'  ⚠ Contrainte UNIQUE: {e}')
        
        # Renommer la clé étrangère
        try:
            cursor.execute("EXEC sp_rename 'FK_WEB_DROITS_ACCES_ID_Section', 'FK_WEB_ACTIONS_ID_Section', 'OBJECT'")
            cursor.connection.commit()
            print('  ✓ Clé étrangère renommée')
        except Exception as e:
            print(f'  ⚠ Clé étrangère: {e}')
        
        print('')
        print('[2/3] Renommage de la table...')
        
        # Renommer la table
        cursor.execute("EXEC sp_rename 'dbo.WEB_DROITS_ACCES', 'WEB_ACTIONS'")
        cursor.connection.commit()
        print('  ✓ Table renommée: WEB_DROITS_ACCES → WEB_ACTIONS')
        print('')
        
        print('[3/3] Vérification...')
        
        # Vérifier que la nouvelle table existe
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'WEB_ACTIONS'")
        if cursor.fetchone()[0] > 0:
            print('  ✓ Table WEB_ACTIONS créée avec succès')
        else:
            print('  ✗ ERREUR: Table WEB_ACTIONS non trouvée')
            exit(1)
        
        # Compter les lignes
        cursor.execute("SELECT COUNT(*) FROM dbo.WEB_ACTIONS")
        row_count = cursor.fetchone()[0]
        print(f'  ✓ Nombre de lignes dans WEB_ACTIONS: {row_count}')
        
        print('')
        print('==============================================================================')
        print('RENOMMAGE TERMINE AVEC SUCCES')
        print('==============================================================================')
except Exception as e:
    print(f'ERREUR: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"@

# Activer l'environnement virtuel si disponible
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
}

# Exécuter le script Python
python -c $pythonScript

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Renommage terminé avec succès!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Erreur lors du renommage" -ForegroundColor Red
    exit 1
}
