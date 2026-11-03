# Réseau local de confiance

[English](network.md) · [Guides utilisateur](README.fr.md)

L’accès local utilise `http://localhost:8080` sur le PC CCS. Sur un autre PC, une tablette ou un téléphone, localhost désigne cet appareil, pas le serveur CCS. Le LAN est facultatif et nécessite une configuration volontaire sur un réseau privé fiable. **HTTP et WebSocket ne sont pas chiffrés ; le PIN ne chiffre pas le trafic. N’exposez jamais CCS directement sur Internet et ne redirigez pas son port sur un routeur.**

Lors d’une nouvelle installation guidée, lisez les deux confirmations LAN. Pour une installation existante, depuis sa racine avec Docker Desktop démarré :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\install.ps1 -Lan
```

Il s’agit d’une opération d’installation : elle peut vérifier/modifier la configuration GSI et recréer le service, pas simplement afficher le réseau. Préservez d’abord les fichiers privés. Après confirmation, `BIND_HOST=0.0.0.0` est appliqué ; aucune règle de pare-feu n’est ajoutée. Voir [installation](installation.fr.md).

1. Sur le PC serveur, lancez `ipconfig` dans PowerShell (lecture seule). Identifiez l’IPv4 de l’interface Ethernet/Wi-Fi privée active, pas celle d’un VPN ou adaptateur virtuel sans rapport. Ne publiez pas cette sortie.
2. Connectez l’autre appareil au même réseau fiable. Ouvrez `http://IP_LOCALE_DU_PC:8080`, en remplaçant le libellé et en utilisant le port réellement configuré.
3. Saisissez le PIN sur cet appareil. Ses brouillons appartiennent à son navigateur/origine et ne sont pas recopiés depuis localhost. Les profils publiés sont partagés ; les sélections d’onglets restent indépendantes.
4. En cas d’échec, vérifiez d’abord la santé du serveur localement, puis le profil de pare-feu Windows et une règle entrante volontairement limitée au port/sous-réseau privé. Docker Desktop/WSL2, l’isolation Wi-Fi invité, les VPN et politiques de point d’accès peuvent bloquer l’accès. Ne désactivez pas le pare-feu comme solution générale. Aucune compatibilité universelle entre appareils n’est promise.

Pour revenir à l’écoute locale, utilisez `-LocalOnly` à la place de `-Lan`. Les options sont exclusives. Ce réglage change l’écoute et peut recréer le service ; les credentials existants sont réutilisés. Ne modifiez jamais les règles publiques du routeur pour rendre CCS accessible. Voir [sécurité (anglais)](../../SECURITY.md) et [maintenance](maintenance.fr.md).
