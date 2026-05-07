from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class UserUpdateRead(Base):
    __tablename__ = "user_update_reads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    update_id = Column(Integer, ForeignKey("updates.id", ondelete="CASCADE"), nullable=False)
    read_at = Column(String, nullable=False)

    # Relationships
    user = relationship("User", back_populates="update_reads")
    update = relationship("Update", back_populates="user_reads")

    def __repr__(self):
        return f"<UserUpdateRead user={self.user_id} update={self.update_id}>"
