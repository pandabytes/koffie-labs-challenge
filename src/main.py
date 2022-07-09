from typing import Union
from pydantic import BaseModel, validator
from fastapi import FastAPI, status, HTTPException
import requests
import entity
import vinHelpers
import queries

app = FastAPI()
connection = queries.connectToVinDatabase("vinCache.db")

# https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/1XPWD40X1ED215307?format=json

# def normalize(fieldValue: str):
#   normalizedFieldValue = fieldValue.strip()
#   if len(normalizedFieldValue) == 0:
#     raise ValueError(f"Field value must not be empty")
#   return fieldValue

class VinResponse(BaseModel):
  vin: str
  make: str
  model: str
  modelYear: str
  bodyClass: str
  cachedResult: bool | None

@app.on_event("shutdown")
def shutdown():
  connection.close()

@app.get("/lookup/{vin}", status_code=status.HTTP_200_OK)
def lookup(vin: str):
  vin = vin.strip()
  if not vinHelpers.isVinInCorrectFormat(vin):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Vin {vin} must be a 17 alphanumeric characters string.")
  
  cacheVin = queries.getVin(connection, vin)
  if cacheVin is not None:
    cacheVinDict = cacheVin.dict()
    cacheVinDict["cachedResult"] = True
    return VinResponse(**cacheVinDict)

  response = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json")
  try:
    response.raise_for_status()
    jsonObj = response.json()["Results"][0]

    entityVin = entity.Vin(vin=vin, 
                           make=jsonObj["Make"],
                           model=jsonObj["Model"],
                           modelYear=jsonObj["ModelYear"],
                           bodyClass=jsonObj["BodyClass"])
    queries.insertVin(connection, entityVin)
    
    return VinResponse(**entityVin.dict())
  except requests.HTTPError as ex:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Call to Vehicle API returned an error. Error: {ex}")
  except Exception as ex:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {ex}")


