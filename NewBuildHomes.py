from urllib.parse import urlparse, parse_qs
import utils
import re
import json

property_types = [
  "residential terraced",
  "residential end-terrace",
  "residential semi-detached",
  "residential detached",
  "residential cottage",
  "residential flat",
  "commercial retail",
  "commercial office",
  "commercial warehouse"
]

def get_property_type_index(property_type_text):
  """Returns the index of the property type text from the list."""
  property_type_text = property_type_text.lower()
  for index, property_type in enumerate(property_types):
    if property_type_text in property_type:
      return index
  return -1  # Return -1 if the property type is not found

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

def extract_lat_long(url):
  # Define a regex pattern to find latitude and longitude
  pattern = r"q=([-+]?\d*\.\d+),([-+]?\d*\.\d+)"
  
  # Search for the pattern in the URL
  match = re.search(pattern, url)
  if match:
    latitude = float(match.group(1))
    longitude = float(match.group(2))
    return latitude, longitude
  else:
    return None, None
    
def getNewBuildHomesDetails(soup, url):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
    
  # Check for the presence of 'channel' and its value
  is_rent_or_sale = None
  if 'sale' in url:
    is_rent_or_sale = 'sale'
  elif 'rent' in url:
    is_rent_or_sale = 'rent'

  price = None
  
  parentElement = utils.getElementTextBySelector(soup, 'body > div.min-h-screen.flex.flex-col > div > div > nav')
  if parentElement:
    town = utils.getElementTextBySelector(soup, 'body > div.min-h-screen.flex.flex-col > div > div > nav > a:nth-child(3)')
    street = utils.getElementTextBySelector(soup, 'body > div.min-h-screen.flex.flex-col > div > div > nav > a:nth-child(5)')
  else:
    town = None
    street = None
  postcode = None

  # Floor plans
  floor_plans = None
        
  # Property Type, Bedrooms, Bathrooms
  
  property_type = None
  bedrooms = None
  bathrooms = None
  size_sq_ft = None
  size_sq_mtr = None
  tenure = None
  description = None
  latitude = None
  longitude = None
  
  description = utils.getElementTextBySelector(soup, '.blog-content .leading-relaxed')
  
  key_features_elements = soup.select('div.property-features > div > div.items-center')
  key_features = [element.get_text(strip=True) for element in key_features_elements]
  json_key_features = json.dumps(key_features)
  
  map_URL_soruce = soup.select_one('body > div.min-h-screen.flex.flex-col > div > div > div > div > div:last-child > iframe')
  if map_URL_soruce:
    map_URL = map_URL_soruce.get('src')
  else:
    map_URL = None
  if map_URL != None:
    latitude, longitude = extract_lat_long(map_URL)
  else:
    latitude, longitude = None, None

  data = {
    "Number": None,
    "Name": None,
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
    "council_tax_band": None,
    "parking": None,
    "garden": None,
    "EPC_certificate": None,
    "geo_lat": latitude,
    "geo_lon": longitude,
    "map_url": map_URL,
    "description": description,
    "key_features": json_key_features,
    "new_build": None
  }

  return data

# Price Issue