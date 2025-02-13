import requests
import json
import time
from typing import Dict, List
import uuid

class ZomatoScraper:
    def __init__(self, city_id: int, latitude: float, longitude: float, csrf_token: str, 
                 entity_id: int, entity_type: str, cookies: Dict[str, str]):
        """
        Initialize the Zomato scraper with required parameters and authentication.
        
        Args:
            city_id: Zomato city ID (e.g., 31 for Mangalore)
            latitude: Location latitude
            longitude: Location longitude
            csrf_token: CSRF token for authentication
            entity_id: Location entity ID
            entity_type: Location entity type (e.g., 'subzone')
            cookies: Dictionary of required cookies
        """
        self.base_url = 'https://www.zomato.com/webroutes/search/home'
        self.city_id = city_id
        self.latitude = latitude
        self.longitude = longitude
        self.csrf_token = csrf_token
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.search_id = str(uuid.uuid4())
        self.cookies = cookies
        
        # Complete headers from the original request
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'x-zomato-csrft': csrf_token,
            'Origin': 'https://www.zomato.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }

    def _create_payload(self, page: int = 1) -> Dict:
        """Create the request payload with all required metadata."""
        payload = {
            "context": "dineout",
            "filters": json.dumps({
                "searchMetadata": {
                    "previousSearchParams": json.dumps({
                        "PreviousSearchId": self.search_id,
                        "PreviousSearchFilter": [
                            json.dumps({"category_context": "go_out_home"}),
                            "",
                            json.dumps({"context": "dineout_home"})
                        ]
                    }),
                    "postbackParams": json.dumps({
                        "total_restaurants_shown": (page - 1) * 15,
                        "total_results_shown": (page - 1) * 15,
                        "page": page,
                        "solr_offset": (page - 1) * 15,
                        "vg_set": True,
                        "search_id": self.search_id
                    }),
                    "totalResults": 1115,
                    "hasMore": True,
                    "getInactive": False
                },
                "dineoutAdsMetaData": {},
                "appliedFilter": [
                    {
                        "filterType": "category_sheet",
                        "filterValue": "go_out_home",
                        "isHidden": True,
                        "isApplied": True,
                        "postKey": json.dumps({"category_context": "go_out_home"})
                    },
                    {
                        "filterType": "context",
                        "filterValue": "dineout_home",
                        "isHidden": True,
                        "isApplied": True,
                        "postKey": json.dumps({"context": "dineout_home"})
                    }
                ],
                "urlParamsForAds": {}
            }),
            "addressId": 0,
            "entityId": self.entity_id,
            "entityType": self.entity_type,
            "locationType": "",
            "isOrderLocation": 1,
            "cityId": self.city_id,
            "latitude": str(self.latitude),
            "longitude": str(self.longitude),
            "userDefinedLatitude": self.latitude,
            "userDefinedLongitude": self.longitude,
            "entityName": "Kodailbail, Mangaluru",
            "orderLocationName": "Kodailbail, Mangaluru",
            "cityName": "Mangalore",
            "countryId": 1,
            "countryName": "India",
            "displayTitle": "Kodailbail, Mangaluru",
            "o2Serviceable": True,
            "placeId": "ChIJpRGFv1paozsRx99KGviuZec",
            "cellId": "4297377815256367104",
            "deliverySubzoneId": 18013,
            "placeType": "GOOGLE_PLACE",
            "placeName": "Kodailbail, Mangaluru",
            "isO2City": True,
            "fetchFromGoogle": False,
            "fetchedFromCookie": True,
            "isO2OnlyCity": False,
            "address_template": [],
            "otherRestaurantsUrl": ""
        }
        return payload

    def scrape_restaurants(self, max_pages: int = 5) -> List[Dict]:
        """
        Scrape restaurant data from multiple pages.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of dictionaries containing restaurant information
        """
        all_restaurants = []
        
        for page in range(1, max_pages + 1):
            try:
                payload = self._create_payload(page)
                print("\nSending request with payload:", json.dumps(payload, indent=2))
                
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    json=payload
                )
                
                print("\nResponse status code:", response.status_code)
                print("Response headers:", dict(response.headers))
                
                try:
                    print("\nResponse content:", response.text[:500])  # Print first 500 chars of response
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"\nFailed to decode JSON response: {str(e)}")
                    print("Full response content:", response.text)
                    raise
                if 'sections' not in data or 'SECTION_SEARCH_RESULT' not in data['sections']:
                    print(f"No more results on page {page}")
                    break
                
                restaurants = data['sections']['SECTION_SEARCH_RESULT']
                for restaurant in restaurants:
                    if restaurant['type'] == 'restaurant':
                        info = restaurant['info']
                        all_restaurants.append({
                            'name': info['name'],
                            'url': f"https://www.zomato.com{info['locality']['localityUrl']}",
                            'rating': info['rating']['aggregate_rating'] if 'rating' in info else 'N/A',
                            'cuisine': [c['name'] for c in info['cuisine']] if 'cuisine' in info else [],
                            'cost_for_two': info.get('cft', {}).get('text', 'N/A'),
                            'address': info['locality']['address'] if 'locality' in info else 'N/A'
                        })
                
                print(f"Scraped page {page} - Found {len(restaurants)} restaurants")
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error on page {page}: {str(e)}")
                break
        
        return all_restaurants

