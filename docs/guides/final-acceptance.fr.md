# Recette finale CCS — P10-A et P10-B

> HISTORICAL RECORD — this dated phase report/plan is retained for provenance, not current operating instructions or current test evidence. Production is now target-only; historical files are refused without replacement. Use the [documentation index](../README.md) and [current operator procedure](../development/production-activation.md).


P10-A utilise uniquement des instances jetables et des données synthétiques. **P10-B et l’activation de l’installation personnelle nécessitent une autorisation distincte du mainteneur.** Ce guide ne constitue pas cette autorisation. La fusion d’une PR ne déclenche aucune remise à zéro.

Le [guide technique d’activation](../development/production-activation.md) décrit les formats, les sauvegardes et les erreurs. La procédure ci-dessous concerne le mainteneur et ses essais manuels.

## 1. Conditions avant P10-B

- Disposer du rapport P10-A, du commit exact approuvé et des limites des tests locaux. Aucun résultat GitHub Actions non exécuté ne vaut une réussite.
- Identifier le dossier de l’installation réellement utilisée, le service qui l’exécute et les chemins effectifs de ses données. Ne pas supposer qu’un snapshot de développement est cette installation.
- Identifier une version historiquement compatible et conserver son code ou son image Docker, ainsi que son commit exact. Le numéro `1.0.0` affiché dans l’interface ne suffit pas à identifier un commit. Ne pas inventer ce SHA si sa provenance est inconnue : préparer et tester une version compatible connue avant la bascule.
- Valider la sauvegarde et la restauration sur une instance synthétique ; obtenir ensuite l’autorisation explicite de l’activation réelle.
- Prévoir une interruption du service. Fermer les anciens onglets et arrêter tous les écrivains, y compris les éventuels autres services utilisant le même dossier. Le verrou protège les outils coopératifs sur le même système de fichiers ; il ne remplace pas cet arrêt.

Dans ce guide, `BACKUP_ID` est l’identifiant affiché par la préparation ; `HISTORICAL_COMMIT` est le commit compatible réellement conservé. Les valeurs de PIN et de token existantes ne sont jamais à recopier dans les commandes ou les rapports.

## 2. Préserver la version et les fichiers privés

Depuis le dossier d’installation confirmé, relever uniquement l’identifiant de l’image, sans afficher son environnement :

```powershell
$ccsContainer = docker compose ps -q cs2-companion-studio
docker inspect --format '{{.Image}}' $ccsContainer
```

Conserver cette image ou une archive privée de celle-ci, le code compatible et les fichiers de lancement nécessaires. Ne pas utiliser un simple tag mutable comme seule preuve de version. Conserver `.env`, `data/`, les configurations privées et les sauvegardes existantes dans un emplacement privé. Ne pas publier ces copies.

Le mécanisme CCS sauvegarde intégralement les octets des deux fichiers de profils quand ils existent ; il ne copie pas inutilement les credentials. Une copie privée complète de l’installation reste utile pour préserver les autres réglages. Les ACL Windows et les permissions du dossier doivent limiter l’accès ; les sauvegardes ne sont pas un coffre chiffré.

## 3. Arrêter, préparer et vérifier

Après l’autorisation distincte de P10-B :

```powershell
docker compose stop cs2-companion-studio
docker compose ps --status running -q cs2-companion-studio
```

La seconde commande ne doit pas indiquer un service encore actif. Vérifier également les autres lanceurs éventuels. Construire ou sélectionner l’image contenant le commit P10 approuvé, sans démarrer le serveur. Ne pas modifier `.env`, le PIN, le token GSI ou le réseau pour réaliser cette transition.

Avec cette image, le lanceur de commande ci-dessous utilise le montage `data/` du projet et n’exécute pas le serveur :

```powershell
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --inspect
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --prepare-activation --application-revision HISTORICAL_COMMIT --service-stopped
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --inspect-activation BACKUP_ID
```

Ces commandes ne doivent être utilisées que depuis l’installation identifiée, après vérification des montages. Ne pas créer un autre projet Compose qui pointerait par erreur vers un autre dossier.

La préparation doit annoncer un dossier privé unique sous `data/profile-reset-backups/`. Elle vérifie les octets originaux, taille, SHA-256, relecture, validité et absence de changement des sources. L’inspection revérifie le dossier et le candidat. Une erreur interdit de continuer. Garder aussi les fichiers privés `.profiles-activation-*` dans `data/`.

Une préparation d’activation version 1 peut être inspectée et restaurée, mais P10 exige une préparation neuve pour l’activer. Une tentative déjà engagée laisse un marqueur `.attempted` : **ne pas le supprimer pour réutiliser l’identifiant**. Après échec, interruption ou retour arrière, préparer un nouvel identifiant et une nouvelle génération. `prepared_or_restored` décrit les fichiers ; il ne signifie pas qu’un ancien candidat est réutilisable.

