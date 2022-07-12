import os
import pytest
from fastapi.testclient import TestClient
from fastapi import status
# from src.main import app, cacheFilePath
import src.main as main

client = TestClient(main.app)

def __removeInsertedVin(vin: str):
  """ The vin cache persists until the application is shutdown, so we
      have to remove the inserted vin just in case subsequent tests
      also use the same vin number.
  """
  response = client.delete(f"/remove/{vin}")
  assert response.status_code == status.HTTP_200_OK

class TestLookupApi:
  @pytest.mark.parametrize("vin", ["xxxxxxxxxxxxxxxxxx", "xxxxxxxxxxxxxxxx;", "123"])
  def test_lookup_bad_format_vin(self, vin: str):
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST

  @pytest.mark.parametrize("vin", ["xxxxxxxxxxxxxxxxx", "01234567891234567"])
  def test_lookup_vin_not_found(self, vin: str):
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
  @pytest.mark.parametrize("vin", ["1XPWD40X1ED215307 ", "1XKWDB0X57J211825"])
  def test_lookup_vin_found_but_not_in_cache(self, vin: str):
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_200_OK

    lookupResponse = main.LookupResponse(**response.json())
    assert lookupResponse.cachedResult == False

    __removeInsertedVin(vin)

  def test_lookup_vin_found_in_cache(self):
    vin = "1XPWD40X1ED215307"
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_200_OK

    lookupResponse = main.LookupResponse(**response.json())
    assert lookupResponse.cachedResult == False

    # This time the vin should be in the cache
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_200_OK

    lookupResponse = main.LookupResponse(**response.json())
    assert lookupResponse.cachedResult == True

    __removeInsertedVin(vin)

class TestRemoveApi:
  @pytest.mark.parametrize("vin", ["xxxxxxxxxxxxxxxxxx", "xxxxxxxxxxxxxxxx;", "123"])
  def test_remove_bad_format_vin(self, vin: str):
    response = client.get(f"/lookup/{vin}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
