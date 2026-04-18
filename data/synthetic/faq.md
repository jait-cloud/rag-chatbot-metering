# FAQ — Service client MetriSmart

## Comment lire ma consommation sur le compteur ?

Sur tous les compteurs MetriSmart, l'écran LCD affiche en rotation les informations principales. Pour consulter votre consommation actuelle :

1. Appuyez sur la touche bleue du compteur.
2. Faites défiler jusqu'à l'affichage "ENERGIE TOTALE" (code OBIS 1.8.0).
3. La valeur est exprimée en kWh. Un point décimal sépare les dizièmes.

Si votre compteur est en mode double tarif, vous verrez successivement :
- `1.8.1` — Heures creuses
- `1.8.2` — Heures pleines

En cas d'écran éteint, appuyez sur n'importe quelle touche pour le réactiver.

## Mon compteur affiche "ERR-01", que faire ?

Le code `ERR-01` indique une erreur de communication interne. Ce n'est **pas** une erreur de mesure — votre consommation continue d'être enregistrée correctement. Étapes à suivre :

1. Notez la valeur affichée avant l'erreur.
2. Coupez votre disjoncteur principal pendant 30 secondes, puis rétablissez.
3. Si l'erreur persiste plus de 24h, contactez le service technique avec le numéro de série du compteur.

Les autres codes d'erreur courants :
- `ERR-02` : tension hors plage (vérifier votre installation)
- `ERR-05` : détection de fraude (intervention technicien obligatoire)
- `ERR-07` : batterie interne à remplacer (pas urgent, durée de grâce 6 mois)

## Puis-je basculer vers le prépayé ?

Oui, sous deux conditions :
1. Votre contrat actuel doit être soldé (aucune facture en retard).
2. Votre compteur doit être un modèle compatible (voir liste ci-dessous) ou être remplacé par un MS-PREPAY-30.

Compteurs compatibles avec activation prépayée à distance :
- MS-MONO-100 (firmware ≥ 2.4)
- MS-TRI-400 n'est **pas** compatible prépayé.

Le délai d'activation est de 48h ouvrées après validation de la demande.

## Combien de temps dure la batterie interne ?

La batterie au lithium-thionyle (LiSOCl₂) du compteur alimente uniquement l'horloge interne et la mémoire de sauvegarde pendant les coupures secteur. Sa durée de vie nominale est de **15 ans** en conditions normales.

Vous n'avez **jamais à la remplacer vous-même** — c'est une opération technicien. Quand la batterie arrive en fin de vie, le compteur affiche `ERR-07` et remonte une alerte automatiquement au centre de supervision.

## Comment recharger un compteur prépayé (STS) ?

Le rechargement utilise le standard STS (Standard Transfer Specification), un code à 20 chiffres unique lié à votre compteur.

1. Achetez un crédit auprès d'un point de vente agréé ou via l'application mobile.
2. Le système génère un code STS de 20 chiffres.
3. Sur votre compteur, appuyez sur la touche bleue pour entrer en mode saisie.
4. Tapez le code à 20 chiffres. L'écran confirme par "ACCEPT" et affiche le nouveau crédit.
5. Si l'écran affiche "REJECT", vérifiez la saisie. Un code ne peut être utilisé qu'une fois et est lié au numéro de série de votre compteur.

En cas de doute, le ticket de caisse conserve le code pendant 90 jours.

## Que faire en cas de coupure prolongée ?

Votre compteur est conçu pour fonctionner normalement après une coupure, même longue :
- L'horloge interne est sauvegardée pendant au moins 72h sans alimentation.
- Toutes les mesures enregistrées (courbe de charge, index) sont conservées en mémoire non volatile (pas de perte).
- Après retour du secteur, le compteur reprend automatiquement la communication.

Si après le retour du courant votre compteur ne s'allume pas du tout (écran totalement noir même en appuyant sur une touche), vérifiez votre disjoncteur. S'il est en position correcte mais le compteur reste éteint, c'est une panne matérielle — contactez le service technique.

## Mon compteur est-il connecté en temps réel ?

Pas exactement "temps réel", mais proche. Les compteurs MetriSmart remontent les données toutes les **15 minutes** vers le concentrateur de quartier via PLC G3. Le concentrateur agrège ces données et les transmet au centre de gestion toutes les heures via 4G.

Cela signifie que :
- Votre consommation détaillée est disponible sur le portail client avec un délai de **~1 heure**.
- Les alarmes critiques (fraude, coupure, panne) remontent en moins de **5 minutes**.
- La commande de coupure/remise en service à distance prend typiquement **2 à 10 minutes**.

## Comment détectez-vous les fraudes ?

Plusieurs capteurs et algorithmes travaillent en parallèle :

- **Capteur d'ouverture du capot** : détecte toute tentative d'ouverture du compteur.
- **Capteur magnétique** : détecte l'approche d'un aimant puissant (fraude classique).
- **Détection de neutre coupé** : anomalie typique d'un bypass.
- **Analyse de profil de consommation** : un algorithme côté serveur compare votre courbe à celle de foyers similaires pour détecter des anomalies.

Toute détection génère une alarme `ERR-05`, verrouille certaines fonctions du compteur, et déclenche une intervention technique sous 72h ouvrées.
