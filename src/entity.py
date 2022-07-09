from pydantic import BaseModel

class Vin(BaseModel):
  vin: str
  make: str
  model: str
  modelYear: str
  bodyClass: str
