"""Serveur MCP Alibaba FR : sourcing B2B, recherche de grossistes/fabricants et fiches techniques.

Expose les outils MCP pour Claude Desktop, Cursor et agents ChatGPT :
- search_alibaba_products : recherche par mots-clés, filtres de prix, MOQ (quantité min.) et fournisseurs vérifiés
- get_alibaba_product_details : fiche technique complète, paliers de prix, coordonnées usine et garanties
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Annotated, Any, Literal

import anyio.to_thread
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .scraper import AlibabaScraper

logger = logging.getLogger("alibaba_mcp")
logger.setLevel(logging.INFO)

INSTRUCTIONS = """\
Serveur MCP officiel pour Alibaba France (sourcing B2B, prix de gros en euros, fabricants et grossistes).

Outils disponibles :
- search_alibaba_products : Recherche d'offres de gros avec filtres de prix, MOQ (quantité minimum) et fournisseurs vérifiés.
- get_alibaba_product_details : Fiche détaillée d'un produit avec spécifications techniques complètes, paliers tarifaires et profil usine.
"""

mcp = MCPServer(name="Alibaba FR", instructions=INSTRUCTIONS)
scraper = AlibabaScraper()

# Verrou pour sérialiser les requêtes (queue FIFO) et temporisation humaine
REQUEST_QUEUE_LOCK = asyncio.Lock()
READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)


async def _human_paced_call(func, *args, **kwargs):
    """Exécute un appel bloquant de manière sérialisée avec un léger délai aléatoire."""
    async with REQUEST_QUEUE_LOCK:
        jitter = random.uniform(0.4, 0.9)
        await asyncio.sleep(jitter)
        try:
            return await anyio.to_thread.run_sync(lambda: func(*args, **kwargs))
        except Exception as exc:
            logger.error(f"Erreur d'exécution Alibaba: {exc}")
            raise ToolError(f"Erreur Alibaba: {exc}") from None


@mcp.tool(
    name="search_alibaba_products",
    title="Rechercher des produits de gros et fournisseurs sur Alibaba FR",
    annotations=READ_ONLY,
)
async def search_alibaba_products(
    ctx: Context,
    query: Annotated[
        str,
        Field(description="Mots-clés de recherche B2B en français (ex: 'esp32', 'panneau solaire', 'batterie lifepo4')."),
    ],
    page: Annotated[
        int,
        Field(ge=1, le=50, description="Numéro de page de résultats (défaut: 1)."),
    ] = 1,
    min_price: Annotated[
        float | None,
        Field(ge=0, description="Prix unitaire minimum en euros (€)."),
    ] = None,
    max_price: Annotated[
        float | None,
        Field(ge=0, description="Prix unitaire maximum en euros (€)."),
    ] = None,
    max_moq: Annotated[
        int | None,
        Field(ge=1, description="Quantité minimum de commande maximale (ex: 50 pour filtrer les offres accessibles en petite quantité)."),
    ] = None,
    verified_only: Annotated[
        bool,
        Field(description="Filtrer uniquement les fournisseurs certifiés 'Gold Supplier' vérifiés."),
    ] = False,
    sort: Annotated[
        Literal["default", "price_asc", "price_desc", "moq_asc", "rating_desc"],
        Field(description="Critère de tri : 'default', 'price_asc' (prix croissant), 'price_desc' (prix décroissant), 'moq_asc' (plus faible quantité min.), 'rating_desc' (meilleure note fournisseur)."),
    ] = "default",
) -> dict[str, Any]:
    """Recherche des produits de gros et fabricants sur Alibaba France avec MOQ, filtres de prix et certification usine."""
    res = await _human_paced_call(
        scraper.search_products,
        query=query,
        page=page,
        min_price=min_price,
        max_price=max_price,
        max_moq=max_moq,
        verified_only=verified_only,
        sort=sort,
    )
    return res.model_dump()


@mcp.tool(
    name="get_alibaba_product_details",
    title="Obtenir la fiche technique et les informations fabricant d'un article Alibaba",
    annotations=READ_ONLY,
)
async def get_alibaba_product_details(
    ctx: Context,
    product_id_or_url: Annotated[
        str,
        Field(description="Identifiant numérique (ex: '60824135633') ou URL de la fiche produit Alibaba."),
    ],
) -> dict[str, Any]:
    """Récupère les détails complets, spécifications techniques, tarifs de gros et profil de l'usine fournisseur."""
    res = await _human_paced_call(scraper.get_product_details, product_id_or_url)
    return res.model_dump()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Serveur MCP Alibaba FR")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Protocole de transport (stdio pour CLI/Claude Desktop, sse pour HTTP)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Adresse d'écoute pour le mode HTTP/SSE")
    parser.add_argument("--port", type=int, default=8002, help="Port d'écoute HTTP/SSE (défaut: 8002)")
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
