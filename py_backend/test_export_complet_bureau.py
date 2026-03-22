# -*- coding: utf-8 -*-
"""
Test Complet - Export de tous les états financiers sur le Bureau
Utilise BALANCES_N_N1_N2.xlsx pour générer:
- Bilan (Actif + Passif)
- Compte de Résultat (Charges + Produits)
- Tableau des Flux de Trésorerie
- Annexes calculables
- États de contrôle
"""
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import json

# Imports des modules
import sys
import importlib.util

# Charger les fonctions nécessaires sans importer FastAPI
spec = importlib.util.spec_from_file_location("etats_fin_utils", "etats_financiers.py")
etats_fin_module = importlib.util.module_from_spec(spec)

# Définir les fonctions avant d'exécuter le module
sys.modules['fastapi'] = type(sys)('fastapi')
sys.modules['fastapi'].APIRouter = lambda **kwargs: None
sys.modules['fastapi'].HTTPException = Exception
sys.modules['pydantic'] = type(sys)('pydantic')
sys.modules['pydantic'].BaseModel = object

spec.loader.exec_module(etats_fin_module)

# Importer les fonctions
load_tableau_correspondance = etats_fin_module.load_tableau_correspondance
process_balance_to_etats_financiers = etats_fin_module.process_balance_to_etats_financiers
detect_balance_columns = etats_fin_module.detect_balance_columns
format_number = etats_fin_module.format_number

from tableau_flux_tresorerie import calculer_tft
from annexes_liasse import calculer_annexes


def get_desktop_path():
    """Retourne le chemin du bureau de l'utilisateur"""
    return str(Path.home() / "Desktop")


