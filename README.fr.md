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
| `config` | Gérer les identifiants | `set`, `show`, `clear`, `list-profiles` |
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

# Diffusion via le canal bot
lansenger message send-bot-message text '{"content":"Avis"}' --chat-id user001 --chat-id user002

# Canal message de groupe (user_token facultatif, affiché comme bot sans)
lansenger message send-group-message group123 text '{"content":"Message de groupe"}'

# Envoyer en tant qu'utilisateur humain (nécessite user_token)
lansenger message send-group-message group123 text '{"content":"Message"}' --user-token YOUR_USER_TOKEN --sender-id staff001

# Canal compte public
lansenger message send-account-message text '{"content":"Message compte"}' --chat-id user001 --account-id acct001

# Canal utilisateur (nécessite user_token)
lansenger message send-user-message user001 text '{"content":"Message privé"}' --user-token YOUR_USER_TOKEN

# Révoquer des messages
lansenger message revoke msg001 msg002
```

### Gestion des groupes

```bash
# Créer un groupe
lansenger group create "Groupe Projet" org001 --staff staff001 --staff staff002

# Voir les infos du groupe
lansenger group info group123

# Voir les membres du groupe
lansenger group members group123

# Voir la liste des groupes (bot peut lister ses groupes)
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

# Messages de groupe (bot peut récupérer)
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

# Télécharger un média application/bot
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

```bash
# Sortie JSON (utile pour les scripts)
lansenger -j staff basic-info staff001
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
# Configurer la première application (bot personnel)
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

# Voir les détails d'un profil
lansenger config show --profile my-app
```

## Sécurité

- Identifiants stockés par profil dans `~/.lansenger/sdk_state.json` avec permissions `0600`
- `config show` masque tous les champs secrets (`***`), seuls `api_gateway_url` et `passport_url` sont affichés en clair
- Variables d'environnement `LANSENGER_APP_ID` / `LANSENGER_APP_SECRET` / `LANSENGER_ENCODING_KEY` / `LANSENGER_CALLBACK_TOKEN` supportées pour CI/CD

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
