import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from curl_cffi import requests

from .models import (
    AlibabaProductDetail,
    AlibabaProductSummary,
    AlibabaSearchResponse,
    AlibabaSupplier,
)

logger = logging.getLogger("alibaba_mcp")
logger.setLevel(logging.INFO)


class AlibabaScraper:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session(impersonate="chrome124")
        # Cookie pour forcer la région France, la langue française et la devise EUR
        self.session.cookies.set(
            "sc_g_cfg_f",
            "sc_b_site=FR&sc_b_locale=fr_FR&sc_b_currency=EUR",
            domain=".alibaba.com",
        )
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def _extract_offer_list_json(self, html: str) -> Optional[Dict[str, Any]]:
        """Extrait le bloc JSON _offer_list du HTML de recherche Alibaba."""
        target = "._offer_list = {"
        idx = html.find(target)
        if idx == -1:
            return None

        b_idx = html.find("{", idx)
        if b_idx == -1:
            return None

        depth = 0
        for i in range(b_idx, len(html)):
            char = html[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[b_idx : i + 1])
                    except Exception as e:
                        logger.warning(f"Erreur parsing JSON _offer_list: {e}")
                        return None
        return None

    def _extract_detail_data_json(self, html: str) -> Optional[Dict[str, Any]]:
        """Extrait le bloc JSON window.detailData du HTML de détail produit."""
        target = "window.detailData ="
        idx = html.find(target)
        if idx == -1:
            return None

        b_idx = html.find("{", idx)
        if b_idx == -1:
            return None

        depth = 0
        for i in range(b_idx, len(html)):
            char = html[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[b_idx : i + 1])
                    except Exception as e:
                        logger.warning(f"Erreur parsing JSON detailData: {e}")
                        return None
        return None

    def _format_url(self, url: Any) -> Optional[str]:
        if not url:
            return None
        if isinstance(url, dict):
            url = url.get("original") or url.get("big") or url.get("imageUrl") or url.get("url") or str(url)
        if not isinstance(url, str):
            return None
        if url.startswith("//"):
            return f"https:{url}"
        return url

    def _parse_prices(self, price_str: Optional[str]) -> tuple[Optional[float], Optional[float]]:
        if not price_str:
            return None, None
        clean = price_str.replace("\xa0", " ").replace("€", "").strip()
        nums = re.findall(r"(\d+(?:[.,]\d+)?)", clean)
        if not nums:
            return None, None
        try:
            parsed = [float(n.replace(",", ".")) for n in nums]
            return min(parsed), max(parsed)
        except Exception:
            return None, None

    def _parse_moq(self, moq_str: Optional[str]) -> Optional[int]:
        if not moq_str:
            return None
        m = re.search(r"(\d+[\d\s,]*)", moq_str)
        if m:
            clean_digits = re.sub(r"[^\d]", "", m.group(1))
            if clean_digits:
                try:
                    return int(clean_digits)
                except ValueError:
                    return None
        return None

    def search_products(
        self,
        query: str,
        page: int = 1,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_moq: Optional[int] = None,
        verified_only: bool = False,
        sort: str = "default",
    ) -> AlibabaSearchResponse:
        """
        Recherche des produits et fournisseurs B2B sur Alibaba France.
        """
        clean_kw = "-".join(re.sub(r"[^\w\s-]", "", query).split())
        if not clean_kw:
            clean_kw = quote(query)

        url = f"https://french.alibaba.com/products/{clean_kw}.html"
        params: Dict[str, Any] = {}
        if page > 1:
            params["page"] = page

        resp = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
        if resp.status_code != 200 or "punish" in resp.text or "nocaptcha" in resp.text:
            logger.warning(f"Recherche Alibaba bloquée ou statut {resp.status_code}")
            return AlibabaSearchResponse(query=query, page=page, total_results=0, products=[])

        data = self._extract_offer_list_json(resp.text)
        if not data:
            return AlibabaSearchResponse(query=query, page=page, total_results=0, products=[])

        offer_result = data.get("offerResultData", {})
        total_count = offer_result.get("totalCount", 0)
        offers_raw = offer_result.get("offers", [])

        products: List[AlibabaProductSummary] = []
        for o in offers_raw:
            pid = str(o.get("id") or o.get("productId") or "")
            if not pid:
                continue

            title = o.get("title") or o.get("enPureTitle") or "Article sans titre"
            price_formatted = o.get("price") or o.get("priceV2") or "Sur devis"
            min_p, max_p = self._parse_prices(price_formatted)

            moq_raw = o.get("moqV2")
            moq_units = self._parse_moq(moq_raw)

            gold_years_raw = o.get("goldSupplierYears")
            gold_years = None
            if gold_years_raw:
                try:
                    gold_years = int(re.sub(r"[^\d]", "", str(gold_years_raw)))
                except ValueError:
                    pass

            score_raw = o.get("reviewScore")
            score = float(score_raw) if score_raw is not None else None

            rev_count_raw = o.get("reviewCount")
            rev_count = int(rev_count_raw) if rev_count_raw is not None else None

            supplier = AlibabaSupplier(
                name=o.get("companyName") or "Fournisseur non spécifié",
                country=o.get("countryCode"),
                gold_years=gold_years,
                rating=score,
                review_count=rev_count,
                store_url=self._format_url(o.get("supplierHref")),
            )

            # Filtres
            if verified_only and (not gold_years or gold_years < 1):
                continue

            if max_moq is not None and moq_units is not None and moq_units > max_moq:
                continue

            if min_price is not None and min_p is not None and min_p < min_price:
                continue

            if max_price is not None and max_p is not None and max_p > max_price:
                continue

            img_url = self._format_url(o.get("mainImage"))
            prod_url = o.get("productUrl") or f"https://www.alibaba.com/product-detail/{pid}.html"
            customizable = bool(o.get("customizable"))

            products.append(
                AlibabaProductSummary(
                    product_id=pid,
                    title=title,
                    price_formatted=price_formatted,
                    min_price_eur=min_p,
                    max_price_eur=max_p,
                    moq_raw=moq_raw,
                    moq_units=moq_units,
                    supplier=supplier,
                    image_url=img_url,
                    product_url=prod_url,
                    customizable=customizable,
                )
            )

        # Tri
        if sort == "price_asc":
            products.sort(key=lambda x: (x.min_price_eur is None, x.min_price_eur or 0.0))
        elif sort == "price_desc":
            products.sort(key=lambda x: (x.max_price_eur is None, x.max_price_eur or 0.0), reverse=True)
        elif sort == "moq_asc":
            products.sort(key=lambda x: (x.moq_units is None, x.moq_units or 0))
        elif sort == "rating_desc":
            products.sort(key=lambda x: (x.supplier.rating is None, x.supplier.rating or 0.0), reverse=True)

        return AlibabaSearchResponse(
            query=query,
            page=page,
            total_results=len(products),
            products=products,
        )

    def get_product_details(self, product_id_or_url: str) -> AlibabaProductDetail:
        """
        Récupère les détails complets d'un article Alibaba avec repli de recherche si nécessaire.
        """
        id_match = re.search(r"(\d{9,20})", product_id_or_url)
        if not id_match:
            raise ValueError(f"Impossible d'extraire l'ID produit de: {product_id_or_url}")

        pid = id_match.group(1)
        url = f"https://french.alibaba.com/p-detail/detail-{pid}.html"

        try:
            resp = self.session.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200 and "nocaptcha" not in resp.text and "punish" not in resp.text:
                data = self._extract_detail_data_json(resp.text)
                if data:
                    global_data = data.get("globalData", {})
                    prod = global_data.get("product", {})
                    seller = global_data.get("seller", {})
                    review_data = global_data.get("review", {})

                    title = prod.get("subject") or f"Article {pid}"
                    price_obj = prod.get("price", {})
                    range_prices = price_obj.get("productRangePrices", {})
                    price_range_text = range_prices.get("priceRangeText") or "Sur devis"
                    unit = price_obj.get("unit") or "pièce"

                    moq = prod.get("moq")
                    if moq is not None:
                        try:
                            moq = int(moq)
                        except (ValueError, TypeError):
                            moq = None

                    specs: Dict[str, str] = {}
                    for prop in prod.get("productBasicProperties", []):
                        name = prop.get("attrName")
                        val = prop.get("attrValue")
                        if name and val:
                            specs[name.strip()] = str(val).strip()

                    supplier_rev = seller.get("supplierRatingReviews", {})
                    avg_score = supplier_rev.get("averageStar")
                    total_orders = supplier_rev.get("totalReviewOrderCount")

                    supplier = AlibabaSupplier(
                        name=seller.get("companyName") or "Fournisseur non spécifié",
                        country=seller.get("companyRegisterCountry"),
                        gold_years=seller.get("companyJoinYears"),
                        rating=float(avg_score) if avg_score else None,
                        review_count=int(total_orders) if total_orders else None,
                        store_url=self._format_url(seller.get("homeUrl")),
                        business_type=seller.get("companyBusinessType"),
                        response_time=seller.get("responseTimeText"),
                        on_time_delivery_rate=seller.get("supplierOnTimeDeliveryRate"),
                    )

                    ratings: Dict[str, Any] = {}
                    prod_rev = review_data.get("productReview", {})
                    if prod_rev.get("averageStar") is not None:
                        ratings["product_score"] = prod_rev.get("averageStar")
                        ratings["product_review_count"] = prod_rev.get("totalReviewCount")

                    for lat in supplier_rev.get("latitudeScoreDTOList", []):
                        lat_type = lat.get("latitudeType")
                        lat_score = lat.get("latitudeAverageScore")
                        if lat_type and lat_score:
                            ratings[lat_type] = float(lat_score)

                    gallery: List[str] = []
                    for media in prod.get("mediaItems", []):
                        img_u = self._format_url(media.get("imageUrl"))
                        if img_u and img_u not in gallery:
                            gallery.append(img_u)

                    return AlibabaProductDetail(
                        product_id=pid,
                        title=title,
                        price_range_text=price_range_text,
                        moq=moq,
                        unit=unit,
                        supplier=supplier,
                        specifications=specs,
                        ratings=ratings,
                        gallery_images=gallery,
                        product_url=f"https://www.alibaba.com/product-detail/{pid}.html",
                    )
        except Exception as e:
            logger.debug(f"Erreur tentative accès direct p-detail {pid}: {e}")

        # Repli de recherche ciblée par ID
        logger.info(f"Repli recherche catalogue pour l'ID {pid}")
        search_res = self.search_products(pid, page=1)
        matched = next((p for p in search_res.products if p.product_id == pid), None)
        if not matched and search_res.products:
            matched = search_res.products[0]

        if matched:
            gallery = [matched.image_url] if matched.image_url else []
            return AlibabaProductDetail(
                product_id=matched.product_id,
                title=matched.title,
                price_range_text=matched.price_formatted,
                moq=matched.moq_units,
                unit="pièce",
                supplier=matched.supplier,
                specifications={"Quantité min.": matched.moq_raw or "N/A"},
                ratings={"fournisseur_note": matched.supplier.rating} if matched.supplier.rating else {},
                gallery_images=gallery,
                product_url=matched.product_url,
            )

        raise RuntimeError(f"Impossible de récupérer les détails de l'article Alibaba {pid}")
