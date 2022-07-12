from pydantic import BaseModel

class RemoveResponse(BaseModel):
  """ The response data returned by the `remove` API. """
  vin: str
  cacheDeleteSuccess: bool
