# Guide de dépannage — Compteurs MetriSmart

## Diagnostic par code d'erreur

### ERR-01 — Erreur de communication interne

**Symptôme** : affichage `ERR-01` clignotant, mesure non interrompue.

**Cause probable** : corruption temporaire du bus I2C entre le DSP de mesure et le module de communication.

**Résolution** :
1. Noter la valeur d'index avant reset.
2. Coupure disjoncteur 30 secondes puis remise sous tension.
3. Si l'erreur réapparaît dans les 7 jours, remplacer le module de communication (kit de réparation `KIT-COM-V2`).

**Criticité** : faible — la mesure continue, l'erreur concerne uniquement la télérelève.

---

### ERR-02 — Tension hors plage

**Symptôme** : affichage `ERR-02`, possible blocage de l'afficheur.

**Cause probable** : tension d'alimentation < 180 V ou > 260 V pendant plus de 10 secondes.

**Résolution** :
1. Mesurer la tension aux bornes du compteur au multimètre.
2. Si la tension est effectivement anormale, c'est un problème réseau (à remonter au gestionnaire de réseau, pas au client).
3. Si la tension est normale (230 V ± 5 %), problème de capteur interne → remplacement du compteur.

**Criticité** : moyenne — peut indiquer un défaut du réseau d'alimentation.

---

### ERR-03 — Sens de flux inversé

**Symptôme** : affichage `ERR-03`, une icône "flèche inversée" apparaît.

**Cause probable** : raccordement phase entrée/sortie inversé lors de la pose, OU installation photovoltaïque non déclarée qui injecte sur le réseau.

**Résolution** :
1. Vérifier le câblage : bornes 1 (phase amont) vers réseau, borne 2 (phase aval) vers abonné.
2. Si câblage correct, contrôler si une installation PV est présente chez l'abonné.
3. Si PV légitime, basculer le compteur en mode bidirectionnel (commande DLMS `0.0.96.1.1.0`).

**Criticité** : moyenne — nécessite une vérification terrain.

---

### ERR-05 — Alarme de fraude

**Symptôme** : affichage `ERR-05`, LED rouge fixe, certaines fonctions (coupure à distance, modification tarif) verrouillées.

**Cause probable** : ouverture du capot détectée, ou champ magnétique anormal détecté par le capteur hall.

**Résolution** :
1. **Ne pas réinitialiser sur site** sans autorisation.
2. Intervention technique obligatoire sous 72h ouvrées.
3. Inspection visuelle : traces d'outillage, plombage rompu, traces d'aimant.
4. Remplacement du compteur si fraude confirmée, remise en service avec procédure d'enquête.

**Criticité** : haute — implique la conformité contractuelle et potentiellement des sanctions.

---

### ERR-07 — Batterie interne à remplacer

**Symptôme** : affichage `ERR-07` clignotant 1 fois par heure.

**Cause probable** : la batterie LiSOCl₂ alimentant l'horloge arrive en fin de vie (15 ans nominaux).

**Résolution** :
1. Pas d'urgence — 6 mois de marge avant perte d'horloge.
2. Planifier un remplacement du compteur lors de la prochaine tournée.
3. **Ne pas tenter d'ouvrir** pour remplacer la batterie : les scellés métrologiques sont invalidés définitivement.

**Criticité** : faible — préventif.

---

## Problèmes sans code d'erreur

### Écran LCD totalement éteint

**Causes possibles**, par ordre de probabilité :
1. **Pas de tension secteur** : disjoncteur ouvert en amont.
2. **Alimentation interne HS** : composant le plus sensible (condensateurs X2 vieillis).
3. **Écran LCD HS mais compteur fonctionnel** : rare, vérifiable par lecture du port optique.

**Test rapide** :
- Pointer une caméra de smartphone sur la LED métrologique rouge.
- Si la LED clignote, le compteur mesure correctement → problème d'affichage uniquement.
- Si la LED est éteinte, le compteur est HS ou privé d'alimentation.

---

### Compteur "hors communication" côté serveur

**Symptôme** : le HES (Head-End System) remonte le compteur comme "unreachable" depuis plus de 24h, mais le compteur fonctionne normalement sur site.

**Arbre de décision** :

1. **Vérifier le concentrateur de quartier** : est-il lui-même en ligne ? Si non, problème réseau amont.
2. **Vérifier la topologie PLC G3** : le compteur doit être sur la même phase BT que le concentrateur. En cas de repiquage récent, la topologie peut avoir changé.
3. **Forcer un re-appairage** : commande côté HES `discover-nodes` sur le concentrateur, attendre 30 min.
4. **Diagnostic local** : technicien sur site avec interface optique, lecture des compteurs de trames PLC (OBIS `0.0.96.10.1.255`).

Si après toutes ces étapes le compteur reste injoignable, suspecter un défaut du modem PLC interne → remplacement.

---

### Incohérence entre relevé manuel et télérelève

**Scénario** : un technicien relève `12345 kWh` sur l'afficheur mais le portail client affiche `12412 kWh`.

**Analyse** :
- Écart < 1 % ou < 10 kWh : normal. La télérelève est remontée toutes les 15 min, le relevé manuel est instantané. L'écart correspond à la consommation entre deux télérelèves.
- Écart > 1 % ou > 10 kWh : anomalie. Causes possibles :
  * Compteur de remplacement posé avec index initial mal saisi dans le SI.
  * Bug connu sur firmware < 2.3 (correction disponible via OTA).
  * Tentative de fraude (incohérence volontaire).

Procédure : croiser avec la courbe de charge horaire. Si la courbe est cohérente et seule la valeur d'index diverge, c'est probablement une erreur d'initialisation côté SI.

---

## Procédure d'escalade

Si un problème n'est pas couvert par ce guide ou persiste après application de la procédure :

1. **Niveau 1 (support client)** : tentative de résolution téléphonique, reset guidé, création de ticket.
2. **Niveau 2 (support technique)** : analyse des logs distants, recommandation de remplacement.
3. **Niveau 3 (R&D / retour usine)** : compteur remonté en laboratoire pour analyse. Délai typique 4 à 6 semaines.

Pour tout retour usine, inclure :
- Numéro de série du compteur.
- Description précise du symptôme et conditions d'apparition.
- Dump des paramètres OBIS via port optique.
- Photo de l'installation et de l'étiquette compteur.
