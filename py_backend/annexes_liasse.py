# -*- coding: utf-8 -*-
def calculer_annexes(results):
    return {'note_13': {'titre': 'NOTE 13', 'resultat_net': results.get('totaux', {}).get('resultat_net', 0), 'type': 'Test', 'montant_absolu': 0}}
