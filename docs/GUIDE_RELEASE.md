# Guide — publier la Release GitHub de VRAM Zero 2.0

Durée : environ 10 minutes. Vous publiez **exactement le fichier analysé par VirusTotal**, afin que les empreintes de la note correspondent au fichier téléchargé.

---

## Étape 1 — Récupérer le bon fichier

1. Ouvrez le run GitHub qui a produit les fichiers analysés :
   https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/actions/runs/39667699353
2. Descendez tout en bas de la page, section **Artifacts**.
3. Cliquez sur **VRAM-Zero-installer-unsigned** : un ZIP se télécharge.
4. Extrayez le ZIP : il contient `VRAM_Zero_Setup_2.0.exe`.

## Étape 2 — Vérifier l'empreinte

Dans PowerShell, dans le dossier du fichier extrait :

```
Get-FileHash .\VRAM_Zero_Setup_2.0.exe -Algorithm SHA256
```

Le résultat doit être exactement :

```
65CB240BBA11022F53DA92E35A49DDCA199555F391FD6273AD2B0BF58242E7F7
```

Si ce n'est pas le cas, **ne publiez pas** : ce n'est pas le fichier analysé (voir « En cas de problème »).

## Étape 3 — Créer la Release

1. Ouvrez le dépôt : https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA
2. Colonne de droite, section **Releases** → **Create a new release** (ou onglet *Releases* → *Draft a new release*).
3. **Choose a tag** : tapez `v2.0.0`, puis cliquez sur **Create new tag: v2.0.0 on publish**.
4. **Target** : `main`.
5. **Release title** : `VRAM Zero 2.0`.

## Étape 4 — Coller la note

1. Ouvrez le fichier `NOTE_RELEASE.md`.
2. Copiez tout son contenu.
3. Collez-le dans la zone **Describe this release**.
4. Onglet **Preview** : vérifiez l'affichage des tableaux et des liens.

## Étape 5 — Joindre l'installeur

1. Zone **Attach binaries by dropping them here**.
2. Glissez `VRAM_Zero_Setup_2.0.exe`.
3. Attendez que le fichier apparaisse dans la liste, avec une barre de chargement terminée.
4. Facultatif : joignez aussi les deux rapports `VIRUSTOTAL_…md`.

## Étape 6 — Choisir comment publier

| Choix | Effet |
|---|---|
| **Save draft** | Brouillon visible de vous seul. Permet de tout vérifier. |
| **Set as a pre-release** | Publié, mais marqué « Pre-release ». |
| **Publish release** (cocher *Set as the latest release*) | Publié pour tout le monde. |

Recommandation : **Save draft** d'abord, relire, puis **Publish release** quand vous êtes prêt.

## Étape 7 — Contrôler après publication

1. Ouvrez la page de la Release (non connecté ou en navigation privée, pour voir ce que voit un client).
2. Téléchargez `VRAM_Zero_Setup_2.0.exe` depuis cette page.
3. Recalculez l'empreinte (étape 2) : elle doit être identique.
4. Testez l'installation.

## Étape 8 — Partager

Diffusez **le lien de la page de la Release**, par exemple :

```
https://github.com/graphixxgeek-boop/VRAM-Zero-by-MEXAGORA/releases/tag/v2.0.0
```

Ne diffusez pas de lien direct vers un autre hébergement.

---

## À savoir

- **Création du tag** : le workflow « Build VRAM Zero » se relance automatiquement et produit un nouvel installeur non signé, d'empreinte différente. Ce nouvel installeur n'est pas celui de la Release : ne l'utilisez pas.
- **Après l'obtention d'une signature de code** : on publie une nouvelle Release (par exemple `v2.0.1`) avec le fichier signé, et on refait un rapport VirusTotal.
- **Changement de fichier** : toute nouvelle compilation produit une nouvelle empreinte. Les empreintes et les liens VirusTotal de la note doivent alors être mis à jour.

## En cas de problème

| Problème | Solution |
|---|---|
| L'empreinte ne correspond pas | Vous avez téléchargé un autre run. Reprenez le lien de l'étape 1. |
| Section Artifacts introuvable | Connectez-vous à GitHub : le téléchargement l'exige. |
| Artifacts expirés | Relancez le workflow, refaites un rapport VirusTotal, puis mettez à jour les empreintes dans la note. |
| Le tag existe déjà | Choisissez-le dans la liste, ou utilisez un nouveau numéro. |