## 4. Confirmation et activation

Relire les conséquences : les noms, dispositions et personnalisations historiques ne seront plus l’état actif. Il n’y a pas de conversion automatique `span` vers X/Y. Les octets historiques restent dans la sauvegarde vérifiée.

```powershell
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --activate BACKUP_ID --service-stopped
```

Saisir exactement `ACTIVATE BACKUP_ID` seulement si l’autorisation réelle a été donnée. Entrée seule annule. Toute erreur impose une inspection avant une nouvelle action. Une nouvelle tentative exige une nouvelle préparation si le candidat a déjà été tenté.

Démarrer ensuite l’application compatible avec le format installé, sans reconstruction ou téléchargement implicite :

```powershell
docker compose up -d --no-build --pull never
```

Vérifier la santé, la connexion avec le PIN conservé et l’ouverture du nouveau Studio. Ne pas rouvrir un ancien onglet avec une intention de publication d’une autre génération. Ne pas effacer les anciens brouillons inconnus ni réécrire leur révision ; toute récupération de configuration doit être examinée et publiée explicitement dans le contexte approprié.

## 5. Recette UI et données publiées

| Essai | Résultat attendu |
| --- | --- |
| Connexion, Dashboard → Studio → Settings | Un seul cycle de connexion ; pas de PIN redemandé à chaque écran |
| Ajouter, supprimer et dupliquer un widget | Modification du brouillon ; Dashboard publié inchangé |
| Choisir Standard, Compact, Minimal | Présentation individuelle, indépendante de la densité globale et des dimensions |
| Modifier X/Y, largeur/hauteur | Alignement en cellules ; collision refusée sans pousser les voisins |
| Annuler/rétablir un geste | Une opération complète par geste ; aucun enregistrement serveur |
| Fermer/recharger après conservation locale confirmée | Brouillon proposé à la reprise ; PIN à ressaisir après une nouvelle session |
| Conserver et quitter | Brouillon confirmé localement, aucune publication |
| Abandonner | Confirmation ; suppression du brouillon concerné, version publiée conservée |
| Enregistrer et appliquer | Réussite seulement après confirmation serveur ; variante et géométrie conservées après redémarrage |
| Deux onglets, deux profils | Sélections indépendantes, sans changement imposé à l’autre onglet |
| Deux contextes indépendants, même profil | Conflit explicite après publication concurrente ; brouillon conservé |
| Import cible | Revue/prévisualisation puis brouillon ; publication séparée |
| Export | Nom/configuration uniquement ; pas de contexte d’accès, reçu, token, PIN ou partie |
| Déconnexion annulée / confirmée | Annulation intacte ; confirmation efface le contexte local avant la déconnexion |
| Navigation masquée sans bouton flottant | Retour possible par le bord, le clavier lorsque permis et le tactile |
| Logo, plein écran et sortie | Aucun rechargement inutile, perte de travail ou piège d’accès |
| Démonstration | Données clairement synthétiques, aucun profil privé accessible ni publication |

Vérifier FR et EN, les quatre thèmes, le clavier et le zoom. Contrôler 1920×1080, 1366×768, 1280×900, 1024×768, 768×1024, 390×844 et 320×740. Noter si un résultat vient d’une émulation ou d’un appareil physique. La projection mobile ne doit pas modifier les coordonnées desktop enregistrées.

## 6. Recette avec un véritable CS2

Cette recette n’a pas été réalisée par les tests synthétiques. Elle utilise une session d’entraînement autorisée, sans lecture mémoire, injection, modification d’anti-triche ou contournement. Vérifier les règles applicables avant tout usage compétitif. Ne pas activer le compte à rebours estimé pour cette recette ; son défaut reste désactivé et il ne constitue pas une durée officielle.

Utiliser la configuration GSI normale de l’installation, dont le token est conservé. Si elle doit être installée ou modifiée, obtenir l’accord du mainteneur et utiliser le mécanisme prévu avec sauvegarde ; ne pas la remplacer aveuglément. Redémarrer CS2 si cette configuration vient d’être ajoutée ou changée.

Créer un profil de recette avec les widgets pertinents et le publier explicitement.

