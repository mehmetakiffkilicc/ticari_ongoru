"""Explainable Customer 360 analytics built on accepted movement records.

This module intentionally has no write side effects. It can be wired into the shared
engine dispatcher as ``customer_analytics`` and ``customer_detail`` actions.
Purchasing invoices are excluded through the canonical invoice semantics.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from contextlib import closing
from datetime import date, datetime, timedelta
from statistics import median
from typing import Any

from analysis import engine


WINDOW_DAYS = 90


def _number(value: Any) -> float:
    try:
        number = float(value or 0)
        return number if math.isfinite(number) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _day(value: Any) -> date | None:
    try:
        return datetime.fromisoformat(str(value)).date()
    except (TypeError, ValueError):
        return None


def _latest_rows() -> tuple[list[dict[str, Any]], str | None]:
    with closing(engine.db()) as con:
        batch = con.execute(
            "SELECT id FROM batches WHERE kind='movement' ORDER BY created DESC LIMIT 1"
        ).fetchone()
        if not batch:
            return [], None
        rows = [json.loads(row["converted"]) for row in con.execute(
            "SELECT converted FROM records WHERE kind='movement' AND batch_id=?", (batch["id"],)
        )]
    return rows, str(batch["id"])


def _quantile(values: list[float], ratio: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    position = (len(ordered) - 1) * ratio
    lo, hi = math.floor(position), math.ceil(position)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - position) + ordered[hi] * (position - lo)


def _signed(row: dict[str, Any], field: str) -> float:
    value = _number(row.get(field))
    # A loss on a sale is still a loss; only return amounts use magnitude normalization.
    if field == "Satir Kari" and engine.invoice_kind(row) == "sale":
        return value
    value = abs(value)
    return -value if engine.invoice_kind(row) == "return" else value


def _severity_score(severity: str, impact: float, reference: float, confidence: str) -> tuple[int, dict[str, int]]:
    severity_component = {"info": 25, "attention": 50, "high": 72, "critical": 90}[severity]
    impact_component = min(100, round(abs(impact) / max(abs(reference), 1) * 100))
    confidence_component = {"Düşük": 45, "Orta": 70, "Yüksek": 92}.get(confidence, 70)
    score = round(severity_component * .5 + impact_component * .3 + confidence_component * .2)
    return score, {"severity": severity_component, "impact": impact_component, "confidence": confidence_component}


def _tag(code: str, name: str, severity: str, observed: float | None, reference: float | None,
         impact: float, confidence: str, current: tuple[date, date], previous: tuple[date, date],
         explanation: str, action: str) -> dict[str, Any]:
    score, breakdown = _severity_score(severity, impact, reference or 0, confidence)
    return {
        "code": code, "name": name, "severity": severity, "score": score, "confidence": confidence,
        "explanation": explanation, "recommendedAction": action, "scoreBreakdown": breakdown,
        "evidence": {
            "observed": None if observed is None else round(observed, 2),
            "reference": None if reference is None else round(reference, 2),
            "impact": round(impact, 2),
            "currentPeriod": [current[0].isoformat(), current[1].isoformat()],
            "previousPeriod": [previous[0].isoformat(), previous[1].isoformat()],
        },
    }


def _build(data: dict[str, Any]) -> dict[str, Any]:
    raw_rows, batch_id = _latest_rows()
    sales_rows = [row for row in raw_rows if engine.invoice_kind(row) in ("sale", "return") and _day(row.get("Fatura Tarihi"))]
    if not sales_rows:
        return {"status": "no_data", "customers": [], "options": {"segments": [], "cities": []}}

    maximum = max(_day(row["Fatura Tarihi"]) for row in sales_rows)
    requested = _day(data.get("analysisDate")) or maximum
    analysis_date = min(requested, maximum)
    current = (analysis_date - timedelta(days=WINDOW_DAYS - 1), analysis_date)
    previous = (analysis_date - timedelta(days=WINDOW_DAYS * 2 - 1), analysis_date - timedelta(days=WINDOW_DAYS))
    sales_rows = [row for row in sales_rows if _day(row["Fatura Tarihi"]) <= analysis_date]

    groups: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "name": "Bilinmiyor", "city": "Bilinmiyor", "country": "Bilinmiyor", "seller": "Bilinmiyor",
        "rows": [], "saleDates": [], "invoiceDates": {}, "allSales": 0.0, "allProfit": 0.0,
        "allReturns": 0.0, "currentSales": 0.0, "previousSales": 0.0, "currentProfit": 0.0,
        "currentReturns": 0.0, "previousReturns": 0.0, "currentInvoices": set(), "previousInvoices": set(),
        "currentProducts": set(), "previousProducts": set(), "currentProductSales": defaultdict(float),
        "historicBeforePrevious": False,
    })
    for row in sales_rows:
        customer_code = str(row.get("Müsteri Kodu") or "Bilinmiyor").strip() or "Bilinmiyor"
        g = groups[customer_code]
        g["name"] = str(row.get("Müsteri Ünvani") or g["name"] or customer_code)
        g["city"] = str(row.get("Sehir") or g["city"])
        g["country"] = str(row.get("Ülke") or g["country"])
        g["seller"] = str(row.get("Satici") or g["seller"])
        g["rows"].append(row)
        day = _day(row["Fatura Tarihi"])
        kind = engine.invoice_kind(row)
        amount, profit = _signed(row, "Net Satir Tutari"), _signed(row, "Satir Kari")
        g["allSales"] += amount
        g["allProfit"] += profit
        if kind == "return":
            g["allReturns"] += abs(_number(row.get("Net Satir Tutari")))
        if kind == "sale":
            invoice = str(row.get("Fatura No") or f"satir-{len(g['rows'])}")
            g["invoiceDates"][invoice] = day
            g["saleDates"].append(day)
        if current[0] <= day <= current[1]:
            g["currentSales"] += amount
            g["currentProfit"] += profit
            if kind == "return":
                g["currentReturns"] += abs(_number(row.get("Net Satir Tutari")))
            else:
                g["currentInvoices"].add(str(row.get("Fatura No") or day))
                product = str(row.get("Malzeme Kodu") or "Bilinmiyor")
                g["currentProducts"].add(product)
                g["currentProductSales"][product] += abs(_number(row.get("Net Satir Tutari")))
        elif previous[0] <= day <= previous[1]:
            g["previousSales"] += amount
            if kind == "return":
                g["previousReturns"] += abs(_number(row.get("Net Satir Tutari")))
            else:
                g["previousInvoices"].add(str(row.get("Fatura No") or day))
                g["previousProducts"].add(str(row.get("Malzeme Kodu") or "Bilinmiyor"))
        elif day < previous[0] and kind == "sale":
            g["historicBeforePrevious"] = True

    current_total = sum(max(0, g["currentSales"]) for g in groups.values())
    previous_total = sum(max(0, g["previousSales"]) for g in groups.values())
    changes = []
    for g in groups.values():
        current_share = max(0, g["currentSales"]) / current_total * 100 if current_total else 0
        previous_share = max(0, g["previousSales"]) / previous_total * 100 if previous_total else 0
        changes.append(current_share - previous_share)
        g["currentShare"], g["previousShare"], g["shareDelta"] = current_share, previous_share, current_share - previous_share
    grow_cut, shrink_cut = _quantile(changes, .8), _quantile(changes, .2)
    monetary_values = [max(0, g["currentSales"]) for g in groups.values()]
    frequency_values = [len(g["currentInvoices"]) for g in groups.values()]
    monetary_hi, frequency_hi = _quantile(monetary_values, .8), _quantile(frequency_values, .8)

    customers = []
    for code, g in groups.items():
        invoice_days = sorted(set(g["invoiceDates"].values()))
        last_sale = max(g["saleDates"]) if g["saleDates"] else None
        first_sale = min(g["saleDates"]) if g["saleDates"] else None
        recency = (analysis_date - last_sale).days if last_sale else None
        gaps = [(right - left).days for left, right in zip(invoice_days, invoice_days[1:])]
        cadence = median(gaps) if gaps else None
        late_threshold = max(30, round(cadence * 1.5)) if cadence else 60
        lost_threshold = max(60, round(cadence * 2.5)) if cadence else 120
        overdue = max(0, (recency or 0) - late_threshold)
        if recency is None or recency > lost_threshold:
            lifecycle = "Kayıp riski"
        elif recency > late_threshold:
            lifecycle = "Geciken"
        elif g["currentSales"] > 0 and not g["previousInvoices"] and g["historicBeforePrevious"]:
            lifecycle = "Geri kazanılan"
        elif first_sale and first_sale >= current[0]:
            lifecycle = "Yeni"
        elif g["shareDelta"] >= grow_cut and g["shareDelta"] > 0:
            lifecycle = "Büyüyen"
        elif g["shareDelta"] <= shrink_cut and g["shareDelta"] < 0:
            lifecycle = "Küçülen"
        else:
            lifecycle = "Aktif"

        r_score = 5 if (recency or 9999) <= 14 else 4 if recency <= 30 else 3 if recency <= 60 else 2 if recency <= 90 else 1
        f_score = 5 if len(g["currentInvoices"]) >= max(4, frequency_hi) else 4 if len(g["currentInvoices"]) >= 3 else 3 if len(g["currentInvoices"]) >= 2 else 2 if len(g["currentInvoices"]) == 1 else 1
        m_score = 5 if g["currentSales"] >= monetary_hi and monetary_hi else 4 if g["currentSales"] >= monetary_hi * .6 and monetary_hi else 3 if g["currentSales"] > 0 else 1
        top_product_share = max(g["currentProductSales"].values(), default=0) / g["currentSales"] * 100 if g["currentSales"] > 0 else 0
        tags = []
        confidence = "Yüksek" if len(invoice_days) >= 4 else "Orta" if len(invoice_days) >= 2 else "Düşük"
        if lifecycle == "Kayıp riski":
            tags.append(_tag("CUSTOMER_LOSS_RISK", "Kayıp riski", "critical", recency, lost_threshold, g["previousSales"], confidence, current, previous, f"Son satıştan beri {recency} gün geçti; müşterinin kayıp eşiği {lost_threshold} gün.", "Müşteriyle temas kurun ve son ürün/sepet örüntüsüne göre geri kazanım teklifi hazırlayın."))
        elif lifecycle == "Geciken":
            tags.append(_tag("CUSTOMER_OVERDUE", "Alışverişi gecikti", "high", recency, late_threshold, g["previousSales"], confidence, current, previous, f"Beklenen alışveriş ritmi {cadence or 'hesaplanamadı'} gün; gecikme {overdue} gün.", "Satıcıya hatırlatma aksiyonu atayın ve müşterinin son siparişini kontrol edin."))
        if lifecycle == "Yeni":
            tags.append(_tag("CUSTOMER_NEW", "Yeni müşteri", "info", (analysis_date-first_sale).days if first_sale else 0, WINDOW_DAYS, g["currentSales"], confidence, current, previous, "İlk doğrulanmış satış güncel 90 günlük pencere içinde.", "İkinci siparişi hızlandıracak tamamlayıcı ürün önerisi hazırlayın."))
        if lifecycle == "Geri kazanılan":
            tags.append(_tag("CUSTOMER_REACTIVATED", "Geri kazanılan", "info", g["currentSales"], 0, g["currentSales"], confidence, current, previous, "Önceki 90 günde satış yokken daha eski geçmişten sonra yeniden satış oluştu.", "Geri dönüş nedenini doğrulayın ve süreklilik için takip tarihi belirleyin."))
        if g["shareDelta"] >= grow_cut and g["shareDelta"] > 0:
            tags.append(_tag("CUSTOMER_GROWING", "Büyüyen müşteri", "info", g["currentShare"], g["previousShare"], g["currentSales"]-g["previousSales"], confidence, current, previous, f"Ciro payı {g['previousShare']:.2f} puandan {g['currentShare']:.2f} puana yükseldi.", "Büyümeyi taşıyan ürünleri inceleyip çapraz satış fırsatı oluşturun."))
        if g["shareDelta"] <= shrink_cut and g["shareDelta"] < 0:
            tags.append(_tag("CUSTOMER_SHRINKING", "Küçülen müşteri", "high", g["currentShare"], g["previousShare"], g["previousSales"]-g["currentSales"], confidence, current, previous, f"Ciro payı {abs(g['shareDelta']):.2f} puan geriledi.", "Eksilen ürünleri ve sipariş frekansını inceleyip müşteri görüşmesi planlayın."))
        if top_product_share >= 60 and g["currentSales"] > 0:
            tags.append(_tag("CUSTOMER_PRODUCT_CONCENTRATION", "Ürün yoğunlaşması", "attention", top_product_share, 60, g["currentSales"] * top_product_share / 100, confidence, current, previous, f"Güncel cironun %{top_product_share:.1f} kadarı tek üründen geliyor.", "Bağımlılığı azaltmak için tamamlayıcı kategori ve ürünleri değerlendirin."))
        if g["currentReturns"] > 0:
            return_rate = g["currentReturns"] / max(g["currentSales"] + g["currentReturns"], 1) * 100
            if return_rate >= 10:
                tags.append(_tag("CUSTOMER_HIGH_RETURN", "Yüksek iade etkisi", "high", return_rate, 10, g["currentReturns"], confidence, current, previous, f"Güncel dönemde iade oranı %{return_rate:.1f}.", "İade edilen ürünleri ve satış fiyatlarını inceleyerek kök nedeni doğrulayın."))
        customers.append({
            "code": code, "name": g["name"], "city": g["city"], "country": g["country"], "seller": g["seller"],
            "segment": lifecycle, "sales": round(g["currentSales"], 2), "previousSales": round(g["previousSales"], 2),
            "lifetimeSales": round(g["allSales"], 2), "profit": round(g["currentProfit"], 2),
            "margin": round(g["currentProfit"] / g["currentSales"] * 100, 1) if g["currentSales"] else None,
            "returns": round(g["currentReturns"], 2), "invoices": len(g["currentInvoices"]),
            "products": len(g["currentProducts"]), "recency": recency, "cadence": cadence,
            "nextExpectedDate": (last_sale + timedelta(days=round(cadence))).isoformat() if last_sale and cadence else None,
            "daysOverdue": overdue, "shareDelta": round(g["shareDelta"], 3), "topProductShare": round(top_product_share, 1),
            "rfm": {"r": r_score, "f": f_score, "m": m_score, "score": f"{r_score}{f_score}{m_score}"},
            "tags": sorted(tags, key=lambda tag: tag["score"], reverse=True),
        })
    customers.sort(key=lambda item: item["sales"], reverse=True)
    segment_counts = defaultdict(int)
    for customer in customers:
        segment_counts[customer["segment"]] += 1
    return {
        "status": "ready", "analysisDate": analysis_date.isoformat(), "simulation": requested != maximum,
        "batchId": batch_id, "periods": {"current": [current[0].isoformat(), current[1].isoformat()], "previous": [previous[0].isoformat(), previous[1].isoformat()]},
        "summary": {
            "customers": len(customers), "active": sum(1 for c in customers if c["sales"] > 0),
            "atRisk": sum(1 for c in customers if c["segment"] in ("Geciken", "Kayıp riski")),
            "growing": segment_counts["Büyüyen"], "new": segment_counts["Yeni"], "reactivated": segment_counts["Geri kazanılan"],
            "sales": round(sum(c["sales"] for c in customers), 2), "profit": round(sum(c["profit"] for c in customers), 2),
        },
        "thresholds": {"method": "20-60-20", "growingShareDelta": round(grow_cut, 3), "shrinkingShareDelta": round(shrink_cut, 3), "windowDays": WINDOW_DAYS},
        "options": {"segments": sorted(segment_counts), "cities": sorted({c["city"] for c in customers}), "sellers": sorted({c["seller"] for c in customers})},
        "customers": customers,
        "methodology": "RFM güncel 90 günlük satış penceresinden; ritim benzersiz satış faturası günleri arasındaki medyan aralıktan hesaplanır. Satın alma belgeleri kapsam dışıdır.",
    }


def customer_analytics(data: dict[str, Any]) -> dict[str, Any]:
    return _build(data)


def customer_detail(data: dict[str, Any]) -> dict[str, Any]:
    code = str(data.get("code") or "").strip()
    overview = _build(data)
    if overview.get("status") != "ready":
        return overview
    customer = next((item for item in overview["customers"] if item["code"] == code), None)
    if not customer:
        return {"status": "not_found", "code": code}
    raw_rows, _ = _latest_rows()
    end = _day(overview["analysisDate"])
    rows = [row for row in raw_rows if str(row.get("Müsteri Kodu") or "Bilinmiyor").strip() == code and engine.invoice_kind(row) in ("sale", "return") and _day(row.get("Fatura Tarihi")) and _day(row["Fatura Tarihi"]) <= end]
    monthly = defaultdict(lambda: {"sales": 0.0, "profit": 0.0, "returns": 0.0, "invoices": set()})
    products = defaultdict(lambda: {"name": "Bilinmiyor", "category": "Bilinmiyor", "sales": 0.0, "profit": 0.0, "returns": 0.0, "quantity": 0.0, "invoices": set()})
    invoices = defaultdict(lambda: {"date": None, "sales": 0.0, "profit": 0.0, "products": set(), "kind": "Satış"})
    for row in rows:
        day = _day(row["Fatura Tarihi"]); kind = engine.invoice_kind(row)
        key = day.strftime("%Y-%m")
        month = monthly[key]; month["sales"] += _signed(row, "Net Satir Tutari"); month["profit"] += _signed(row, "Satir Kari")
        if kind == "return": month["returns"] += abs(_number(row.get("Net Satir Tutari")))
        if row.get("Fatura No"): month["invoices"].add(str(row["Fatura No"]))
        product_code = str(row.get("Malzeme Kodu") or "Bilinmiyor")
        product = products[product_code]; product["name"] = str(row.get("Malzeme Aciklamasi") or product_code); product["category"] = str(row.get("Malzeme Grubu") or "Bilinmiyor")
        product["sales"] += _signed(row, "Net Satir Tutari"); product["profit"] += _signed(row, "Satir Kari")
        product["quantity"] += (-1 if kind == "return" else 1) * abs(_number(row.get("Miktar")))
        if kind == "return": product["returns"] += abs(_number(row.get("Net Satir Tutari")))
        if row.get("Fatura No"): product["invoices"].add(str(row["Fatura No"]))
        invoice_no = str(row.get("Fatura No") or f"satir-{len(invoices)}")
        invoice = invoices[invoice_no]; invoice["date"] = day.isoformat(); invoice["sales"] += _signed(row, "Net Satir Tutari"); invoice["profit"] += _signed(row, "Satir Kari"); invoice["products"].add(product_code); invoice["kind"] = "İade" if kind == "return" else "Satış"
    from analysis.customer_recommendations import recommendations
    suggestions = recommendations(raw_rows, code, end)
    return {
        "recommendations": suggestions,
        "status": "ready", "analysisDate": overview["analysisDate"], "periods": overview["periods"], "customer": customer,
        "timeline": [{"period": key, "sales": round(value["sales"], 2), "profit": round(value["profit"], 2), "returns": round(value["returns"], 2), "invoices": len(value["invoices"])} for key, value in sorted(monthly.items())],
        "products": sorted([{"code": key, "name": value["name"], "category": value["category"], "sales": round(value["sales"], 2), "profit": round(value["profit"], 2), "returns": round(value["returns"], 2), "quantity": round(value["quantity"], 2), "invoices": len(value["invoices"])} for key, value in products.items()], key=lambda item: item["sales"], reverse=True),
        "invoices": sorted([{"number": key, "date": value["date"], "sales": round(value["sales"], 2), "profit": round(value["profit"], 2), "products": len(value["products"]), "type": value["kind"]} for key, value in invoices.items()], key=lambda item: item["date"] or "", reverse=True)[:100],
    }
