from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base


class MarketBenchmark(Base):
    """
    CS2 market index benchmarks — daily values.

    Sourced purely from public price data (price_history aggregations),
    not from user portfolio data.

    Metrics:
        'cs2_index'      — weighted avg price movement across top 100 most-traded items
        'cases_index'    — cases & capsules category
        'knives_index'   — knives & gloves category
        'stickers_index' — stickers category (especially tournament stickers)

    Powers Pro feature: "Your portfolio is up 12% vs CS2 market index +5%"
    """
    __tablename__ = "market_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    metric = Column(String(30), nullable=False)     # 'cs2_index' | 'cases_index' | 'knives_index' | 'stickers_index'
    value = Column(Float, nullable=False)           # Index value (e.g. 100.0 = baseline)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='SET NULL'), nullable=True)  # Optional: item-level benchmark
    source = Column(String(50), nullable=False, default='internal')
    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationship
    item = relationship("Item", back_populates="market_benchmarks")

    __table_args__ = (
        UniqueConstraint('date', 'metric', name='uq_benchmark_date_metric'),
    )

    def __repr__(self):
        return f"<MarketBenchmark metric={self.metric} date={self.date} value={self.value}>"
