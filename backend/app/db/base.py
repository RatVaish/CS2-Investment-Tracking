from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models.user import User  # noqa
from app.models.investment import Investment  # noqa
from app.models.item import Item  # noqa
from app.models.item_price import ItemPrice  # noqa
from app.models.price_history import PriceHistory  # noqa