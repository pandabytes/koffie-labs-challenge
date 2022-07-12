import os
import requests
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
dbConnection = queries.connectToVinDatabase(cacheFilePath)

def __validateVinFormat(vin: str):
  vin = vin.strip().upper()
  if not isVinInCorrectFormat(vin):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"VIN {vin} must be a 17 alphanumeric characters string.")
  return vin

@app.on_event("shutdown")
def shutdown():
  logger.info("Shutting down service.")
  if dbConnection is not None:
    logger.info("Closing database connection.")
    dbConnection.close()

@app.get("/lookup/{vin}", status_code=status.HTTP_200_OK)
def lookup(vin: str):
  """ Lookup the given vin number in the cache. If the vin is not in the
      cache, then try to get it from [Vehicle API](https://vpic.nhtsa.dot.gov/api/)
      and insert the vin in the cache if found.
  """
  vin = __validateVinFormat(vin)
  
  # Try to get vin from cache first
  cacheVin = queries.getVin(dbConnection, vin)
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
    queries.insertVin(dbConnection, entityVin)

    return LookupResponse(**entityVin.dict(), cachedResult=False)
  except requests.HTTPError as ex:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Call to Vehicle API returned an error. Error: {ex}")
  except ValidationError as ex:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cannot find VIN {vin}.")
  except Exception as ex:
    logger.exception("Encountered unexpected error in trying to lookup VIN %s.", vin)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Something happened on our end.")

@app.delete("/remove/{vin}", status_code=status.HTTP_200_OK)
def remove(vin: str):
  """ Remove the vin from cache. This API will return a status of 200, whether
      the vin was successfully removed or not from the cache. Client can use the 
      field `cacheDeleteSuccess` to check the actual success status of the API.
  """
  vin = __validateVinFormat(vin)
  try:
    isVinRemoved = queries.removeVin(dbConnection, vin)
    return RemoveResponse(vin=vin, cacheDeleteSuccess=isVinRemoved)
  except Exception as ex:
    logger.exception("Encountered unexpected error in trying to remove VIN %s. Error: %s", vin, ex)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Something happened on our end.")

@app.get("/export", status_code=status.HTTP_200_OK)
def export():
  """ Export the cache to a parq file (Parquet format). If the cache is empty,
      then export an empty parq file.
  """
  # Always create an empty parquet file
  parquetFilePath = "vins.parq"
  with open(parquetFilePath, "w") as _: 
    pass

  if not os.path.exists(cacheFilePath):
    # This shouldn't happen as we always connect to the database at the start
    # But if it does, it means we have a bug so we log a warning
    logger.warn("Cache file not found for export.")
  else:
    try:
      vins = queries.getAllVinsRaw(dbConnection)
      if len(vins) > 0:
        logger.info(f"Writing {len(vins)} vin(s) to file \"{parquetFilePath}\".")
        dataFrame = pd.DataFrame(vins, columns=["vin", "make", "model", "modelYear", "bodyClass"])
        fastparquet.write(parquetFilePath, dataFrame)
    except Exception as ex:
      logger.exception("Encountered unexpected error in trying to export parq file. Error: %s", ex)
      raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Something happened on our end.")

  return FileResponse(parquetFilePath, filename=os.path.basename(parquetFilePath))
