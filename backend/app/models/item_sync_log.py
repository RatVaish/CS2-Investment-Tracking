from sqlalchemy import Column, Integer, String, TIMESTAMP
from app.db.base import Base


class ItemSyncLog(Base):
    """
    Audit trail for automatic CS2 item database syncs.

    The sync job checks the ByMykel/CSGO-API GitHub repo commit SHA
    against the last known SHA. If different, it pulls new items,
    upserts existing ones, and marks removed items is_active=False.

    This table records every sync attempt for debugging and monitoring.
    """
    __tablename__ = "item_sync_log"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, default='byMykel_github')

    # The GitHub commit SHA that triggered this sync
    commit_sha = Column(String(40), nullable=True)
    previous_sha = Column(String(40), nullable=True)

    # What changed
    items_added = Column(Integer, nullable=True, default=0)
    items_updated = Column(Integer, nullable=True, default=0)
    items_deactivated = Column(Integer, nullable=True, default=0)

    synced_at = Column(TIMESTAMP, server_default='NOW()')
    status = Column(String(20), nullable=False)     # 'success' | 'partial' | 'failed' | 'no_changes'
    error_msg = Column(String(1000), nullable=True)

    def __repr__(self):
        return f"<ItemSyncLog status={self.status} added={self.items_added} at={self.synced_at}>"
