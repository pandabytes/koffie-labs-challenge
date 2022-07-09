from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
import requests
import entity
import vinHelpers
import queries

app = FastAPI()
connection = queries.connectToVinDatabase("vinCache.db")

class LookupResponse(BaseModel):
  vin: str
  make: str
  model: str
  modelYear: str
  bodyClass: str
  cachedResult: bool

class RemoveResponse(BaseModel):
  vin: str
  cacheDeleteSuccess: bool

def __validateVinFormat(vin: str):
  vin = vin.strip()
  if not vinHelpers.isVinInCorrectFormat(vin):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Vin {vin} must be a 17 alphanumeric characters string.")
  return vin

@app.on_event("shutdown")
def shutdown():
  connection.close()

@app.get("/lookup/{vin}", status_code=status.HTTP_200_OK)
def lookup(vin: str):
  vin = __validateVinFormat(vin)
  
  cacheVin = queries.getVin(connection, vin)
  if cacheVin is not None:
    return LookupResponse(**cacheVin.dict(), cachedResult=True)

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
    
    return LookupResponse(**entityVin.dict(), cachedResult=False)
  except requests.HTTPError as ex:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Call to Vehicle API returned an error. Error: {ex}")
  except Exception as ex:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {ex}")

@app.delete("/remove/{vin}", status_code=status.HTTP_200_OK)
def remove(vin: str):
  vin = __validateVinFormat(vin)
  try:
    isVinRemoved = queries.removeVin(connection, vin)
    return RemoveResponse(vin=vin, cacheDeleteSuccess=isVinRemoved)
  except Exception as ex:
    return RemoveResponse(vin=vin, cacheDeleteSuccess=False)
