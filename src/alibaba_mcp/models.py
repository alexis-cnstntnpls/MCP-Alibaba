from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AlibabaSupplier(BaseModel):
    name: str = Field(..., description="Nom de l'entreprise ou de l'usine fournisseur")
    country: Optional[str] = Field(None, description="Pays d'enregistrement du fournisseur (ex: 'CN', 'US', 'FR')")
    gold_years: Optional[int] = Field(None, description="Nombre d'années en tant que 'Gold Supplier' vérifié")
    rating: Optional[float] = Field(None, description="Note moyenne du fournisseur sur 5 étoiles")
    review_count: Optional[int] = Field(None, description="Nombre total d'avis clients reçus par le fournisseur")
    store_url: Optional[str] = Field(None, description="URL de la vitrine / usine du fournisseur")
    business_type: Optional[str] = Field(None, description="Type d'activité (ex: Fabricant, Société commerciale)")
    response_time: Optional[str] = Field(None, description="Temps moyen de réponse du fournisseur")
    on_time_delivery_rate: Optional[str] = Field(None, description="Taux de livraison dans les délais (ex: '98.5%')")


class AlibabaProductSummary(BaseModel):
    product_id: str = Field(..., description="Identifiant unique de l'offre Alibaba")
    title: str = Field(..., description="Titre descriptif du produit en français")
    price_formatted: str = Field(..., description="Fourchette de prix de gros affichée (ex: '1,71-2,76 €')")
    min_price_eur: Optional[float] = Field(None, description="Prix unitaire minimum en euros")
    max_price_eur: Optional[float] = Field(None, description="Prix unitaire maximum en euros")
    moq_raw: Optional[str] = Field(None, description="Quantité minimum de commande textuelle (ex: 'Quantité min. : 50 pièces')")
    moq_units: Optional[int] = Field(None, description="Quantité minimum de commande numérique (MOQ)")
    supplier: AlibabaSupplier = Field(..., description="Informations sur le fabricant / grossiste")
    image_url: Optional[str] = Field(None, description="URL de l'image principale")
    product_url: str = Field(..., description="Lien direct vers la fiche de l'offre")
    customizable: bool = Field(False, description="Personnalisation OEM/ODM disponible (logo, packaging...)")


class AlibabaSearchResponse(BaseModel):
    query: str
    page: int
    total_results: int
    products: List[AlibabaProductSummary]


class AlibabaProductDetail(BaseModel):
    product_id: str
    title: str
    price_range_text: Optional[str] = None
    moq: Optional[int] = None
    unit: Optional[str] = None
    supplier: AlibabaSupplier
    specifications: Dict[str, str] = Field(default_factory=dict, description="Spécifications techniques complètes du fabricant")
    ratings: Dict[str, Any] = Field(default_factory=dict, description="Évaluations qualité, délais et service fournisseur")
    gallery_images: List[str] = Field(default_factory=list, description="Photos haute résolution de l'article")
    product_url: str
