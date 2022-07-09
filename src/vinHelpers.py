
def isVinInCorrectFormat(vin: str) -> bool:
  return len(vin) == 17 and vin.isalnum()
  

