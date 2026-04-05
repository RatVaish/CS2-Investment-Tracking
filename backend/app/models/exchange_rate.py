from sqlalchemy import Column, Integer, String, Float, Date, TIMESTAMP, UniqueConstraint
from app.db.base import Base


class ExchangeRate(Base):
    """
    Daily foreign exchange rates.

    Primary use: convert Buff163 CNY prices to USD for display.
    One row per currency pair per day.

    Source examples: 'openexchangerates' | 'manual' | 'frankfurter'
    """
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    from_currency = Column(String(3), nullable=False)   # e.g. 'CNY'
    to_currency = Column(String(3), nullable=False)     # e.g. 'USD'
    rate = Column(Float, nullable=False)                # 1 from_currency = rate to_currency
    source = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(TIMESTAMP, server_default='NOW()')

    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', 'date', name='uq_exchange_rate_date'),
    )

    def __repr__(self):
        return f"<ExchangeRate {self.from_currency}/{self.to_currency} = {self.rate} on {self.date}>"
