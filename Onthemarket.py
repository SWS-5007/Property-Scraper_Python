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
    
def getOnthemarketDetails(soup, url):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
      
  # Check for the presence of 'channel' and its value

  property_title = utils.getElementTextByDataTest(soup, "data-test", "property-title")
  is_rent_or_sale = None
  if 'sale' in property_title.lower():
    is_rent_or_sale = 'sale'
  elif 'rent' in property_title.lower():
    is_rent_or_sale = 'rent'

  price = utils.getElementTextByDataTest(soup, "data-test", "property-price")
  address = utils.getElementTextBySelector(soup, '.text-slate.leading-none', 0)
  if address :
    street, town, postcode = utils.extractAddressPartsUpdate(address)
  else:
    address = None
    street = None
    town = None
    postcode = None
  
  try:
    floor_plans = [
      img['src'] 
      for a_tag in soup.select('a.flex-shrink-0 div.select-none')[1].find_all('img')
      if (img := a_tag.find('img')) is not None
    ]
  except (IndexError, AttributeError):
    floor_plans = None

  try:
    map_URL = [
      img['src'] 
      for a_tag in soup.select('a.flex-shrink-0 div.select-none')[0].find_all('img')
      if (img := a_tag.find('img')) is not None
    ]
  except (IndexError, AttributeError):
    map_URL = None

  # utils.getElementTextByDataTest(soup,  "data-test", "media-pills").getElementText('a','flex-shrink-0', None, None, 1)

  # Property Type, Bedrooms, Bathrooms
  
  property_type = None
  bedrooms = None
  bathrooms = None
  size_sq_ft = None
  size_sq_mtr = None
  tenure = None
  
  property_type = utils.getElementTextBySelector(soup, ".gdk9FE div", None)
  bedrooms_text = utils.getElementTextBySelector(soup, ".block .text-xs .leading-none", 0)
  bedrooms_match = re.search(r'\d+', bedrooms_text)
  if bedrooms_match:
    bedrooms = int(bedrooms_match.group())
  bathrooms_text = utils.getElementTextBySelector(soup, ".block .text-xs .leading-none", 1)
  bathrooms_match = re.search(r'\d+', bathrooms_text)
  if bathrooms_match:
    bathrooms = int(bathrooms_match.group())
  size_text = utils.getElementTextBySelector(soup, ".block .text-xs .leading-none", 2)
  
  # Extract size_sq_ft and size_sq_mtr from size_text
  size_sq_ft = None
  size_sq_mtr = None
  if size_text:
    size_match = re.search(r'(\d+)\s*sq\s*ft\s*/\s*(\d+)\s*sq\s*m', size_text)
    if size_match:
      size_sq_ft = size_match.group(1)
      size_sq_mtr = size_match.group(2)

  # Extract tenure and council_tax_band
  key_info_divs = soup.select('section > div.text-body.text-denim.mt-5 > div')
  
  if key_info_divs:
    for div in key_info_divs:
      title = div.find('span', class_='whitespace-nowrap float-left font-bold').get_text(strip=True)
      value = div.select('span')[1].get_text(strip=True)
      if 'Tenure' in title:
        tenure = value
      elif 'Council tax' in title:
        council_tax_band = value

  description = soup.find('div', itemprop='description').get_text(strip=True)
  parking = 'parking' in description.lower()
  garden = 'garden' in description.lower()

  key_features_elements = soup.select_one('section > div.text-body.text-denim.mt-5 > div').find_all('div')
  key_features = [element.get_text(strip=True) for element in key_features_elements]
  json_key_features = json.dumps(key_features)

  map_URL = utils.getElementAttribute(soup, 'a', '.select-none img', 'img', 'src')
  if map_URL != None:
    latitude, longitude = extract_lat_long(map_URL)
  else:
    latitude, longitude = None, None

  data = {
    "Number": None,
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
    "geo_lat": latitude,
    "geo_lon": longitude,
    "map_url": map_URL,
    "description": description,
    "key_features": json_key_features,
    "new_build": bool(soup.select_one('qlVuSS select-none', string='New build'))
  }

  return data