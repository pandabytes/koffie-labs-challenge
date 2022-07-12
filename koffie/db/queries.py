import sqlite3
from .entities import Vin

def connectToVinDatabase(filePath: str):
  connection = sqlite3.connect(filePath, check_same_thread=False)
  cursor = connection.cursor()
  try:
    # This ensures we always have fresh table 
    cursor.execute("DROP TABLE IF EXISTS Vin")

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
  finally:
    cursor.close()

def __mapRowToVin(row: tuple) -> Vin:
  try:
    return Vin(vin=row[0], make=row[1], model=row[2], modelYear=row[3], bodyClass=row[4])
  except Exception as ex:
    raise ValueError(f"Unable to map from object {row} to Vin entity object. Error: {ex}")

def insertVin(connection: sqlite3.Connection, vin: Vin):
  cursor = connection.cursor()
  try:
    insertParams = (vin.vin, vin.make, vin.model, vin.modelYear, vin.bodyClass)
    cursor.execute("INSERT INTO Vin VALUES (?, ?, ?, ?, ?)", insertParams)
    connection.commit()
  finally:
    cursor.close()

def getVin(connection: sqlite3.Connection, vin: str) -> Vin | None:
  cursor = connection.cursor()
  try:
    rows = cursor.execute("SELECT * FROM Vin WHERE vin = :vin", { "vin": vin })
    firstRow = rows.fetchone()
    if firstRow is None:
      return None

    return __mapRowToVin(firstRow)
  finally:
    cursor.close()
  
def getAllVinsRaw(connection: sqlite3.Connection) -> list[tuple]:
  """ Only use this if the size of the data is small.
      This returns the raw data from sqlite, in the form
      of tuple (a, b, c, d, etc...) where each index
      represents the corresponding column in the Vin table.
  """
  cursor = connection.cursor()
  try:
    rows = cursor.execute("SELECT * FROM Vin")
    return [row for row in rows]
  finally:
    cursor.close()

def removeVin(connection: sqlite3.Connection, vin: str):
  cursor = connection.cursor()
  try:
    rows = cursor.execute("DELETE FROM Vin WHERE vin = :vin", { "vin": vin })
    connection.commit()
    return rows.rowcount == 1
  finally:
    cursor.close()
