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

def getSpareroomDetails(soup, url):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
      
  # Check for the presence of 'channel' and its value

  price = None
  street = None  
  town = None
  postcode = None
  property_type = None
  description = None
  is_rent_or_sale = None

  price = utils.getElementTextBySelector(soup, 'feature--price_room_only .feature-list .feature-list__key', 0)
  street = utils.getElementTextBySelector(soup, '.feature--details .key-features .key-features__feature', 1)
  town = utils.getElementTextBySelector(soup, '.feature--details .key-features .key-features__feature', 3)
  postcode = utils.getElementTextBySelector(soup, '.feature--details .key-features .key-features__feature', 2)
  property_type = utils.getElementTextBySelector(soup, '.feature--details .key-features .key-features__feature', 0)
  description = utils.getElementTextBySelector(soup, '.listing__content .detaildesc')

  is_rent_or_sale = None
  if description:
    if 'sale' in description.lower():
      is_rent_or_sale = 'sale'
    elif 'rent' in description.lower():
      is_rent_or_sale = 'rent'

  # Extract amenities
  amenities = {}
  amenities_section = soup.select_one('.feature--amenities .feature-list')
  if amenities_section:
    for dt, dd in zip(amenities_section.find_all('dt', class_='feature-list__key'), amenities_section.find_all('dd', class_='feature-list__value')):
      key = dt.get_text(strip=True)
      value = dd.get_text(strip=True)
      amenities[key] = value

  parking = amenities.get('Parking', 'No').lower() == 'yes'
  garden = amenities.get('Garden/patio', 'No').lower() == 'yes'


  key_features_elements = soup.select_one('.feature--amenities .feature-list')
  key_features = {}
  if key_features_elements:
    for dt, dd in zip(key_features_elements.find_all('dt', class_='feature-list__key'), key_features_elements.find_all('dd', class_='feature-list__value')):
      key = dt.get_text(strip=True)
      value = dd.get_text(strip=True)
      key_features[key] = value
  json_key_features = json.dumps(key_features)

  data = {
    "number": None,
    "Name": None,
    "street": street,
    "town": town,
    "postcode": postcode,
    "price": price,
    "sale_type": is_rent_or_sale,
    "property_type": property_type,
    "tenure": None,
    "bedrooms": None,
    "bathrooms": None,
    "reception_rooms": None,
    "size_sq_ft": None,
    "size_sq_mtr": None,
    "floor_plans": None,
    "council_tax_band": None,
    "parking": parking,
    "garden": garden,
    "EPC_certificate": None,
    "geo_lat": None,
    "geo_lon": None,
    "map_url": None,
    "description": description,
    "key_features": json_key_features,
    "new_build": None
  }

  return data
