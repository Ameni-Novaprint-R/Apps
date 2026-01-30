# -*- coding: utf-8 -*-
"""
Routes d’administration : initialisation des tables WEB_PROJETS et WEB_SECTIONS.

Permet d’exécuter les scripts de création depuis le navigateur (sans lancer
manuellement des .bat ou python en ligne de commande).
"""

import io
import sys
from flask import Blueprint, render_template, jsonify

# Import des fonctions des scripts à la racine du projet (c:\Apps)
from creer_table_web_projets import creer_table_web_projets
from creer_table_web_sections import creer_table_web_sections
from creer_table_web_droits_acces import creer_table_web_droits_acces
from inserer_actions_projet11 import inserer_actions_projet11
from db import get_db_cursor

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/init-web-tables")
def init_web_tables():
    """
    Crée ou met à jour WEB_PROJETS et WEB_SECTIONS.
    Capture la sortie des scripts pour l’afficher sur la page.
    """
    out = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    ok1, ok2, ok3 = False, False, False
    try:
        ok1 = creer_table_web_projets()
        ok2 = creer_table_web_sections()
        ok3 = creer_table_web_droits_acces()
    except Exception as e:
        out.write(f"\n[ERREUR ROUTE] {e}\n")
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout

    logs = out.getvalue()
    success = ok1 and ok2 and ok3

    return render_template(
        "admin_init_web_result.html",
        ok1=ok1,
        ok2=ok2,
        ok3=ok3,
        success=success,
        logs=logs or "(aucune sortie)",
    )


@admin_bp.route("/init-web-tables.json")
def init_web_tables_json():
    """
    Version API JSON de init_web_tables.
    Retourne un JSON au lieu d'une page HTML.
    Permet d'appeler depuis un script Python.
    """
    out = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    ok1, ok2, ok3 = False, False, False
    error = None
    try:
        ok1 = creer_table_web_projets()
        ok2 = creer_table_web_sections()
        ok3 = creer_table_web_droits_acces()
    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout

    logs = out.getvalue()
    success = ok1 and ok2 and ok3

    return jsonify({
        "success": success,
        "ok1": ok1,
        "ok2": ok2,
        "ok3": ok3,
        "logs": logs or "(aucune sortie)",
        "error": error
    })


@admin_bp.route("/inserer-actions-projet11.json")
def inserer_actions_projet11_json():
    """
    Insère les actions du Projet 11 dans WEB_DROITS_ACCES.
    Retourne un JSON avec le résultat.
    """
    out = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    success = False
    error = None
    try:
        success = inserer_actions_projet11()
    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout

    logs = out.getvalue()

    return jsonify({
        "success": success,
        "logs": logs or "(aucune sortie)",
        "error": error
    })


