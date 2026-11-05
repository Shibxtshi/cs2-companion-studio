# Installation Windows

[English](installation.md) · [Guides utilisateur](README.fr.md)

## Prérequis

Windows PowerShell 5.1 ou PowerShell 7, Steam avec CS2 installé, Docker Desktop avec Compose v2 démarré. Aucun Python n’est nécessaire pour l’assistant ; Docker n’est pas installé silencieusement. Utilisez une archive de confiance : la version `1.0.0` du code ne prouve pas qu’une release officielle existe. Extrayez tout le ZIP dans un dossier accessible en écriture avant de lancer un script.

## Installation guidée

1. Démarrez Docker Desktop et attendez son moteur.
2. Double-cliquez sur `INSTALLER_WINDOWS.cmd` à la racine extraite. Le lanceur contourne la politique d’exécution PowerShell pour ce processus uniquement ; utilisez des scripts fiables.
3. Choisissez EN (défaut), FR, RU, PL, UK, CS ou RO. La langue du navigateur reste indépendante. Confirmez le dossier Steam/CS2 détecté ; les bibliothèques secondaires sont recherchées.
4. Si la détection échoue, trouvez le dossier contenant `game/csgo/cfg` via Steam → CS2 → Gérer → Parcourir les fichiers locaux. Depuis la racine du projet, remplacez le chemin d’exemple :

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Language FR -Cs2Path 'D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive'
   ```

5. Une nouvelle installation génère un PIN privé et un token GSI distinct. Un `.env` existant est réutilisé ; ne partagez ni ce fichier ni le PIN affiché. Laissez le chronomètre estimatif désactivé sauf autorisation explicite dans le contexte d’utilisation.
6. L’assistant vérifie l’accès au dossier GSI. Seul un problème d’autorisation de fichiers peut proposer une élévation UAC avec consentement ; une panne Docker ne le justifie pas. Refuser une opération nécessaire arrête cette installation. Le remplacement d’un fichier GSI différent non géré demande confirmation (sauf forçage explicite). Un fichier correspondant encore à son empreinte gérée peut être actualisé sans cette question supplémentaire. Les originaux sauvegardés restent dans `.installer-state/`, à garder pour la récupération ou la désinstallation.
7. Restez en accès local sauf besoin d’un autre appareil. Lisez le [guide LAN](network.fr.md) avant de l’activer. Aucune règle de pare-feu n’est créée automatiquement.
8. L’assistant construit/démarre CCS. Ouvrez `http://localhost:8080` (ou le port configuré). Testez Démonstration, puis connectez-vous avec le PIN. Le nouveau Dashboard est vide ; suivez la [première utilisation](first-use.fr.md).
9. Redémarrez CS2 après ajout/modification de `gamestate_integration_companion.cfg`, puis lancez un entraînement. Recevoir du GSI ne signifie pas forcément qu’une partie est active.

Les lettres de confirmation affichées sont EN : Y, FR : O, RU : D, PL/UK : T, CS : A et RO : D. Une réponse vide/inconnue refuse normalement. Pour une automatisation, examinez les paramètres du script ; n’utilisez pas les options de remplacement ou non interactives pour contourner un conflit inexpliqué.

L’assistant n’efface ni ne convertit un stockage incompatible. Les anciens profils nécessitent une [récupération hors ligne](backup.fr.md). Le [guide développeur (anglais)](../development/README.md) décrit Linux et l’exécution native ; ce guide ne constitue pas une matrice de support matériel Windows vérifiée. Consultez la [maintenance](maintenance.fr.md) avant mise à jour ou désinstallation.
