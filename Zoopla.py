from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import utils
import re
import json

property_types = [
  "semi-detached",
  "bungalows",
  "terraced",
  "flats",
  "forms/land",
  "detached"
]

def extract_property_type(text):
  text = text.lower()
  for property_type in property_types:
    if property_type in text:
      return property_type
  return None

def get_property_type_index(property_type_text):
  """Returns the index of the property type text from the list."""
  property_type_text = property_type_text.lower()
  for index, property_type in enumerate(property_types):
    if property_type_text in property_type:
      return index
  return -1  # Return -1 if the property type is not found

def getElementAttribute(sourceCode, parentElement, className, childrenElement, attribute, index=None):
  try:
    # Determine whether to use indexed access or direct find
    if index is not None:
      selected_element = sourceCode[index].find(parentElement, class_=className)
    else:
      selected_element = sourceCode.find(parentElement, class_=className)

    if selected_element:
      img_tag = selected_element.find(childrenElement)
      if img_tag:
        return img_tag.get(attribute)
      
  except AttributeError:
    # Handle cases where `.find()` returns None
    pass

  return None 

def extract_lat_long(url):
  # Define a regex pattern to find latitude and longitude
  pattern = r"[-+]?\d*\.\d+|\d+"
  
  # Search for the pattern in the URL
  match = re.findall(pattern, url)
  if match and len(match) >= 2:
    latitude = float(match[1])
    longitude = float(match[0])
    return latitude, longitude
  else:
    return None, None

def getImageUrls(soup, driver):
  button = soup.find('li', class_='xa3di82').find('button', class_='_194zg6t9 xa3di83')
  if button:
    driver.execute_script("arguments[0].click();", button)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ds9quu1")))

  parent_element = soup.find('div', class_='ds9quu1').find('div', class_='_15j4h5e0')
  floor_plan_element = parent_element.find('picture', class_='_15j4h5e4')

  source_tag = floor_plan_element.find('source')
  srcset = source_tag.get('srcset') if source_tag else None

  # Extract the first URL from the 'srcset' attribute
  floor_plan = None
  if srcset:
    floor_plan = srcset.split(',')[0].split()[0]
  
  return floor_plan

