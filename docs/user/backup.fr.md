# Export, sauvegarde et récupération

[English](backup.md) · [Guides utilisateur](README.fr.md)

## Un export de profil n’est pas une sauvegarde complète

Le Studio exporte le profil sélectionné **publié** au format `ccs-dashboard-export` v1 : nom et configuration complète, dont thème, widgets, variantes et géométrie. Sont exclus génération/contexte, révisions serveur, reçus, tombstones, authentification, métadonnées de brouillon et partie. Les titres personnalisés peuvent rester personnels : vérifiez avant partage. Un brouillon non appliqué n’est pas inclus.

L’import exige un export cible valide (70 000 octets encodés maximum ; les autres limites JSON/profil s’appliquent aussi). Les formats inconnus/futurs/malformés sont refusés. Les anciens `cs2-companion-layout` sont reconnus mais incompatibles, sans conversion. Dans le Studio : Importer, examiner le contenu/la prévisualisation, puis créer explicitement un brouillon ou remplacer le brouillon courant. Remplacer un brouillon ne remplace pas le profil serveur publié. Enregistrer et appliquer reste une action distincte. Conservez le travail existant avant remplacement et examinez tout conflit de révision.

## Sauvegarde privée complète

**Arrêtez les écrivains avant de copier le stockage actif.** Fermez les onglets d’édition après conservation du brouillon, lancez `docker compose stop cs2-companion-studio` depuis la racine installée, puis vérifiez `docker compose ps --all`. Une copie pendant l’écriture n’est pas une sauvegarde cohérente garantie.

Copiez `.env`, tout `data/` (dont `.bak`, bundles et marqueurs), `.installer-state/` et les configurations GSI générées nécessaires dans un emplacement privé distinct de l’installation et des ressources web. Conservez aussi la révision applicative/source/image compatible. Ne publiez rien. Cette copie est une opération de l’opérateur, pas une fonction automatique de sauvegarde complète CCS. Vérifiez tailles et SHA-256 (`Get-FileHash -Algorithm SHA256 -LiteralPath <file>` avec un vrai chemin), relisez les copies et conservez les originaux. Une empreinte détecte les octets modifiés, sans protéger contre un attaquant pouvant modifier le bundle. Les brouillons IndexedDB sont séparés et absents de cette sauvegarde serveur.

Une mise à jour cible compatible conserve génération/révisions. Ne modifiez pas storeId à la main et ne rejouez pas d’anciennes opérations après retour arrière. `profiles.json.bak` est le précédent document accepté rotatif, pas une archive indépendante. La restauration cible volontaire renouvelle la génération et efface les anciens reçus.

## Récupération hors ligne

Suivez la [référence opérateur (anglais)](../development/production-activation.md) et le [guide des commandes hors ligne (anglais)](../guides/profile-recovery.md). Identifiez les vrais chemins et la version compatible conservée avant remplacement. Gardez le service arrêté, inspectez, sauvegardez puis confirmez explicitement. Ne supprimez jamais un marqueur `.pending` ou `.attempted` pour contourner une erreur.

- Document cible endommagé avec sauvegarde cible valide : `--restore-target --service-stopped` préserve l’état en échec, valide la sauvegarde et installe une nouvelle génération. Les publications plus récentes peuvent manquer.
- Stockage historique : le démarrage courant le refuse sans le modifier. Préparation/activation explicites et vérifiées réinitialisent vers un Dashboard cible vide ; **aucune migration** des noms, dispositions ou personnalisations n’est réalisée. Conservez les octets originaux, le `.bak` historique et l’application/image historique compatible avant d’approuver.
- Revenir aux octets historiques exige cette application historique archivée ; le runtime cible actuel ne peut pas les servir.

Les outils agissent sur les profils/bundles, pas sur le PIN ou le token GSI. Conservez séparément `.env` et les sauvegardes d’installation/GSI. Une sauvegarde invalide ou une source modifiée impose l’arrêt, jamais l’effacement de données. Les brouillons locaux inconnus/corrompus ne sont ni adoptés ni supprimés silencieusement. La déconnexion volontaire suit sa politique distincte d’effacement après avertissement.