def parse_cookies_from_string(cookie_string: str) -> Dict[str, str]:
    """Parse cookies from cookie header string into dictionary."""
    cookies = {}
    for cookie in cookie_string.split('; '):
        if '=' in cookie:
            name, value = cookie.split('=', 1)
            cookies[name] = value.strip('"')  # Remove any quotes
    print("\nParsed cookies:", json.dumps(cookies, indent=2))
    return cookies

def main():
    # Cookie string from the original request
    cookie_string = """AWSALBTG=QB6x9itPuxwiOcVW0eFaJIeX0QQkVQ4rXwJ2WkXl0j7Ia4pbIvN3A1eI6wwjJlQxW+W654tFMVoDGBRZ2LMHTM1QpphyTFkk78vfZkbT+EYNCzfzsRcFJwGig22lPEgte90mSoTUkPVg0jlkheLfoHUdOaZvP1HEodPZITJoerzv; AWSALBTGCORS=QB6x9itPuxwiOcVW0eFaJIeX0QQkVQ4rXwJ2WkXl0j7Ia4pbIvN3A1eI6wwjJlQxW+W654tFMVoDGBRZ2LMHTM1QpphyTFkk78vfZkbT+EYNCzfzsRcFJwGig22lPEgte90mSoTUkPVg0jlkheLfoHUdOaZvP1HEodPZITJoerzv; fbcity=31; fre=0; rd=1380000; zl=en; fbtrack=c1e5f5e9fe70e75e1ece20da5ba894c1; ltv=83931; lty=83931; csrf=745a72b5770f93f1ab402c1591c9b276; PHPSESSID=e494a3d5b4221fd2ba1af3111fc8e8f4"""
    
    cookies = parse_cookies_from_string(cookie_string)
    
    # Example usage with Mangalore/Kodailbail parameters
    scraper = ZomatoScraper(
        city_id=31,  # Mangalore
        latitude=12.877367,
        longitude=74.83755,
        csrf_token="745a72b5770f93f1ab402c1591c9b276",  # From the cookie
        entity_id=83931,  # Kodailbail entity ID
        entity_type="subzone",
        cookies=cookies
    )
    
    restaurants = scraper.scrape_restaurants(max_pages=5)
    
    # Save results to JSON file
    with open('restaurants.json', 'w', encoding='utf-8') as f:
        json.dump(restaurants, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal restaurants collected: {len(restaurants)}")

if __name__ == "__main__":
    main()