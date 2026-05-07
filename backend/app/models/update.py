from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Update(Base):
    __tablename__ = "updates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
    created_at = Column(String, nullable=False)

    # Relationships
    user_reads = relationship("UserUpdateRead", back_populates="update", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Update {self.id}: {self.title}>"
