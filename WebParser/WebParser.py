# -*- coding: iso-8859-1 -*- 
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json


class FlyerParser:
    """Parser class for extracting supermarket flyers."""
    
    def __init__(self, url):
        """Initialize the parser with the provided URL."""
        self.url = url

    def get_html(self, url):
        """Fetch the HTML content of the given URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching URL '{url}': {e}")
            return None

    def get_shop_links(self):
        """Retrieve shop links from the main page."""
        html = self.get_html(self.url)
        if html is None:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        shop_list = soup.select('#left-category-shops a')
        return [(shop.text.strip(), f"https://www.prospektmaschine.de{shop['href']}") for shop in shop_list]

    def is_flyer_valid(self, title, shop_name):
        """Check if the flyer title contains the shop name."""
        return shop_name.lower() in title.lower()

    def get_shop_details(self, shop_url, shop_name):
        """Get details for flyers available at the specified shop URL."""
        html = self.get_html(shop_url)
        if html is None:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('div', class_=lambda x: x and 'grid-item box' in x)

        results = []  # List to store flyer details
        now = datetime.now()

        for item in items:
            title = item.find('a')['title'] if item.find('a') and 'title' in item.find('a').attrs else None
            
            if title and self.is_flyer_valid(title, shop_name):
                img_link = self.get_image_link(item)
                valid_dates = self.extract_valid_dates(item, now)

                if valid_dates:
                    valid_from, valid_to = valid_dates
                    if valid_from <= now <= valid_to:
                        results.append({
                            'title': title,
                            'thumbnail': img_link,
                            'shop_name': shop_name,
                            'valid_from': valid_from.strftime("%Y-%m-%d"),
                            'valid_to': valid_to.strftime("%Y-%m-%d"),
                            'parsed_time': now.strftime("%Y-%m-%d %H:%M:%S")
                        })

        return results

    def get_image_link(self, item):
        """Get the image link of the flyer item."""
        img_tag = item.find('img')
        return img_tag['src'] if img_tag and 'src' in img_tag.attrs else img_tag.get('data-src')

    def extract_valid_dates(self, item, now):
        """Extract and parse the validity dates from the flyer item."""
        date_tag = item.find('small', class_='visible-sm')
        date_text = date_tag.get_text(strip=True) if date_tag else None

        if date_text:
            valid_dates = date_text.split(' - ')
            if len(valid_dates) == 2:
                start_date_str = valid_dates[0].strip()
                end_date_str = valid_dates[1].strip()

                start_date = self.parse_date(start_date_str, now.year)
                end_date = self.parse_date(end_date_str, now.year)

                return start_date, end_date
        return None

    def parse_date(self, date_str, current_year):
        """Parse a date string and append the current year if needed."""
        if date_str.count('.') == 2 and len(date_str.split('.')[-1]) == 0:
            date_str += str(current_year)

        try:
            return datetime.strptime(date_str, "%d.%m.%Y")
        except ValueError as ve:
            print(f"Error while processing date '{date_str}': {ve}")
            return None


def save_to_json(data, filename):
    """Save the flyer data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def main():
    """Main function to execute the flyer parser."""
    parser = FlyerParser("https://www.prospektmaschine.de/hypermarkte/")
    shop_links = parser.get_shop_links() 

    all_results = []  # List to store all flyer information

    for shop_name, shop_url in shop_links:
        print(f"Processing shop: {shop_name}, URL: {shop_url}")
        item_details = parser.get_shop_details(shop_url, shop_name)  
        all_results.extend(item_details)

    save_to_json(all_results, 'flyer.json')
    print("Information has been stored in 'flyer.json'.")


if __name__ == "__main__":
    main()