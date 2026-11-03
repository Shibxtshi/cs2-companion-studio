# Première utilisation

[English](first-use.md) · [Guides utilisateur](README.fr.md)

Terminez d’abord l’[installation](installation.fr.md). Démarrez Docker Desktop et CCS. Si l’image est déjà construite, exécutez `docker compose up -d --no-build --pull never` depuis la racine installée : le service configuré démarre et son conteneur peut être créé. Arrêtez-vous si l’image manque ou si le stockage est incompatible. N’effacez aucun fichier pour forcer le démarrage.

1. Ouvrez `http://localhost:8080` (adaptez le port). Choisissez EN ou FR.
2. Essayez **Démonstration**. Ses valeurs synthétiques ne vérifient pas le GSI et ne révèlent pas les profils privés. Quittez-la pour vous connecter normalement.
3. Saisissez le PIN privé sur l’écran de connexion, jamais dans une URL ou un rapport.
4. Ouvrez Dashboard et choisissez le profil publié. Une installation neuve peut ne contenir aucun widget ; c’est normal.
5. Ouvrez **Customization Studio**. Recherchez Santé dans la bibliothèque et ajoutez-le.
6. Sélectionnez la carte. Dans les propriétés, choisissez sa présentation, X/Y, largeur et hauteur ; sur ordinateur, déplacement et redimensionnement s’alignent aussi sur les cellules. Utilisez les champs numériques sur écran étroit.
7. Attendez le statut du brouillon local. Il est enregistré dans ce navigateur uniquement, pas sur le serveur.
8. Choisissez **Enregistrer et appliquer**. Attendez la confirmation ; un délai réseau dépassé n’est pas une réussite.
9. Revenez au Dashboard par la navigation ou le logo CCS. Il lit la disposition publiée ; rechargez pour vérifier la persistance.
10. Pour les données réelles, redémarrez CS2 après sa configuration GSI et lancez un entraînement. Serveur connecté, GSI actif et partie active sont des états distincts. Les valeurs absentes restent indisponibles.

L’aide propose un démarrage rapide facultatif, fermable et réouvrable. Settings/Paramètres regroupe aperçus d’apparence, connexion et diagnostics. Consultez le [Studio](studio.fr.md) pour les sorties/conflits et la [maintenance](maintenance.fr.md) en cas de problème.
