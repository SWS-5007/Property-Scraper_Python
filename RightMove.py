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
                if childrenClassName:
                    selected_element = sourceCode[index].find(childrenElement, class_=childrenClassName)
                else:
                    selected_element = sourceCode[index].find(childrenElement)
            else:
                selected_element = None
        else:
            if sourceCode:
                if childrenClassName:
                    selected_element = sourceCode[0].find(childrenElement, class_=childrenClassName)
                else:
                    selected_element = sourceCode[0].find(childrenElement)
            else:
                selected_element = None
        
        result = selected_element.get_text(strip=True) if selected_element else None

        if result == "Ask":
            result = None

        return result
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

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
    
def getRightMoveDetails(soup, url):
  parsed_url = urlparse(url)
  query_params = parse_qs(parsed_url.fragment)
    
  # Check for the presence of 'channel' and its value
  is_rent_or_sale = None
  if '/?channel' in query_params:
    channel_value = query_params['/?channel'][0]
    if channel_value == 'RES_LET':
      is_rent_or_sale = 'rent'
    elif channel_value == 'RES_BUY':
      is_rent_or_sale = 'sale'

  price = getElementText(soup, 'div', '_1gfnqJ3Vtd1z40MlC0MzXu', 'span', '')
  address = getElementText(soup, 'div', 'h3U6cGyEUf76tvCpYisik', 'h1', '_2uQQ3SV0eMHL1P6t5ZDo2q')
  if(address) :
    street, town, postcode = utils.extractAddressParts(address)
  else :
    address = None
    street = None
    town = None
    postcode = None
  # Floor plans
  floor_plans = [
    img['src'] 
    for a_tag in soup.find_all('a', class_='_1EKvilxkEc0XS32Gwbn-iU')
    if (img := a_tag.find('img')) is not None
  ]
        
  # Property Type, Bedrooms, Bathrooms
  dataList = soup.find_all('div', class_='_3gIoc-NFXILAOZEaEjJi1n')
  
  property_type = None
  bedrooms = None
  bathrooms = None
  size_sq_ft = None
  size_sq_mtr = None
  tenure = None
  
  for index, data in enumerate(dataList):
    text_element = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dt', 'IXkFvLy8-4DdLI1TIYLgX', index)
    if text_element == "PROPERTY TYPE":
      property_type = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
    elif text_element == "BEDROOMS":
      bedrooms = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
    elif text_element == "BATHROOMS":
      bathrooms = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
    elif text_element == "SIZE":
      size_sq_ft = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
      if "Ask" in size_sq_ft:
        size_sq_ft = None
        size_sq_mtr = None
      else:
        size_sq_mtr = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
    elif "TENURE" in text_element:
      tenure = getElementText(soup, 'div', '_3gIoc-NFXILAOZEaEjJi1n', 'dd', '_3ZGPwl2N1mHAJH3cbltyWn', index)
  
  council_tax_band_text = getElementText(soup, 'div', '_9u6R9n55iQlZi-JF6H59W', 'dd', '_2zXKe70Gdypr_v9MUDoVCm', 0)
  if council_tax_band_text:
    council_tax_band = council_tax_band_text.split(":")[-1].strip()
  else:
    council_tax_band = None
  
  parking_text = getElementText(soup, 'div', '_9u6R9n55iQlZi-JF6H59W', 'span', '_3rQAUgsu_ICdA55QUiiUxg', 1)
  parking = parking_text != "Ask agent"
  garden_text = getElementText(soup, 'div', '_9u6R9n55iQlZi-JF6H59W', 'span', '_3rQAUgsu_ICdA55QUiiUxg', 2)
  garden = garden_text != "Ask agent"

  if soup.find ('ul', class_='_1uI3IvdF5sIuBtRIvKrreQ') :
    key_features_elements = soup.find('ul', class_='_1uI3IvdF5sIuBtRIvKrreQ').find_all('li', class_='lIhZ24u1NHMa5Y6gDH90A')
    key_features = [element.get_text(strip=True) for element in key_features_elements]
    json_key_features = json.dumps(key_features)
  else : 
    json_key_features = None
  
  map_URL = getElementAttribute(soup, 'a', '_1kck3jRw2PGQSOEy3Lihgp', 'img', 'src')
  if map_URL != None:
    latitude, longitude = extract_lat_long(map_URL)
  else:
    latitude, longitude = None, None

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
    "description": soup.find(class_='STw8udCxUaBUMfOOZu0iL').get_text(strip=True),
    "key_features": json_key_features,
    "new_build": bool(soup.find('p', class_='_194zg6t9 _1wz55u83', string='New home'))
  }

  return data