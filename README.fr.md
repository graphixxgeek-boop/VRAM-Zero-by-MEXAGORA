<div align="center">

<img src="docs/images/illustration-VRAM-Zero.png" alt="VRAM Zero" width="220">

# VRAM Zero

**Surveillez la mémoire des cartes NVIDIA et libérez-la en fermant les processus qui l'occupent, pensé pour ceux qui font tourner des modèles d'IA en local.**

[![Dernière version](https://img.shields.io/github/v/release/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA?label=version)](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/releases/latest)
[![Licence : MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)
![Plateforme : Windows](https://img.shields.io/badge/plateforme-Windows%2010%20%7C%2011-lightgrey)
![GPU : NVIDIA](https://img.shields.io/badge/GPU-NVIDIA-76b900)

[**Télécharger**](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/releases/latest) · [English](README.md) · [Signaler un bug](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/issues/new/choose)

</div>

<p align="center">
  <img src="docs/images/screenshot-main.png" alt="Fenêtre principale de VRAM Zero (données d'exemple)" width="720"><br>
  <sub>Capture d'écran avec des données d'exemple.</sub>
</p>

## Pourquoi

Après une session avec Ollama, ComfyUI, LM Studio ou une interface Stable Diffusion, la VRAM reste souvent occupée : un modèle reste chargé, un processus Python traîne, et la tâche suivante manque de mémoire. Trouver le coupable oblige à lire la sortie de `nvidia-smi` et à fermer les processus à la main.

VRAM Zero affiche ce qui occupe la mémoire de votre GPU, distingue les outils d'IA locale du reste, et vous laisse fermer ceux que vous choisissez, après confirmation.

## Fonctionnalités

- VRAM et utilisation du GPU en direct, actualisées toutes les 3 secondes, sur une ou plusieurs cartes NVIDIA
- Processus classés en trois niveaux :
  - **IA locale** (vert) : Ollama, ComfyUI, LM Studio, llama.cpp, KoboldCpp, interfaces Stable Diffusion, etc.
  - **Non essentiel** (orange) : navigateurs, lanceurs, messageries, outils créatifs
  - **Critique** (rouge) : composants Windows et pilotes, masqués par défaut
- Actions en un clic : fermer la sélection, fermer toutes les IA locales, ou fermer tout ce qui est affiché
- Confirmation avant chaque fermeture, avec un avertissement supplémentaire pour les processus critiques
- Copie d'un rapport texte de l'état courant dans le presse-papiers
- Aucun accès réseau, aucune télémétrie, rien d'écrit sur le disque

## Installation

**Installeur (recommandé) :** téléchargez `VRAM_Zero_Setup_2.0.exe` depuis la [dernière version](https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/releases/latest) et lancez-le.

**Prérequis :** Windows 10 ou 11 (64 bits), une carte NVIDIA avec son pilote installé (fournit `nvidia-smi`).

> **winget :** un paquet a été soumis ([pull request](https://github.com/microsoft/winget-pkgs/pull/458325)). Une fois accepté, il s'installera avec `winget install MEXAGORA.VRAMZero`.

### Vérifier le téléchargement

Le SHA-256 de chaque fichier est indiqué dans les notes de version. Dans PowerShell :

```powershell
Get-FileHash .\VRAM_Zero_Setup_2.0.exe -Algorithm SHA256
```

### À propos des alertes antivirus

Les fichiers ne sont **pas encore signés numériquement** : certains antivirus peuvent donc signaler le programme. L'application est empaquetée avec PyInstaller et peut terminer des processus, deux caractéristiques qui provoquent couramment des faux positifs heuristiques.

Les résultats VirusTotal de la version 2.0 sont publiés dans [`docs/virustotal`](docs/virustotal/) : 2 moteurs sur 69 pour l'installeur et 4 sur 70 pour l'exécutable, dont aucun parmi Microsoft, Avast, AVG, Kaspersky, ESET ou BitDefender.

Tout est construit à partir de ce dépôt par [GitHub Actions](.github/workflows/build.yml). Vous pouvez aussi lire le code ou le compiler vous-même.

## Compiler depuis les sources

Nécessite Python 3 avec Tkinter (inclus dans l'installeur Windows standard). Aucune dépendance tierce.

```powershell
python src\vram_zero.pyw          # lancer depuis les sources
.\RECREER_EXE.bat                 # construire dist\VRAM Zero\VRAM Zero.exe avec PyInstaller
```

Pour construire l'installeur, ouvrez `installer\VRAM_Zero.iss` dans [Inno Setup](https://jrsoftware.org/isinfo.php) et compilez. Voir [docs/GUIDE_INNO_SETUP.md](docs/GUIDE_INNO_SETUP.md).

## À savoir

- Les données viennent de `nvidia-smi`. Sous Windows, le pilote n'expose pas toujours la VRAM par processus (WDDM) : certaines lignes affichent `N/A`. Les chiffres globaux en haut restent exacts.
- Seuls les processus rapportés par `nvidia-smi --query-compute-apps` sont listés. Certaines applications purement graphiques peuvent ne pas apparaître.
- La fermeture d'un processus est immédiate et les données non enregistrées sont perdues. Fermer des processus système peut déstabiliser Windows, d'où leur masquage par défaut.

## Contribuer

Les rapports de bugs et les idées sont bienvenus. Voir [CONTRIBUTING.md](CONTRIBUTING.md). Failles de sécurité : voir [SECURITY.md](SECURITY.md).

## Licence

[MIT](LICENSE) © 2026 MEXAGORA
