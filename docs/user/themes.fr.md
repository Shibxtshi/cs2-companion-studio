# Les dix thèmes

[English](themes.md) · [Guides utilisateur](README.fr.md)

| ID | Nom | Palette |
|---|---|---|
| `tactical-blue` | Tactical Blue | Graphite et bleu ; défaut |
| `competitive-red` | Competitive Red | Graphite neutre, rouge vif |
| `performance-green` | Performance Green | Surfaces sombres, vert |
| `creator-purple` | Creator Purple | Surfaces sombres, violet |
| `midnight` | Midnight | Noir profond aux nuances bleutées |
| `arctic-white` | Arctic White | Surfaces claires et texte foncé |
| `neon-pink` | Neon Pink | Surfaces sombres, rose affirmé |
| `crimson` | Crimson | Surfaces bordeaux, rouge rosé |
| `solar-orange` | Solar Orange | Surfaces sombres, orange chaud |
| `monochrome` | Monochrome | Noir/blanc/gris neutres |

Dans le Studio, ouvrez les propriétés du profil, choisissez le thème et vérifiez la prévisualisation. Annuler/Rétablir peut restaurer le choix précédent. Seul **Enregistrer et appliquer** publie le thème de ce profil. Rechargement/reconnexion réapplique le thème publié ; les autres profils ne changent pas. Un sélecteur temporaire proposé dans les paramètres agit sur cet affichage seulement, sans publication.

Arctic White est un vrai thème clair : panneaux, texte, champs, menus natifs et messages utilisent les couleurs claires et `color-scheme: light`. Les neuf autres utilisent le mode sombre. Crimson possède des surfaces bordeaux distinctes du rouge vif sur graphite de Competitive Red. Midnight garde des nuances froides ; Monochrome reste neutre, mais les états critiques conservent texte/couleurs fonctionnels.

Les accents/fonds/opacités individuels des widgets priment sur les valeurs automatiques. Le thème ne corrige pas un choix personnalisé illisible ; vérifiez surtout les fonds transparents sur Arctic White. Surface Solid/Glass/Outline, présentation Standard/Compact/Minimal et densité globale restent indépendantes. Les mesures de contraste de composants sélectionnés ne constituent pas une certification WCAG globale. Voir [design technique (anglais)](../development/design-system.md).