def getZooplaDetails(soup, url, driver):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
    
  # Check for the presence of 'channel' and its value
  rent_or_sale_text = None

  element = soup.select_one('h1._194zg6t8._1olqsf97')
  if element:
    rent_or_sale_text = element.get_text()
  else:
    print("The specified element was not found.")

  if 'sale' in rent_or_sale_text:
    is_rent_or_sale = 'sale'
  elif 'rent' in rent_or_sale_text:
    is_rent_or_sale = 'rent'
  else:
    is_rent_or_sale = None
  
  price = None
  address = None
  street = None
  town = None
  postcode = None

  price = utils.getElementText(soup, 'div', 'r4q9to0', 'p', '_194zg6t3 r4q9to1')
  address_element = soup.select_one('p._194zg6t8.ic4y6k0')
  if address_element:
    address = address_element.get_text(strip=True) if address_element else None
    if address:
      street, town, postcode = utils.extractAddressParts(address)
        
  # Property Type, Bedrooms, Bathrooms
  dataList = soup.find_all('ul', class_='_1wmbmfq1')
  dataList_update = soup.find_all('ul', class_='_1khto1l1')
  
  property_type = None
  bedrooms = None
  bathrooms = None
  reception_rooms = None
  size_sq_ft = None
  size_sq_mtr = None
  tenure = None
  council_tax_band = None
  
  for index, data in enumerate(dataList):
    text_element = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
    if "bed" in text_element.lower():
      bedrooms = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
    if "bath" in text_element.lower():
      bathrooms = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
    if "reception" in text_element.lower():
      reception_rooms = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
    if "sq. ft" in text_element.lower():
      size_sq_ft = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
      size_sq_mtr = None
    if "sq. mtr" in text_element.lower():
      size_sq_mtr = utils.getElementText(soup, 'li', '_1wmbmfq2', 'p', '_194zg6t8 _1wmbmfq3', index)
      size_sq_ft = None

  for index, data in enumerate(dataList_update):
    text_element = utils.getElementText(soup, 'li', '_1khto1l2', 'p', '_194zg6t8 _1khto1l3', index)
    if "tenure" in text_element.lower():
      tenure = utils.getElementText(soup, 'div', '_1khto1l5', 'p', '_194zg6t8 _1khto1l6', index)
    if "council tax band" in text_element.lower():
      council_tax_band_text = utils.getElementText(soup, 'li', '_1khto1l2', 'p', '_194zg6t8 _1khto1l6', index)
      council_tax_band = council_tax_band_text.split(":")[-1].strip()

  property_type_text = utils.getElementText(soup, 'div', '_1olqsf96', 'h1', '_194zg6t8 _1olqsf97')
  property_type = extract_property_type(property_type_text)
  
  # Extract EPC rating text
  epc_rating_text = utils.getElementText(soup, 'li', '_1olqsf9a', 'p', '_194zg6t8 w9r0350')
  epc_rating = None
  if epc_rating_text:
    match = re.search(r"EPC Rating: (\w)", epc_rating_text)
    if match:
      epc_rating = match.group(1)

  # Extract key features
  key_features_elements = soup.find('ul', class_='_15a8ens0').find_all('li', class_='_15a8ens1')
  key_features = [element.get_text(strip=True) for element in key_features_elements]

  # Determine parking and garden values
  parking = any("parking" in feature.lower() for feature in key_features)
  garden = any("garden" in feature.lower() for feature in key_features)

  json_key_features = json.dumps(key_features)
  
  # Click the button to load the image
  li_element = soup.find('li', class_='xa3di82')
  buttons = driver.find_elements(By.CSS_SELECTOR, '._194zg6t9.xa3di83')
  floor_plans = []
  if len(buttons) > 0:
    for button in buttons:
      button_text = button.text.lower()
      if "map" in button_text:
        driver.execute_script("arguments[0].click();", button)
        time.sleep(2)  # Wait for the image to load

        # Get the map URL
        map_URL = getElementAttribute(soup, 'div', 'haukfo1', 'source', 'srcset')
        if map_URL != None:
          latitude, longitude = extract_lat_long(map_URL)
        else:
          latitude, longitude = None, None
      elif "floor" in button_text:
        driver.execute_script("arguments[0].click();", button)
        time.sleep(2)  # Wait for the image to load
        parent_element_1 = soup.select_one('div.ds9quu1')
        if parent_element_1:
            parent_element_2 = parent_element_1.select_one('div._15j4h5e0')
            if parent_element_2:
              floor_plan_elements = parent_element_2.select('picture._15j4h5e4')
              for fp_element in floor_plan_elements:
                img_tag = fp_element.find('img', class_='_15j4h5e5 _15j4h5e7')
                if img_tag:
                  # Process the img tag as needed
                  print("Found img tag with the specified classes.")
                  # Extract the first URL from the 'srcset' attribute
                  source_tag = fp_element.select_one('source')
                  srcset = source_tag.get('srcset') if source_tag else None
                  floor_plan = None
                  if srcset:
                    floor_plan = srcset.split(',')[0].split()[0]
                    floor_plans.append(floor_plan)
            else:
                print("The specified element 'div._15j4h5e0' was not found.")
        else:
            print("The specified element 'div.ds9quu1' was not found.")
  if floor_plans == []:
    floor_plans = None
  else:
    json_floor_plans = json.dumps(floor_plans)
  # Floor plans
  # floor_plans = getImageUrls(soup, driver, buttons[2])

  data = {
    "number": None,
    "name": address,
    "street": street,
    "town": town,
    "postcode": postcode,
    "price": price,
    "sale_type": is_rent_or_sale,
    "property_type": property_type,
    "tenure": tenure,
    "bedrooms": bedrooms,
    "bathrooms": bathrooms,
    "reception_rooms": reception_rooms,
    "size_sq_ft": size_sq_ft,
    "size_sq_mtr": size_sq_mtr,
    "floor_plans": json.dumps(floor_plans),
    "council_tax_band": council_tax_band,
    "parking": parking,
    "garden": garden,
    "EPC_certificate": epc_rating,
    "geo_lat": latitude,
    "geo_lon": longitude,
    "map_url": map_URL,
    "description": soup.find('p', class_='rl22a31 rl22a33').get_text(strip=True),
    "key_features": json_key_features,
    "new_build": 'new-homes' in url
  }

  return data
