import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import utils

# _api_server = 'http://65.108.207.102:8002'
_api_server = 'https://controllerserver.zgo.uk'
_driver = None

_site_map = {
  'https://www.rightmove.co.uk': {
    'next_button': 'button.pagination-button.pagination-direction--next',
    'cookie_button': '#onetrust-reject-all-handler',
    'next_loading_element': '.searchLoading.searchLoading--active',
    'page_loading_element': '',
    'link_selector': 'a.propertyCard-link',
  },
  'https://www.zoopla.co.uk': {
    'next_button': '._14xj7k70 ._14bi3x329._14bi3x31e > a',
    'cookie_button': ['._1eyq7orc._1eyq7ore._1eyq7orm._1eyq7ort ._1stqcn1._1stqcn4._1stqcn9', '#usercentrics-root@.sc-eeDRCY.fnyekb > button:nth-child(2)'],
    'next_loading_element': '.searchLoading.searchLoading--active',
    'page_loading_element': '._1c20rz90',
    'link_selector': '.dkr2t86 a._1lw0o5c2',
  },
  'https://www.newbuildhomes.org': {
    'next_button': '.mt-6.flex.justify-between.items-center button:nth-child(3)',
    'cookie_button': '',
    'next_loading_element': '.mt-6.flex.justify-between.items-center .inline-block.animate-spin',
    'page_loading_element': '',
    'link_selector': '.bg-white.rounded-lg.overflow-hidden.shadow-sm > a',
  },
  'https://www.onthemarket.com': {
    'next_button': 'a.order-last',
    'cookie_button': '#cookie-notification button',
    'next_loading_element': '.react-loading-skeleton',
    'page_loading_element': '',
    'link_selector': 'li.otm-PropertyCard .title > a',
  },
  'https://www.primelocation.com': {
    'next_button': '.paginate.bg-muted > a:last-child',
    'cookie_button': '#usercentrics-root@.sc-eeDRCY.fnyekb > button:nth-child(2)',
    'next_loading_element': '',
    'page_loading_element': '',
    'link_selector': '.listing-results-wrapper a.photo-hover',
  },
  'https://www.spareroom.co.uk': {
    'next_button': '#paginationNextPageLink',
    'cookie_button': '#onetrust-accept-btn-handler',
    'next_loading_element': '',
    'page_loading_element': '',
    'link_selector': 'a.listing-card__link',
  },
  'https://www.openrent.co.uk': {
    'next_button': '',
    'cookie_button': '',
    'next_loading_element': '#LoadingMoreProperties',
    'page_loading_element': '#page-loader',
    'link_selector': 'a.pli.clearfix',
  },
  'https://www.home.co.uk': {
    'next_button': '.property-results-nav.property-results-nav-top span.bluebold:nth-of-type(3) + a.homeco_v6_results_pagelink',
    'cookie_button': ['.fc-cta-do-not-consent', 'input[name="agree_to_cookies"]'],
    'next_loading_element': '',
    'page_loading_element': '',
    'link_selector': '.property-listing__title a.house_link',
  }
}

def scrape_page(page_source, domain):
    soup = BeautifulSoup(page_source, 'html.parser')
    
    links = [link.get('href') for link in soup.select(_site_map[domain]['link_selector'])]
    links = list(set([
      link if link and (link.startswith('https://') or link.startswith('http://')) else f"{domain}{link}" 
      for link in links if link is not None
    ]))

    utils.printLog(f'----- found {len(links)} links -----')
    return links

