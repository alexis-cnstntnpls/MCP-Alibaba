import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from alibaba_mcp.scraper import AlibabaScraper


def test_alibaba_scraper():
    scraper = AlibabaScraper()

    print("=== TEST 1: RECHERCHE B2B ALIBABA FR (ESP32) ===")
    res = scraper.search_products("esp32", page=1, verified_only=True)
    print(f"Recherche ESP32: {res.total_results} offres trouvées (fournisseurs vérifiés)")
    assert res.total_results > 0, "Aucun produit trouvé"

    first = res.products[0]
    print(f"Offre 1: {first.title[:65]}...")
    print(f"  Prix: {first.price_formatted} (min: {first.min_price_eur}€, max: {first.max_price_eur}€)")
    print(f"  MOQ: {first.moq_raw} (unités: {first.moq_units})")
    print(f"  Fournisseur: {first.supplier.name} ({first.supplier.country}, {first.supplier.gold_years} ans Gold)")
    print(f"  Note: {first.supplier.rating}/5 ({first.supplier.review_count} avis)")
    print(f"  Personnalisable (OEM): {first.customizable}")
    print(f"  URL: {first.product_url}")

    test_pid = first.product_id

    print(f"\n=== TEST 2: FICHE TECHNIQUE COMPLÈTE ({test_pid}) ===")
    detail = scraper.get_product_details(test_pid)
    print(f"Titre: {detail.title[:70]}...")
    print(f"Paliers de prix: {detail.price_range_text} par {detail.unit}")
    print(f"MOQ: {detail.moq} {detail.unit}s")
    print(f"Fabricant: {detail.supplier.name} ({detail.supplier.business_type or 'Usine'})")
    print(f"Photos HD: {len(detail.gallery_images)} images")
    print(f"Spécifications techniques ({len(detail.specifications)} attributs) :")
    for k, v in list(detail.specifications.items())[:6]:
        print(f"  - {k} : {v}")

    print("\n TOUS LES TESTS ALIBABA SONT PASSÉS AVEC SUCCÈS !")


if __name__ == "__main__":
    test_alibaba_scraper()
