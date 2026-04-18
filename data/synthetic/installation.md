# Guide d'installation — Compteurs MetriSmart

Ce document s'adresse aux techniciens certifiés. Toute intervention sur un compteur électrique doit respecter les normes NF C 14-100 (installation extérieure) et NF C 15-100 (installation intérieure) ainsi que les procédures de consignation électrique.

## Prérequis avant intervention

- EPI complets : gants classe 00 (1000V), lunettes, chaussures de sécurité.
- VAT (Vérificateur d'Absence de Tension) calibré < 1 an.
- Outillage isolé 1000V.
- Bon d'intervention signé par le donneur d'ordre.
- Accord écrit de l'abonné pour toute coupure > 15 min.

## Installation d'un compteur monophasé MS-MONO-100

### Étape 1 — Consignation

1. Prévenir l'abonné de la coupure imminente.
2. Ouvrir le disjoncteur d'abonné (position 0).
3. Couper le disjoncteur de branchement (si présent en amont).
4. Vérifier l'absence de tension avec VAT sur les deux conducteurs de phase et neutre, côté amont ET aval du futur emplacement du compteur.
5. Poser le cadenas de consignation et conserver la clé.

### Étape 2 — Raccordement électrique

Les bornes du MS-MONO-100 sont disposées comme suit, de gauche à droite, vues de face :

| Borne | Fonction | Section conducteur |
|-------|----------|--------------------|
| 1     | Phase entrée (amont réseau) | 16 mm² mini |
| 2     | Phase sortie (vers abonné) | 16 mm² mini |
| 3     | Neutre entrée | 16 mm² mini |
| 4     | Neutre sortie | 16 mm² mini |

Couple de serrage : **2.5 Nm ± 0.2**. Utiliser un tournevis dynamométrique.

⚠️ **Erreur fréquente** : inverser phase entrée et phase sortie. Le compteur fonctionnera quand même mais la détection de fraude par analyse de sens de flux sera désactivée, et une alarme `ERR-03` apparaîtra au prochain relevé.

### Étape 3 — Mise en service

1. Déconsigner dans l'ordre inverse (disjoncteur de branchement, puis disjoncteur abonné).
2. Vérifier l'allumage de l'écran LCD — le compteur démarre en 3 à 5 secondes.
3. Contrôler l'affichage : `1.8.0 = 0.0 kWh` sur un compteur neuf.
4. Vérifier la présence de la LED rouge clignotante (impulsion métrologique, 1000 imp/kWh).
5. Connecter un client de test (prise étalon + charge) et vérifier que l'index avance.

### Étape 4 — Appairage réseau PLC

L'appairage au concentrateur est automatique :
- Le compteur scanne les canaux PLC G3 pendant 10 minutes après mise sous tension.
- Le concentrateur doit être en mode "découverte" (commande côté HES).
- L'appairage réussi se traduit par l'icône "antenne pleine" sur l'écran LCD.

Si l'appairage échoue après 30 min :
1. Vérifier que la phase côté compteur correspond au même point de livraison que celui desservant le concentrateur.
2. Relancer le scan via le port optique (commande DLMS `7.0.128.96.50.0`).
3. Si toujours KO, le compteur doit être remonté vers le lab pour diagnostic firmware.

## Installation d'un compteur triphasé MS-TRI-400

### Raccordement direct (courant ≤ 100 A)

Schéma de raccordement direct (4 fils, neutre distribué) :

```
L1 ──▶ [1] ══════ [2] ──▶ L1 charge
L2 ──▶ [3] ══════ [4] ──▶ L2 charge
L3 ──▶ [5] ══════ [6] ──▶ L3 charge
 N ──▶ [7] ══════ [8] ──▶ N charge
```

Couple de serrage : **3.0 Nm ± 0.3** pour tous les bornes de puissance.

### Raccordement indirect via TC (courant > 100 A)

Pour les installations > 100 A, utiliser des transformateurs de courant. Le MS-TRI-400 supporte des TC de rapport 100/5, 200/5, 400/5, 800/5, 1000/5.

Le rapport TC doit être programmé dans le compteur via logiciel de paramétrage (port optique) AVANT la mise sous tension, sinon la mesure sera fausse d'un facteur égal au rapport.

### RS485 Modbus — raccordement GTB

Le port RS485 est situé sur la face inférieure du compteur, connecteur Phoenix 3 broches :
- A (D+) : borne gauche
- B (D−) : borne centrale
- GND : borne droite (shield câble uniquement, non relié à la terre)

Paramètres par défaut : 9600 bauds, 8N1, adresse esclave 1. Modifiable via registre Modbus `0x0010`.

Résistance de terminaison 120 Ω à activer sur le dernier esclave (switch DIP à côté du connecteur).

## Tests finaux obligatoires

À consigner sur le bon d'intervention :

1. ✅ Tension entre phase et neutre : 230 V ± 10 % (mono) / 400 V ± 10 % (tri entre phases).
2. ✅ Rotation triphasée correcte : contrôle au séquencemètre (sens horaire L1-L2-L3).
3. ✅ Index de départ noté sur le bon (photo conseillée).
4. ✅ Scellés de plombage posés sur le capot principal ET sur le capot bornes.
5. ✅ Remontée du compteur visible dans le HES (délai max 1h après mise en service).

## Sécurité et responsabilité

Rappel : toute intervention non-consignée sur un compteur en service est un manquement grave aux procédures sécurité. En cas de doute sur l'état d'un compteur (capot forcé, scellé manquant), **ne pas intervenir** et escalader au responsable secteur.