@admin_bp.route("/modifier-actions-projet11.json")
def modifier_actions_projet11_json():
    """
    Modifie les actions du Projet 11 dans WEB_DROITS_ACCES.
    - Archive EXPORT_EXCEL et EXPORT_PDF de Statistiques
    - Ajoute EXPORT_EXCEL et EXPORT_PDF à Liste des Traitements
    Retourne un JSON avec le résultat.
    """
    from db import get_db_cursor
    
    out = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    success = False
    error = None
    
    try:
        print("=" * 70)
        print("Modification des actions du Projet 11 dans WEB_DROITS_ACCES")
        print("=" * 70)
        print()
        
        with get_db_cursor() as cursor:
            # Récupérer l'ID du Projet 11
            cursor.execute("SELECT ID FROM dbo.WEB_PROJETS WHERE NumProj = 11")
            proj_row = cursor.fetchone()
            if not proj_row:
                print("[ERREUR] Projet 11 introuvable dans WEB_PROJETS.")
                return jsonify({"success": False, "logs": out.getvalue(), "error": "Projet 11 introuvable"})
            
            id_proj = proj_row.ID
            
            # ÉTAPE 1: Archiver EXPORT_EXCEL et EXPORT_PDF de Statistiques
            print("[1] Archivage des actions EXPORT_EXCEL et EXPORT_PDF de la section Statistiques...")
            cursor.execute("SELECT ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = 'Statistiques'", (id_proj,))
            section_stats = cursor.fetchone()
            
            if section_stats:
                id_section_stats = section_stats.ID
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 1 WHERE ID_Section = ? AND Action = 'EXPORT_EXCEL' AND archive = 0", (id_section_stats,))
                print(f"  {'✓ EXPORT_EXCEL archivé' if cursor.rowcount > 0 else '(déjà archivé) EXPORT_EXCEL'}")
                cursor.execute("UPDATE dbo.WEB_DROITS_ACCES SET archive = 1 WHERE ID_Section = ? AND Action = 'EXPORT_PDF' AND archive = 0", (id_section_stats,))
                print(f"  {'✓ EXPORT_PDF archivé' if cursor.rowcount > 0 else '(déjà archivé) EXPORT_PDF'}")
            print()
            
            # ÉTAPE 2: Ajouter EXPORT_EXCEL et EXPORT_PDF à Liste des Traitements
            print("[2] Ajout des actions EXPORT_EXCEL et EXPORT_PDF à la section Liste des Traitements...")
            cursor.execute("SELECT ID FROM dbo.WEB_SECTIONS WHERE ID_Proj = ? AND Nom = 'Liste des Traitements'", (id_proj,))
            section_liste = cursor.fetchone()
            
            if section_liste:
                id_section_liste = section_liste.ID
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                    SELECT ?, 'EXPORT_EXCEL', 0
                    WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = 'EXPORT_EXCEL')
                """, (id_section_liste, id_section_liste))
                print(f"  {'+ EXPORT_EXCEL ajouté' if cursor.rowcount > 0 else '(déjà présent) EXPORT_EXCEL'}")
                
                cursor.execute("""
                    INSERT INTO dbo.WEB_DROITS_ACCES (ID_Section, Action, archive)
                    SELECT ?, 'EXPORT_PDF', 0
                    WHERE NOT EXISTS (SELECT 1 FROM dbo.WEB_DROITS_ACCES WHERE ID_Section = ? AND Action = 'EXPORT_PDF')
                """, (id_section_liste, id_section_liste))
                print(f"  {'+ EXPORT_PDF ajouté' if cursor.rowcount > 0 else '(déjà présent) EXPORT_PDF'}")
            print()
            
            cursor.connection.commit()
            success = True
            
            # Récapitulatif
            print("=" * 70)
            print("Récapitulatif")
            print("=" * 70)
            cursor.execute("""
                SELECT s.Nom AS Section, da.Action, da.archive
                FROM dbo.WEB_DROITS_ACCES da
                INNER JOIN dbo.WEB_SECTIONS s ON s.ID = da.ID_Section
                INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                WHERE p.NumProj = 11 AND da.archive = 0
                ORDER BY s.Nom, da.Action
            """)
            print("\nActions ACTIVES:")
            for row in cursor.fetchall():
                print(f"  {row.Section} | {row.Action}")
            
    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
        print(f"[ERREUR] {e}")
    finally:
        sys.stdout = old_stdout

    logs = out.getvalue()

    return jsonify({
        "success": success,
        "logs": logs or "(aucune sortie)",
        "error": error
    })


@admin_bp.route("/corriger-actions-projet11.json")
def corriger_actions_projet11_json():
    """
    Corrige les actions du Projet 11 dans WEB_DROITS_ACCES selon la configuration attendue.
    Retourne un JSON avec le résultat.
    """
    from corriger_actions_projet11 import corriger_actions_projet11
    
    out = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = out
    success = False
    error = None
    try:
        success = corriger_actions_projet11()
    except Exception as e:
        error = str(e)
        import traceback
        traceback.print_exc()
    finally:
        sys.stdout = old_stdout

    logs = out.getvalue()

    return jsonify({
        "success": success,
        "logs": logs or "(aucune sortie)",
        "error": error
    })


@admin_bp.route("/reload-templates")
def reload_templates():
    """
    Force le rechargement du cache des templates Flask.
    Utile après modification des templates pour voir les changements immédiatement.
    """
    from flask import current_app
    try:
        if hasattr(current_app, 'jinja_env'):
            current_app.jinja_env.cache.clear()
            # Recharger aussi les modules Python si nécessaire
            import importlib
            import sys
            if 'routes.projet11_routes' in sys.modules:
                importlib.reload(sys.modules['routes.projet11_routes'])
            return jsonify({
                "success": True,
                "message": "Cache des templates vidé avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Jinja2 environment non trouvé"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_bp.route("/renommer-web-droits-acces-en-web-actions", methods=['POST'])
def renommer_table_web_droits_acces():
    """
    Renomme WEB_DROITS_ACCES en WEB_ACTIONS avec toutes ses contraintes.
    """
    try:
        with get_db_cursor() as cursor:
            results = []
            
            # Vérifier que la table existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if not table_exists:
                return jsonify({
                    "success": False,
                    "error": "La table WEB_DROITS_ACCES n'existe pas."
                }), 404
            
            # Vérifier que la nouvelle table n'existe pas déjà
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_ACTIONS'
            """)
            new_table_exists = cursor.fetchone()[0] > 0
            
            if new_table_exists:
                return jsonify({
                    "success": False,
                    "error": "La table WEB_ACTIONS existe déjà."
                }), 400
            
            results.append("[1/3] Renommage des contraintes...")
            
            # Renommer la clé primaire
            try:
                cursor.execute("EXEC sp_rename 'PK_WEB_DROITS_ACCES', 'PK_WEB_ACTIONS', 'OBJECT'")
                cursor.connection.commit()
                results.append("✓ Clé primaire renommée: PK_WEB_DROITS_ACCES → PK_WEB_ACTIONS")
            except Exception as e:
                results.append(f"⚠ Clé primaire: {str(e)}")
            
            # Renommer la contrainte UNIQUE
            try:
                cursor.execute("EXEC sp_rename 'UQ_WEB_DROITS_ACCES_ID_Section_Action', 'UQ_WEB_ACTIONS_ID_Section_Action', 'OBJECT'")
                cursor.connection.commit()
                results.append("✓ Contrainte UNIQUE renommée")
            except Exception as e:
                results.append(f"⚠ Contrainte UNIQUE: {str(e)}")
            
            # Renommer la clé étrangère
            try:
                cursor.execute("EXEC sp_rename 'FK_WEB_DROITS_ACCES_ID_Section', 'FK_WEB_ACTIONS_ID_Section', 'OBJECT'")
                cursor.connection.commit()
                results.append("✓ Clé étrangère renommée")
            except Exception as e:
                results.append(f"⚠ Clé étrangère: {str(e)}")
            
            results.append("")
            results.append("[2/3] Renommage de la table...")
            
            # Renommer la table
            cursor.execute("EXEC sp_rename 'dbo.WEB_DROITS_ACCES', 'WEB_ACTIONS'")
            cursor.connection.commit()
            results.append("✓ Table renommée: WEB_DROITS_ACCES → WEB_ACTIONS")
            results.append("")
            
            results.append("[3/3] Vérification...")
            
            # Vérifier que la nouvelle table existe
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_ACTIONS'
            """)
            if cursor.fetchone()[0] > 0:
                results.append("✓ Table WEB_ACTIONS créée avec succès")
            else:
                return jsonify({
                    "success": False,
                    "error": "Table WEB_ACTIONS non trouvée après renommage",
                    "results": results
                }), 500
            
            # Compter les lignes
            cursor.execute("SELECT COUNT(*) FROM dbo.WEB_ACTIONS")
            row_count = cursor.fetchone()[0]
            results.append(f"✓ Nombre de lignes dans WEB_ACTIONS: {row_count}")
            
            return jsonify({
                "success": True,
                "message": "Table renommée avec succès",
                "results": results,
                "row_count": row_count
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@admin_bp.route("/creer-table-web-droits-acces", methods=['POST'])
def creer_table_web_droits_acces():
    """Route pour créer la table WEB_DROITS_ACCES"""
    try:
        with get_db_cursor() as cursor:
            # Vérifier si la table existe déjà
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'WEB_DROITS_ACCES'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                return jsonify({
                    "success": False,
                    "message": "La table WEB_DROITS_ACCES existe déjà.",
                    "error": None
                }), 400
            
            # Créer la table WEB_DROITS_ACCES
            cursor.execute("""
                CREATE TABLE WEB_DROITS_ACCES (
                    ID INT IDENTITY(1,1) NOT NULL,
                    Matricule INT NOT NULL,
                    ID_Action INT NOT NULL,
                    Autorise BIT NOT NULL DEFAULT 1,
                    
                    CONSTRAINT PK_WEB_DROITS_ACCES PRIMARY KEY (ID),
                    
                    CONSTRAINT FK_WEB_DROITS_ACCES_Matricule 
                        FOREIGN KEY (Matricule) 
                        REFERENCES personel(Matricule)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    CONSTRAINT FK_WEB_DROITS_ACCES_ID_Action 
                        FOREIGN KEY (ID_Action) 
                        REFERENCES WEB_ACTIONS(ID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    
                    CONSTRAINT UQ_WEB_DROITS_ACCES_Matricule_ID_Action 
                        UNIQUE (Matricule, ID_Action)
                )
            """)
            
            # Créer des index
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_Matricule 
                ON WEB_DROITS_ACCES(Matricule)
            """)
            
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_ID_Action 
                ON WEB_DROITS_ACCES(ID_Action)
            """)
            
            cursor.execute("""
                CREATE INDEX IDX_WEB_DROITS_ACCES_Autorise 
                ON WEB_DROITS_ACCES(Autorise)
            """)
            
            cursor.connection.commit()
            
            return jsonify({
                "success": True,
                "message": "Table WEB_DROITS_ACCES créée avec succès!",
                "details": {
                    "structure": {
                        "ID": "INT IDENTITY(1,1) PRIMARY KEY",
                        "Matricule": "INT NOT NULL (FK -> personel.Matricule)",
                        "ID_Action": "INT NOT NULL (FK -> WEB_ACTIONS.ID)",
                        "Autorise": "BIT NOT NULL DEFAULT 1"
                    },
                    "contraintes": [
                        "PK_WEB_DROITS_ACCES: Clé primaire sur ID",
                        "FK_WEB_DROITS_ACCES_Matricule: Clé étrangère vers personel(Matricule)",
                        "FK_WEB_DROITS_ACCES_ID_Action: Clé étrangère vers WEB_ACTIONS(ID)",
                        "UQ_WEB_DROITS_ACCES_Matricule_ID_Action: Unicité (Matricule, ID_Action)"
                    ],
                    "index": [
                        "IDX_WEB_DROITS_ACCES_Matricule",
                        "IDX_WEB_DROITS_ACCES_ID_Action",
                        "IDX_WEB_DROITS_ACCES_Autorise"
                    ]
                }
            }), 200
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return jsonify({
            "success": False,
            "message": f"Erreur lors de la création de la table: {str(e)}",
            "error": error_trace
        }), 500


@admin_bp.route("/ajouter-colonnes-codeproj-nom-sections", methods=['POST'])
def ajouter_colonnes_codeproj_nom_sections():
    """
    Ajoute les colonnes CodeProj et Nom_SECTIONS à WEB_ACTIONS.
    """
    try:
        with get_db_cursor() as cursor:
            results = []
            
            # Déterminer le nom de la table
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('WEB_ACTIONS', 'WEB_DROITS_ACCES')
            """)
            table_row = cursor.fetchone()
            if not table_row:
                return jsonify({
                    "success": False,
                    "error": "Ni WEB_ACTIONS ni WEB_DROITS_ACCES n'existent."
                }), 404
            
            table_name = table_row.TABLE_NAME
            results.append(f"Table trouvée: {table_name}")
            
            # Étape 1: Ajouter CodeProj
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND COLUMN_NAME = 'CodeProj'
            """, (table_name,))
            
            if cursor.fetchone()[0] > 0:
                results.append("⚠ Colonne CodeProj existe déjà")
            else:
                cursor.execute(f"ALTER TABLE dbo.{table_name} ADD CodeProj NVARCHAR(50) NULL")
                cursor.connection.commit()
                results.append("✓ Colonne CodeProj ajoutée")
            
            # Étape 2: Ajouter Nom_SECTIONS
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = ? AND COLUMN_NAME = 'Nom_SECTIONS'
            """, (table_name,))
            
            if cursor.fetchone()[0] > 0:
                results.append("⚠ Colonne Nom_SECTIONS existe déjà")
            else:
                cursor.execute(f"ALTER TABLE dbo.{table_name} ADD Nom_SECTIONS NVARCHAR(200) NULL")
                cursor.connection.commit()
                results.append("✓ Colonne Nom_SECTIONS ajoutée")
            
            # Étape 3: Mettre à jour les valeurs
            cursor.execute(f"""
                UPDATE dbo.{table_name}
                SET 
                    CodeProj = (
                        SELECT p.CodeProj
                        FROM dbo.WEB_SECTIONS s
                        INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                        WHERE s.ID = {table_name}.ID_Section
                    ),
                    Nom_SECTIONS = (
                        SELECT s.Nom
                        FROM dbo.WEB_SECTIONS s
                        WHERE s.ID = {table_name}.ID_Section
                    )
                WHERE ID_Section IS NOT NULL
            """)
            row_count = cursor.rowcount
            cursor.connection.commit()
            results.append(f"✓ {row_count} ligne(s) mise(s) à jour")
            
            # Étape 4: Créer le trigger
            cursor.execute("""
                SELECT COUNT(*) 
                FROM sys.triggers 
                WHERE name = 'TRG_WEB_ACTIONS_UPDATE_CODE_NOM'
            """)
            if cursor.fetchone()[0] > 0:
                cursor.execute("DROP TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM")
                cursor.connection.commit()
            
            trigger_sql = f"""
                CREATE TRIGGER TRG_WEB_ACTIONS_UPDATE_CODE_NOM
                ON dbo.{table_name}
                AFTER INSERT, UPDATE
                AS
                BEGIN
                    SET NOCOUNT ON;
                    UPDATE wa
                    SET 
                        CodeProj = (
                            SELECT p.CodeProj
                            FROM dbo.WEB_SECTIONS s
                            INNER JOIN dbo.WEB_PROJETS p ON p.ID = s.ID_Proj
                            WHERE s.ID = wa.ID_Section
                        ),
                        Nom_SECTIONS = (
                            SELECT s.Nom
                            FROM dbo.WEB_SECTIONS s
                            WHERE s.ID = wa.ID_Section
                        )
                    FROM dbo.{table_name} wa
                    INNER JOIN inserted i ON i.ID = wa.ID
                    WHERE wa.ID_Section IS NOT NULL;
                END
            """
            cursor.execute(trigger_sql)
            cursor.connection.commit()
            results.append("✓ Trigger créé")
            
            return jsonify({
                "success": True,
                "message": "Colonnes ajoutées avec succès",
                "results": results,
                "row_count": row_count
            })
            
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
