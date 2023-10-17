import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import pymongo
from urllib.parse import urlparse


client = pymongo.MongoClient("mongodb://n2ghthack:ACSSPa$$4NHT%402@13.232.150.214:27017")
db = client['Scraping_checklist']
collection = db['Collection1']

previous_data=None

# Define the URL of the page with links to different years
sport_url = input()  
sport = re.search(r'sport-(\w+)', sport_url)
# Send an HTTP GET request to the years page
response_sport = requests.get(sport_url)

# Check if the request was successful (status code 200)
if response_sport.status_code == 200:
    # Parse the HTML content of the years page using BeautifulSoup
    soup_sport = BeautifulSoup(response_sport.text, "html.parser")
    div_attrs = {'class': 'tab-content'}  # Replace with the actual attributes

    target_div = soup_sport.find('div', attrs=div_attrs)
    
    if target_div:
        # Find all anchor tags (links) within the div
        year_links = target_div.find_all('a')
        #print(year_links)    
        for year_link in year_links:
            dir_url = year_link.get("href")
            
            response_dir = requests.get(dir_url)

            # Check if the request was successful (status code 200)
            if response_dir.status_code == 200:
                # Parse the HTML content of the years page using BeautifulSoup
                soup_dir = BeautifulSoup(response_dir.text, "html.parser")
                div_attrs1 = {'class': 'tab-content'}  # Replace with the actual attributes

                 # Find the div using the specified attributes
                target_div1 = soup_dir.find('div', attrs=div_attrs1)
               
                if target_div1:
                    # Find all anchor tags (links) within the div
                    set_links = [a for a in target_div1.find_all('a') if a.text.strip()]
                    pre_set = None
                    # Loop through each year link
                    for set_link in set_links:
                        if str(pre_set) != str(set_link):
                            pre_set = set_link
                            card_url = set_link.get("href")
                            set = set_link.text
                            #print(set)

                            response_img = requests.get(card_url)

                            # Check if the request was successful (status code 200)
                            if response_img.status_code == 200:
                                # Parse the HTML content of the years page using BeautifulSoup
                                soup_img = BeautifulSoup(response_img.text, "html.parser")
                                div_attrs2 = {'class': 'tab-content'}  # Replace with the actual attributes

                                # Find the div using the specified attributes
                                target_div2 = soup_img.find('div', attrs=div_attrs2)
                                img_links=[]
                                if target_div2:
            
                                    img_links = [a for a in target_div2.find_all('a') if a.text.strip()]
                                    print(len(img_links))
                                
                                    prev_img = None
                                    for img_link in img_links:
                                        if str(prev_img) != str(img_link):
                                            prev_img = img_link

                                            img_url = img_link.get("href")
                                            subset = img_link.text
                                            print(subset)

                                            if not img_url.endswith(".jpg"):
                                                response_get = requests.get(img_url)

                                                # Check if the request was successful (status code 200)
                                                if response_get.status_code == 200:
                                                
                                                    soup_sub_field = BeautifulSoup(response_get.text, "html.parser")
                                                    chrome_options = webdriver.ChromeOptions()
                                                    #chrome_options.add_argument('--headless')
                                                    driver = webdriver.Chrome(options=chrome_options)
                                                    driver.get(img_url)

                                                    try:
                                                        # Find all the card elements on the page
                                                        card_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'panel panel-primary')]")
                                                    
                                                        for card_element in card_elements:
                                                            # Extract data for each card
                                                            card_data = {}

                                                            # Extract title
                                                            title = card_element.find_element(By.XPATH, ".//h5[contains(@class, 'h4')]").text
                                                            card_data['season'] = title.split()[0]
                                                            # print("-------------------------------",card_data['season'])
                                                            card_data["title"] = title
                                                            card_data['set'] = set
                                                            card_data['sport'] = sport.group(1)
                                                            card_data['sub_set'] = subset
                                                            match_player = re.search(r'#\d+\s+(.+)', title)
                                                            if match_player:
                                                                card_data['player'] = match_player.group(1)
                                                            else:
                                                                card_data['player'] = None
                                                            pattern = r'#\S+'
                                                            match = re.search(pattern, title)
                                                            if match:
                                                                card_number = match.group()
                                                                card_data['Card_Number'] = card_number
                                                            else:
                                                                card_data['Card_Number'] = None

                                                            # Extract description
                                                            description_element = card_element.find_element(By.XPATH, ".//div[contains(@class, 'border-muted border-bottom mb-3 pb-1')]")
                                                            description = description_element.text.strip() if description_element else ""
                                                            card_data['Rookie'] = True if isinstance(description, str) and 'RC' in description else False
                                                            card_data['Mem'] = True if isinstance(description, str) and 'Mem' in description else False
                                                            card_data['Autograph'] = True if isinstance(description, str) and 'AUTO' in description else False
                                                            serial_match = re.search(r'serial\s*(.*)', description, re.IGNORECASE)
                                                            card_data['Serial'] = 'Serial'+ serial_match.group(1) if serial_match else None
                                                            card_data["description"] = description if description else None

                                                            des=description
                                                            des = re.sub(r'\bMem\b', '', des, flags=re.IGNORECASE)
                                                            des = re.sub(r'\bAuto\b', '', des, flags=re.IGNORECASE)
                                                            des = re.sub(r'\b\w*Serial\w*\b', '', des, flags=re.IGNORECASE)
                                                            team = re.sub(r'\bRC\b', '', des, flags=re.IGNORECASE)
                                                            if team:
                                                                card_data['team'] = team
                                                            else:
                                                                card_data['team'] = None
                                                            # Extract image URLs
                                                            image_elements = card_element.find_elements(By.XPATH, ".//a[contains(@class, 'popup-image')]")
                                                            image_urls = [img.get_attribute("href") for img in image_elements]
                                                            if image_urls:
                                                                card_data["image_urls"] = image_urls
                                                            else:
                                                                card_data['image_urls'] = None

                                                            try:
                                                                button = card_element.find_element(By.XPATH, ".//button[contains(@class, 'DynamicContent btn btn-warning d-block')]")
                                                                button.click()

                                                                price_element = card_element.find_element(By.XPATH, ".//p[contains(@class, 'view-sales-head')]")
                                                                price = price_element.text.strip()
                                                            # print(price)
                                                               
                                                                average = re.search(r'Average (\d+\.\d+)', price).group(1) if re.search(r'Average (\d+\.\d+)', price) else None
                                                                sold_for = re.search(r'Sold For (\d+\.\d+)', price).group(1) if re.search(r'Sold For (\d+\.\d+)', price) else None
                                                                sales_qnt = re.search(r'Sales: (\d+)', price).group(1) if re.search(r'Sales: (\d+)', price) else None
                                                                price = re.search(r'From (.+)', price).group(1) if re.search(r'From (.+)', price) else None
                                                                
                                                                card_data["price"] = price 
                                                                card_data['average'] = average 
                                                                card_data['sold_for'] = sold_for 
                                                                card_data['sales_qnt'] = sales_qnt 
                                                                
                                                            except Exception as e:
                                                                card_data["price"] = None
                                                                card_data['average'] = None
                                                                card_data['sold_for'] = None
                                                                card_data['sales_qnt'] = None
                                                            
                                                            table_data = []

                                                            time.sleep(2)
                                                            try:
                                                                table = card_element.find_element(By.XPATH, ".//table[contains(@class, 'table table-responsive table-bordered')]")

                                                                rows = table.find_elements(By.TAG_NAME, "tr")
                                                                for row in rows:
                                                                    row_data = [cell.text.strip() for cell in row.find_elements(By.TAG_NAME, "td")]
                                                                    if len(row_data) >= 5:  # Ensure the row contains all the required data
                                                                        sale_date, venue, price, listing_title, title = row_data[:5]  # Assuming these are in order
                                                                        
                                                                        # Create a dictionary for the sale entry
                                                                        tdata = {
                                                                            'Sale Date': sale_date,
                                                                            'Venue': venue,
                                                                            'Price': price,
                                                                            'Listing Title': listing_title,
                                                                            'Title': title
                                                                        }
                                                                        #print(sale_entry)
                                                                        table_data.append(tdata)
                                                                card_data['sales']=tdata
                                                            except:
                                                                table_data= None
                                                            
                                                            card_data['sales'] = table_data

                                                            # print(card_data)
                                                            print(" ")
                                                            data_to_insert = {
                                                                                "sport": card_data['sport'],
                                                                                "season": card_data['season'],
                                                                                "set": card_data['set'],
                                                                                "subset":card_data['sub_set'],
                                                                                "title": card_data["title"],
                                                                                "card_number": card_data['Card_Number'],
                                                                                "player_name":card_data['player'],
                                                                                "team": card_data['team'],
                                                                                "description": card_data["description"],
                                                                                "Rookie_card": card_data['Rookie'],
                                                                                "autograph": card_data['Autograph'],
                                                                                "mem": card_data['Mem'],
                                                                                "serial": card_data['Serial'],
                                                                                "image_url": card_data["image_urls"],
                                                                                "sales": card_data['sales_qnt'],
                                                                                "price": card_data["price"],
                                                                                "average_price": card_data['average'],
                                                                                "sold_for": card_data['sold_for'],
                                                                                "Sales Data": card_data["sales"]
                                                                                
                                                                            }
                                                            #print(data_to_insert)
                                                            inserted_id = collection.insert_one(data_to_insert).inserted_id
                                                            print(sport.group(1), "Data inserted with ID:", inserted_id)
                                                            

                                                    except Exception as e:   
                                                        print("------------------------------------",e)

                                                else:
                                                    print("Page unable to load")
                                            else:
                                                print("Link is an image")

                                        else:
                                            print("Link is same as previous one")

                                else:
                                    print("Failed to retrieve data from target_div2")
                                
                        else:
                            print("Link is same as previous one")

                else:
                    print("Failed to retrieve data from target_div1")


driver.quit()                                               