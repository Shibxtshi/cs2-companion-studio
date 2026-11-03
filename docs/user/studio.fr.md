# Customization Studio

[English](studio.md) · [Guides utilisateur](README.fr.md)

## Modifier un profil

Connectez-vous avec le PIN puis ouvrez Customization Studio. Sur ordinateur : bibliothèque à gauche, canevas au centre, inspecteur à droite. Sur tablette/téléphone, alternez bibliothèque, canevas et propriétés. Le canevas peut défiler horizontalement comme référence desktop ; consulter sur mobile ne réécrit pas les coordonnées.

Choisissez le profil dans cet onglet. Les actions du profil permettent de créer ou dupliquer puis nommer un profil. Un nouveau profil reste local jusqu’à publication explicite. Renommez-le dans les propriétés du profil. Supprimer un profil publié exige confirmation et ne peut supprimer le dernier ; les brouillons récupérables ne sont pas effacés silencieusement. Limites : 12 profils publiés, 60 widgets par profil, avec aussi des limites de taille encodée.

Recherchez/filtrez la bibliothèque et ajoutez un widget. Plusieurs instances sont possibles avec des identifiants distincts. Sélectionnez une carte pour modifier titre, accent, fond, opacité et surface dans l’inspecteur. Dupliquez ou retirez la sélection par les actions correspondantes ; le retrait demande confirmation.

## Trois réglages de taille indépendants

| Réglage | Emplacement et effet |
|---|---|
| Densité du Dashboard : Normale / Compacte | Apparence du profil ; espacement global, pas le contenu ni les dimensions de grille |
| Présentation du widget : Standard / Compact / Minimal | Inspecteur de la carte ; contenu complet, dense ou essentiel, avec avertissements/détails nécessaires |
| X/Y, largeur et hauteur | Géométrie de la carte ; cellules entières enregistrées, pas des pixels |

Solid, Glass et Outline décrivent la **surface**, pas la présentation. Les couleurs automatiques vides suivent le thème ; les valeurs personnalisées priment. Des couleurs/opacités arbitraires peuvent réduire le contraste. Thème, densité, navigation et plein écran se modifient dans les propriétés du brouillon de profil. Voir [thèmes](themes.fr.md).

Déplacer/redimensionner sur ordinateur s’aligne à la cellule sans pousser les voisins. Une destination occupée est signalée invalide et refusée au relâchement ; Échap annule. Chaque geste terminé constitue une opération d’historique. Les chevauchements existants restent corrigeables. Les champs numériques et contrôles directionnels/clavier offrent une alternative précise, notamment tactile. Les minima d’affichage peuvent agrandir visuellement une carte sans changer sa taille enregistrée.

Annuler/Rétablir agit sur le brouillon. L’historique est limité à la session, 50 instantanés / 2 Mio de contenu sérialisé ; il ne survit pas à la réouverture. Une nouvelle modification après Annuler efface Rétablir. La prévisualisation ouvre une fenêtre de même origine avec le brouillon et des données transitoires réelles/synthétiques, sans publication. Autorisez cette fenêtre si le navigateur la bloque.

## Enregistrement local et sortie

Le statut distingue enregistrement en cours, conservé et erreur. Attendez la fin de transaction avant de considérer le brouillon sauvegardé. IndexedDB le conserve dans ce navigateur et cette origine ; il n’est pas partagé avec un autre appareil, port ou nom/IP d’accès. Rechargement/fermeture normale conserve les transactions terminées ; effacement, éviction, quota ou fermeture brutale peuvent perdre le travail non confirmé. Les brouillons ne sont pas chiffrés et ne contiennent ni PIN, ni token GSI, ni paquets de partie.

Revenir par la navigation ou le logo propose les choix adaptés :

- **Enregistrer et appliquer** attend la persistance locale, envoie l’opération explicite et attend la confirmation serveur.
- **Conserver le brouillon et quitter** attend l’enregistrement local, laisse le Dashboard publié inchangé et permet la reprise.
- **Abandonner les modifications** confirme la suppression du brouillon concerné, sans effacer le travail plus récent d’un autre onglet.
- **Continuer l’édition** annule la sortie.

À la réouverture, examinez la proposition de reprise. Un brouillon incompatible, lié à un profil supprimé ou à une ancienne révision n’est pas automatiquement recalé ; une copie récupérée explicitement nommée peut être proposée si valide. La déconnexion volontaire prévient puis efface, après confirmation, les brouillons/intentions du contexte courant. Annuler conserve le travail ; une panne réseau ne l’efface pas.

## Publier et résoudre un conflit

Seul **Enregistrer et appliquer** publie les modifications. La réussite correspond à une validation, une écriture atomique et un acquittement serveur. Un délai dépassé ou une perte réseau peut laisser un résultat incertain : conservez le brouillon et utilisez la réconciliation/nouvelle tentative proposée. Une publication confirmée avec nettoyage local échoué possède un statut distinct.

Deux appareils peuvent publier des profils différents indépendamment. Publier le même profil depuis une ancienne révision provoque un conflit. Examinez les versions puis conservez le brouillon, utilisez explicitement la version serveur, ou confirmez le remplacement complet de la révision distante examinée par votre version locale. Aucune fusion automatique. Une génération différente ou une identité supprimée ne peut être écrasée par une relance obsolète.

Les actions d’import/export sont dans le Studio. L’export lit le profil sélectionné **publié**, sans les modifications non appliquées. L’import valide un fichier cible, permet sa prévisualisation puis la création d’un brouillon ou le remplacement explicitement confirmé du brouillon courant. Choisir un fichier ne publie rien ; Enregistrer et appliquer reste distinct. Voir [sauvegardes](backup.fr.md) pour les formats et la récupération.
