import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database.session import Base


class EnvironmentalMetric(Base):
    __tablename__ = "environmental_metrics"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(
        Integer, ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_date = Column(DateTime, nullable=False, index=True)

    # Core environmental metrics
    carbon_value = Column(Float, nullable=False, default=0.0)  # Metric tons of CO2e stored/avoided
    biodiversity_score = Column(Float, nullable=False, default=0.0)  # 0 - 100 Index
    vegetation_value = Column(
        Float, nullable=False, default=0.0
    )  # NDVI (0.0 - 1.0) or Canopy cover %
    carbon_sequestration = Column(Float, nullable=False, default=0.0)  # tCO2e/ha/yr rate

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    site = relationship("Site", back_populates="metrics")
