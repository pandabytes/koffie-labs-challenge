
def isVinInCorrectFormat(vin: str):
  return len(vin) == 17 and vin.isalnum()
