import requests
import entity
import queries
import os
import pandas as pd
import fastparquet
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
import logging
from logging.config import dictConfig
from logConfig import LogConfig

app = FastAPI()

# Set up logging 
loggerName, logConfig = __name__, LogConfig()
logConfig.addLogger(loggerName, "INFO")

dictConfig(logConfig.dict())
logger = logging.getLogger(loggerName)

# Set up connection to database
cacheFilePath = "vinCache.db"
connection = queries.connectToVinDatabase(cacheFilePath)

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
  if len(vin) != 17 or not vin.isalnum():
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Vin {vin} must be a 17 alphanumeric characters string.")
  return vin

@app.on_event("shutdown")
def shutdown():
  logger.info("Shutting down service.")
  if connection is not None:
    logger.info("Closing database connection.")
    connection.close()

@app.get("/lookup/{vin}", status_code=status.HTTP_200_OK)
def lookup(vin: str):
  vin = __validateVinFormat(vin)
  
  cacheVin = queries.getVin(connection, vin)
  if cacheVin is not None:
    logger.info("Got vin %s from cache.", vin)
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
    logger.info("Inserting vin %s to cache.", vin)
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
    logger.warning(f"Error trying to remove vin {vin}. Error: %s", ex)
    return RemoveResponse(vin=vin, cacheDeleteSuccess=False)

@app.get("/export", status_code=status.HTTP_200_OK)
def export():
  # Always create an empty parquet file
  parquetFilePath = "vins.parq"
  with open(parquetFilePath, "w") as _: 
    pass

  if not os.path.exists(cacheFilePath):
    # This shouldn't happen as we always connect to the database at the start
    # But if it does, it means we have a bug so we log a warning
    logger.warn("Cache file not found for export.")
  else:
    vins = queries.getAllVinsRaw(connection)
    if len(vins) > 0:
      logger.info(f"Writing {len(vins)} vin(s) to file {parquetFilePath}.")
      df = pd.DataFrame(vins, columns=["vin", "make", "model", "modelYear", "bodyClass"])
      fastparquet.write(parquetFilePath, df)

  return FileResponse(parquetFilePath, filename=os.path.basename(parquetFilePath))
  
