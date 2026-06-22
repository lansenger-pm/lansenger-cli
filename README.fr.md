[English](README.md) | [简体中文](README.zhHans.md) | [繁体中文](README.zhHant.md) | [繁体中文香港](README.zhHantHK.md) | [Français](README.fr.md)

# Lansenger CLI

Outil en ligne de commande Lansenger — interagissez avec les API Lansenger directement depuis le terminal : envoyez des messages, gérez des groupes, interrogez le personnel/les départements, gérez les calendriers et les tâches, et plus encore.

## Installation

```bash
pip install lansenger-cli
```

Ou compiler depuis les sources :

```bash
git clone https://github.com/lansenger-pm/lansenger-cli.git
cd lansenger-cli
pip install -e .
```

Nécessite Python ≥ 3.10.

## Démarrage rapide

### 1. Configurer les identifiants

Sauvegardez les identifiants via `config set` (stockés par profil dans `~/.lansenger/sdk_state.json`, clés masquées, permissions fichier 0600) :

**Identifiants requis** :

```bash
lansenger config set app_id YOUR_APP_ID
lansenger config set app_secret YOUR_APP_SECRET
lansenger config set api_gateway_url https://apigw.lx.qianxin.com/open/apigw
```

**Authentification OAuth2 (remplissez si vous avez besoin d'un userToken)** :

```bash
lansenger config set passport_url https://passport.lx.qianxin.com
lansenger config set redirect_uri http://localhost:8765   # URI de redirection OAuth2 (défaut)
```

**Réception des callbacks (remplissez si vous devez analyser/vérifier les webhooks)** :

```bash
lansenger config set encoding_key YOUR_ENCODING_KEY
lansenger config set callback_token YOUR_CALLBACK_TOKEN
```

Vous pouvez également configurer via les variables d'environnement (compatible CI/CD) :

```bash
export LANSENGER_APP_ID=YOUR_APP_ID
export LANSENGER_APP_SECRET=YOUR_APP_SECRET
export LANSENGER_ENCODING_KEY=YOUR_ENCODING_KEY
export LANSENGER_CALLBACK_TOKEN=YOUR_CALLBACK_TOKEN
```

### 2. Voir la configuration

```bash
lansenger config show
```

### 3. Vérification de santé

Vérifiez que les identifiants sont corrects et que le token d'application peut être obtenu :

```bash
lansenger health check
```

## Aperçu des commandes

| Groupe | Description | Sous-commandes |
|--------|------|--------|
| `config` | Gérer les identifiants | `set`, `show`, `clear`, `delete-profile`, `list-profiles`, `list-users` |
| `message` | Envoyer et gérer les messages | `send-text`, `send-markdown`, `send-file`, `send-image-url`, `send-link-card`, `send-app-articles`, `send-app-card`, `send-oacard`, `send-bot-message`, `send-group-message`, `send-account-message`, `send-user-message`, `update-dynamic-card`, `revoke`, `query-groups` |
| `group` | Gérer les groupes | `create`, `info`, `members`, `list`, `check`, `update`, `update-members` |
| `staff` | Interroger les infos du personnel | `basic-info`, `detail`, `ancestors`, `id-mapping`, `org-extra-fields`, `search`, `org-info` |
| `department` | Interroger les départements | `detail`, `children`, `staffs` |
| `calendar` | Calendrier et planification | `primary`, `create-schedule`, `fetch-schedule`, `delete-schedule`, `list-schedules`, `attendees`, `add-attendees`, `delete-attendees` |
| `todo` | Gestion des tâches | `create`, `update`, `update-status`, `delete`, `list`, `fetch-by-source`, `fetch-by-id`, `status-counts`, `executor-status`, `add-executors`, `delete-executors`, `executor-list` |
| `oauth` | Authentification OAuth2 | `authorize-url`, `exchange-code`, `refresh-token`, `user-info`, `parse-callback`, `validate-state` |
| `callback` | Analyse des événements callback | `parse-payload`, `decrypt-payload`, `verify-signature`, `event-types` |
| `media` | Opérations sur les fichiers média | `upload`, `upload-app`, `download`, `download-to-file` |
| `streaming` | Messages en streaming (IA) | `create`, `fetch` |
| `chat` | Conversations et messages | `list`, `messages` |
| `health` | Vérification de connexion | `check` |

## Exemples courants

### Messagerie

```bash
# Envoyer un message texte
lansenger message send-text chat123 "Hello World"

# Envoyer un message Markdown
lansenger message send-markdown chat123 "**Gras** texte"

# Envoyer un fichier
lansenger message send-file chat123 /path/to/file.pdf

# Envoyer une image depuis une URL
lansenger message send-image-url chat123 https://example.com/photo.jpg

# Envoyer une carte lien
lansenger message send-link-card chat123 "Annonce" https://example.com --desc "Cliquez pour plus de détails"

# Envoyer une carte applicative
lansenger message send-app-card chat123 "Titre de la carte" --content "Texte" --card-link https://example.com

# Envoyer plusieurs articles
lansenger message send-app-articles chat123 '{"title":"Article 1","url":"https://a.com"}' '{"title":"Article 2","url":"https://b.com"}'

# Envoyer une carte d'approbation OA
lansenger message send-oacard chat123 "Titre approbation" --head "Notification" --field '{"key":"Demandeur","value":"Jean"}'

# Envoyer dans un groupe avec @all
lansenger message send-text group123 "Annonce" --group --mention-all

# @mention spécifique dans un groupe
lansenger message send-text group123 "Veuillez vérifier" --group --mention staff001

# @mention de bots spécifiques dans le groupe
lansenger message send-text group123 "Bot check" --group --mention-bot bot001 --mention-bot bot002

# Répondre à un message (référence de message)
lansenger message send-text group123 "Got it" --group --ref-msg-id 524288-xxx

# Diffusion via le canal robot
lansenger message send-bot-message text '{"content":"Avis"}' --chat-id user001 --chat-id user002

# Réponse du canal bot (référence de message)
lansenger message send-bot-message text '{"content":"Reply"}' --chat-id user001 --ref-msg-id 524288-xxx

# Canal message de groupe (user_token facultatif, affiché comme robot sans)
lansenger message send-group-message group123 text '{"content":"Message de groupe"}'

# Envoyer en tant qu'utilisateur humain (nécessite user_token)
lansenger message send-group-message group123 text '{"content":"Message"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# Répondre avec un message de groupe
lansenger message send-group-message group123 text '{"content":"reply"}' --ref-msg-id 524288-xxx

# Canal compte public
lansenger message send-account-message text '{"content":"Message compte"}' --chat-id user001 --account-id acct001

# Canal utilisateur (nécessite user_token)
lansenger message send-user-message user001 text '{"content":"Message privé"}' --user-token YOUR_USER_TOKEN

# Révoquer des messages
lansenger message revoke msg001 msg002

# Rechercher la liste des identifiants de groupe
lansenger message query-groups --page 0 --size 100
```

### Gestion des groupes

```bash
# Créer un groupe
lansenger group create "Groupe Projet" org001 --staff staff001 --staff staff002

# Voir les infos du groupe
lansenger group info group123

# Voir les membres du groupe
lansenger group members group123

# Voir la liste des groupes (robot peut lister ses groupes)
lansenger group list

# Voir la liste des groupes en tant qu'utilisateur (nécessite user_token)
lansenger group list --user-token YOUR_USER_TOKEN

# Vérifier l'appartenance au groupe
lansenger group check group123 --staff-id staff001

# Mettre à jour les infos du groupe
lansenger group update group123 --name "Nouveau nom" --desc "Nouvelle description"

# Ajouter/supprimer des membres
lansenger group update-members group123 --add staff003 --remove staff001
```

### Interrogation du personnel

```bash
# Infos de base
lansenger staff basic-info staff001

# Infos détaillées
lansenger staff detail staff001

# Rechercher du personnel
lansenger staff search ZhangSan

# Mapping d'ID (téléphone/email → staffId)
lansenger staff id-mapping org001 phone 13800138000

# Infos organisation
lansenger staff org-info org001
```

### Interrogation des départements

```bash
# Détail du département
lansenger department detail dept001

# Sous-départements
lansenger department children dept001

# Personnel du département
lansenger department staffs dept001
```

### Conversations et messages

```bash
# Liste des conversations (nécessite user_token)
lansenger chat list --user-token YOUR_USER_TOKEN

# Conversations de groupe uniquement
lansenger chat list --type 2 --user-token YOUR_USER_TOKEN

# Rechercher par mot-clé
lansenger chat list --type 1 --keyword ZhangSan --user-token YOUR_USER_TOKEN

# Messages privés
lansenger chat messages --staff-id staff001 --user-token YOUR_USER_TOKEN

# Messages de groupe (robot peut récupérer)
lansenger chat messages --group-id group123

# Messages de groupe en tant qu'utilisateur (nécessite user_token)
lansenger chat messages --group-id group123 --user-token YOUR_USER_TOKEN
```

### Calendrier

```bash
# Calendrier principal
lansenger calendar primary --user-token YOUR_USER_TOKEN

# Créer un événement (start/end en secondes Unix)
lansenger calendar create-schedule cal001 "Réunion" 1747539600 1747543200 \
  '[{"staffId":"staff001","attendeeFlag":"yes"}]' \
  --desc "Standup hebdomadaire" --user-token YOUR_USER_TOKEN

# Lister les événements
lansenger calendar list-schedules cal001 1747539600 1747603200 --user-token YOUR_TOKEN

# Détail d'un événement
lansenger calendar fetch-schedule cal001 schedule001 --user-token YOUR_TOKEN

# Supprimer un événement
lansenger calendar delete-schedule cal001 schedule001 --user-token YOUR_TOKEN
```

### Tâches

```bash
# Créer une tâche
lansenger todo create "Approuver document" https://app.com/doc https://app.com/doc \
  "staff001,staff002" org001 --desc "À réviser" --type 2

# Mettre à jour le statut (11=non lu, 12=lu, 21=en attente, 22=fait)
lansenger todo update-status task001 22 org001

# Lister les tâches
lansenger todo list org001 --status 21,22

# Supprimer une tâche
lansenger todo delete task001 org001
```

### Authentification OAuth2

```bash
# Générer l'URL d'autorisation
lansenger oauth authorize-url https://yourapp.com/callback --scope basic_userinfor

# Échanger le code contre un token
lansenger oauth exchange-code AUTH_CODE --redirect-uri https://yourapp.com/callback

# Rafraîchir le token
lansenger oauth refresh-token YOUR_REFRESH_TOKEN

# Récupérer les infos utilisateur
lansenger oauth user-info YOUR_USER_TOKEN
```

### Événements callback

```bash
# Lister les types d'événements
lansenger callback event-types

# Analyser le payload
lansenger callback parse-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# Déchiffrer le payload
lansenger callback decrypt-payload ENCRYPTED_DATA --encoding-key YOUR_KEY

# Vérifier la signature
lansenger callback verify-signature TIMESTAMP NONCE SIGNATURE ENCODING_KEY --data-encrypt ENCRYPTED_DATA
```

### Fichiers média

```bash
# Télécharger un fichier plateforme principale
lansenger media upload /path/to/file.pdf --media-type 3

# Télécharger un média application/robot
lansenger media upload-app /path/to/file.pdf --media-type file

# Télécharger un média vers un fichier local
lansenger media download-to-file MEDIA_ID --output /path/to/save.pdf
```

### Messages en streaming

```bash
# Créer un message streaming (pour sortie progressive d'agent IA)
lansenger streaming create user123 single stream-session-001

# Obtenir le statut du message streaming
lansenger streaming fetch MSG_ID
```

## Options globales

| Option | Description |
|------|------|
| `--json` / `-j` | Sortie JSON brute au lieu de tableaux formatés |
| `--as <staff_id>` | Charge et rafraîchit automatiquement le jeton utilisateur pour le staff_id spécifié depuis le stockage des identifiants |

```bash
# Sortie JSON (utile pour les scripts)
lansenger -j staff basic-info staff001

# Exécuter une commande en tant qu'utilisateur spécifique (charge automatiquement le jeton utilisateur)
lansenger --as staff001 chat messages --group-id group123
```

## Auto-complétion shell

Support d'auto-complétion intégré via typer :

```bash
# Installer l'auto-complétion
lansenger --install-completion

# Afficher le script d'auto-complétion
lansenger --show-completion
```

Supporte bash, zsh, fish et autres shells majeurs.

## Profils multi-applications / multi-bots

Le CLI prend en charge plusieurs profils, chacun correspondant à un appID, avec des identifiants isolés :

```bash
# Configurer la première application (robot personnel)
lansenger config set app_id xxx1 --profile my-bot
lansenger config set app_secret xxx1 --profile my-bot

# Configurer la deuxième application
lansenger config set app_id xxx2 --profile my-app
lansenger config set app_secret xxx2 --profile my-app
lansenger config set encoding_key yyy2 --profile my-app
lansenger config set callback_token zzz2 --profile my-app

# Exécuter avec un profil spécifique
lansenger message send-text staff123 "Hello" --profile my-bot
lansenger callback parse-payload DATA --profile my-app

# Lister tous les profils
lansenger config list-profiles

# Supprimer un profil (bascule automatiquement vers default si actif)
lansenger config delete-profile my-bot

# Voir les détails d'un profil
lansenger config show --profile my-app
```

## Sécurité

- Identifiants stockés par profil dans `~/.lansenger/sdk_state.json` avec permissions `0600`
- `config show` masque tous les champs secrets (`***`), seuls `api_gateway_url` et `passport_url` sont affichés en clair
- Variables d'environnement `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` / `LANSENGER_ENCODING_KEY` / `LANSENGER_CALLBACK_TOKEN` supportées pour CI/CD

## Identité & Permissions

### Matrice des capacités par identité

La plateforme Lansenger propose trois types d'identité avec différents accès API :

| Domaine de commande | Robot personnel | App Org (auto-hébergée) | App Org + Robot | Notes |
|--------|:---:|:---:|:---:|------|
| `message send-text/markdown/file/...` (DM robot) | **Y** | N | **Y** | Seuls les robots peuvent envoyer des DM robot |
| `message send-text --group` (chat de groupe) | **Y** | N | **Y** | Le robot personnel prend désormais en charge la messagerie de groupe |
| `message send-group-message` | **Y** | N | **Y** | Identique à ci-dessus |
| `message send-account-message` (compte public) | N | **Y** | **Y** | Nécessite la capacité compte public |
| `message send-user-message` (utilisateur à utilisateur) | N | **Y** | **Y** | Nécessite userToken + OAuth2 |
| `message revoke` | **Y** | **Y** | **Y** | Révoquer ses propres messages |
| `staff *` (contacts lecture seule) | N | **Y** | **Y** | `search` nécessite en plus userToken |
| `department *` | N | **Y** | **Y** | Applications niveau organisation uniquement |
| `calendar *` | N | **Y** | **Y** | Avec userToken = identité utilisateur ; sans = identité robot |
| `todo *` | N | **Y** | **Y** | Applications niveau organisation uniquement |
| `chat list/messages` | N | **Y** | **Y** | Applications niveau organisation uniquement |
| `group *` (gestion de groupes V2) | N | N | **Y** | Nécessite que le robot soit dans le groupe |
| `media upload` | **Y** | **Y** | **Y** | Téléchargement général |
| `media upload-app` | **Y** | **Y** | **Y** | Apps auto-hébergées uniquement (pas ISV) |
| `media download/path` | **Y** | **Y** | **Y** | Téléchargement général |
| `oauth *` | N | **Y** | **Y** | Applications niveau organisation uniquement |
| `streaming *` | N | **Y** | **Y** | Applications niveau organisation uniquement |
| `callback *` (analyse d'événements) | N/A | N/A | N/A | Opération pure de données, aucune identité requise |

> \* **N\*** = La capacité API existe.

> **Robot personnel** ne peut qu'envoyer/recevoir des messages et télécharger des fichiers. Ne peut pas accéder aux contacts, calendriers ou OAuth2.
>
> **App Org vs App Org + Robot** : Même appID/appSecret. La seule différence réside dans les canaux de messagerie — seuls les robots peuvent envoyer des DM robot et des messages de groupe (car seuls les robots peuvent rejoindre des groupes). Toutes les autres API (contacts, calendrier, tâches, conversations, OAuth2, streaming) fonctionnent de manière identique pour les deux. Actuellement, seules les apps auto-hébergées supportent la capacité robot.

### Permissions du Centre Développeur

Au-delà du type d'identité, les appels API spécifiques dépendent également des bascules de permission dans le Centre Développeur Lansenger. L'organisation peut restreindre l'accès développeur, nécessitant l'assistance d'un administrateur.

**Permissions de base (activées par défaut) :**

| Permission | Description |
|------|------|
| Obtenir les infos utilisateur de base | Obtenir les informations de base du personnel pour la connexion système/app |
| Envoyer des messages de notification | Obtenir les canaux de messagerie de l'organisation pour envoyer des messages aux personnes/groupes |

**Permissions avancées (désactivées par défaut, doivent être activées manuellement) :**

| Permission | Description | Skill impacté |
|------|------|-------------|
| Contacts lecture seule | Accès en lecture aux contacts | `lansenger-staff`, `lansenger-department` |
| Contacts édition | Accès en édition aux contacts | `lansenger-staff` (créer/mettre à jour/supprimer) |
| Infos sensibles - Téléphone | Accéder aux numéros de téléphone | `lansenger-staff` (détail, id-mapping) |
| Infos sensibles - Email | Accéder aux emails | `lansenger-staff` (détail, id-mapping) |
| Infos sensibles - N° d'identité | Accéder aux numéros d'identité | `lansenger-staff` |
| Infos sensibles - ID employé | Accéder aux IDs employé | `lansenger-staff` |
| Mapper attribut unique vers staff ID | Mapper téléphone/email/ID employé vers staff ID | `lansenger-staff` (id-mapping) |
| Édition d'app | Créer et mettre à jour des apps | Gestion du Centre Développeur |
| Groupes lecture seule | Accès en lecture aux groupes | `lansenger-group` (infos/membres) |
| Groupes édition | Accès en édition aux groupes | `lansenger-group` (créer/mettre à jour/dissoudre/membres) |
| Calendrier lecture seule | Accès en lecture au calendrier | `lansenger-calendar` (requête) |
| Calendrier édition | Accès en édition au calendrier | `lansenger-calendar` (créer/mettre à jour/supprimer) |
| Télécharger média | Permission de télécharger des fichiers média | `lansenger-media` (upload, upload-app) |
| Lecture modèles workbench | Accès en lecture aux modèles workbench | — |
| Écriture modèles workbench | Accès en écriture aux modèles workbench | — |

En cas d'erreurs de permission, vérifiez d'abord que le type d'identité supporte l'opération, puis invitez l'utilisateur à activer la permission avancée correspondante dans le Centre Développeur (contactez l'admin de l'organisation si l'accès est impossible).

## Compatibilité CLI

Ce CLI partage la même syntaxe de commande que les versions TypeScript et Go :

```bash
# Python CLI
pip install lansenger-cli

# Go CLI
go install github.com/lansenger-pm/lansenger-sdk-go/cmd/lansenger@latest

# TypeScript CLI
npm install -g lansenger-cli
```

## Relation avec le SDK

Ce CLI est construit sur `LansengerSyncClient` de [lansenger-sdk-python](https://github.com/lansenger-pm/lansenger-sdk-python), couvrant toutes les API synchrones du SDK sans le modifier.

## Licence

Licence MIT
