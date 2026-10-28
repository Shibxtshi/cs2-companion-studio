# V1P-E — Expérience utilisateur (étape 7)

- Nouvelle connexion avec étapes de démarrage pour les personnes découvrant GSI et Docker.
- Aide contextuelle accessible depuis l'accueil et le tableau de bord, y compris sans jeu lancé.
- Diagnostic en trois parties : serveur, connexion WebSocket authentifiée et données GSI reçues.
- Bandeau d'état lisible : démonstration, jeu connecté, partie en attente ou reconnexion.
- Messages et libellés EN/FR améliorés ; l'anglais reste la langue par défaut.
- Meilleur confort sur téléphone : disposition adaptée, zones d'action et absence de débordement horizontal.
- Accessibilité : raccourci vers le contenu, navigation clavier des onglets, aide modale et focus visible.
- **Profils inchangés** : stockage dans le navigateur et export/import JSON, sans synchronisation serveur pour cette version.
- Aucun changement des données GSI, du PIN, des 29 widgets ou du minuteur.

---

# V1P-D — Studio de widgets (étape 6)

- Ajuster la largeur d’un widget en tirant sa poignée sur ordinateur (ou avec les flèches du clavier).
- 5 modèles de départ : Compétitif, Mobile, Vue du match, Streaming et Page vide.
- Choisir pour chaque carte un fond, un style plein/verre/contour et son opacité.
- Passer les dashboards personnalisés en affichage compact ou normal.
- Filtrer la bibliothèque par catégorie et rechercher un module.
- Importer les anciens exports JSON V3 / V1P (v1) et exporter les nouveaux paramètres au format v2.
- Conserver les profils navigateur existants, l'anglais par défaut, le français et l'installateur corrigé.
- Aucun changement du fonctionnement du minuteur, de l’API GSI ou de l’installation CS2.

---

# V1P-C.2 — Language & Windows permissions

- **EN / FR language selector**: English by default; switch between English and French in the installer and dashboard.
- **Short confirmations**: `Y/N` for English, `O/N` for French; No by default.
- **UAC only when necessary**: the installer checks access rights and asks before elevating to administrator.
- **Existing settings retained**: PIN, token, dashboard layouts and the existing GSI configuration remain compatible.

---

# Changelog fonctionnel — pour les joueurs

## V1P-C.1 — Correctif installateur Windows

- Detection de CS2 plus resistante aux lecteurs reseau ou bibliotheques Steam deconnectes.
- Diagnostic etape par etape : Docker, recherche de CS2, configuration, demarrage.
- Erreurs Docker plus lisibles et conseils pour fournir manuellement le chemin de CS2.
- Aucune modification des widgets, des secrets existants ni du moteur GSI.


## V1P-C — Étape 5 : installation Windows guidée

- Installation lancée en double-cliquant sur un fichier, sans installer Python ni copier à la main un fichier GSI.
- Détection automatique de CS2 et des bibliothèques Steam secondaires, avec sélection manuelle du dossier en secours.
- Nouveau PIN et identifiants générés automatiquement pour chaque nouvelle installation.
- Conservation des identifiants et profils existants lors d'une migration depuis V1P-B.
- Sauvegarde de l'ancien fichier GSI avant remplacement ; désinstallation sans effacer les profils ou les secrets.
- Mode téléphone / réseau domestique optionnel, désactivé par défaut, avec avertissements réseau.
- Nouvelle commande de diagnostic pour vérifier installation, Docker et connexion au serveur.
- 29 widgets, score, inventaire, économie et minuteur : **inchangés**.

## V1P-B — Étape 4 : stabilité GSI

- Reconnexion au jeu mieux gérée.
- Données réinitialisées proprement lors des changements de manche, de carte ou de côté.
- Bonus de défaite estimé lorsque l'historique suffisant existe, avec indication des incertitudes.
- Données manquantes ou anciennes signalées plutôt que présentées comme actuelles.
- Meilleure gestion du démarrage tardif du minuteur de bombe.


### V1P-C.2.1 - Correctif de lancement Windows

- Correction d'un blocage de l'installateur lors du chargement des textes français.
- Menu EN/FR et confirmations Y/N ou O/N conservés.
- Vérification de syntaxe PowerShell disponible dans `tests/windows/check_syntax.ps1`.
- Aucun changement du dashboard, du fichier GSI ni des identifiants.


### V1P-E.1 — Ajustements avant les tests publics

- Recherche de widgets utilisable en français **et** en anglais (dont « map »).
- Profils enregistrés côté serveur Docker et partagés entre appareils authentifiés.
- Possibilité de renommer un dashboard créé auparavant.
- Les dashboards personnels ne sont plus visibles en mode démo public.
- Bloc de diagnostic placé en bas de page ; export simplifié pour les issues GitHub.
- Documentation et aide actualisées avec une mention de non-affiliation Valve / CS2 / FACEIT.
- Pas de migration automatique des anciens profils, conformément à la demande.


### V1P-F — Fiabilité et sécurité avant la publication (étape 8)

- **Dashboard inchangé :** les widgets, les profils partagés, les deux langues et la démo fonctionnent comme avant.
- **Protection renforcée :** contrôle plus strict de la provenance des connexions temps réel.
- **Tests automatiques élargis :** parcours des utilisateurs, synchronisation sur deux appareils et erreurs de connexion simulées.
- **Préparation GitHub :** contrôles Windows, Linux, trois navigateurs, Docker et dépendances.
- **Vérification des archives :** blocage des fichiers de configuration privés et profils si inclus accidentellement.
- **Rapports de qualité :** audit des bibliothèques et inventaire des dépendances logiciel (SBOM).

Cette version est une candidate de tests : la validation sur GitHub Actions et sur Windows reste nécessaire avant publication.


## V1P-F.1 — Verification locale corrigée
- Le contrôle de sécurité accepte désormais le `.env` d’une installation locale.
- Les secrets suivis par Git ou présents dans une archive publique restent interdits.
- Trois scénarios de non-régression ajoutés pour la publication.
