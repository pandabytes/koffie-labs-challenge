from pydantic import BaseModel, validator, fields
from ..utils.vin import isVinInCorrectFormat

class Vin(BaseModel):
  """ The entity that models the data in the Vin cache. """
  vin: str
  make: str
  model: str
  modelYear: str
  bodyClass: str

  @validator("vin", pre=True)
  def makeVinUpperCase(cls, value: str):
    return value.upper()

  @validator("*")
  def checkFieldIsEmpty(cls, value: str, field: fields.ModelField):
    value = value.strip()
    if len(value) == 0:
      raise ValueError(f"Field \"{field}\" must not be an empty string.")
    return value

  @validator("vin")
  def checkVinInCorrectFormat(cls, value: str):
    if not isVinInCorrectFormat(value):
      raise ValueError(f"VIN \"{value}\" must be a 17 alphanumeric characters string.")
    return value
