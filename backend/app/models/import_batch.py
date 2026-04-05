from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.base import Base


class ImportBatch(Base):
    """
    Tracks every import job a user runs.

    Enables:
    - Import history page ("you imported 47 items from Steam on April 5th")
    - Deduplication: check steam_asset_id against existing investments
    - Debugging failed imports

    Sources: 'steam' | 'csv' | 'excel' | 'skinport' | 'manual'
    """
    __tablename__ = "import_batches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    source = Column(String(20), nullable=False)     # 'steam' | 'csv' | 'excel' | 'skinport' | 'manual'
    status = Column(String(20), nullable=False, default='pending')  # 'pending' | 'processing' | 'complete' | 'failed'

    # Item counts
    total_items = Column(Integer, nullable=True)
    imported_items = Column(Integer, nullable=True, default=0)
    skipped_items = Column(Integer, nullable=True, default=0)   # Already exists (deduplication)
    failed_items = Column(Integer, nullable=True, default=0)

    error_msg = Column(String(1000), nullable=True)

    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default='NOW()')

    # Relationships
    user = relationship("User", back_populates="import_batches")
    investments = relationship("Investment", back_populates="import_batch")

    def __repr__(self):
        return f"<ImportBatch user_id={self.user_id} source={self.source} status={self.status}>"
