from pydantic import BaseModel

class RemoveResponse(BaseModel):
  vin: str
  cacheDeleteSuccess: bool
