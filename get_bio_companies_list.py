# -*- coding: utf-8 -*-
"""This program reads a webpage that contains a list of biotechnology companies 
and puts it into a convenient table sorting by distance from home
Inputs:
  -z  - zip code of home
  -o - output file

--requerements.txt--
beautifulsoup4==4.12.3
bs4==0.0.2
certifi==2024.2.2
charset-normalizer==3.3.2
geographiclib==2.0
geopy==2.4.1
idna==3.6
numpy==1.26.4
pandas==2.2.1
pgeocode==0.4.1
python-dateutil==2.9.0.post0
pytz==2024.1
requests==2.31.0
six==1.16.0
soupsieve==2.5
tzdata==2024.1
urllib3==2.2.1
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.distance import geodesic
import pgeocode
from geopy.geocoders import Nominatim
import argparse

# get latitude and longitude given city name
def get_lat_log(city):
    location = geolocator.geocode(city)
    return (location.latitude, location.longitude) if location else None
    

# get latitude and lingitude given 5 digit zip code
def get_lat_log_by_zip(zip):
  nomi = pgeocode.Nominatim('us')
  a = nomi.query_postal_code('94002')
  return(a['latitude'], a['longitude']) if not a.empty else None

# get request from a webpage
def get_request(url):
  try:
    response = requests.get(url)
    if response.status_code == 200:
      return response
    else:
      print (f"Couldn't access website {url}")
  except requests.exceptions.RequestException as err:
    print(f"Connection attempt failed with error: {err}")

parser = argparse.ArgumentParser()
parser.add_argument("-z", metavar="home zip code", help="5 digit zip code of home, default = Belmont, CA", default = 94002)
parser.add_argument("-o", metavar="output_file", help="file to write table of biotech companies to", default = 'bio_companies.csv')
args = parser.parse_args()

geolocator = Nominatim(user_agent="MyApp")

def main():
  # get arguments from user input
  home_zip = args.z
  out_file = args.o

  # get contents of webpage
  url = "https://biopharmguy.com/links/company-by-name-northern-california.php"
  page = get_request(url)
  soup = BeautifulSoup(page.content, "html.parser")
  print(f"Accessed {url}")

   
  # extract information from a webpage and put it into a data frame
  classes = ['sponsor', 'even', 'odd']  #company names are under these classes in html
  company_info = [] #list of dictionaries corresponding to each company
  locations = set() #set of all locations of the companies

  for c in classes:
    for company_element in soup.find_all('tr', class_=c):
      company = {}
      if c == 'sponsor':
        company['name'] = company_element.find('img', class_='database')['alt']
      else:
        company['name'] = company_element.find('td', class_='company').get_text(strip=True)
      company['location'] = company_element.find('td', class_='location').get_text(strip=True)
      locations.add(company['location'])
      company_website = company_element.find_all('a')[1] if len(company_element.find_all('a')) == 2 else company_element.find_all('a')[0]
      company['website'] = company_website.get('href')
      company['description'] = company_element.find('td', class_='description').get_text()

      company_info.append(company)

  print ('Gathered all information about biotech companies.')
  # get home coordinates
  try:
    home_coord = get_lat_log_by_zip(home_zip)
  except:
    print ("Home coordinates couldn't be established! Using Belmont CA as home")
    home_coord = get_lat_log_by_zip(94002)

  print (f"Found home coordinates for zip code {home_zip}")
  # calculate distance from each location to home
  distances = {}
  for l in locations:
    try:
      coord = get_lat_log(l)
    except:
      coord = None
    if coord:
      distances[l] = geodesic(coord, home_coord).miles
    else:
      distances[l] = None

  print ('Found distances from home for all locations')
  # create dataframe with all companies and sort them by distance from home
  df = pd.DataFrame(company_info)
  df['distance'] = df['location'].map(distances)
  df_sorted = df.sort_values(by=['distance','location', 'description'], ascending =True)

  # write resulting dataframe to a file
  df_sorted.to_csv(out_file, index=False)
  print (f"{out_file} is complete.")

if __name__ == '__main__':
	main()
