import sqlite3
from entity import Vin

def connectToVinDatabase(filePath: str):
  connection = sqlite3.connect(filePath, check_same_thread=False)
  cursor = connection.cursor()
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS Vin (
      vin TEXT PRIMARY KEY,
      make TEXT NOT NULL,
      model TEXT NOT NULL,
      modelYear TEXT NOT NULL,
      bodyClass TEXT NOT NULL
    )
  """)

  connection.commit()
  return connection

def __mapRowToVin(row: tuple) -> Vin:
  try:
    return Vin(vin=row[0], make=row[1], model=row[2], modelYear=row[3], bodyClass=row[4])
  except Exception as ex:
    raise ValueError(f"Unable to map from object {row} to Vin entity object. Error: {ex}")

def insertVin(connection: sqlite3.Connection, vin: Vin):
  cursor = connection.cursor()
  insertParams = (vin.vin, vin.make, vin.model, vin.modelYear, vin.bodyClass)
  cursor.execute("INSERT INTO Vin VALUES (?, ?, ?, ?, ?)", insertParams)
  connection.commit()

def getVin(connection: sqlite3.Connection, vin: str) -> Vin | None:
  cursor = connection.cursor()
  rows = cursor.execute("SELECT * FROM Vin WHERE vin = :vin", { "vin": vin })

  firstRow = rows.fetchone()
  if firstRow is None:
    return None

  return __mapRowToVin(firstRow)
  
def removeVin(connection: sqlite3.Connection, vin: str):
  cursor = connection.cursor()
  rows = cursor.execute("DELETE FROM Vin WHERE vin = :vin", { "vin": vin })
  connection.commit()
  return rows.rowcount == 1