def nextPage(driver, domain):
  process_cookie_consent(driver, domain)
  
  if domain == 'https://www.openrent.co.uk':
    # Scroll down to the end of the page on openrent website.
    old_item_count = len(driver.find_elements(By.CSS_SELECTOR, _site_map[domain]['link_selector']))

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    if (_site_map[domain]['next_loading_element'] != ''):
      wait_for_loading_to_disappear(driver, _site_map[domain]['next_loading_element'])

    new_item_count = len(driver.find_elements(By.CSS_SELECTOR, _site_map[domain]['link_selector']))
    return old_item_count != new_item_count
  else:
    #  Click Next button for other pages.
    try:
      next_button = driver.find_element(By.CSS_SELECTOR, _site_map[domain]['next_button'])
      button_text = next_button.text.strip()
      if ("Next" in button_text or ">>" in button_text or domain == 'https://www.home.co.uk') and next_button.is_displayed() and next_button.is_enabled():
        # next_button.click()
        driver.execute_script("arguments[0].click();", next_button)
        if domain == 'https://www.zoopla.co.uk':
          utils.verify_cloudflare_recaptcha(driver)
          process_cookie_consent(driver, domain)
        if (_site_map[domain]['next_loading_element'] != ''):
          wait_for_loading_to_disappear(driver, _site_map[domain]['next_loading_element'])
        return True
      else:
        return False
    except Exception as e:
      utils.printLog("Next button error:", e)
      return False
  
def process_cookie_consent(driver, domain):
    try:
      cookie_selectors = _site_map[domain]['cookie_button']
      if cookie_selectors == '':
        return
      
      if isinstance(cookie_selectors, str):  
        cookie_selectors = [cookie_selectors]

      for selector in cookie_selectors:
        if '@' in selector:
          parent_selector, button_selector = selector.split('@', 1)

          shadow_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, parent_selector))
          )

          shadow_root = shadow_host.shadow_root

          cookie_button = WebDriverWait(shadow_root, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
          )
          cookie_button.click()
        else:
          cookie_buttons = driver.find_elements(By.CSS_SELECTOR, selector)

          for cookie_button in cookie_buttons:
            if cookie_button.is_displayed() and cookie_button.is_enabled():
              cookie_button.click()
    except Exception as e:
        # utils.printLog(f"Error in processing cookie consent: {e}")
        pass
  
def wait_for_loading_to_disappear(driver, loading_class, timeout=10):
  try:
    WebDriverWait(driver, timeout).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, loading_class))
    )
  except Exception as e:
    utils.printLog("Error while waiting for loading class:", e)
    
def post_search_result(search_page, links):
  post_data = {
    'search_page_id': search_page['id'],
    'links': links,
  }
  result = utils.api_post(f"{_api_server}/api/pages/save-pages", post_data)
  utils.printLog(result)
 
def run():
  global _driver
  search_pages = utils.api_get(f"{_api_server}/api/search-pages/all")

  for index, search_page in enumerate(search_pages):
    try:
      domain = utils.get_domain(search_page['link'])
      page = 1
      
      utils.printLog(f"scraping {search_page['link']}...")
      if (index % 5 == 0): # re-open brwoser every N websites to clear memory leaks
        utils.printLog(f"opening new browser")
        _driver = utils.openNewBrowser(_driver)
        utils.printLog(f"opened new browser")
      utils.printLog(f"----- page: {page} -----")

      _driver.get(search_page['link'])
      time.sleep(3)

      utils.verify_cloudflare_recaptcha(_driver)
      if (_site_map[domain]['page_loading_element'] != ''):
        wait_for_loading_to_disappear(_driver, _site_map[domain]['page_loading_element'])

      links = scrape_page(_driver.page_source, domain)
      time.sleep(1)
      
      while(nextPage(_driver, domain)):
        page = page + 1
        utils.printLog(f"----- page: {page} -----")

        time.sleep(3)
        links = links + scrape_page(_driver.page_source, domain)
        time.sleep(3)

      utils.printLog(f"saving scraping result of {search_page['link']}...")
      print('')
      post_search_result(search_page, links)
    except Exception as e:
      utils.printLog(f"skip to next search page due to error on the above page: ", e)
      print('')
      pass

def main():
  while(True):
    run()
    time.sleep(60)

main()