| Action dans CS2 | Résultat à comparer dans CCS |
| --- | --- |
| Démarrer CS2, rester au menu | Distinguer serveur connecté, GSI reçu et données de partie disponibles ; ne pas inventer une partie |
| Entrer dans un entraînement | Carte, contexte et phase reçus ; pas de chiffres inventés pour les champs absents |
| Subir des dégâts dans l’entraînement | Vie correspondant à la valeur reçue ; zéro réel différent d’une valeur inconnue |
| Acheter/consommer de l’armure | Armure et équipements reçus ; absence d’information indiquée comme telle |
| Acheter/changer d’arme, tirer puis recharger | Arme active, chargeur et réserve cohérents avec les données reçues |
| Faire un achat | Argent actualisé ; prévisions séparées et identifiées comme estimations |
| Terminer une manche | Score, numéro/phase et historique disponibles cohérents avec le GSI |
| Jouer plusieurs manches | K/D, statistiques personnelles et MVP uniquement lorsqu’ils sont fournis |
| Planter, désamorcer ou laisser exploser en entraînement | États de bombe reçus ; aucun compte à rebours officiel inventé |
| Passer du Dashboard au Studio et revenir | Widgets rafraîchis, configuration publiée inchangée par la simple consultation |
| Quitter la partie puis le jeu | Fin de validité des anciennes valeurs ; pas de vie/argent/arme périmés présentés comme actuels |
| Relancer CS2 et une partie | Retour des données sans perte du profil ou publication spontanée |

Le serveur utilise un délai de fraîcheur de **20 secondes** et une diffusion périodique de **2 secondes**. Laisser au moins ce délai plus une diffusion pour observer la péremption après arrêt des signaux. Les paquets d’identité seuls ne doivent pas prolonger la fraîcheur des données de partie. Ne pas faire de cette fenêtre une garantie de latence réseau ou une preuve que tous les champs sont toujours fournis par CS2.

Tester les listes longues et valeurs longues lorsqu’elles existent réellement, sans inventer des données manquantes. Les tests automatisés des 87 combinaisons et des cas synthétiques restent une preuve distincte de cette observation réelle.

## 7. Retour arrière

Arrêter le serveur et fermer les onglets avant de restaurer. Si de nouvelles publications cibles ont réussi, elles ne seront pas présentes dans l’ancien état ; conserver les exports/configurations utiles en privé et le snapshot cible créé par l’outil.

Avec l’image P10 contenant l’outil de récupération :

```powershell
docker compose stop cs2-companion-studio
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --inspect-activation BACKUP_ID
docker compose run --rm --no-deps --entrypoint python cs2-companion-studio scripts/recover_profiles.py --data-dir /app/data --restore-activation BACKUP_ID --service-stopped
```

Lire la demande exacte de confirmation. L’outil conserve l’état courant avant de restaurer les deux fichiers historiques. Un marqueur `.pending` interdit le démarrage après interruption : reprendre la restauration avec son propre identifiant, sans supprimer ce marqueur ni lancer un autre écrivain.

Revenir ensuite au code ou à l’image historiquement compatible conservée. Utiliser son identifiant d’image immuable et un fichier Compose d’override privé si nécessaire ; démarrer avec `--no-build --pull never`, puis vérifier les profils et le GSI. L’outil de restauration ne réinstalle pas les binaires à la place de l’opérateur. `.env`, credentials et autres fichiers privés doivent rester identiques.

Exemple d’override privé, en remplaçant la valeur par l’identifiant complet réellement conservé :

```yaml
services:
  cs2-companion-studio:
    image: "sha256:IDENTIFIANT_IMAGE_COMPATIBLE"
```

Depuis le même dossier d’installation, après chargement de l’image privée si nécessaire :

```powershell
docker compose -f compose.yaml -f PRIVATE_OVERRIDE_FILE up -d --no-build --pull never
```

Ne pas modifier le fichier Compose suivi, les credentials ou le réseau pour ce retour arrière. Conserver cet override hors du dépôt et des archives publiques.

Une récupération de `.bak` cible possède sa propre commande `--restore-target`, sa confirmation et une nouvelle génération. Son périmètre exige un fichier courant présent à préserver. Si ce fichier est absent, que les sauvegardes sont inexploitables ou que l’état ne correspond pas à cette procédure, conserver tous les artefacts et demander une récupération spécifique ; ne pas initialiser un dossier supposé vide. Les anciens reçus ne doivent jamais être rejoués dans une nouvelle génération.

## 8. Remonter les résultats et décider

Pour chaque essai, noter : commit, OS, navigateur/version, type d’appareil réel ou émulé, action, attendu, observé et reproductibilité. Classer les défauts : bloquant, important, mineur. Signaler si l’échec existe aussi avec une configuration synthétique.

Ne pas joindre `.env`, PIN, token, `.cfg` GSI, paquets bruts, profils personnels ou logs bruts. Inspecter l’export de diagnostic et masquer les identifiants personnels sur les captures avant partage. Un export de configuration peut contenir des titres personnels : il n’est pas automatiquement public.

Un problème de perte/corruption, publication sans consentement, fuite, contournement du PIN ou restauration impossible impose un **NO-GO**. Un défaut important exige correction ou décision explicite. P10-A réussie autorise seulement à proposer P10-B ; la refonte ne peut être déclarée terminée avant la recette personnelle approuvée. Une publication publique, une release et OBS restent des décisions distinctes.
