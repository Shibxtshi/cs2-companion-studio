# Installation Windows — V1P-E.1 (installateur V1P-C.2.1 conservé)

L'assistant est un script **PowerShell natif** (Windows PowerShell 5.1 ou PowerShell 7) ; Python n'est pas nécessaire. Docker Desktop + Docker Compose v2 doivent être installés et démarrés. Le dashboard utilise le port TCP 8080 par défaut, en local uniquement. La version reste une *préversion de développement*.

## Nouvelle installation

1. Télécharger et décompresser l'archive dans un dossier personnel (ex. `Documents\CS2-Companion`). **Ne pas lancer le script directement dans le ZIP.**
2. Vérifier que Docker Desktop est démarré.
3. Double-cliquer sur `INSTALLER_WINDOWS.cmd` (ou ouvrir PowerShell dans le dossier et exécuter `powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1`). N'exécuter des scripts que depuis une archive fiable : la politique d'exécution est temporairement contournée pour ce processus, **pas modifiée globalement**.
4. L'assistant recherche CS2 via Steam et ses bibliothèques secondaires. Si la détection échoue, ouvrir PowerShell et préciser le chemin :
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Cs2Path 'D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive'
   ```
5. Confirmer expressément tout remplacement d'un fichier GSI déjà présent. Une sauvegarde privée locale est créée auparavant. **Ne pas supprimer** `.installer-state` tant que l'installation doit pouvoir être annulée.
6. Sur une nouvelle installation, conserver le PIN affiché localement. Le token est écrit uniquement dans les fichiers locaux `.env` et GSI : ne jamais les partager.
7. Sur PC, ouvrir `http://localhost:8080`. Redémarrer **CS2** si le fichier GSI vient d'être installé ou modifié. Tester les HP et munitions en entraînement privé.

### Téléphone (optionnel)

Lors d'une **nouvelle** installation, l'assistant propose le mode LAN, qui demande deux confirmations. Pour une installation existante, utiliser explicitement `-Lan` :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Lan
```

Le mode LAN configure `BIND_HOST=0.0.0.0`, donc un port exposé sur les interfaces de l'ordinateur. **Attention : HTTP/WS n'est pas chiffré.** Utiliser seulement un réseau Wi-Fi privé de confiance, vérifier l'isolation/pare-feu Windows (TCP 8080 limité au réseau local) et ne jamais ouvrir/rediriger ce port sur le routeur ou Internet. Un réseau d'invités ou Wi-Fi public n'est pas approprié. Docker Desktop/WSL2 peut modifier le comportement du pare-feu : le vérifier explicitement. Depuis le téléphone, ouvrir `http://IP_LOCALE_DU_PC:8080`.

Pour revenir à une écoute locale uniquement :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -LocalOnly
```

## Migration depuis V1P-B

1. Exporter tes profils de widgets en JSON par précaution.
2. Arrêter **l'ancienne** V1P-B depuis son dossier avec `docker compose down` (sinon deux serveurs voudront le port 8080).
3. Décompresser V1P-C dans un **nouveau** dossier.
4. Copier uniquement ton ancien `.env` personnel dans ce nouveau dossier. L'assistant réutilise le **même PIN, le même token, le même port et le même mode réseau** ; il ne les écrase pas sans demande explicite.
5. Lancer `INSTALLER_WINDOWS.cmd`. Le fichier CS2 GSI est comparé à la configuration désirée ; si sa mise à jour est nécessaire, l'assistant demande confirmation et crée une sauvegarde (même si c'est un fichier GSI de l'ancienne version).
6. Les profils V1P-E.1 résident dans `data/profiles.json` sur le serveur Docker : conserver ce dossier lors des futures mises à jour. Aucun profil navigateur antérieur n’est migré automatiquement.

## Diagnostic

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\status.ps1
docker compose logs --tail=30
```

- `http://localhost:8080/health` doit annoncer `"version":"1p-e.1"`.
- Si le serveur ne démarre pas, vérifier Docker Desktop et qu'aucun ancien conteneur n'occupe 8080.
- Si GSI reste déconnecté, vérifier que CS2 a été **redémarré après installation du .cfg** et que `127.0.0.1:8080` est joignable.
- Les messages du diagnostic ne doivent jamais afficher le token ni le PIN.
- Si Steam est installé à un endroit atypique, utiliser `-Cs2Path` avec le dossier contenant `game\csgo\cfg`.

