# -*- coding: utf-8 -*-
"""
Routes Projet 28 – Gestion des codes-barres matières premières.
Préfixe /projet28 — super-utilisateurs + matricules autorisés (WEB_DROITS_ACCES).
"""
from functools import wraps

from flask import (
    Blueprint, render_template, request, jsonify, redirect, url_for, session,
)

from logic.auth import login_required, is_super_user, has_project_access, get_user_sections
from logic import projet28 as p28

projet28_bp = Blueprint('projet28', __name__, url_prefix='/projet28')

PROJET28_SECTION_KEYS = {
    'Mise en place': 'mise_en_place',
    'Génération': 'generation',
    'Unités': 'unites',
    'Scan': 'scan',
    'Étiquettes': 'etiquettes',
}


def _ensure_tables():
    try:
        p28.init_web_cod_bar_tables()
        p28.ensure_projet28_actions()
    except Exception as e:
        print(f'[Projet28] init tables: {e}')


def projet28_access_required(f):
    """Super-user ou droit projet 28 via WEB_DROITS_ACCES."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_super_user() and not has_project_access(28):
            if request.path.startswith('/projet28/api/'):
                return jsonify({'error': 'Accès non autorisé au Projet 28'}), 403
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def get_projet28_allowed_sections():
    if is_super_user():
        return list(PROJET28_SECTION_KEYS.values())
    raw = get_user_sections(28)
    allowed = []
    for s in raw:
        nom = (s.get('nom') or s.get('Nom') or '').strip()
        key = PROJET28_SECTION_KEYS.get(nom)
        if key and key not in allowed:
            allowed.append(key)
    return allowed


def render_projet28(section=None, **kwargs):
    allowed = get_projet28_allowed_sections()
    if section is not None and section not in allowed:
        if allowed:
            return redirect(url_for(f'projet28.{allowed[0]}'))
        return redirect(url_for('index'))
    kwargs['section'] = section
    kwargs['allowed_sections'] = allowed
    kwargs['is_super'] = is_super_user()
    kwargs['statuts'] = p28.STATUT_LABELS
    kwargs['payload_exemple'] = 'MP184392001;CO;PAP;C90G;P'
    return render_template('projet28.html', **kwargs)


@projet28_bp.before_request
def _projet28_before():
    _ensure_tables()


@projet28_bp.route('/')
@login_required
@projet28_access_required
def index():
    """Accueil : en-tête + choix de section, sans contenu métier par défaut."""
    return render_projet28(section=None)


@projet28_bp.route('/mise-en-place')
@login_required
@projet28_access_required
def mise_en_place():
    return render_projet28(section='mise_en_place')


@projet28_bp.route('/generation')
@login_required
@projet28_access_required
def generation():
    return render_projet28(section='generation')


@projet28_bp.route('/unites')
@login_required
@projet28_access_required
def unites():
    return render_projet28(section='unites')


@projet28_bp.route('/scan')
@login_required
@projet28_access_required
def scan():
    return render_projet28(section='scan')


@projet28_bp.route('/etiquettes')
@login_required
@projet28_access_required
def etiquettes():
    ids = request.args.get('ids', '')
    return render_projet28(section='etiquettes', etiquette_ids=ids)


def ensure_projet28_in_web_projets():
    p28.ensure_projet28_in_web_projets()


def _current_user_label():
    return (
        session.get('username')
        or session.get('nom')
        or str(session.get('matricule') or '')
    )


# --- API ---

@projet28_bp.route('/api/types')
@login_required
@projet28_access_required
def api_types():
    return jsonify(p28.list_types_mp(actif_only=False))


@projet28_bp.route('/api/mouvements')
@login_required
@projet28_access_required
def api_mouvements():
    q = request.args.get('q')
    num = request.args.get('num_ordre')
    limit = request.args.get('limit', 50)
    return jsonify(p28.search_mouvements_entree(q=q, num_ordre=num, limit=limit, for_json=True))


@projet28_bp.route('/api/stocks-inventaire')
@login_required
@projet28_access_required
def api_stocks_inventaire():
    data = p28.search_stocks_inventaire(
        q=request.args.get('q'),
        limit=request.args.get('limit', 100),
        for_json=True,
    )
    return jsonify(data)


@projet28_bp.route('/api/campagnes-inventaire')
@login_required
@projet28_access_required
def api_campagnes_inventaire():
    return jsonify({
        'campagne': p28.get_campagne_active(),
        'campagnes': p28.list_campagnes(limit=request.args.get('limit', 50)),
    })


@projet28_bp.route('/api/campagnes-inventaire', methods=['POST'])
@login_required
@projet28_access_required
def api_campagnes_inventaire_post():
    data = request.get_json(silent=True) or {}
    action = (data.get('action') or 'creer').strip().lower()
    if action == 'activer':
        camp, err = p28.activer_campagne(data.get('code_campagne'))
    else:
        camp, err = p28.creer_ou_activer_campagne(
            type_campagne=data.get('type_campagne') or 'TRIMESTRIEL',
            annee=data.get('annee'),
            trimestre=data.get('trimestre'),
            libelle=data.get('libelle'),
            code_campagne=data.get('code_campagne'),
            activer=bool(data.get('activer', True)),
        )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({
        'success': True,
        'campagne': camp,
        'campagnes': p28.list_campagnes(),
    })


@projet28_bp.route('/api/inventaire-qte', methods=['POST'])
@login_required
@projet28_access_required
def api_inventaire_qte():
    data = request.get_json(silent=True) or {}
    row, err = p28.enregistrer_qte_inventoriee(
        id_stock=data.get('id_stock'),
        qte_inventoriee=data.get('qte_inventoriee'),
        utilisateur=_current_user_label(),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'inventaire': row})


@projet28_bp.route('/api/generer-inventaire', methods=['POST'])
@login_required
@projet28_access_required
def api_generer_inventaire():
    data = request.get_json(silent=True) or {}
    try:
        id_stock = int(data.get('id_stock'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'id_stock invalide'}), 400
    id_mvt = data.get('id_mvt')
    if id_mvt in ('', '-', None):
        id_mvt = None
    elif id_mvt is not None:
        try:
            id_mvt = int(id_mvt)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'id_mvt invalide'}), 400
    # Persister aussi la qté inventoriée cible avant génération
    if data.get('qte_inventoriee') is not None:
        p28.enregistrer_qte_inventoriee(
            id_stock=id_stock,
            qte_inventoriee=data.get('qte_inventoriee'),
            utilisateur=_current_user_label(),
        )
    unites, err = p28.generer_unites_inventaire(
        id_stock=id_stock,
        qte_inventoriee=data.get('qte_inventoriee'),
        lignes=data.get('lignes'),
        mode=data.get('mode'),
        id_mvt=id_mvt,
        utilisateur=_current_user_label(),
        mettre_en_stock=bool(data.get('mettre_en_stock', True)),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'unites': unites, 'count': len(unites)})


@projet28_bp.route('/api/mouvements/<int:id_mvt>')
@login_required
@projet28_access_required
def api_mouvement(id_mvt):
    m = p28.get_mouvement_entree(id_mvt, for_json=True)
    if not m:
        return jsonify({'error': 'Mouvement introuvable'}), 404
    return jsonify(m)


@projet28_bp.route('/api/apercu-payload', methods=['POST'])
@login_required
@projet28_access_required
def api_apercu_payload():
    data = request.get_json(silent=True) or {}
    try:
        id_mvt = int(data.get('id_mvt'))
        seq = int(data.get('sequence') or 1)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'id_mvt / sequence invalides'}), 400
    mode = data.get('mode') or 'P'
    preview, err = p28.apercu_payload(id_mvt, seq, mode)
    if err:
        return jsonify({'success': False, 'error': err}), 400
    # sérialiser mouvement pour JSON
    if preview and preview.get('mouvement'):
        m = preview['mouvement']
        if m.get('DatePiece') and hasattr(m['DatePiece'], 'isoformat'):
            m['DatePiece'] = m['DatePiece'].isoformat(sep=' ', timespec='seconds')
        if m.get('Quantite') is not None:
            m['Quantite'] = float(m['Quantite'])
    return jsonify({'success': True, **preview})


@projet28_bp.route('/api/generer', methods=['POST'])
@login_required
@projet28_access_required
def api_generer():
    data = request.get_json(silent=True) or {}
    try:
        id_mvt = int(data.get('id_mvt'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'id_mvt invalide'}), 400
    unites, err = p28.generer_unites(
        id_mvt=id_mvt,
        nb_unites=data.get('nb_unites'),
        mode=data.get('mode'),
        qte_par_unite=data.get('qte_par_unite'),
        dimensions=data.get('dimensions'),
        lignes=data.get('lignes'),
        utilisateur=_current_user_label(),
        mettre_en_stock=bool(data.get('mettre_en_stock', True)),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    mvt_maj = p28.get_mouvement_entree(id_mvt, for_json=True)
    return jsonify({
        'success': True,
        'unites': unites,
        'count': len(unites),
        'mouvement': mvt_maj,
        'sum_qte_generee': (mvt_maj or {}).get('SumQteGeneree', 0),
        'nb_unites_generees': (mvt_maj or {}).get('NbUnitesGenerees', 0),
        'max_sequence': (mvt_maj or {}).get('MaxSequence', 0),
    })


@projet28_bp.route('/api/unites')
@login_required
@projet28_access_required
def api_unites():
    return jsonify(p28.list_unites(
        id_mvt=request.args.get('id_mvt', type=int),
        statut=request.args.get('statut') or None,
        q=request.args.get('q'),
        limit=request.args.get('limit', 100),
    ))


@projet28_bp.route('/api/unites/<int:unite_id>')
@login_required
@projet28_access_required
def api_unite(unite_id):
    u = p28.get_unite(unite_id=unite_id)
    if not u:
        return jsonify({'error': 'Unité introuvable'}), 404
    return jsonify(u)


@projet28_bp.route('/api/unites/by-ids')
@login_required
@projet28_access_required
def api_unites_by_ids():
    raw = request.args.get('ids') or ''
    ids = []
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return jsonify(p28.get_unites_by_ids(ids))


@projet28_bp.route('/api/scan', methods=['POST'])
@login_required
@projet28_access_required
def api_scan():
    data = request.get_json(silent=True) or {}
    payload = (data.get('payload') or '').strip()
    if not payload:
        return jsonify({'success': False, 'error': 'Payload vide'}), 400
    result = p28.enregistrer_scan(
        payload,
        utilisateur=_current_user_label(),
        matricule=session.get('matricule'),
        lieu=data.get('lieu'),
        action=data.get('action') or 'CONSULTATION',
        detail=data.get('detail'),
    )
    extra = _extra_unite_payload(result.get('unite'))
    return jsonify({'success': result['ok'], **result, **extra})


def _extra_unite_payload(unite):
    if not unite:
        return {}
    uid = unite['ID']
    init_q = _dec_safe(unite.get('QteInitiale'))
    reste_q = _dec_safe(unite.get('QteRestante'))
    return {
        'mouvements': p28.list_mouvements_unite(uid),
        'max_retour': max(0.0, init_q - reste_q),
    }


def _dec_safe(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


@projet28_bp.route('/api/unites/<int:unite_id>/mouvements')
@login_required
@projet28_access_required
def api_mouvements_unite(unite_id):
    unite = p28.get_unite(unite_id=unite_id)
    if not unite:
        return jsonify({'error': 'Unité introuvable'}), 404
    return jsonify({
        'unite': unite,
        **_extra_unite_payload(unite),
    })


@projet28_bp.route('/api/consommer', methods=['POST'])
@login_required
@projet28_access_required
def api_consommer():
    data = request.get_json(silent=True) or {}
    try:
        unite_id = int(data.get('id_unite'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'id_unite invalide'}), 400
    unite, err = p28.consommer_unite(
        unite_id,
        data.get('qte'),
        utilisateur=_current_user_label(),
        lieu=data.get('lieu'),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({'success': True, 'unite': unite, **_extra_unite_payload(unite)})


@projet28_bp.route('/api/annuler-sortie', methods=['POST'])
@login_required
@projet28_access_required
def api_annuler_sortie():
    data = request.get_json(silent=True) or {}
    try:
        unite_id = int(data.get('id_unite'))
        scan_id = int(data.get('scan_id'))
    except (TypeError, ValueError):
        return jsonify({
            'success': False,
            'error': 'id_unite et scan_id (ligne de sortie) sont requis',
        }), 400
    unite, info, err = p28.annuler_sortie(
        unite_id,
        scan_id,
        utilisateur=_current_user_label(),
        lieu=data.get('lieu'),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({
        'success': True,
        'unite': unite,
        'info': info,
        **_extra_unite_payload(unite),
    })


@projet28_bp.route('/api/retour-stock', methods=['POST'])
@login_required
@projet28_access_required
def api_retour_stock():
    data = request.get_json(silent=True) or {}
    try:
        unite_id = int(data.get('id_unite'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'error': 'id_unite invalide'}), 400
    unite, info, err = p28.retour_en_stock(
        unite_id,
        data.get('qte'),
        utilisateur=_current_user_label(),
        lieu=data.get('lieu'),
    )
    if err:
        return jsonify({'success': False, 'error': err}), 400
    return jsonify({
        'success': True,
        'unite': unite,
        'info': info,
        **_extra_unite_payload(unite),
    })


@projet28_bp.route('/api/payload-spec')
@login_required
@projet28_access_required
def api_payload_spec():
    return jsonify({
        'format': 'MP{ID_MVT}{SEQ3};{TYPE_MP};{CODE_FAM};{CODE_ART};{P|B}',
        'exemple': 'MP184392001;CO;PAP;C90G;P',
        'separateur': ';',
        'encodage': 'Code 128',
        'type_piece_entree': p28.TYPE_PIECE_ENTREE,
        'cpte_var_stk': p28.CPTE_VAR_STK_MP,
        'types': p28.TYPES_MP_SEED,
        'statuts': p28.STATUT_LABELS,
        'notes': [
            'NumOrdrePiece affiché sur étiquette uniquement (hors payload).',
            'TypePiece=C provisoire — validation dépôt à venir (G=retour).',
            'Homonyme: TypePiece B=réservation ≠ payload B=bobine.',
        ],
    })
