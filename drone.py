import os
import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import RightMove
import Zoopla
import NewBuildHomes
import utils
import Onthemarket
import Primelocation
import Spareroom
import Openrent
import Home

load_dotenv()

# _api_server = 'http://65.108.207.102:8002'
_api_server = 'https://controllerserver.zgo.uk'
_drone_id = os.getenv("DRONEID") or 1
_total_page_number = 0
_driver = None

print(_drone_id)
exit()

globalUrls = [
  "https://www.rightmove.co.uk/",
  "https://www.zoopla.co.uk/",
  "https://www.newbuildhomes.org/",
  "https://www.onthemarket.com/",
  "https://www.primelocation.com/",
  "https://www.spareroom.co.uk/",
  "https://www.openrent.co.uk/",
  "https://www.home.co.uk/"
]

def identifyUrlIndex(url):
  for index, urlItem in enumerate(globalUrls):
    if url.startswith(urlItem):
      # Logic for when the condition is met
      return index  
  return -1  

def identifyScrappingMethod(index, url):
  page_source = _driver.page_source
  soup = BeautifulSoup(page_source, 'html.parser')

  def case_0():
    scrappingData = RightMove.getRightMoveDetails(soup, url)
    return scrappingData

  def case_1():
    scrappingData = Zoopla.getZooplaDetails(soup, url, _driver)
    resultDisplay(scrappingData)
    return scrappingData

  def case_2():
    scrappingData = NewBuildHomes.getNewBuildHomesDetails(soup, url)
    return scrappingData

  def case_3():
    scrappingData = Onthemarket.getOnthemarketDetails(soup, url)
    return scrappingData

  def case_4():
    scrappingData = Primelocation.getPrimelocationDetails(soup, url, _driver)
    return scrappingData

  def case_5():
    scrappingData = Spareroom.getSpareroomDetails(soup, url)
    return scrappingData

  def case_6():
    scrappingData = Openrent.getOpenRentDetails(soup, url)
    return scrappingData

  def case_7():
    if 'onthemarket' in url:
      scrappingData = Onthemarket.getOnthemarketDetails(soup, url)
      return scrappingData
    else:
      return None

  def default_case():
      return None

  def switch_case(urlIndex):
    cases = {
      0: case_0,
      1: case_1,
      2: case_2,
      3: case_3,
      4: case_4,
      5: case_5,
      6: case_6,
      7: case_7
    }
    return cases.get(urlIndex, default_case)()
  
  return_data = switch_case(index)
  return return_data

def main():
  global _total_page_number
  global _driver
  
  while True:
    try:
      if (_total_page_number % 20 == 0):
        utils.printLog(f"opening new browser")
        _driver = utils.openNewBrowser(_driver)
        utils.printLog(f"opened new browser")
      _total_page_number = _total_page_number + 1      
        
      scrape_datas = utils.api_get(f"{_api_server}/api/scrape-logs/run/{_drone_id}")
      
      if scrape_datas:
        link = scrape_datas['scrape_log']['page']['link']
        pause_time = scrape_datas['pause_time']
        # link = 'https://www.rightmove.co.uk/properties/156241640#/?channel=RES_BUY'
        # pause_time = 15

        page_id = scrape_datas['scrape_log']['page_id']
        drone_id = scrape_datas['scrape_log']['drone_id']
        scrape_log_id = scrape_datas['scrape_log']['id']
        
        utils.printLog(f"Link: {link}, Pause Time: {pause_time}")

        try:
          _driver.get(link)
        except Exception as e:
          utils.printLog(f"Error navigating to {link}: {e}")
          pass

        # Avoid Cloudflare protection
        if "Just a moment..." in _driver.title:
          time.sleep(30)  # Wait for 30 seconds to pass the Cloudflare protection

        urlIndex = identifyUrlIndex(link)
        data = identifyScrappingMethod(urlIndex, link)

        post_data = {
          "drone_id": drone_id,
          "page_id": page_id,
          "scrape_log_id": scrape_log_id,
          "data": data
        }

        api_result = utils.api_post(f"{_api_server}/api/properties/save", post_data)
        time.sleep(pause_time)
      else:
        utils.printLog("internal error.")
    except Exception as e:
      utils.printLog(f"skip to next page due to error on the above page: ", e)
      pass

def resultDisplay(data):
  print(data)

main()

