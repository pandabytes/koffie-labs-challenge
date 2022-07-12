import requests
import os
import pandas as pd
import fastparquet
import logging
from .db import entities, queries
from .logConfig import LogConfig
from .schemas.lookup import LookupResponse
from .schemas.remove import RemoveResponse
from .utils.vin import isVinInCorrectFormat
from pydantic import ValidationError
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from logging.config import dictConfig

app = FastAPI()

# Set up logging 
loggerName, logConfig = __name__, LogConfig()
logConfig.addLogger(loggerName, "INFO")

dictConfig(logConfig.dict())
logger = logging.getLogger(loggerName)

# Set up connection to database
cacheFilePath = "vinCache.db"
connection = queries.connectToVinDatabase(cacheFilePath)

def __validateVinFormat(vin: str):
  vin = vin.strip().upper()
  if not isVinInCorrectFormat(vin):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"VIN {vin} must be a 17 alphanumeric characters string.")
  return vin

@app.on_event("shutdown")
def shutdown():
  logger.info("Shutting down service.")
  if connection is not None:
    logger.info("Closing database connection.")
    connection.close()

  if os.path.exists(cacheFilePath):
    logger.info(f"Removing cache file {cacheFilePath}.")
    os.remove(cacheFilePath)

@app.get("/lookup/{vin}", status_code=status.HTTP_200_OK)
def lookup(vin: str):
  vin = __validateVinFormat(vin)
  
  cacheVin = queries.getVin(connection, vin)
  if cacheVin is not None:
    logger.info("Got VIN %s from cache.", vin)
    return LookupResponse(**cacheVin.dict(), cachedResult=True)
  
  response = requests.get(f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{vin}?format=json")
  try:
    response.raise_for_status()
    jsonObj = response.json()["Results"][0]
    entityVin = entities.Vin(vin=vin, 
                             make=jsonObj["Make"],
                             model=jsonObj["Model"],
                             modelYear=jsonObj["ModelYear"],
                             bodyClass=jsonObj["BodyClass"])
    logger.info("Inserting VIN %s to cache.", vin)
    queries.insertVin(connection, entityVin)
    
    return LookupResponse(**entityVin.dict(), cachedResult=False)
  except requests.HTTPError as ex:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Call to Vehicle API returned an error. Error: {ex}")
  except ValidationError as ex:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cannot find VIN {vin}.")
  except Exception as ex:
    logger.exception(f"Encountered unexpected error in trying to lookup VIN {vin}.")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Something happened on our end.")

@app.delete("/remove/{vin}", status_code=status.HTTP_200_OK)
def remove(vin: str):
  vin = __validateVinFormat(vin)
  try:
    isVinRemoved = queries.removeVin(connection, vin)
    return RemoveResponse(vin=vin, cacheDeleteSuccess=isVinRemoved)
  except Exception as ex:
    logger.warning(f"Error trying to remove VIN {vin}. Error: %s", ex)
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
      logger.info(f"Writing {len(vins)} vin(s) to file \"{parquetFilePath}\".")
      df = pd.DataFrame(vins, columns=["vin", "make", "model", "modelYear", "bodyClass"])
      fastparquet.write(parquetFilePath, df)

  return FileResponse(parquetFilePath, filename=os.path.basename(parquetFilePath))
