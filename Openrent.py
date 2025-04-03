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

def extract_number(text):
  match = re.match(r"(\d+)", text)
  if match:
    return match.group(1)
  return None

def get_street_and_postcode(scraped_text):
    # Define the regex pattern to extract the street and postcode
    pattern = r'^(.*?),\s*([A-Z0-9]+\s?[A-Z0-9]+)$'
    
    match = re.search(pattern, scraped_text)
    if match:
        # Extract the street and postcode using groups
        street = match.group(1).strip()
        postcode = match.group(2).strip()
        return street, postcode
    else:
        return None, None

def getOpenRentDetails(soup, url):
  parsed_url = urlparse(url)

  price = utils.getElementTextBySelector(soup, '.vstack .fw-semibold', 0)
  address = utils.getElementTextBySelector(soup, '.listing__content h1')

  if address : 
    street, postcode = get_street_and_postcode(address)
  else:
    address = None
    street = None
    postcode = None

  property_type = None
  if address : 
    for p_type in property_types:
      if p_type in address.lower():
        property_type = p_type
        break
  else:
    property_type = None

  # Extract bedrooms and bathrooms
  overview_section = soup.select_one('.listing__content ul.align-items-center')
  bedrooms = None
  bathrooms = None
  town = None
  if overview_section:
    for div in overview_section.find_all('li', class_='align-items-center'):
      dt = div.select_one('.text-secondary-emphasis span')
      dd = div.find('span', class_='text-secondary-emphasis')
      if dt and dd:
        title = dt.get_text(strip=True).lower()
        value = dd.get_text(strip=True)
        if 'bedrooms' in title:
          bedrooms = extract_number(value)
        elif 'bathrooms' in title:
          bathrooms = extract_number(value)
        elif 'location' in title:
          town = value
  
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
  if key_info_divs:
    for div in key_info_divs:
      title = div.find('span', class_='nts_label').get_text(strip=True)
      value = div.find('div', class_='nts_value').get_text(strip=True)
      if 'Tenure' in title:
        tenure = value
      elif 'Council tax' in title:
        council_tax_band = value
  else:
    tenure = None
    council_tax_band = None

  description = soup.select_one('#descriptionText').get_text(strip=True)

  parking = False
  garden = False

  key_features_elements = soup.select('div.listing.container-xl.mx-auto.gap-2.gap-md-4.vstack.gap-0 > div.listing__content.d-grid.row-gap-4.row-gap-md-6.px-2.py-1.pe-md-3.py-md-0.py-xl-2.pe-xl-8.vstack.gap-4 > div.p-3.p-md-4.p-lg-6.rounded-3.bg-white > div > div')
  for featured_title in key_features_elements:
    if featured_title.select_one('h2').get_text(strip=True).lower() == 'features':
      table_element = featured_title

  for tr in table_element.select('table tr'):
    td_key = tr.find('td', class_='fw-medium')
    td_value = tr.find('td', class_='lucide')
    if td_key and td_value:
      key = td_key.get_text(strip=True).lower()
      value_class = td_value.find('svg').get('class', [])
      if 'parking' in key:
        parking = 'lucide-check' in value_class
      elif 'garden' in key:
        garden = 'lucide-check' in value_class


  key_features = [element.get_text(strip=True) for element in key_features_elements]
  json_key_features = json.dumps(key_features)
  
  # Floor plans
  floor_plan = None

  try:
    map_URL = soup.select_one('#staticGoogleMap').get('src')
  except (IndexError, AttributeError):
    map_URL = None

  data = {
    "number": None,
    "name": address,
    "street": street,
    "town": town,
    "postcode": postcode,
    "price": price,
    "sale_type": 'rent',
    "property_type": property_type,
    "tenure": tenure,
    "bedrooms": bedrooms,
    "bathrooms": bathrooms,
    "reception_rooms": None,
    "size_sq_ft": size_sq_ft,
    "size_sq_mtr": size_sq_mtr,
    "floor_plans": floor_plan,
    "council_tax_band": council_tax_band,
    "parking": parking,
    "garden": garden,
    "EPC_certificate": None,
    "geo_lat": None,
    "geo_lon": None,
    "map_url": map_URL,
    "description": description,
    "key_features": json_key_features,
    "new_build": None
  }

  return data
