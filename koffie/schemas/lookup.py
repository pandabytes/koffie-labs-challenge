from pydantic import BaseModel

class LookupResponse(BaseModel):
  vin: str
  make: str
  model: str
  modelYear: str
  bodyClass: str
  cachedResult: bool
