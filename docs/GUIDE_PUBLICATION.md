# Guide de publication et antivirus — VRAM Zero

## 1. La vérité sur Avast (à lire en premier)

- **Ajouter une exclusion dans votre Avast ne concerne que votre PC.** Les clients ne sont pas protégés.
- Aucune astuce ne garantit « zéro alerte » chez tous les antivirus. Ce qui marche, par ordre d'efficacité :
  1. **Signer le programme** avec un certificat de signature de code (la « signature » dont vous parlez).
  2. **Faire examiner le fichier par les éditeurs** (faux positifs) : quand Avast, Microsoft, etc. valident le fichier, la correction vaut pour **tous** leurs utilisateurs.
  3. **Laisser la réputation se construire** (téléchargements, ancienneté, même éditeur signé).
  4. **Être transparent** : code public, empreinte SHA-256, explication dans la publication.
- Pourquoi VRAM Zero est suspect : l'EXE est fait avec PyInstaller (très souvent faussement détecté) et le programme **termine des processus** (`taskkill`), ce que les heuristiques surveillent.

## 2. Ce qui est déjà fait

- Informations d'éditeur intégrées à l'EXE et à l'installeur (société MEXAGORA, produit, version, licence).
- EXE en mode « dossier » (moins suspect que le mode « fichier unique »), sans compresseur UPX.
- Code source public sous licence MIT, aucune connexion réseau.
- Script d'installeur prêt, signature préparée (lignes commentées dans `VRAM_Zero.iss`).

**Ce qui n'est PAS fait : la signature.** Elle demande un certificat à votre nom, que je ne peux pas obtenir à votre place.

## 3. Signer le programme (le point décisif)

| Option | Coût indicatif | Remarques |
|---|---|---|
| **SignPath Foundation** | gratuit | Pour projets open source (le vôtre : dépôt public, MIT). Demande de candidature, signature faite par leur service depuis GitHub Actions. Candidature refusée en novembre 2026 (visibilité du projet insuffisante) : à redéposer quand le projet sera plus connu. |
| **Azure Artifact Signing** (ex Trusted Signing) | environ 10 $/mois | Certificat géré par Microsoft. Disponibilité selon pays et type de structure : à vérifier pour vous. |
| **Certificat OV** (Sectigo, DigiCert…) | environ 200–400 €/an | Livré sur clé USB/HSM. Réputation SmartScreen lente à venir. |
| **Certificat EV** | environ 300–600 €/an | Meilleure confiance immédiate. Clé physique obligatoire. |

**Recommandation :** rester non signé tant que le projet n'a pas d'utilisateurs, puis redéposer chez SignPath Foundation (gratuit) quand il sera plus connu. Sinon, Azure Artifact Signing si vous y êtes éligible, ou un certificat payant.
Je peux ensuite brancher la signature dans le build et dans GitHub Actions.

Une fois le certificat obtenu, on signe **l'EXE** puis **l'installeur** (les deux, dans cet ordre) avec `signtool`, avec un horodatage (`/tr` + `/td sha256`). Le script `VRAM_Zero.iss` sait ensuite le faire automatiquement (décommenter `SignTool=`).

## 4. Soumettre aux éditeurs d'antivirus (global, gratuit)

À faire pour chaque version publiée, avec l'**installeur** et l'**EXE** :

1. **Avast / AVG** : formulaire de faux positifs sur avast.com (« False positive file form »). Joignez le fichier et l'adresse du dépôt GitHub.
2. **Microsoft Defender** : portail de soumission « Submit a file for malware analysis » (compte Microsoft requis), en précisant « Software developer ».
3. **VirusTotal** : envoyez le fichier sur virustotal.com et gardez le lien du rapport pour la publication. Attention : un fichier envoyé là est consultable par les éditeurs de sécurité.
4. Autres (Kaspersky, ESET, Bitdefender, etc.) : uniquement si VirusTotal montre une détection.

## 5. Publier sur GitHub (standard du métier)

1. Sur GitHub : **Releases → Draft a new release**.
2. **Tag** : `v2.0.0`, **titre** : « VRAM Zero 2.0 ».
3. Joignez **`VRAM_Zero_Setup_2.0.exe`** (l'installeur) et idéalement le ZIP portable.
4. Dans la description : nouveautés, configuration requise, **empreinte SHA-256**, lien VirusTotal.
5. Calculez l'empreinte avec cette commande (dans le dossier de l'installeur) :

```
Get-FileHash .\VRAM_Zero_Setup_2.0.exe -Algorithm SHA256
```

6. Cochez **Set as the latest release**, puis **Publish release**.

Ensuite, partagez **le lien de la page Release**, jamais un lien de fichier hébergé ailleurs.

## 6. Texte à mettre dans la publication (modèle)

> **VRAM Zero 2.0** — surveillance et libération de la VRAM NVIDIA.
>
> **À propos des alertes antivirus.** VRAM Zero est un programme open source (licence MIT, code
> entièrement visible dans ce dépôt) fabriqué avec PyInstaller. Ce type de programme, qui plus est
> capable de terminer des processus, est parfois signalé à tort (« faux positif ») par certains
> antivirus. Le programme ne se connecte à aucun réseau et ne conserve aucune donnée.
> Vous pouvez vérifier l'intégrité du fichier avec l'empreinte SHA-256 ci-dessous, consulter le
> rapport VirusTotal, ou reconstruire l'EXE vous-même avec `RECREER_EXE.bat`.
>
> SHA-256 : `(à compléter)`  ·  VirusTotal : `(lien)`

## 7. Check-list avant chaque diffusion

- [ ] EXE reconstruit (`RECREER_EXE.bat`) puis installeur compilé (F9)
- [ ] EXE et installeur **signés** (quand le certificat est obtenu)
- [ ] Test d'installation sur un autre PC / une machine virtuelle
- [ ] Rapport VirusTotal et soumissions Avast / Microsoft faites
- [ ] Release GitHub publiée avec empreinte SHA-256 et texte explicatif
