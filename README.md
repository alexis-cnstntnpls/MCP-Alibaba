# MCP-Alibaba (France)

Serveur MCP (Model Context Protocol) dédié au **sourcing B2B sur Alibaba France** (`french.alibaba.com`), avec prix de gros en euros (€) et recherche de fabricants vérifiés.

Permet à Claude Desktop, Cursor et aux Custom GPTs de ChatGPT de rechercher des grossistes et usines, de filtrer par MOQ (quantités minimales de commande) et de consulter les fiches techniques des produits.

---

## Fonctionnalités

1. **`search_alibaba_products`** :
   - Recherche par mots-clés en français.
   - Filtre par quantité minimum de commande (`max_moq`, ex: 10 ou 50 pour petites commandes).
   - Filtre fournisseurs vérifiés (`verified_only=True` pour Gold Suppliers certifiés).
   - Filtre budget unitaire (`min_price`, `max_price`).
   - Tri : `default`, `price_asc`, `price_desc`, `moq_asc`, `rating_desc`.
   - Données retournées : ID produit, titre complet, fourchette de prix EUR, MOQ textuel et numérique, profil fabricant (nom, pays, années Gold, note, nombre d'avis), option OEM/personnalisation et lien direct.

2. **`get_alibaba_product_details`** :
   - Fiche technique complète d'un produit (spécifications détaillées, matériaux, puissance, dimensions).
   - Profil usine du fournisseur (type d'entreprise, taux de livraison dans les délais, temps de réponse).
   - Évaluations détaillées (score qualité produit, délai d'expédition, service client).
   - Galerie photos HD.

3. **Protection & Résilience** :
   - Utilise `curl_cffi` avec émulation d'empreinte TLS/JA3/JA4 Chrome 124+.
   - Cookie de localisation `sc_g_cfg_f` pour forcer la France et l'EUR.
   - File d'attente sérialisée avec temporisation aléatoire (`0.4s` - `0.9s`).

---

## Installation locale

```bash
git clone https://github.com/votre-user/MCP-Alibaba.git && cd MCP-Alibaba && python3 -m venv .venv && .venv/bin/pip install -e .
```

---

## Lancement

### Mode stdio (Claude Desktop / Cursor)

```bash
/home/alexis/MCP-Alibaba/.venv/bin/alibaba-mcp --transport stdio
```

### Mode HTTP / SSE (Agent distant / ChatGPT sur port 8002)

```bash
/home/alexis/MCP-Alibaba/.venv/bin/alibaba-mcp --transport sse --host 0.0.0.0 --port 8002
```

---

## Configuration Claude Desktop

Ajoutez dans votre fichier `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "alibaba-fr": {
      "command": "/home/alexis/MCP-Alibaba/.venv/bin/alibaba-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

---

## Tests locaux

```bash
/home/alexis/MCP-Alibaba/.venv/bin/python /home/alexis/MCP-Alibaba/tests/test_scraper.py
```

```bash
/home/alexis/MCP-Alibaba/.venv/bin/python /home/alexis/MCP-Alibaba/tests/test_server_mcp.py
```
