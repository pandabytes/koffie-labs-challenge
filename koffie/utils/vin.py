
def isVinInCorrectFormat(vin: str):
  """ Check if the given vin is 17 characters and all characters are alphanumeric. """
  return len(vin) == 17 and vin.isalnum()
