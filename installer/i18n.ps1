# Centralized, extensible installer translations. Default: English.
$script:Languages = [ordered]@{ EN = 'English'; FR = 'Français' }
$script:InstallLanguage = 'EN'
$script:Strings = @{
 EN = @{
  intro='CS2 Companion Studio - V1P-E setup'; disclaimer='Uses official CS2 GSI only; requires Windows and Docker Desktop.'
  stage1='[1/4] Checking Docker Desktop...'; stage2='[2/4] Finding CS2 in Steam libraries...'; stage3='[3/4] Preparing personal configuration and GSI...'; stage4='[4/4] Building and starting the dashboard...'
  detected='CS2 config folder:'; existing_env='Existing .env found: your credentials are preserved.'; new_env='Unique PIN and token generated for this installation.'
  lan_warning='WARNING: LAN mode exposes an unencrypted HTTP service. Allow it only on your trusted private network; never forward its port to the Internet.'
  confirm_lan='Enable LAN mode deliberately?'; lan_private='I confirm that this network is private and trusted.'
  mobile_intro='Would you like to connect from a phone on the same private Wi-Fi?'; enable_mobile='Enable access from a phone?'
  gsi_replace='A different GSI file already exists. Back it up and replace it?'; gsi_backup='Previous GSI file backed up.'
  gsi_ok='GSI configuration installed. Restart CS2 if the file changed.'; docker_ok='Dashboard is ready!'
  docker_wait='Server not yet confirmed. Check docker compose logs.'; page_pc='PC dashboard'; page_phone='Phone'; phone_note='Use your PC LAN address and the same Wi-Fi.'
  personal_pin='Personal PIN'; secrets='Never publish .env or a real GSI CFG on GitHub. Do not forward the HTTP port.'
  other_tools='Uninstall: DESINSTALLER_WINDOWS.cmd | Diagnostics: installer/status.ps1'
  failstage='FAILED AT STEP'; source='Source'; fail_note='Do not manually delete an existing configuration. See docs/INSTALLATION_WINDOWS.md.'
  elevation_reason='CS2 config folder is not writable with current permissions.'; elevation_question='Request Windows administrator permission (UAC) to finish installing GSI?'
  elevation_declined='Administrator permission was declined. No game files were modified.'
  elevation_failed='Elevated setup did not complete. Check the administrator console output.'
  elevation_ok='Launching elevated installer. Please respond to the Windows UAC prompt.'
  denied_admin='The CS2 folder is still not writable even as administrator. Check Windows permissions and the installation path.'
  write_check='Checking write access to the CS2 GSI folder...'; yes_prompt='[y/N]'; invalid_choice='Unrecognized answer: choosing No.'
  language='Select language / Choisir la langue'; default_lang='Press Enter for English (default).'; invalid_lang='Unknown language: using English.'
  uninstall='CS2 Companion Studio - Uninstall'; uninstall_q='Restore/remove the installer-managed GSI file?'; uninstall_unchanged='The existing GSI file was changed after setup and will be preserved.'
  uninstall_none='No managed GSI configuration found; nothing to remove.'; uninstall_old='Previous GSI file restored.'; uninstall_removed='Installer-created GSI file removed.'
  uninstall_keep='No GSI changes.'; uninstall_preserve='Your .env, GSI backups and browser layouts are kept.'
  uninstall_restart='Restart CS2 to reload GSI.'; noninteractive='Interactive authorization required. No changes were made.'
  bad_path='Invalid CS2 path:'; bad_access_path='Invalid or inaccessible CS2 path:'; not_found='CS2 was not found in accessible Steam libraries. Use -Cs2Path to specify its location.'
  no_docker='Docker was not found. Install and start Docker Desktop.'; docker_down='Docker Desktop cannot be reached. Open Docker Desktop, then run docker info.'; no_compose='Docker Compose v2 is unavailable. Check docker compose version.'
 }
 FR = @{
  intro='CS2 Companion Studio - installation V1P-E'; disclaimer='Utilise uniquement la GSI officielle CS2 ; nécessite Windows et Docker Desktop.'
  stage1='[1/4] Vérification de Docker Desktop...'; stage2='[2/4] Recherche de CS2 dans les bibliothèques Steam...'; stage3='[3/4] Préparation de la configuration personnelle et du GSI...'; stage4='[4/4] Construction et démarrage du dashboard...'
  detected='Dossier de configuration CS2 :'; existing_env='Fichier .env existant : identifiants conservés.'; new_env='PIN et token personnels générés pour cette installation.'
  lan_warning='ATTENTION : le mode LAN expose un service HTTP non chiffré. Utilise-le uniquement sur ton réseau privé ; aucune redirection du port sur Internet.'
  confirm_lan='Activer volontairement le mode LAN ?'; lan_private='Je confirme que ce réseau est privé et de confiance.'
  mobile_intro='Tu peux te connecter depuis un téléphone sur le même Wi-Fi privé.'; enable_mobile='Activer l''accès depuis un téléphone ?'
  gsi_replace='Un fichier GSI différent existe déjà. Le sauvegarder puis le remplacer ?'; gsi_backup='Sauvegarde du GSI précédent créée.'
  gsi_ok='Configuration GSI installée. Redémarre CS2 si le fichier a changé.'; docker_ok='Dashboard prêt !'
  docker_wait='Serveur non confirmé. Consulte docker compose logs.'; page_pc='Dashboard PC'; page_phone='Téléphone'; phone_note='Utilise l''adresse LAN du PC et le même Wi-Fi.'
  personal_pin='PIN personnel'; secrets='Ne publie jamais .env ni un vrai fichier GSI sur GitHub. Ne redirige pas le port HTTP.'
  other_tools='Désinstallation : DESINSTALLER_WINDOWS.cmd | Diagnostic : installer/status.ps1'
  failstage='ÉCHEC À L''ÉTAPE'; source='Source'; fail_note='Ne supprime aucun fichier existant manuellement. Voir docs/INSTALLATION_WINDOWS.md.'
  elevation_reason='Le dossier GSI de CS2 n''est pas accessible en écriture avec les permissions actuelles.'; elevation_question='Demander les droits administrateur Windows (UAC) pour installer le GSI ?'
  elevation_declined='Demande de droits administrateur refusée. Aucun fichier de jeu modifié.'
  elevation_failed='L''installation avec élévation n''a pas abouti. Consulte la console administrateur.'
  elevation_ok='Lancement de l''installateur élevé. Réponds à la demande UAC Windows.'
  denied_admin='Le dossier CS2 reste inaccessible en écriture même en administrateur. Vérifie les droits Windows et le chemin.'
  write_check='Vérification des droits d''écriture dans le dossier GSI...'; yes_prompt='[o/N]'; invalid_choice='Réponse inconnue : Non choisi.'
  language='Select language / Choisir la langue'; default_lang='Entrée = anglais par défaut.'; invalid_lang='Langue inconnue : anglais utilisé.'
  uninstall='CS2 Companion Studio - Désinstallation'; uninstall_q='Restaurer/supprimer le fichier GSI géré par l''installateur ?'; uninstall_unchanged='Le fichier GSI a été modifié depuis l''installation et sera conservé.'
  uninstall_none='Aucun fichier GSI géré par l''installateur. Rien à supprimer.'; uninstall_old='Ancien fichier GSI restauré.'; uninstall_removed='Fichier GSI installé supprimé.'
  uninstall_keep='Aucune modification GSI.'; uninstall_preserve='Le .env, les sauvegardes GSI et les profils du navigateur sont conservés.'
  uninstall_restart='Redémarre CS2 pour recharger le GSI.'; noninteractive='Confirmation interactive nécessaire. Aucune modification.'
  bad_path='Chemin CS2 invalide :'; bad_access_path='Chemin CS2 invalide ou inaccessible :'; not_found='CS2 introuvable dans les bibliothèques Steam accessibles. Utilise -Cs2Path pour donner le chemin.'
  no_docker='Docker introuvable. Installe et démarre Docker Desktop.'; docker_down='Docker Desktop ne répond pas. Ouvre Docker Desktop, puis vérifie docker info.'; no_compose='Docker Compose v2 est indisponible. Vérifie docker compose version.'
 }
}
function Set-InstallLanguage([string] $Code) {
    if ([string]::IsNullOrWhiteSpace($Code)) { $script:InstallLanguage='EN'; return }
    $normalized = $Code.Trim().ToUpperInvariant()
    if (-not $script:Languages.Contains($normalized)) { throw "Unsupported language: $Code (available: EN, FR)." }
    $script:InstallLanguage = $normalized
}
function T([string] $Key) {
    $item = $script:Strings[$script:InstallLanguage][$Key]
    if ($null -eq $item) { $item = $script:Strings.EN[$Key] }
    if ($null -eq $item) { return $Key }
    return [string]$item
}
function Select-InstallLanguage([bool] $NonInteractive, [string] $Requested = '') {
    if (-not [string]::IsNullOrWhiteSpace($Requested)) { Set-InstallLanguage $Requested; return }
    if ($NonInteractive) { Set-InstallLanguage 'EN'; return }
    Write-Host "`nSelect language / Choisir la langue :" -ForegroundColor Cyan
    $count = 0
    foreach ($entry in $script:Languages.GetEnumerator()) {
        $count++
        Write-Host ('  ' + $count + ') ' + $entry.Key + ' — ' + $entry.Value + $(if ($entry.Key -eq 'EN') { ' [default]' } else { '' }))
    }
    $choice = (Read-Host 'Language / Langue [EN]').Trim().ToUpperInvariant()
    if ($choice -eq '') { Set-InstallLanguage 'EN'; return }
    $codes = @($script:Languages.Keys)
    $index = 0
    if ([int]::TryParse($choice,[ref]$index) -and $index -ge 1 -and $index -le $codes.Count) {
        Set-InstallLanguage $codes[$index-1]
    } elseif ($script:Languages.Contains($choice)) {
        Set-InstallLanguage $choice
    } else {
        Write-Host (T 'invalid_lang') -ForegroundColor Yellow
        Set-InstallLanguage 'EN'
    }
}
