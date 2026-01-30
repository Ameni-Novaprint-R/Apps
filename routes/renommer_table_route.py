#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Route temporaire pour renommer WEB_DROITS_ACCES en WEB_ACTIONS
À supprimer après utilisation
"""

from flask import Blueprint, jsonify
from db import get_db_cursor

renommer_bp = Blueprint('renommer_table', __name__, url_prefix='')

@renommer_bp.route('/admin/renommer-web-droits-acces-en-web-actions', methods=['POST'])
def renommer_table():
    """Renomme WEB_DROITS_ACCES en WEB_ACTIONS avec toutes ses contraintes"""
    
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
