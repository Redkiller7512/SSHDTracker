# Autotracking des entrées (apworld sshd_v3f / client SSHD)

Le client SSHD de l'apworld `sshd_v3f` détecte les portes empruntées en lisant la mémoire du jeu (module `EntranceTracker.py`)
et les publie sur le serveur Archipelago. Le tracker les lit tout seul, sans réglage.

## Clé du DataStorage

`sshd_<nom_de_la_seed>_<nom_du_slot>_entrances` (le nom de la seed vient de `RoomInfo.seed_name`, le slot est celui saisi dans la barre du haut).
Le client écrit avec `Set` (opération `update`) un dictionnaire `{ clé: enregistrement }` ; le tracker fait `Get` puis `SetNotify`.

## Enregistrement utilisé

- `door` : connexion de la porte empruntée (ex. `Deep Woods -> Skyview Entry`) — absent ou `ambiguous: true` si plusieurs portes possibles (ignoré par le tracker, compté comme « ambiguë »).
- `arrival_connection` : connexion dont on rejoint l'arrivée (ex. `Near Temple Entrance -> Earth Temple First Room`) → la porte mène là où mène cette connexion.
- `arrives_at` : zone d'arrivée. Pour la porte `Link's Spawn -> Knight Academy`, c'est le point d'apparition (une statue d'oiseau).

## Ce que fait le tracker

- applique chaque porte, déduit les retours (sauf si « découplées » est coché), puis laisse les observations réelles prendre le dessus ;
- une porte observée **normale** (elle mène à son arrivée d'origine) ne change jamais tes réglages ;
- dès que **2 portes** ne mènent pas à leur arrivée d'origine, il passe tout seul en mode « entrées mélangées » pour leurs types (donjons, portes, intérieurs…). Si tu décoches ensuite un type qu'il avait activé, il ne le réactive pas ;
- règle le point d'apparition ;
- hors connexion : bouton d'import d'un fichier `entrances_….json` (dossier `~/.sshd_ap_tracker/`) ou `tracker_state.json` dans le panneau « Entrées mélangées ».

L'ancienne clé `sshd_er_<équipe>_<slot>` reste lue (compatibilité).