## Désinstallation et retour arrière

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\uninstall.ps1
```

Ou double-cliquer sur `DESINSTALLER_WINDOWS.cmd`.

L'assistant arrête le conteneur, puis **restaure la sauvegarde** du fichier GSI qu'il a remplacé ou **supprime** uniquement le fichier GSI créé par lui, à condition qu'il n'ait pas été modifié depuis l'installation. Un fichier GSI modifié manuellement est conservé. Si l'ancien fichier était déjà identique à la configuration attendue, il est conservé. En cas de sauvegarde manquante, il refuse d'écraser le fichier.

**Par sécurité, `.env`, `.installer-state`, `data/` et `logs/` ne doivent jamais être supprimés automatiquement.** Les identifiants et sauvegardes restent privés ; pour effacer les traces après avoir restauré le GSI, supprimer ces dossiers/fichiers manuellement après avoir vérifié que tu n'en as plus besoin.

## Limitations connues

- Assistant **Windows uniquement**, fonctionnement de Steam/Docker à confirmer sur de vrais PC utilisateurs ; les tests automatisés de l'installateur utilisent des fichiers simulés.
- Pas d'installation automatique de Docker (l'utilisateur doit l'installer).
- Pas d'élévation automatique en administrateur ni de création de règle de pare-feu, pour éviter de modifier silencieusement la sécurité réseau.
- Plusieurs installations de CS2 ou bibliothèques Steam atypiques peuvent nécessiter le chemin explicite `-Cs2Path`.
- Les fonctionnalités sujettes aux règles FACEIT, notamment le minuteur estimatif de la bombe, restent désactivées par défaut dans une installation neuve.

## Correctif V1P-C.2 : chemin reseau non trouve

Si un lecteur reseau Windows est deconnecte, l'ancien assistant pouvait s'interrompre
lors de la recherche de bibliotheques Steam. Le correctif ignore les chemins inaccessibles
et indique l'etape fautive. Il distingue egalement un moteur Docker inaccessible.

Si la recherche automatique echoue, lancer depuis le dossier du projet :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Cs2Path 'D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive'
```

Remplacer le chemin par le dossier CS2 reel (Steam > CS2 > Gerer > Parcourir les fichiers locaux).
En cas d'echec a l'etape Docker, executer `docker info` et `docker compose version` dans PowerShell.
Aucun `.env` ou fichier GSI existant ne doit etre supprime pour corriger cette erreur.


## Language and permissions — V1P-C.2

Choose **1 / EN** (default) or **2 / FR** at startup. Change the dashboard language independently through its **EN / FR** selector; no restart is needed.

For short prompts, answer `Y` (English) or `O` (French). `N`, Enter, unknown input or refusal of UAC means **No** by default.

Administrator permissions are **not requested by default**. The installer first tests the Steam CS2 config folder and Docker. If access is denied it asks whether you want to request UAC. Approve only if you trust the downloaded archive and recognize the Windows administrator request. If you refuse, you can still use the previous version safely.

For a forced language in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Language FR
```

**Important:** The elevation logic is tested for syntax and helper behavior in Windows CI, but must also be tested interactively on a Windows PC (standard user, accepted UAC, refused UAC). Avoid relying on an always-elevated terminal for normal use.


## V1P-E.1 — Où sont les profils et les diagnostics ?

- `data/profiles.json` : vos profils sauvegardés et partagés entre appareils connectés.
  **Ne jamais transmettre ce fichier à un ticket public**, car il peut contenir des titres personnalisés.
- `logs/support-summary.json` et `logs/events.jsonl` : informations de diagnostic
  limitées à des codes d'événements, des compteurs et des dates UTC, sans paquet GSI.
  Ces deux fichiers peuvent être joints à un ticket après vérification manuelle.
- Ne pas partager `.env`, des fichiers GSI, les journaux Docker bruts, des captures
  contenant le PIN ni le répertoire `data/`.
- Lors d'une mise à jour vers **un nouveau dossier**, conserver votre `.env` et recopier
  votre dossier `data/` si vous souhaitez retrouver vos nouveaux profils centralisés.
- En cas de création des dossiers manquants, Windows avec Docker Desktop les montera
  automatiquement. Sur Linux, vérifier les droits en écriture pour l'utilisateur 10001.
