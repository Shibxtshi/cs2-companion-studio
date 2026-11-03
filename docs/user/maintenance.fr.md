# Maintenance et dépannage

[English](maintenance.md) · [Guides utilisateur](README.fr.md)

Exécutez les commandes dans PowerShell depuis la vraie racine installée, Docker Desktop démarré. Lisez leurs effets avant exécution ; elles ne donnent pas le droit de modifier une autre installation. Ne supprimez jamais `data/` pour résoudre un démarrage.

## Vérifier ou redémarrer

```powershell
powershell -NoProfile -File .\installer\status.ps1
docker compose ps --all
```

Ces commandes inspectent l’état. Ouvrez `http://localhost:8080/health` (adaptez le port hôte) : la réponse prouve la santé HTTP, pas une partie fonctionnelle ni le commit exact. Après conservation des brouillons, `docker compose restart cs2-companion-studio` interrompt les connexions et réinitialise la partie en mémoire, en préservant les fichiers montés. Il ne recharge **pas** les variables d’environnement modifiées.

Pour appliquer des réglages `.env` volontairement changés, lancez `APPLIQUER_REGLAGES_WINDOWS.cmd`, ou :

```powershell
docker compose up -d --no-build --pull never --force-recreate --wait --wait-timeout 120 cs2-companion-studio
```

Le conteneur est recréé depuis l’image existante, sans build/pull. Cette image doit déjà exister. Profils et `.env` restent, mais toutes ses modifications prennent effet : nouveau PIN implique reconnexion ; changement de token GSI/port hôte implique configuration CS2 cohérente et redémarrage. Ne renouvelez pas les credentials ni n’activez le chronomètre estimatif sans raison. Modifier `.env` seul n’applique rien.

## Mise à jour cible compatible ou réinstallation

1. Vérifiez les formats explicitement pris en charge par la version candidate. Conservez l’ancienne source/image compatible. Aucune migration historique générale n’est promise.
2. Conservez les brouillons, fermez l’édition et arrêtez CCS. Créez/vérifiez une [sauvegarde privée complète](backup.fr.md), dont `.env`, `data/`, `.installer-state/` et fichiers de récupération GSI.
3. Extrayez les nouveaux fichiers fiables dans un dossier séparé. Ne restaurez des copies de configuration/données que si leur format cible est explicitement compatible. Gardez ancienne installation/sauvegarde intactes ; ne lancez pas deux instances sur les mêmes données ou port hôte.
4. Depuis le nouveau dossier, lancez `docker compose up -d --build`. Cette commande construit l’image et peut télécharger base/dépendances ; elle diffère de l’application de réglages sans build. Vérifiez PIN, profil, Studio, publication explicite, rechargement et entraînement.
5. En cas d’échec, arrêtez le nouvel écrivain et suivez la [récupération vérifiée](backup.fr.md). Ne copiez pas de fichiers sur un service en cours d’exécution.

Une réinstallation neuve crée une instance privée, sans conversion de profils ni transfert automatique de brouillons. Un import transfère une configuration examinée, pas les credentials/historique serveur. La récupération historique utilise les outils hors ligne et l’application archivée compatible. `docker compose down` arrête/supprime les conteneurs et le réseau par défaut du projet ; sans `--volumes`, il ne demande pas la suppression des volumes nommés et n’efface pas les bind mounts hôtes `data/`, `logs/` ou `.env`. N’ajoutez pas de drapeau de suppression comme dépannage général.

## Diagnostiquer sans exposer de secrets

| Symptôme | Contrôle |
|---|---|
| Serveur indisponible | Moteur Docker, état Compose, port configuré et autre instance occupant ce port |
| PIN refusé | Bonne instance et PIN conservé localement ; attendre après échecs répétés (limitation temporaire), ne jamais publier le code |
| GSI en attente | CS2 redémarré après installation du CFG ; URI/token/port cohérents localement ; entraînement plutôt que menu seul |
| Valeur absente | Champ éventuellement non fourni ; comparer fraîcheur de partie/GSI et diagnostics, pas un zéro supposé |
| Données périmées | Ne plus les considérer actuelles ; vérifier CS2 et reconnexion WebSocket |
| Échec LAN | Suivre le [guide réseau](network.fr.md), sans désactiver le pare-feu ni ouvrir le routeur |
| Erreur de brouillon | Garder l’onglet/travail et vérifier autorisations/quota ; ne pas effacer le navigateur en première intention |
| Publication incertaine/conflit | Conserver le brouillon, examiner le serveur et utiliser la réconciliation explicite proposée |
| Stockage incompatible | Arrêter/inspecter hors ligne ; ne pas effacer/réinitialiser pour forcer le démarrage |

Settings/Paramètres → Diagnostics distingue serveur, WebSocket authentifié, GSI et partie active. Aide/démarrage rapide restent réouvrables. La démonstration ne prouve pas le GSI réel. `docker compose logs --tail=30` aide **localement**, mais peut contenir des informations sensibles : ne partagez pas de sortie brute sans examen. Suivez [SUPPORT.md (anglais)](../../SUPPORT.md) pour les exports vérifiés manuellement, [SECURITY.md (anglais)](../../SECURITY.md) pour les vulnérabilités.

## Désinstaller

Conservez d’abord les sauvegardes privées. Fermez les onglets et lancez `DESINSTALLER_WINDOWS.cmd` (ou `powershell -NoProfile -File .\installer\uninstall.ps1`) depuis l’installation. L’outil restaure le GSI sauvegardé ou supprime le nouveau fichier géré seulement si son empreinte correspond encore à celle installée. Un GSI modifié à la main est conservé ; une sauvegarde nécessaire absente entraîne un refus. Le nettoyage GSI réussi peut retirer son fichier d’état ; conservez votre copie. Sauf `-KeepDocker`, Compose down est appelé. `.env`, profils, logs et répertoires de sauvegarde ne sont pas automatiquement effacés. Redémarrez CS2 après retrait/restauration GSI. Effacer les fichiers privés conservés reste une action séparée après vérification des besoins de récupération.