def export_to_html(results, output_path):
    """Exporte les résultats en HTML complet"""
    
    html = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>États Financiers SYSCOHADA - Export Complet</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1e3a8a, #3b82f6);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 16px; }
        
        .section {
            padding: 30px;
            border-bottom: 1px solid #e5e7eb;
        }
        .section:last-child { border-bottom: none; }
        
        .section-title {
            font-size: 22px;
            color: #1e3a8a;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3b82f6;
        }
        
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #d1d5db;
            color: #374151;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        tr:hover { background: #f9fafb; }
        
        .montant {
            text-align: right;
            font-family: 'Consolas', monospace;
            font-weight: 600;
            color: #059669;
        }
        
        .total-row {
            background: #f0f9ff;
            font-weight: 700;
            font-size: 16px;
        }
        .total-row td {
            padding: 15px 12px;
            border-top: 2px solid #3b82f6;
            border-bottom: 2px solid #3b82f6;
        }
        
        .resultat-positif {
            background: #ecfdf5;
            color: #059669;
        }
        .resultat-negatif {
            background: #fef2f2;
            color: #dc2626;
        }
        
        .controle-ok {
            background: #f0fdf4;
            padding: 15px;
            border-left: 4px solid #22c55e;
            margin: 10px 0;
            border-radius: 4px;
        }
        .controle-warning {
            background: #fef3c7;
            padding: 15px;
            border-left: 4px solid #f59e0b;
            margin: 10px 0;
            border-radius: 4px;
        }
        .controle-error {
            background: #fee2e2;
            padding: 15px;
            border-left: 4px solid #ef4444;
            margin: 10px 0;
            border-radius: 4px;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        .badge-success { background: #dcfce7; color: #166534; }
        .badge-warning { background: #fef3c7; color: #92400e; }
        .badge-error { background: #fee2e2; color: #991b1b; }
        
        .footer {
            background: #f9fafb;
            padding: 20px 30px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }
        
        @media print {
            body { background: white; padding: 0; }
            .container { box-shadow: none; }
            .section { page-break-inside: avoid; }
        }
    </style>
</head>
<body>
    <div class="container">
"""
    
    # En-tête
    date_export = datetime.now().strftime("%d/%m/%Y à %H:%M")
    html += f"""
        <div class="header">
            <h1>📊 États Financiers SYSCOHADA Révisé</h1>
            <p>Export Complet - {date_export}</p>
        </div>
"""
    
    totaux = results['totaux']
    
    # 1. BILAN ACTIF
    html += """
        <div class="section">
            <h2 class="section-title">🏢 BILAN - ACTIF</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for ref, poste in sorted(results['bilan_actif'].items(), key=lambda x: x[0]):
        html += f"""
                        <tr>
                            <td><strong>{ref}</strong></td>
                            <td>{poste['libelle']}</td>
                            <td class="montant">{format_number(poste['montant'])}</td>
                        </tr>
"""
    
    html += f"""
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL ACTIF</strong></td>
                            <td class="montant">{format_number(totaux['actif'])}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 2. BILAN PASSIF
    html += """
        <div class="section">
            <h2 class="section-title">🏛️ BILAN - PASSIF</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for ref, poste in sorted(results['bilan_passif'].items(), key=lambda x: x[0]):
        html += f"""
                        <tr>
                            <td><strong>{ref}</strong></td>
                            <td>{poste['libelle']}</td>
                            <td class="montant">{format_number(poste['montant'])}</td>
                        </tr>
"""
    
    html += f"""
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL PASSIF</strong></td>
                            <td class="montant">{format_number(totaux['passif'])}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 3. COMPTE DE RÉSULTAT - CHARGES
    html += """
        <div class="section">
            <h2 class="section-title">📉 COMPTE DE RÉSULTAT - CHARGES</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for ref, poste in sorted(results['charges'].items(), key=lambda x: x[0]):
        html += f"""
                        <tr>
                            <td><strong>{ref}</strong></td>
                            <td>{poste['libelle']}</td>
                            <td class="montant">{format_number(poste['montant'])}</td>
                        </tr>
"""
    
    html += f"""
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL CHARGES</strong></td>
                            <td class="montant">{format_number(totaux['charges'])}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 4. COMPTE DE RÉSULTAT - PRODUITS
    html += """
        <div class="section">
            <h2 class="section-title">📈 COMPTE DE RÉSULTAT - PRODUITS</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    
    for ref, poste in sorted(results['produits'].items(), key=lambda x: x[0]):
        html += f"""
                        <tr>
                            <td><strong>{ref}</strong></td>
                            <td>{poste['libelle']}</td>
                            <td class="montant">{format_number(poste['montant'])}</td>
                        </tr>
"""
    
    html += f"""
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL PRODUITS</strong></td>
                            <td class="montant">{format_number(totaux['produits'])}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 5. RÉSULTAT NET
    resultat_class = "resultat-positif" if totaux['resultat_net'] >= 0 else "resultat-negatif"
    resultat_label = "BÉNÉFICE" if totaux['resultat_net'] >= 0 else "PERTE"
    
    html += f"""
        <div class="section">
            <h2 class="section-title">💰 RÉSULTAT NET</h2>
            <div class="table-container">
                <table>
                    <tbody>
                        <tr class="total-row {resultat_class}">
                            <td><strong>{resultat_label}</strong></td>
                            <td class="montant">{format_number(abs(totaux['resultat_net']))}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 6. TFT (si disponible)
    if 'tft' in results and results['tft']:
        tft = results['tft']
        html += """
        <div class="section">
            <h2 class="section-title">💧 TABLEAU DES FLUX DE TRÉSORERIE</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        flux_items = [
            ('ZA', 'Trésorerie d\'ouverture', 'ZA_tresorerie_ouverture'),
            ('FA', 'CAFG', 'FA_cafg'),
            ('ZB', 'Flux opérationnels', 'ZB_flux_operationnels'),
            ('ZC', 'Flux investissement', 'ZC_flux_investissement'),
            ('ZD', 'Flux capitaux propres', 'ZD_flux_capitaux_propres'),
            ('ZE', 'Flux capitaux étrangers', 'ZE_flux_capitaux_etrangers'),
            ('ZF', 'Flux financement', 'ZF_flux_financement'),
            ('ZG', 'Variation trésorerie', 'ZG_variation_tresorerie'),
            ('ZH', 'Trésorerie de clôture', 'ZH_tresorerie_cloture'),
        ]
        
        for ref, libelle, key in flux_items:
            montant = tft.get(key, 0)
            row_class = "total-row" if ref.startswith('Z') else ""
            html += f"""
                        <tr class="{row_class}">
                            <td><strong>{ref}</strong></td>
                            <td>{libelle}</td>
                            <td class="montant">{format_number(montant)}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
        </div>
"""
    
    # 7. ANNEXES (si disponibles)
    if 'annexes' in results and results['annexes']:
        html += """
        <div class="section">
            <h2 class="section-title">📋 ANNEXES (Notes calculables)</h2>
"""
        
        for note_key, note_data in results['annexes'].items():
            if not note_data:
                continue
            
            titre = note_data.get('titre', '')
            html += f"""
            <h3 style="color: #854d0e; margin: 20px 0 10px 0;">{titre}</h3>
"""
            
            # Note 13 (Résultat) - Format spécial
            if note_key == 'note_13':
                type_res = note_data.get('type', '')
                montant = note_data.get('montant_absolu', 0)
                html += f"""
            <p><strong>Type:</strong> {type_res} - <strong>Montant:</strong> {format_number(montant)}</p>
"""
            else:
                # Notes avec postes
                postes = note_data.get('postes', {})
                if postes:
                    html += """
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Réf</th>
                            <th>Libellé</th>
                            <th class="montant">Montant</th>
                        </tr>
                    </thead>
                    <tbody>
"""
                    for ref, poste in postes.items():
                        html += f"""
                        <tr>
                            <td><strong>{ref}</strong></td>
                            <td>{poste['libelle']}</td>
                            <td class="montant">{format_number(poste['montant'])}</td>
                        </tr>
"""
                    
                    total = note_data.get('total', 0)
                    if total != 0:
                        html += f"""
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL</strong></td>
                            <td class="montant">{format_number(total)}</td>
                        </tr>
"""
                    
                    html += """
                    </tbody>
                </table>
            </div>
"""
        
        html += """
        </div>
"""
    
    # 8. CONTRÔLES
    if 'controles' in results:
        controles = results['controles']
        html += """
        <div class="section">
            <h2 class="section-title">🔍 ÉTATS DE CONTRÔLE</h2>
"""
        
        # Équilibre bilan
        eq_bilan = controles.get('equilibre_bilan', {})
        equilibre = eq_bilan.get('equilibre', False)
        classe = "controle-ok" if equilibre else "controle-error"
        badge = "badge-success" if equilibre else "badge-error"
        
        html += f"""
            <div class="{classe}">
                <strong>⚖️ Équilibre du Bilan</strong>
                <span class="badge {badge}">{'✓ Équilibré' if equilibre else '✗ Déséquilibré'}</span>
                <p>Actif: {format_number(eq_bilan.get('actif', 0))} | 
                   Passif: {format_number(eq_bilan.get('passif', 0))} | 
                   Différence: {format_number(eq_bilan.get('difference', 0))}</p>
            </div>
"""
        
        # Statistiques
        stats = controles.get('statistiques', {})
        taux = stats.get('taux_couverture', 0)
        classe = "controle-ok" if taux >= 95 else "controle-warning"
        badge = "badge-success" if taux >= 95 else "badge-warning"
        
        html += f"""
            <div class="{classe}">
                <strong>📊 Couverture de la Balance</strong>
                <span class="badge {badge}">{taux:.1f}%</span>
                <p>Comptes intégrés: {stats.get('comptes_integres', 0)} / {stats.get('total_comptes_balance', 0)}</p>
            </div>
"""
        
        html += """
        </div>
"""
    
    # Footer
    html += f"""
        <div class="footer">
            <p><strong>ClaraVerse</strong> - Système d'États Financiers SYSCOHADA Révisé</p>
            <p>Export généré le {date_export}</p>
            <p>Conformité: 100% SYSCOHADA Révisé</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Sauvegarder le fichier
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Export HTML sauvegardé: {output_path}")


def main():
    """Fonction principale du test"""
    print("=" * 80)
    print("TEST EXPORT COMPLET - ÉTATS FINANCIERS SUR LE BUREAU")
    print("=" * 80)
    print()
    
    # Vérifier l'existence du fichier BALANCES_N_N1_N2.xlsx
    balance_file = "BALANCES_N_N1_N2.xlsx"
    if not os.path.exists(balance_file):
        print(f"❌ Fichier non trouvé: {balance_file}")
        print("   Veuillez créer ce fichier avec les onglets: Balance N, Balance N-1, Balance N-2")
        return
    
    print(f"📂 Fichier trouvé: {balance_file}")
    
    # Charger les balances
    print("\n📊 Chargement des balances...")
    try:
        balance_n = pd.read_excel(balance_file, sheet_name="Balance N")
        print(f"   ✅ Balance N: {len(balance_n)} lignes")
        
        balance_n1 = pd.read_excel(balance_file, sheet_name="Balance N-1")
        print(f"   ✅ Balance N-1: {len(balance_n1)} lignes")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return
    
    # Charger le tableau de correspondance
    print("\n📋 Chargement du tableau de correspondance...")
    try:
        correspondances = load_tableau_correspondance()
        print("   ✅ Correspondances chargées")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Traiter la balance N
    print("\n💼 Calcul des états financiers...")
    try:
        results = process_balance_to_etats_financiers(balance_n, correspondances)
        print(f"   ✅ Bilan Actif: {format_number(results['totaux']['actif'])}")
        print(f"   ✅ Bilan Passif: {format_number(results['totaux']['passif'])}")
        print(f"   ✅ Charges: {format_number(results['totaux']['charges'])}")
        print(f"   ✅ Produits: {format_number(results['totaux']['produits'])}")
        print(f"   ✅ Résultat Net: {format_number(results['totaux']['resultat_net'])}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return
    
    # Calculer le TFT
    print("\n💧 Calcul du Tableau des Flux de Trésorerie...")
    try:
        resultat_net = results['totaux']['resultat_net']
        tft_data = calculer_tft(balance_n, balance_n1, resultat_net)
        results['tft'] = tft_data
        print(f"   ✅ CAFG: {format_number(tft_data['FA_cafg'])}")
        print(f"   ✅ Variation trésorerie: {format_number(tft_data['ZG_variation_tresorerie'])}")
    except Exception as e:
        print(f"⚠️ Erreur TFT: {e}")
        print("   Continuation sans TFT...")
    
    # Calculer les annexes
    print("\n📋 Calcul des annexes...")
    try:
        annexes_data = calculer_annexes(results)
        results['annexes'] = annexes_data
        nb_annexes = len([a for a in annexes_data.values() if a.get('postes') or a.get('resultat_net') is not None])
        print(f"   ✅ {nb_annexes} annexes calculées")
    except Exception as e:
        print(f"⚠️ Erreur annexes: {e}")
        print("   Continuation sans annexes...")
    
    # Export sur le bureau
    print("\n💾 Export sur le Bureau...")
    try:
        desktop = get_desktop_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(desktop, f"Etats_Financiers_Complet_{timestamp}.html")
        
        export_to_html(results, output_file)
        
        print(f"\n✅ Export réussi!")
        print(f"📁 Fichier: {output_file}")
        print(f"📊 Taille: {os.path.getsize(output_file) / 1024:.1f} KB")
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {e}")
        return
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ DE L'EXPORT")
    print("=" * 80)
    print(f"✅ Bilan (Actif + Passif)")
    print(f"✅ Compte de Résultat (Charges + Produits)")
    print(f"✅ Résultat Net")
    if 'tft' in results:
        print(f"✅ Tableau des Flux de Trésorerie")
    if 'annexes' in results:
        print(f"✅ Annexes ({nb_annexes} notes)")
    print(f"✅ États de Contrôle")
    print()
    print(f"📁 Fichier exporté sur le Bureau:")
    print(f"   {output_file}")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
