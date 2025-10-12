from pydantic import BaseModel, Field

class NormalizedEnvironmentalData(BaseModel):
    city: str = Field(..., description="Name of the city")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    hazard_type: str = Field(..., description="Type of environmental hazard")
    risk_level: str = Field(..., description="Risk severity such as Low, Moderate, High")