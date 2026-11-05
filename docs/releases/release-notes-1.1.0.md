# CS2 Companion Studio v1.1.0

## English

CCS now supports seven interface languages: English, French, Russian, Polish, Ukrainian, Czech and Romanian. The five new translations also cover the Windows installer and offline maintenance tools.

- Complete shared catalogs with 684 message keys and language-specific item-count plurals.
- Language switching without reloading, including PIN errors, Studio dialogs and the grid caption.
- Preserved personal titles, profile names and game data: these are not translated.
- The existing 29 widget types, Standard/Compact/Minimal presentations and ten themes remain available.
- No changes to profile/export/draft formats, explicit publication, credentials, GSI or network configuration.

### Installation and distribution

Download `CS2-Companion-Studio-v1.1.0.zip`, verify its SHA-256 against the attached `.sha256` file, and extract it completely before running `INSTALLER_WINDOWS.cmd`. Docker Desktop with Compose v2 and a Steam CS2 installation are required for the guided Windows setup. See the [installation guide](../user/installation.md).

The official asset is a source ZIP with the Windows installer, Dockerfile, Compose, documentation and license notices. No prebuilt Docker image is published. Preserve existing `.env`, `data/`, installation/GSI backups and recovery files; this release does not authorize a reset or promise migration of incompatible historical storage.

### Known limitations

The additional translations were prepared with machine translation and AI-assisted terminology review; native-speaker review has not been completed. Some phrasing may need refinement. Unsupported Latin/Cyrillic glyphs use local system-font fallback. Product and theme names remain unchanged.

Local targeted validation covers catalogs, Python/JavaScript, synthetic Windows installer operations and Chromium production journeys. Firefox/WebKit and hosted CI results must be assessed separately; do not infer them from local Chromium success. No new real CS2, UAC or physical LAN tests are claimed for this release.

CCS remains intended for localhost or a trusted LAN: HTTP/WebSocket traffic is not encrypted. Do not expose it directly to the Internet. The estimated bomb timer is disabled by default. No competitive-platform approval or independent security certification is claimed.

The [Community No-Resale License v1.0](../../LICENSE) remains unchanged: CCS is source-available, not OSI-approved open source. Third-party licenses remain applicable. The [French license translation](../legal/LICENSE.fr.md) is informative. Substantial ChatGPT/Codex assistance is disclosed in [AI_DISCLOSURE.md](../../AI_DISCLOSURE.md). CCS is not affiliated with or endorsed by Valve, Counter-Strike 2, FACEIT or OpenAI.

## Français

CCS propose désormais sept langues : anglais, français, russe, polonais, ukrainien, tchèque et roumain. Les cinq nouvelles traductions couvrent aussi l’installateur Windows et les outils de maintenance hors ligne.

- Catalogues partagés complets : 684 clés, avec pluriels adaptés aux compteurs d’objets.
- Changement de langue à chaud, y compris les erreurs de PIN, les dialogues du Studio et la légende de la grille.
- Titres personnels, noms de profils et données de jeu préservés, sans traduction automatique.
- Les 29 widgets, leurs trois présentations et les dix thèmes restent disponibles.
- Aucun changement des formats de profils/export/brouillons, de la publication explicite, des credentials, du GSI ou du réseau.

Téléchargez le ZIP source et son fichier SHA-256, vérifiez l’empreinte, puis extrayez l’archive avant de lancer l’installateur. Consultez le [guide Windows](../user/installation.fr.md). Conservez vos fichiers privés et sauvegardes ; aucune réinitialisation ni migration automatique n’est effectuée.

Les traductions supplémentaires ont été préparées automatiquement puis révisées avec assistance IA. Elles n’ont pas encore été relues par des locuteurs natifs. Le cyrillique et certains caractères latins utilisent les polices système lorsque nécessaire. Les contrôles locaux ne constituent ni une validation de tous les navigateurs, ni de nouveaux essais CS2 réels, ni une certification de sécurité ou juridique.

La licence Community No-Resale v1.0 reste inchangée. Aucun changement d’affiliation, d’approbation compétitive ou de limites réseau : utilisation locale ou LAN de confiance, HTTP/WS non chiffré, chronomètre estimé de bombe désactivé par défaut. Aucune image Docker préconstruite n’est distribuée.
