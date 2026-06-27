from __future__ import annotations

from mardior.db.storage import Storage


class ShippingComparator:
    def __init__(self):
        self.storage = Storage()

    def compare_all(self) -> list[dict]:
        with self.storage.get_session() as session:
            from mardior.db.schema import ShippingRate
            rates = session.query(ShippingRate).all()

        results = []
        for rate in rates:
            diff = round(rate.store_price - (rate.real_price or rate.store_price), 2)
            savings = rate.real_price and rate.store_price > rate.real_price
            results.append({
                "id": rate.id,
                "zone": rate.zone,
                "carrier": rate.carrier,
                "method": rate.method_name,
                "store_price": rate.store_price,
                "real_price": rate.real_price,
                "source": rate.source,
                "difference": diff,
                "has_savings": bool(savings),
                "savings_amount": round(rate.store_price - rate.real_price, 2) if savings else 0,
                "recommended": rate.real_price and rate.real_price < rate.store_price,
            })

        return results

    def get_best_carrier_per_zone(self) -> list[dict]:
        with self.storage.get_session() as session:
            from mardior.db.schema import ShippingRate
            from sqlalchemy import func
            subq = session.query(
                ShippingRate.zone,
                func.min(ShippingRate.real_price).label("min_price")
            ).filter(ShippingRate.real_price.isnot(None)).group_by(ShippingRate.zone).subquery()

            best = session.query(ShippingRate).join(
                subq,
                (ShippingRate.zone == subq.c.zone) & (ShippingRate.real_price == subq.c.min_price)
            ).all()

        return [
            {
                "zone": r.zone,
                "carrier": r.carrier,
                "method": r.method_name,
                "price": r.real_price,
            }
            for r in best
        ]

    def get_zones(self) -> list[str]:
        with self.storage.get_session() as session:
            from mardior.db.schema import ShippingRate
            results = session.query(ShippingRate.zone).distinct().all()
            return [r[0] for r in results]

    def get_carriers(self) -> list[str]:
        with self.storage.get_session() as session:
            from mardior.db.schema import ShippingRate
            results = session.query(ShippingRate.carrier).distinct().all()
            return [r[0] for r in results]
