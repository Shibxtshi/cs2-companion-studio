# Dashboard

[English](dashboard.md) · [Guides utilisateur](README.fr.md)

Le Dashboard sert à consulter. Il lit le profil **publié**, pas le brouillon du Studio. Choisissez un profil dans le sélecteur : chaque onglet garde sa sélection, alors que les configurations publiées sont partagées entre appareils authentifiés. Publier un autre profil ne force pas sa sélection dans votre onglet. Si le profil sélectionné est supprimé, l’onglet choisit un profil restant ; un brouillon ouvert est conservé pour récupération explicite.

Le Dashboard initial peut être vide. Ajoutez des widgets dans le [Studio](studio.fr.md), puis publiez explicitement. Le thème, la navigation et le plein écran appartiennent au profil. Les contrôles d’apparence proposés dans Settings/Paramètres sont des aperçus temporaires ; utilisez le Studio pour les enregistrer durablement. Les couleurs individuelles des widgets priment sur le thème.

La navigation complète affiche les libellés ; la compacte conserve les icônes essentielles ; la masquée maximise la surface des widgets. Retrouvez les contrôles avec le bouton de bord, le bouton flottant facultatif ou Alt+M hors des champs de saisie si le navigateur le permet. Le bouton de bord reste disponible même sans bouton flottant. Le logo CCS revient au Dashboard sans rechargement ; une sortie du Studio respecte ses choix de conservation.

Le plein écran utilise l’API du navigateur avec un repli immersif. Le profil choisit widgets seuls ou widgets avec statut de connexion. Échap ou les contrôles de sortie/récupération permettent d’en sortir sans réécrire la disposition.

Les positions sont enregistrées en unités de grille. Quand la largeur disponible diminue, CCS calcule une réorganisation déterministe et restitue la projection desktop quand la place revient. Les collisions et minima de contenu peuvent déplacer/agrandir visuellement une carte sans enregistrer de nouvelles coordonnées. Les listes longues et détails restent accessibles au clavier et au toucher.

## Comprendre la connexion

| État | Signification |
|---|---|
| Serveur disponible | Réponse HTTP de santé ; aucune preuve d’authentification ou de CS2 |
| WebSocket connecté | Connexion authentifiée à CCS |
| GSI actif, en attente de partie | Paquets CS2 récents, données de partie insuffisantes |
| Partie active | Données de partie valides et récentes |
| Hors ligne/périmé | Données actuelles nécessaires absentes ; ne pas traiter les anciennes comme actives |
| Démonstration | Valeurs synthétiques, aucune connexion réelle prouvée |

Zéro est une valeur connue ; un tiret ou un libellé indisponible n’est pas zéro. Les prévisions et temps de bombe conservent leurs avertissements d’estimation. Consultez les diagnostics dans les paramètres pour les états serveur/WebSocket/GSI et l’âge des paquets disponible. L’aide et le démarrage rapide restent réouvrables. Voir [widgets](widgets.fr.md) et [dépannage](maintenance.fr.md).
