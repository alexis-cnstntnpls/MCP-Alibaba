# Alibaba FR MCP Server (Sourcing B2B)

Serveur [MCP (Model Context Protocol)](https://modelcontextprotocol.io) spécialisé dans le **sourcing B2B et l'achat de gros sur Alibaba France** (`french.alibaba.com`), avec prix de gros en euros (€), gestion des quantités minimales de commande (MOQ) et profils d'usines fabricants.

Permet à **Claude Desktop**, **Cursor**, **Cline**, **Claude Code** et aux agents **ChatGPT** d'automatiser la recherche de fournisseurs, de comparer les paliers de prix usine et d'analyser la fiabilité des grossistes certifiés (*Gold Suppliers*).

---

## Sommaire

- [Fonctionnalités clés](#-fonctionnalités-clés)
- [Catalogue des Outils MCP](#-catalogue-des-outils-mcp)
- [Architecture & Extraction de Données B2B](#-architecture--extraction-de-données-b2b)
- [Prérequis & Installation](#-prérequis--installation)
- [Modes d'Exécution & Configuration](#-modes-dexécution--configuration)
  - [1. Mode local standard : stdio (Claude Desktop / Cursor)](#1-mode-local-standard--stdio-claude-desktop--cursor)
  - [2. Mode serveur HTTP : Streamable HTTP / SSE (ChatGPT / Accès distant)](#2-mode-serveur-http--streamable-http--sse-chatgpt--accès-distant)
- [Variables d'Environnement](#-variables-denvironnement)
- [Tests & Validation](#-tests--validation)
- [Bibliothèques & Références](#-bibliothèques--références)
- [Licence & Avertissement](#-licence--avertissement)

---

## 🌟 Fonctionnalités clés

1. **Recherche Sourcing B2B Spécialisée :**
   - Recherche en français orientée fabricants, grossistes et produits de gros.
   - **Filtre MOQ (Minimum Order Quantity) :** Filtrage précis sur la quantité minimale requise (`max_moq`, par ex. ≤ 10 ou ≤ 50 pièces pour les commandes tests ou petits volumes).
   - **Filtre Fournisseurs Vérifiés :** Sélection stricte des fournisseurs avec audit d'usine (*Verified Gold Suppliers*).
   - Fourchette de prix unitaires en euros (`min_price`, `max_price`).
   - Tris personnalisés : pertinence (`default`), prix croissant (`price_asc`), prix décroissant (`price_desc`), plus petite quantité minimale (`moq_asc`) ou meilleure note fournisseur (`rating_desc`).

2. **Fiches Techniques & Profils d'Usines :**
   - Récupération des détails via ID produit numérique ou URL Alibaba.
   - Paliers tarifaires dégressifs selon les volumes commandés (ex: 10-99 pcs : 4.50 €, 100-499 pcs : 3.80 €, 500+ pcs : 3.10 €).
   - Tableau complet des spécifications techniques (matériaux, certifications CE/RoHS, puissance, dimensions).
   - Profil usine : nom de l'entreprise, pays d'implantation, années d'ancienneté, score d'évaluation et garanties *Trade Assurance*.

3. **Protection & Stabilité :**
   - Émulation d'empreinte TLS / JA3 / JA4 via `curl_cffi` pour prévenir les défis de sécurité.
   - Localisation automatique en France avec devise EUR (`sc_g_cfg_f`).
   - Queue de requêtes asynchrone sérialisée avec temporisation humaine aléatoire.

---

## 🛠 Catalogue des Outils MCP

| Outil | Description | Paramètres principaux |
| :--- | :--- | :--- |
| **`search_alibaba_products`** | Recherche des offres de gros et fabricants avec filtres B2B spécifiques (prix, MOQ, certification usine). | `query` (str, obligatoire), `page` (int, 1-50), `min_price` (float), `max_price` (float), `max_moq` (int, ex: 50), `verified_only` (bool), `sort` (`default`, `price_asc`, `price_desc`, `moq_asc`, `rating_desc`). |
| **`get_alibaba_product_details`** | Récupère la fiche technique complète d'un produit, les paliers de prix de gros et les coordonnées de l'usine. | `product_id_or_url` (str, ID ou URL de la fiche article). |

---

## 🛡 Architecture & Extraction de Données B2B

Alibaba s'appuie sur une structure d'application web moderne avec chargement asynchrone :

1. **Extraction de Données Structurées :**
   - Le moteur inspecte et extrait les flux de données pré-rendus (`window.__INITIAL_DATA__`, `window.runParams`, etc.) pour récupérer les informations B2B complètes sans dépendance à un navigateur headless lourd.
2. **Normalisation des Paliers Tarifaires :**
   - Les structures de prix B2B (qui varient selon les tranches de quantité) sont uniformisées et converties en objets typés exploitables directement par les LLM.
3. **Protection Réseau & TLS :**
   - Utilisation de `curl_cffi` avec émulation des empreintes de navigateurs modernes (Chrome) pour contourner les protections CDN.
4. **Gestion de Cadence :**
   - Verrou asynchrone (`REQUEST_QUEUE_LOCK`) évitant les surcharges de requêtes simultanées.

---

## 📦 Prérequis & Installation

- **Python :** Version 3.10 ou supérieure.
- **Système d'exploitation :** Linux, macOS ou Windows.

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/votre-compte/MCP-Alibaba.git
cd MCP-Alibaba

# 2. Créer l'environnement virtuel Python
python3 -m venv .venv

# 3. Activer l'environnement virtuel
# Sur Linux / macOS :
source .venv/bin/activate
# Sur Windows :
# .venv\Scripts\activate

# 4. Installer les dépendances en mode éditable
pip install --upgrade pip
pip install -e .
```

---

## 🚀 Modes d'Exécution & Configuration

### 1. Mode local standard : stdio (Claude Desktop / Cursor)

#### Configuration pour Claude Desktop

Ouvrez le fichier de configuration de Claude Desktop :
- **macOS :** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows :** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux :** `~/.config/Claude/claude_desktop_config.json`

Ajoutez la section suivante :

```json
{
  "mcpServers": {
    "alibaba-fr": {
      "command": "/chemin/absolu/vers/MCP-Alibaba/.venv/bin/alibaba-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

Redémarrez ensuite Claude Desktop.

#### Configuration pour Claude Code (CLI)

```bash
claude mcp add alibaba-fr -- /chemin/absolu/vers/MCP-Alibaba/.venv/bin/alibaba-mcp --transport stdio
```

---

### 2. Mode serveur HTTP : Streamable HTTP / SSE (ChatGPT / Accès distant)

Pour connecter le serveur à **ChatGPT** (menu *Plugins / Serveurs MCP*) ou pour l'héberger sur un serveur distant derrière un reverse-proxy HTTPS :

```bash
python run_http.py
```

Par défaut, le serveur écoute sur `http://127.0.0.1:8002/mcp/alibaba`.

#### Exemple de service systemd (Linux)

```ini
[Unit]
Description=Serveur MCP Alibaba FR
After=network.target

[Service]
Type=simple
User=votre_utilisateur
WorkingDirectory=/chemin/vers/MCP-Alibaba
Environment="MCP_HOST=127.0.0.1"
Environment="MCP_PORT=8002"
Environment="MCP_PATH=/mcp/alibaba"
Environment="MCP_PUBLIC_HOST=localhost"
ExecStart=/chemin/vers/MCP-Alibaba/.venv/bin/python /chemin/vers/MCP-Alibaba/run_http.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## ⚙️ Variables d'Environnement

| Variable | Défaut | Description |
| :--- | :--- | :--- |
| `MCP_HOST` | `127.0.0.1` | Adresse IP d'écoute en mode HTTP. |
| `MCP_PORT` | `8002` | Port d'écoute en mode HTTP. |
| `MCP_PATH` | `/mcp/alibaba` | Préfixe du chemin HTTP pour l'endpoint MCP. |
| `MCP_PUBLIC_HOST` | `localhost` | Nom d'hôte public attendu dans les en-têtes HTTP (protection anti-rebinding). |
| `LOG_LEVEL` | `INFO` | Niveau de journalisation (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

---

## 🧪 Tests & Validation

Suite de tests automatisés :

```bash
# Tester le scraper (recherche B2B, filtres MOQ, fiches techniques)
python tests/test_scraper.py

# Tester le serveur MCP et les outils
python tests/test_server_mcp.py
```

---

## 📚 Bibliothèques & Références

Ce projet s'appuie sur les bibliothèques suivantes :

- **[Model Context Protocol SDK (`mcp`)](https://github.com/modelcontextprotocol/python-sdk)** : SDK officiel Anthropic pour l'interopérabilité IA.
- **[curl_cffi](https://github.com/yifeikong/curl_cffi)** : Client HTTP Python avec support de l'émulation TLS et gestion de sessions avancée.
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** : Parsing et navigation dans le DOM HTML.
- **[Pydantic v2](https://github.com/pydantic/pydantic)** : Typage strict des modèles de données et validation de schémas.
- **[Uvicorn](https://www.uvicorn.org/) & [Starlette](https://www.starlette.io/)** : Moteur ASGI pour le transport Streamable HTTP.

---

## ⚖️ Licence & Avertissement

- Publié sous **Licence MIT**.
- **Avertissement :** Ce projet est un outil indépendant et n'a aucun lien officiel avec *Alibaba Group*. Il doit être utilisé de manière responsable à des fins de veille commerciale, d'analyse de marché ou d'assistance au sourcing.
