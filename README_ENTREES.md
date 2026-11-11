# Autotracking des entrées (pour ton client Archipelago modifié)

Le tracker sait déjà gérer les entrées mélangées à la main (panneau « Entrées mélangées »). Pour qu'il les suive tout seul,
ton client doit écrire une valeur dans le **DataStorage** du serveur Archipelago. Le tracker la lit à la connexion (`Get`) et
à chaque changement (`SetNotify`), puis met à jour ses portes sans rien demander.

## Clé

`sshd_er_<team>_<slot>` — par exemple `sshd_er_0_1` pour l'équipe 0, slot 1.

## Valeur (JSON)

```json
{
  "entrances": {
    "Deep Woods -> Skyview Entry": "Near Temple Entrance -> Earth Temple First Room"
  },
  "spawn": "Faron Woods Entry Statue"
}
```

- **`entrances`** : pour chaque porte empruntée, `"<connexion de la porte prise>": "<connexion dont on rejoint l'arrivée>"`.
  Ici, entrer par `Deep Woods -> Skyview Entry` t'a fait arriver là où mène normalement `Near Temple Entrance -> Earth Temple First Room`.
  Les noms sont les champs `connection` de `entrance_shuffle_data.yaml` (dans l'apworld, dossier `sshd-rando-backend/data/`).
- **`spawn`** (facultatif) : zone d'apparition, parmi les statues d'oiseau (ex. `Faron Woods Entry Statue`).

## Notes

- Le tracker applique le **couplage** automatiquement (sauf si « découplées » est coché) : si tu renseignes une porte, le retour
  correspondant est déduit. Un client qui envoie les deux sens ne gêne pas.
- Pour écrire la valeur depuis le client : paquet `Set` avec `key`, `default: {}` et une opération `update` avec la nouvelle entrée.
- Tant qu'aucune donnée n'arrive, tout reste modifiable à la main dans le tracker ; les saisies manuelles et automatiques se mélangent.
