# CS2 Companion Studio v1.0.0 — présentation en français

**Projet personnel indépendant, à code source accessible et modifiable.** Le projet a été développé avec l'aide importante de **ChatGPT d'OpenAI** pour le code, l'interface, les tests, le dépannage et la documentation. Cette aide n'est pas dissimulée : voir la [déclaration détaillée (anglais)](../AI_DISCLOSURE.md).

**Aucune affiliation ni approbation** de Valve, Counter-Strike 2, FACEIT ou OpenAI. Les règles des plateformes compétitives restent applicables ; l'usage de GSI et l'absence d'injection ne garantissent pas qu'un outil est autorisé en compétition.

## Fonctionnalités

- Dashboard CS2 via Game State Integration (GSI), affichable dans un navigateur sur PC, tablette ou téléphone.
- **29 widgets**, personnalisation des cartes, profils enregistrés dans `data/` et synchronisés entre appareils authentifiés.
- Démo avec données fictives, distincte des profils privés.
- Installateur Windows, interface en anglais (défaut) et français.
- Score, arme, munitions, économie estimée et statistiques. Les champs manquants ne sont pas inventés.
- Minuteur de bombe **estimatif, désactivé par défaut**, réservé aux contextes où son usage est permis ; ne pas l'utiliser sur FACEIT sans autorisation explicite.

## Installation simplifiée

1. Installer et démarrer **Docker Desktop** ; avoir CS2 installé via Steam.
2. Décompresser le projet depuis une source de confiance, puis lancer `INSTALLER_WINDOWS.cmd`.
3. Choisir FR ou EN, confirmer le chemin de CS2, et suivre les questions `O/N` ou `Y/N`.
4. Redémarrer CS2 si sa configuration GSI vient d'être installée ou modifiée.
5. Ouvrir `http://localhost:8080`, entrer le PIN affiché par l'installateur et commencer un entraînement pour tester les données.
6. L'accès sur téléphone doit être activé explicitement, **uniquement sur un réseau local de confiance**.

**Important :** garder `.env` **et** `data/` lors des mises à jour. Ne jamais publier le PIN, le token, le `.cfg` généré ou `data/profiles.json`.

## Sécurité, support et licence

Le réseau local utilise HTTP/WebSocket **sans chiffrement**. Ne pas ouvrir le port 8080 sur Internet. Les diagnostics conçus pour le support doivent tout de même être vérifiés avant partage.

Les issues GitHub serviront aux bugs et suggestions ; les vulnérabilités doivent être signalées en privé selon [SECURITY.md](../SECURITY.md). Une **licence communautaire interdisant la revente** est en préparation. Elle autoriserait l'utilisation professionnelle, les streams et coachings rémunérés, les modifications privées et la redistribution gratuite (avec crédits et accès au code source des forks distribués), mais pas la vente du logiciel ou d'une version dérivée. Le cadre des prestations d'installation, de support et d'hébergement payants reste à préciser. Le texte de `LICENSE` est un **brouillon sans effet**, à faire relire juridiquement et à approuver avant publication (copyright déjà attribué à Shibxtshi). Ce modèle n'est pas « open source » au sens de l'OSI.

Le projet n'a pas fait l'objet d'un audit de sécurité indépendant ni d'une validation FACEIT. Lire le [README anglais](../README.md), le [guide de contribution](../CONTRIBUTING.md) et la [checklist de publication](releases/checklist.md).

## Recette finale

La [recette P10-A/P10-B](guides/final-acceptance.fr.md) distingue les essais isolés, les contrôles manuels CS2 et l’autorisation séparée nécessaire avant toute activation personnelle.
