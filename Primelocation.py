from urllib.parse import urlparse, parse_qs
import utils
import re
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

property_types = [
  "terraced",
  "end-terrace",
  "semi-detached",
  "detached",
  "cottage",
  "flat",
  "retail",
  "office",
  "warehouse"
]

def get_property_type_index(property_type_text):
  """Returns the index of the property type text from the list."""
  property_type_text = property_type_text.lower()
  for index, property_type in enumerate(property_types):
    if property_type_text in property_type:
      return index
  return -1  # Return -1 if the property type is not found

def extract_lat_long(url):
  # Define a regex pattern to find latitude and longitude
  pattern = r"latitude=([-+]?\d*\.\d+|\d+)&longitude=([-+]?\d*\.\d+|\d+)"
  
  # Search for the pattern in the URL
  match = re.search(pattern, url)
  if match:
    latitude = float(match.group(1))
    longitude = float(match.group(2))
    return latitude, longitude
  else:
    return None, None

def extract_address_parts(address):
  """
  Extracts the street, town, and postcode from an address string.
  """
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

def getPrimelocationDetails(soup, url, driver):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
      
  # Check for the presence of 'channel' and its value

  price = utils.getElementText(soup, 'div', 'listing-details-price', 'span', 'price')
  address = utils.getElementTextBySelector(soup, '#listing-details .clearfix .listing-details-h1')
  is_rent_or_sale = None

  if address:
    street, town, postcode = extract_address_parts(address)
    if 'sale' in address.lower():
      is_rent_or_sale = 'sale'
    elif 'rent' in address.lower():
      is_rent_or_sale = 'rent'
  else: 
    address = None
    street = None
    town = None
    postcode = None


  # Property Type, Bedrooms, Bathrooms
  
  property_type = None
  for p_type in property_types:
    if p_type in address.lower():
      property_type = p_type
      break

  bedrooms = utils.getElementTextBySelector(soup, ".listing-details-attr span.num-beds")
  bathrooms = utils.getElementTextBySelector(soup, ".listing-details-attr span.num-icon.num-baths")
  
  # Extract size_sq_ft and size_sq_mtr from size_text
  size_text = utils.getElementTextBySelector(soup, '#tab-details .clearfix')
  size_sq_ft = None
  size_sq_mtr = None
  if size_text:
    size_match = re.search(r'(\d+)\s*sq\s*ft\s*/\s*(\d+)\s*sq\s*m', size_text)
    if size_match:
      size_sq_ft = size_match.group(1)
      size_sq_mtr = size_match.group(2)

  # Extract tenure and council_tax_band
  key_info_divs = soup.select('.nts_box .nts_field')
  for div in key_info_divs:
    title = div.find('span', class_='nts_label').get_text(strip=True)
    value = div.find('div', class_='nts_value').get_text(strip=True)
    if 'Tenure' in title:
      tenure = value
    elif 'Council tax' in title:
      council_tax_band = value

  description = soup.select_one('.bottom-plus-half .top').get_text(strip=True)
  parking = 'parking' in description.lower()
  garden = 'garden' in description.lower()

  key_elements = soup.select('#tab-details .clearfix')

  key_features_elements = soup.select('#tab-details .clearfix ul li')
  key_features = [element.get_text(strip=True) for element in key_features_elements]
  json_key_features = json.dumps(key_features)

  
  # Floor plans
  floor_plans = []
  map_URL = []
  
  floor_btn = driver.find_element(By.CSS_SELECTOR, '.tab-floorplan')
  if floor_btn:
    driver.execute_script("arguments[0].click();", floor_btn)
    try:
      floor_plans = [
        img['src'] 
        for a_tag in soup.select('.floorplan-container').find_all('img')
        if (img := a_tag.find('img')) is not None
      ]
    except (IndexError, AttributeError):
      floor_plans = None
    time.sleep(1)

  map_btn = driver.find_element(By.CSS_SELECTOR, '.tab-map')
  if map_btn:
    driver.execute_script("arguments[0].click();", map_btn)
    try:
      map_URL = [
        img['src']
        for a_tag in soup.select('#map-map .gm-style').find_all('img')
        if (img := a_tag.find('img')) is not None
      ]
    except (IndexError, AttributeError):
      map_URL = None

  data = {
    "number": None,
    "Name": address,
    "street": street,
    "town": town,
    "postcode": postcode,
    "price": price,
    "sale_type": is_rent_or_sale,
    "property_type": property_type,
    "tenure": tenure,
    "bedrooms": bedrooms,
    "bathrooms": bathrooms,
    "reception_rooms": None,
    "size_sq_ft": size_sq_ft,
    "size_sq_mtr": size_sq_mtr,
    "floor_plans": floor_plans,
    "council_tax_band": council_tax_band,
    "parking": parking,
    "garden": garden,
    "EPC_certificate": None,
    "geo_lat": None,
    "geo_lon": None,
    "map_url": map_URL,
    "description": description,
    "key_features": json_key_features,
    "new_build": bool(soup.find('p', class_='_194zg6t9 _1wz55u83', string='New home'))
  }

  return data
