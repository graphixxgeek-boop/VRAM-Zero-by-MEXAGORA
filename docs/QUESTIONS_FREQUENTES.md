# VRAM Zero : questions fréquentes

Un petit guide pour bien démarrer. Si une question manque, vous pouvez en poser une sur la [page des tickets](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/issues/new/choose) : les réponses utiles sont ajoutées ici.

## À quoi sert VRAM Zero ?
Quand vous utilisez des outils d'intelligence artificielle sur votre ordinateur (Ollama, ComfyUI, LM Studio…), la mémoire de votre carte graphique NVIDIA (la « VRAM ») reste parfois occupée après usage. VRAM Zero vous montre ce qui l'occupe et vous laisse fermer les programmes de votre choix, pour retrouver de la place.

## Comment ça se passe concrètement ?
1. Vous ouvrez VRAM Zero : la mémoire utilisée s'affiche, avec la liste des programmes concernés.
2. Chaque programme porte une couleur : vert pour un outil d'IA reconnu, orange pour une application courante, gris pour un programme non reconnu.
3. Vous choisissez ce que vous voulez fermer, puis vous confirmez. Rien n'est fermé sans votre accord.

## VRAM Zero peut-il fermer quelque chose par erreur ?
Plusieurs précautions sont prévues :
- une confirmation est toujours demandée, avec le nom de chaque programme ;
- les programmes essentiels de Windows sont masqués par défaut ;
- Claude, Docker et Wallpaper Engine ne sont jamais inclus dans « Fermer tout » ;
- juste avant la fermeture, VRAM Zero revérifie chaque programme, pour être certain de viser le bon ;
- vous pouvez toujours choisir ligne par ligne avec « Fermer la sélection ».

Pensez simplement à enregistrer votre travail avant de fermer un programme : ce qui n'est pas enregistré à l'intérieur ne peut pas être récupéré.

## Que fait VRAM Zero de mes données ?
L'application elle-même ne se connecte à aucun réseau et n'enregistre aucun fichier. Elle lit simplement les informations que fournit `nvidia-smi`, l'outil officiel de NVIDIA, installé avec vos pilotes.

## Windows ou mon antivirus affiche un message à l'installation. Que faire ?
C'est un cas courant pour les petits logiciels indépendants. Deux raisons à cela :
- **Le fichier n'est pas encore signé numériquement.** La signature est un certificat payant, que le projet n'a pas encore. Windows demande donc une confirmation : cliquez sur « Informations complémentaires », puis « Exécuter quand même ».
- **Quelques moteurs d'analyse réagissent par prudence.** Pour la version 2.0.1, 4 moteurs sur 71 la signalent sur VirusTotal, sur la base de critères généraux (fichier compressé, capable de fermer des programmes). Les principaux (Microsoft, Avast, AVG, Kaspersky, ESET, BitDefender) ne signalent rien.

Pour vous en assurer vous-même, tout est vérifiable :
- le code est entièrement public, dans ce dépôt (licence MIT) ;
- l'installeur est construit automatiquement par GitHub à partir de ce code ;
- son empreinte SHA-256 est indiquée dans les notes de la version : `Get-FileHash .\VRAM_Zero_Setup_2.0.1.exe -Algorithm SHA256` doit donner la même valeur ;
- les rapports VirusTotal sont publiés dans [`docs/virustotal`](virustotal/).

Si vous préférez ne pas installer le fichier tant qu'une signature n'existe pas, c'est un choix tout à fait légitime : vous pouvez aussi lancer le programme depuis les sources (voir le README).

## Comment l'installer et le désinstaller ?
- **Installer :** téléchargez `VRAM_Zero_Setup_2.0.1.exe` depuis la [dernière version](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/releases/latest), lancez-le et suivez l'assistant.
- **Désinstaller :** Paramètres Windows, Applications, VRAM Zero, Désinstaller.

## Faut-il être administrateur ?
Non. Certains programmes protégés par Windows peuvent toutefois refuser d'être fermés : VRAM Zero vous l'indique alors clairement.

## Pourquoi vois-je « N/A » dans la colonne VRAM ?
Sous Windows, le pilote ne communique pas toujours la mémoire utilisée par chaque programme. Le total affiché en haut de la fenêtre reste exact.

## Mon outil d'IA n'apparaît pas, ou apparaît en gris. Est-ce normal ?
Oui. VRAM Zero reconnaît les outils les plus courants. Un programme qu'il ne connaît pas s'affiche en gris : il reste visible, et vous pouvez le fermer à la main avec « Fermer la sélection ».

## Quelle configuration faut-il ?
Windows 10 ou 11 (64 bits) et une carte graphique NVIDIA avec ses pilotes installés.

## Où en est le projet ?
VRAM Zero est maintenu pour sa fiabilité et sa sûreté, sans nouvelle fonction prévue pour l'instant. Vos retours sont les bienvenus : ils orientent la suite.