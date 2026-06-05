from pydantic import BaseModel, Field


class DiscoveryRequest(BaseModel):
    industry: str = Field(..., examples=["ferreteria"])
    country: str = "Argentina"
    city: str = Field(..., examples=["Cordoba"])
    limit: int = 20
    source: str = "serpapi"


class LeadIn(BaseModel):
    business_name: str
    industry: str | None = None
    country: str | None = None
    city: str | None = None
    source: str = "manual"
    source_url: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    instagram: str | None = None
    linkedin: str | None = None
    address: str | None = None


class OutreachRequest(BaseModel):
    lead_id: int
    channel: str = Field(..., examples=["email", "whatsapp", "instagram", "linkedin"])
    step: str = Field("initial", examples=["initial", "follow_up_1", "follow_up_2", "breakup"])
