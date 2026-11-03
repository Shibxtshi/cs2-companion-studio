# Customization Studio

[Français](studio.fr.md) · [User guides](README.md)

## Edit a profile

Connect with the PIN, then open Customization Studio. Desktop shows the library (left), canvas (center) and inspector (right). On tablet/phone switch between library, canvas and properties rather than using three tiny columns. The canvas may scroll horizontally as a desktop reference; narrow-screen viewing does not rewrite saved coordinates.

Select a profile in this tab. Use the profile actions to create or duplicate one, then enter its name. New profiles are local until explicitly published. Rename in profile properties. Deletion of a published profile requires confirmation and cannot remove the last profile; it does not silently erase recoverable local drafts. Limits: 12 published profiles and 60 widgets per profile, subject also to encoded-size limits.

Search/filter the library and add a widget. Multiple instances are allowed with distinct IDs. Select a card to edit its title, accent, background, opacity and surface in the inspector. Duplicate or remove the selected widget using the corresponding actions; removal asks for confirmation.

## Three independent size controls

| Control | Location and effect |
|---|---|
| Dashboard density: Normal / Compact | Profile appearance; global padding/density, not widget content or grid dimensions |
| Widget presentation: Standard / Compact / Minimal | Selected widget inspector; detailed, denser or essential content, retaining necessary warnings/details |
| X/Y, width and height | Selected widget geometry; integer saved grid cells, not pixels |

Solid, Glass and Outline describe the **surface**, not presentation. Empty automatic colors follow the theme; custom values override it. Arbitrary color/opacity choices can reduce contrast. Theme, density, navigation and fullscreen settings are edited as profile draft properties. See [themes](themes.md).

Desktop dragging/resizing snaps to whole cells and does not push neighbours. An occupied destination is marked invalid and rejected on release; Escape cancels. Each completed gesture is one undo operation. Existing overlaps remain correctable. Use numeric geometry fields and directional/keyboard controls as precise alternatives, particularly on touch screens. Display minima can enlarge the visible card without changing its saved size.

Undo/Redo applies to draft edits. History is session-only, bounded to 50 snapshots / 2 MiB of serialized content; it does not survive reopening. A new edit after Undo clears Redo. Preview opens a same-origin window showing the current draft with transient game/synthetic data, not a publication. Allow that popup if your browser blocks it.

## Local saving and exit

The local status distinguishes saving, saved and error. Wait for transaction completion before assuming a draft is retained. Drafts are stored in IndexedDB in this browser and origin; they are not shared with another device or port/IP address. Reload/normal closure retains confirmed writes; browser clearing, eviction, quota failures or abrupt closure can lose unconfirmed work. Drafts are not encrypted and contain no PIN, GSI token or game packets.

Returning via navigation or logo offers the appropriate exit choices:

- **Save and apply** waits for local persistence, sends an explicit operation and waits for server confirmation.
- **Keep draft and leave** waits for local saving, leaves the published Dashboard unchanged and permits later resume.
- **Discard changes** confirms removal of the relevant local draft; it must not erase another tab’s newer work.
- **Continue editing** cancels leaving.

On reopening, review the offered draft before resuming. Incompatible, deleted-profile or stale drafts are not automatically rebased; where valid, use an explicitly named recovery copy. Voluntary logout warns and, when confirmed, erases drafts/intents in the current context. Cancelling logout keeps them; network loss does not erase them.

## Publish and resolve a conflict

Only **Save and apply** publishes edits. Success means the server accepted and atomically wrote the version, then acknowledged it. A timeout/lost connection may mean an uncertain result: retain the draft and use the offered reconciliation/retry, not a guessed success. A confirmed publication with failed local cleanup has a separate cleanup state.

Two devices can publish different profiles independently. Publishing the same profile from an old revision causes a conflict. Review local and server versions, then keep the draft, explicitly use the server version, or explicitly confirm replacing the reviewed remote revision with your complete local version. There is no automatic merge. A changed generation or deleted identity cannot be overwritten by retrying stale work.

Import/export actions are available in Studio. Export reads the selected **published** profile, so uncommitted edits are not included. Import validates a target file, lets you preview it, then create a local draft or explicitly replace the current draft. Selecting a file never publishes; Save and apply remains separate. See [backups](backup.md) for accepted formats and recovery.
