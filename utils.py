import re
import time
import requests
import os
from urllib.parse import urlparse
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from datetime import datetime

def api_get(url, responseType="json"):
  try:
    response = requests.get(url)
    response.raise_for_status()
    
    if responseType == "json":
      return response.json()
    else:
      return response.text
  
  except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
  except Exception as err:
    print(f"Other error occurred: {err}")
    
def api_post(url, data):
  try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()
  
  except requests.exceptions.HTTPError as http_err:
    print(f"HTTP error occurred: {http_err}")
  except Exception as err:
    print(f"Other error occurred: {err}")

def get_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}"
  
def verify_cloudflare_recaptcha(driver):
  while(1):
    elements = driver.find_elements(By.CSS_SELECTOR, "#pShg7")
    if (elements and elements[0].is_displayed() and ("Verifying" in elements[0].text or "Verify" in elements[0].text)):
      print("detected cloudflare recaptcha...")
      start_x, start_y = 403, 206
      target_x, target_y = 523, 286
      steps = 10
      x_step = (target_x - start_x) / steps
      y_step = (target_y - start_y) / steps
      actions = ActionChains(driver)

      time.sleep(1)

      actions.move_by_offset(start_x, start_y)
      for i in range(steps):
        start_x += x_step
        start_y += y_step
        actions.move_by_offset(x_step, y_step).perform()
      
      time.sleep(1)
      actions.click().perform()
      time.sleep(3)
      actions.move_by_offset(-start_x, -start_y).perform()
    else:
      return

def restartVPN():
  print("stoping vpn...")
  os.system("service openvpn@client stop")
  time.sleep(10)
  print("starting vpn...")
  os.system("service openvpn@client start")
  time.sleep(10)
  return

def extractAddressParts(address_text):
    # Define patterns for street, town, and postcode
    postcode_pattern = r'\b[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}\b'
    town_pattern = r', ([^,]+),'
    street_pattern = r'^([^,]+)'

    # Initialize variables
    street = None
    town = None
    postcode = None

    # Extract postcode
    postcode_match = re.search(postcode_pattern, address_text)
    if postcode_match:
        postcode = postcode_match.group(0).strip()
        address_text = address_text.replace(postcode, '').strip()

    # Extract town
    town_match = re.search(town_pattern, address_text)
    if town_match:
        town = town_match.group(1).strip()
        address_text = address_text.replace(town, '').strip(', ')

    # Extract street
    street_match = re.search(street_pattern, address_text)
    if street_match:
        street = street_match.group(1).strip()

    return street, town, postcode

def extract_address_parts_zoopla(address):
  # Define a regex pattern to match the address parts
  pattern = r'^(.*?),\s*(.*?)(\s+\w+\d+\s*\w*)$'
  match = re.match(pattern, address)
  
  if match:
    street = match.group(1).strip()
    town = match.group(2).strip()
    postcode = match.group(3).strip()
    return street, town, postcode
  else:
    return None, None, None

# Grove Avenue, London N3
def extractAddressPartsUpdate(address):
  # Define a regex pattern to match the address parts
  pattern = r'^(.*?),\s*(.*?)(\s+\w+\d+\w*)$'
  match = re.match(pattern, address)
  
  if match:
    street = match.group(1).strip()
    town = match.group(2).strip()
    postcode = match.group(3).strip()
    return street, town, postcode
  else:
    return None, None, None
    
def getElementTextBySelector(soup, selector, index=None):
  try:
    if index is not None:
      selected_elements = soup.select(selector)
      if len(selected_elements) > index:
        selected_element = selected_elements[index]
      else:
        selected_element = None
    else:
      selected_element = soup.select_one(selector)
      
    result = selected_element.get_text() if selected_element else None

    if result == "Ask":
        result = None

  except Exception as e:
    print(f"An error occurred: {e}")
    result = None
  
  return result


def getElementText(soup, parentElement, parentClassName, childrenElement, childrenClassName, index=None):
	try:
		if parentElement:
			sourceCode = soup.find_all(parentElement, class_=parentClassName)
		else:
			sourceCode = soup.find_all(class_=parentClassName)
		
		if index is not None:
			if len(sourceCode) > index:
				selected_element = sourceCode[index].find(childrenElement, class_=childrenClassName)
			else:
				selected_element = None
		else:
			if sourceCode:
				selected_element = sourceCode[0].find(childrenElement, class_=childrenClassName)
			else:
				selected_element = None
		
		result = selected_element.get_text() if selected_element else None

		if result == "Ask":
			result = None

	except Exception as e:
		print(f"An error occurred: {e}")
		result = None
    
	return result	

def getElementTextByDataTest(soup, attr, data_test_value):
    try:
        selected_element = soup.find(attrs={attr: data_test_value})
        result = selected_element.get_text() if selected_element else None

    except Exception as e:
        print(f"An error occurred: {e}")
        result = None
    
    return result

def getElementAttribute(sourceCode, parentElement, className, childrenElement, attribute, index=None):
	try:
		# Determine whether to use indexed access or direct find
		if index is not None:
			selected_element = sourceCode[index].find(parentElement, class_=className)
		else:
			selected_element = sourceCode.find(parentElement, class_=className)

		# Debug print to check the selected element

		if selected_element:
			img_tag = selected_element.find(childrenElement)
			if img_tag:
				return img_tag.get(attribute)
			
	except AttributeError:
		# Handle cases where `.find()` returns None
		pass

	return None 

def openNewBrowser(driver):
  if driver:
    driver.quit()
    restartVPN()

  chrome_options = Options()
  chrome_options.add_argument("--window-size=1920,1080")
  chrome_options.add_argument("--no-sandbox")
  chrome_options.add_argument("--disable-dev-shm-usage")
  chrome_options.add_argument("--headless")
  chrome_options.add_argument("--disable-gpu")
  # chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36')
  # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
  # chrome_options.add_experimental_option('useAutomationExtension', False)
  # service = Service(ChromeDriverManager().install())
  # driver = webdriver.Chrome(service=service, options=chrome_options)
  driver = uc.Chrome(
    options=chrome_options,
    use_subprocess=False,
    headless=True,
  )

  return driver

def printLog(param1, param2 = None):
  if (param2):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {param1}", param2)
  else:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {param1}")
