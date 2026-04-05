from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models so Alembic can detect them for autogenerate
# Order matters — parents before children (FK dependencies)
from app.models.user import User                          # noqa
from app.models.user_consent import UserConsent           # noqa
from app.models.item import Item                          # noqa
from app.models.item_price import ItemPrice               # noqa
from app.models.price_history import PriceHistory         # noqa
from app.models.exchange_rate import ExchangeRate         # noqa
from app.models.item_sync_log import ItemSyncLog          # noqa
from app.models.price_update_log import PriceUpdateLog    # noqa
from app.models.market_benchmark import MarketBenchmark   # noqa
from app.models.import_batch import ImportBatch           # noqa
from app.models.investment import Investment               # noqa
from app.models.investment_sticker import InvestmentSticker  # noqa
from app.models.investment_tag import InvestmentTag       # noqa
from app.models.investment_audit import InvestmentAudit   # noqa
from app.models.portfolio_snapshot import PortfolioSnapshot  # noqa
from app.models.price_alert import PriceAlert             # noqa
from app.models.notification import Notification          # noqa
from app.models.user_watchlist import UserWatchlist       # noqa
