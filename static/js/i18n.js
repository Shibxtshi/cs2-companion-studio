/* CS2 Companion Studio internationalization. UI source strings are French.
 * Add future languages under translations[CODE] and add a select option.
 * No dynamic HTML is generated from external input by this translator. */
(()=>{'use strict';
const STORAGE='cs2-companion-language';
const translations={
 EN:{
 'grenades reçues':'grenades received',
 'Données périmées · hors ligne':'Stale data · offline',
 'Arme active':'Active weapon',
 'Scénarios de démo':'Demo scenarios',
 'Plus de détails':'More details',
 'objets reçus':'items received',
 'Dernière manche reçue':'Last received round',
 'Données simulées':'Simulated data',
 'Hors ligne — données indisponibles':'Offline — data unavailable',
 'Valeur indisponible':'Value unavailable',
 'Munitions':'Ammunition',
 "Ouvre Customization Studio pour ajouter, déplacer et redimensionner tes widgets avec l’éditeur actuel. La sauvegarde automatique et le partage des profils entre appareils restent actifs. Tu peux aussi exporter un JSON.":"Open Customization Studio to add, move and resize widgets with the current editor. Automatic saving and profile sharing across devices remain active. You can also export JSON.",
 'Thème d’aperçu':'Theme preview',
 'Non enregistré · cet onglet':'Not saved · this tab',
 'Renommer':'Rename',
 'Nouveau nom du dashboard :':'New dashboard name:',
 'Dashboard renommé':'Dashboard renamed',
 'Télécharger le diagnostic':'Download diagnostics',
 'Projet indépendant — non affilié':'Independent project — not affiliated',
 'Projet personnel réalisé avec une aide importante de ChatGPT (OpenAI) pour le code, l’interface, les tests et la documentation. Aucune affiliation avec OpenAI.':'Personal project developed with substantial help from ChatGPT (OpenAI) for code, UI, tests, and documentation. Not affiliated with OpenAI.',
 'CS2 Companion Studio est un projet indépendant, développé et partagé par une personne de la communauté. Il n’est ni créé, ni sponsorisé, ni approuvé par Valve, Counter-Strike 2 ou FACEIT. Les noms et marques appartiennent à leurs propriétaires respectifs. L’utilisation de certains modules en compétition peut être soumise aux règles des plateformes concernées.':'CS2 Companion Studio is an independent project developed and shared by a community member. It is not created, sponsored, endorsed or affiliated with Valve, Counter-Strike 2 or FACEIT. All names and trademarks belong to their respective owners. Some features may be subject to competitive platform rules.',
 'Profils sauvegardés dans cette instance · Connexion par PIN · Sans injection dans CS2':'Profiles stored on this instance · PIN-protected access · No CS2 injection',
 'Les profils sont sauvegardés dans cette instance Docker et partagés entre les appareils connectés. Tu peux aussi exporter un JSON.':'Profiles are saved on this Docker instance and shared across authenticated devices. You can also export JSON.',
 'Profils modifiés sur un autre appareil : actualisation.':'Profiles changed on another device: refreshing.',
 'Enregistrement impossible. Vérifie le stockage du serveur.':'Could not save profiles. Check server storage.',
 'Non connecté':'Disconnected','Connexion':'Sign in','Entre ton code PIN pour afficher les données du jeu.':'Enter your PIN to view live game data.',
 'Se connecter':'Connect','Voir la démo':'View demo','Démo':'Demo','Vue par défaut':'Default dashboard','Mon dashboard ✦':'My dashboard ✦',
 'Personnaliser':'Customize','✎ Personnaliser':'✎ Customize','✓ Terminer':'✓ Done','＋ Widget':'＋ Widget',
 'Profil':'Profile','Nouveau':'New','Dupliquer':'Duplicate','Supprimer':'Delete','Exporter':'Export','Importer':'Import','Réinitialiser':'Reset',
 'Bibliothèque de widgets':'Widget library','Rechercher un widget…':'Find a widget…','Rechercher':'Search','Fermer':'Close',
 'Ton dashboard est vide. Ouvre Customization Studio pour ajouter des widgets.':'Your dashboard is empty. Open Customization Studio to add widgets.',
 'Déconnexion':'Log out','Quitter la démo':'Exit demo','Profils enregistrés uniquement sur cet appareil · GSI officiel CS2 · Aucune injection dans le jeu':'Layouts stored on this device only · Official CS2 GSI · No game injection',
 'Partie':'Match','Armement':'Weapons','Économie':'Economy','Statistiques':'Statistics','Joueur':'Player','Bombe':'Bomb','Système':'System',
 'Carte':'Map','Manche':'Round','Score détaillé':'Detailed score','Phase du match':'Match phase','Historique des manches':'Round history',
 'Disponible selon les données envoyées par CS2':'Available when provided by CS2','Arme équipée':'Equipped weapon','Munitions':'Ammo',
 'Inventaire':'Inventory','Grenades possédées':'Carried grenades','Inventaire personnel uniquement':'Personal inventory only',
 'Valeur d’équipement':'Equipment value','Valeur rapportée par CS2':'Value reported by CS2','Équipement':'Gear',
 'Argent disponible':'Available money','Si défaite · estimation':'On loss · estimate','Argent actuel':'Current money','Disponible':'Available','Prochain round':'Next round',
 'Statistiques K / A / D':'K / A / D statistics','Éliminations':'Kills','Morts':'Deaths','Ratio K / D':'K/D ratio','Éliminations / morts':'Kills / deaths',
 'Étoiles MVP':'MVP stars','Score personnel':'Personal score','Points au scoreboard':'Scoreboard points',
 'Statistiques du round':'Round stats','Dégâts':'Damage','Santé':'Health','Armure':'Armor','Effets subis':'Effects',
 'Feu':'Fire','Intensité rapportée par CS2 · 0–255':'Intensity reported by CS2 · 0–255',
 'État de la bombe':'Bomb state','Chrono estimé':'Estimated timer','En attente':'Waiting','En attente d’une pose':'Waiting for plant',
 'Connexion GSI':'GSI connection','Journal de la partie':'Match events','Événements déduits des données GSI reçues':'Events inferred from GSI data',
 'Version du jeu':'Game version','Donnée GSI provider':'GSI provider data',
 'Titre':'Title','Largeur':'Width','Pleine':'Full','Couleur automatique':'Automatic color','Glisser pour déplacer':'Drag to move',
 'Monter le widget':'Move widget up','Descendre le widget':'Move widget down','Options du widget':'Widget settings','Supprimer le widget':'Remove widget',
 'Aucun widget trouvé':'No widgets found','Aucune donnée':'No data','Historique indisponible':'History unavailable',
 'Aucun événement enregistré':'No events recorded',
 'Mode démo':'Demo mode','Partie connectée':'Match connected','GSI actif · en attente de partie':'GSI active · waiting for match',
 'CS2 hors ligne':'CS2 offline','Données simulées':'Simulated data','En attente de données de partie CS2.':'Waiting for CS2 match data.',
 'Données en direct':'Live data','GSI actif · match en attente':'GSI active · waiting for match','Hors ligne':'Offline',
 'Bonus indisponible':'Bonus unavailable','Bonus fourni par GSI · hors exceptions':'Bonus provided by GSI · excluding exceptions',
 'Estimation à partir des manches · règles standard':'Estimated from rounds · standard rules',
 'Historique insuffisant · bonus inconnu':'Insufficient history · unknown bonus',
 'Casque —':'Helmet —','✓ Casque':'✓ Helmet','Sans casque':'No helmet','Kit —':'Kit —','✓ Kit':'✓ Kit','Sans kit':'No kit',
 'Équipe —':'Team —','Plantée':'Planted','Désamorcée':'Defused','Explosée':'Exploded','Au sol':'Dropped','Pose en cours':'Planting',
 'Désamorçage possible sans kit':'Defuse possible without kit','Kit nécessaire pour commencer':'Kit required to start',
 'Trop tard pour commencer':'Too late to start','Explosion estimée':'Estimated explosion',
 'Minuteur désactivé':'Timer disabled','Données interrompues':'Data interrupted','Heure de pose inconnue':'Plant time unknown',
 'Bombe désamorcée':'Bomb defused','Bombe explosée':'Bomb exploded',
 'Code PIN trop court.':'PIN is too short.','Connexion…':'Connecting…','Mise à jour requise':'Update required',
 'Code incorrect.':'Incorrect PIN.','PIN incorrect':'Incorrect PIN','Connecté':'Connected','Erreur réseau':'Network error',
 'Déconnecté':'Disconnected','Reconnexion…':'Reconnecting…','Impossible de se connecter au WebSocket.':'Could not connect to WebSocket.',
 'Maximum 12 profils.':'Maximum 12 profiles.','Maximum 60 widgets par profil.':'Maximum 60 widgets per profile.',
 'Stockage local indisponible : exporte ton profil.':'Local storage unavailable: export your layout.',
 'Sans nom':'Unnamed','Mon dashboard':'My dashboard','Mon setup':'My setup','Nom du nouveau profil :':'New profile name:',
 'Supprimer ce profil ?':'Delete this profile?','Remettre ce profil à sa disposition initiale ?':'Reset this layout to its defaults?',
 'Profil exporté':'Profile exported','Profil importé':'Profile imported','Fichier trop volumineux.':'File too large.',
 'Format inconnu':'Unknown format','Aucun widget trouvé':'No widgets found','Import impossible :':'Import failed:',
 'Ajouter':'Add','copie':'copy', 'ajouté':'added',
 'Historique insuffisant':'Insufficient history',
 'Bonus de défaite':'Loss bonus','Gagnant :':'Winner:','Armure :':'Armor:','Dernier paquet :':'Last update:',
 'En attente de données':'Waiting for data','Redémarre Docker avec la version 1.0.0.':'Restart Docker with version 1.0.0.',
 'Modèles':'Templates','Modèles de dashboard':'Dashboard templates','Compétitif compact':'Competitive compact',
 'Essentiel mobile':'Mobile essentials','Vue du match':'Match overview','Streaming / statistiques':'Streaming / statistics',
 'Page vide':'Blank canvas','Créer un profil':'Create profile','Profil créé':'Profile created',
 'Densité':'Density','Normale':'Normal','Compacte':'Compact','Toutes catégories':'All categories','Catégorie':'Category',
 'En mode édition : déplace les cartes, tire la poignée ⇲ pour ajuster leur largeur ou utilise les flèches du clavier. Les tailles sont adaptées à l’écran ; sur mobile les cartes occupent toute la largeur.':'Edit mode: move cards, drag ⇲ to resize or use keyboard arrow keys. Widths adapt to screen size; mobile cards are full width.',
 'Couleur de fond':'Background color','Fond':'Background','Fond automatique':'Automatic background','Style':'Style',
 'Plein':'Solid','Verre':'Glass','Contour':'Outline','Opacité du fond':'Background opacity',
 'Redimensionner le widget':'Resize widget','Glisser pour redimensionner · flèches gauche/droite au clavier':'Drag to resize · Left/Right arrow keys',
 'Redémarre Docker avec la version V1P-D.':'Restart Docker with V1P-D.',
 'Serveur indisponible :':'Server unavailable:', 'Élimination · 18 au total':'Kill · 18 total', 'Nouvelle manche · MIRAGE':'New round · MIRAGE',

 'Aller au contenu principal':'Skip to main content',
 'Aide':'Help',
 'Bienvenue dans CS2 Companion Studio':'Welcome to CS2 Companion Studio',
 'Code PIN':'PIN',
 'Première utilisation ?':'First time here?',
 'Démarre le serveur Companion avec Docker.':'Start Companion with Docker.',
 'Ajoute le fichier GSI à CS2 et redémarre le jeu.':'Add the GSI file to CS2 and restart the game.',
 'Connecte-toi ici ou explore sans CS2 avec la démo.':'Sign in here, or explore without CS2 in demo mode.',
 'Voir les conseils de connexion':'Connection tips',
 'État de la connexion':'Connection status',
 'Chargement des données…':'Loading data…',
 'Diagnostic':'Diagnostics',
 'Diagnostic de connexion':'Connection diagnostics',
 'Actualiser':'Refresh',
 'Serveur Companion':'Companion server',
 'Non vérifié':'Not checked',
 'Connexion en direct':'Live connection',
 'CS2 / GSI':'CS2 / GSI',
 'En attente de données':'Waiting for data',
 'En attente de données de partie':'Waiting for match data',
 'Si CS2 n\'est pas détecté : vérifie le fichier GSI dans le dossier cfg du jeu et redémarre CS2. Aucun match FACEIT n\'est nécessaire pour tester.':'If CS2 is not detected, check the GSI file in the game cfg folder and restart CS2. A FACEIT match is not needed for testing.',
 'Guide de démarrage':'Getting started',
 'Fermer l\'aide':'Close help',
 'Comment commencer':'How to start',
 'Lance Docker et l\'installation du Companion.':'Launch Docker and install Companion.',
 'Installe le fichier GSI dans CS2, puis redémarre le jeu.':'Install the GSI file in CS2, then restart the game.',
 'Sur le même Wi-Fi, ouvre l\'adresse de ton PC sur ton téléphone et saisis le PIN.':'On the same Wi-Fi, open your PC address on your phone and enter the PIN.',
 'Tu peux aussi choisir « Voir la démo » : aucun jeu ni PIN requis.':'You can also choose “View demo”: no game or PIN required.',
 'Personnaliser':'Customize',
 'Ouvre « Mon dashboard », puis « Personnaliser » pour ajouter, déplacer et redimensionner tes widgets. Les réglages restent sur cet appareil. Exporte un profil JSON pour le déplacer ailleurs.':'Open “My dashboard”, then “Customize” to add, move and resize widgets. Layouts stay on this device. Export a JSON profile to transfer it elsewhere.',
 'En cas de problème':'Troubleshooting',
 'Le PIN est refusé : vérifie celui de ton installation actuelle.':'If your PIN is rejected, check the PIN from your current installation.',
 'Pas de données : vérifie le fichier GSI et redémarre CS2.':'No data? Check the GSI file and restart CS2.',
 'Le téléphone ne voit rien : vérifie que les deux appareils sont sur le même réseau privé et que l\'accès LAN est autorisé.':'If your phone cannot connect, check that both devices use the same private network and LAN access is allowed.',
 'FACEIT et confidentialité':'FACEIT and privacy',
 'Le Companion lit les données officielles GSI. Cela ne garantit pas que tous les widgets soient autorisés par FACEIT. Le minuteur de bombe est une estimation et nécessite une autorisation avant usage compétitif. N\'ouvre pas ton port 8080 sur Internet.':'Companion reads official GSI data. This does not guarantee that all widgets are allowed by FACEIT. The bomb timer is an estimate and requires approval before competitive use. Do not expose port 8080 to the internet.',
 'J\'ai compris':'Got it',
 'En attente de CS2':'Waiting for CS2',
 'La connexion est établie, mais les données de partie ne sont pas encore disponibles.':'Connected, but match data is not yet available.',
 'Exemples simulés. Aucune donnée CS2 réelle n’est utilisée.':'Simulated examples. No live CS2 data is being used.',
 'Connexion en cours':'Connecting',
 'Connexion au serveur Companion…':'Connecting to Companion server…',
 'Connexion interrompue':'Connection interrupted',
 'Le dashboard tente de se reconnecter. Vérifie Docker et ton réseau.':'Trying to reconnect. Check Docker and your network.',
 'Connexion au serveur':'Server connection',
 'Entre ton PIN pour recevoir les données du jeu.':'Enter your PIN to receive live game data.',
 'CS2 connecté':'CS2 connected',
 'Les données de la partie sont reçues en direct.':'Live match data is being received.',
 'GSI actif, partie en attente':'GSI active, waiting for match',
 'CS2 communique avec le serveur. Lance une partie ou un entraînement pour afficher les données.':'CS2 is communicating with the server. Start a match or practice session to see data.',
 'Serveur disponible':'Server available',
 'Serveur inaccessible':'Server unreachable',
 'Mode démo (sans connexion)':'Demo mode (no connection)',
 'Authentifiée et active':'Authenticated and active',
 'Reconnexion en cours':'Reconnecting',
 'Connexion impossible':'Could not connect',
 'Non connectée':'Not connected',
 'Signal GSI reçu, partie en attente':'GSI signal received, waiting for match',
 'Aucune donnée récente de CS2':'No recent CS2 data',
 'Quitter le mode démo':'Exit demo mode',
 "Modifications non enregistrées. Choisis une action.":"Unsaved changes. Choose an action.",
 "Modifications non enregistrées.":"Unsaved changes.",
 "Enregistrement…":"Saving…",
 "Enregistrement impossible. Vérifie le stockage du serveur.":"Could not save. Check server storage.",
 "Modifications non enregistrées. Connexion interrompue.":"Unsaved changes. Connection interrupted.",
 "Modifications non enregistrées. Le serveur a une autre version.":"Unsaved changes. The server has another version.",
 "Enregistrer ma version":"Save my version",
 "Remplacer la version du serveur par mes modifications":"Replace the server version with my changes",
 "Charger la version du serveur":"Load the server version",
 "Abandonner mes modifications non enregistrées":"Discard my unsaved changes",
 "Des modifications ne sont pas enregistrées. Les abandonner ?":"Some changes are not saved. Discard them?",
 },FR:{}
};
const formatDynamic=(s,lang)=>{
 if(lang==='FR')return s;
 let value=s;
 const dictionary=translations[lang]||{};
 if(Object.prototype.hasOwnProperty.call(dictionary,value))return dictionary[value];
 const rules=[
 [/^Dégâts · ([0-9]+) HP$/,(_m,n)=>`Damage · ${n} HP`],
 [/^Soins · ([0-9]+) HP$/,(_m,n)=>`Healing · ${n} HP`],
 [/^Round ([0-9—]+) · (.*)$/,(_m,n,state)=>`Round ${n} · ${state}`],
 [/^Bonus de défaite \+(.*)$/,(_m,x)=>`Loss bonus +${x}`],
 [/^Gagnant : (.*)$/ ,(_m,x)=>`Winner: ${x}`],
 [/^Armure : (.*)$/ ,(_m,x)=>`Armor: ${x}`],
 [/^Dernier paquet : (.*)$/ ,(_m,x)=>`Last update: ${x}`],
 [/^Serveur indisponible : (.*)$/ ,(_m,x)=>`Server unavailable: ${x}`],
 [/^Import impossible : (.*)$/ ,(_m,x)=>`Import failed: ${x}`],
 [/^Profil importé · (.*) widgets$/ ,(_m,x)=>`Profile imported · ${x} widgets`],
 [/^(.*) ajouté$/ ,(_m,x)=>`${dictionary[x]||x} added`],
 [/^Élimination · (.*) au total$/ ,(_m,x)=>`Kill · ${x} total`],
 [/^Nouvelle manche · (.*)$/ ,(_m,x)=>`New round · ${x}`]
 ];
 for(const [re,handler] of rules){if(re.test(value))return value.replace(re,handler);}
 return value;
};
const dictionaryText=(original,lang)=>{
 const match=original.match(/^(\s*)([\s\S]*?)(\s*)$/);
 if(!match)return original;
 return match[1]+formatDynamic(match[2],lang)+match[3];
};
let code='EN'; try{const saved=localStorage.getItem(STORAGE);if(saved&&Object.prototype.hasOwnProperty.call(translations,saved))code=saved;}catch{}
const seenText=new WeakMap(), seenAttrs=new WeakMap();
function visit(node){
 const owner=node.nodeType===1?node:node.parentElement;
 if(owner?.closest('[translate="no"]'))return;
 if(node.nodeType===3){
   const existing=seenText.get(node),current=node.nodeValue;
   const original=existing && current===existing.rendered?existing.original:current;
   const translated=dictionaryText(original,code);
   seenText.set(node,{original,rendered:translated});
   if(current!==translated)node.nodeValue=translated;
   return;
 }
 if(node.nodeType!==1)return;
 if(node.matches('script,style,textarea,option[value="FR"],option[value="EN"]'))return;
 let prev=seenAttrs.get(node)||{};
 for(const attr of ['placeholder','aria-label','title']){
   if(!node.hasAttribute(attr))continue;
   const current=node.getAttribute(attr),old=prev[attr],original=old&&current===old.rendered?old.original:current;
   const rendered=dictionaryText(original,code);
   prev[attr]={original,rendered};
   if(current!==rendered)node.setAttribute(attr,rendered);
 }
 seenAttrs.set(node,prev);
 for(const child of Array.from(node.childNodes))visit(child);
}
let pending=new Set(),scheduled=false;
function flush(){scheduled=false;const nodes=Array.from(pending);pending.clear();for(const node of nodes){if(node.isConnected)visit(node);}}
function enqueue(n){pending.add(n);if(!scheduled){scheduled=true;queueMicrotask(flush);}}
function setLocale(next){if(!Object.prototype.hasOwnProperty.call(translations,next))return;code=next;document.documentElement.lang=code.toLowerCase();try{localStorage.setItem(STORAGE,code);}catch{}
 const select=document.getElementById('locale-select');if(select)select.value=code;const label=document.querySelector('.language-label');if(label)label.textContent=code==='FR'?'Langue':'Language';
 enqueue(document.body);
 if(typeof CustomEvent==='function')document.dispatchEvent(new CustomEvent('cs2:locale-changed',{detail:{locale:code}}));
}
const messages={
 'profile.pending':'Modifications non enregistrées.',
 'profile.choose':'Modifications non enregistrées. Choisis une action.',
 'profile.saving':'Enregistrement…',
 'profile.disconnected':'Modifications non enregistrées. Connexion interrompue.',
 'profile.conflict':'Modifications non enregistrées. Le serveur a une autre version.',
 'profile.error':'Enregistrement impossible. Vérifie le stockage du serveur.',
 'profile.discardPrompt':'Des modifications ne sont pas enregistrées. Les abandonner ?'
};
window.CS2I18N={message:key=>dictionaryText(messages[key]||'',code),locale:()=>code, translate:s=>dictionaryText(s,code),setLocale,available:()=>Object.keys(translations)};
document.addEventListener('DOMContentLoaded',()=>{
 const select=document.getElementById('locale-select');if(select){select.value=code;select.addEventListener('change',e=>setLocale(e.target.value));}
 setLocale(code);
 const observer=new MutationObserver(records=>{for(const rec of records){if(rec.type==='characterData')enqueue(rec.target);else if(rec.type==='attributes')enqueue(rec.target);else for(const n of rec.addedNodes)enqueue(n);}});
 observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['placeholder','aria-label','title']});
});
})();
