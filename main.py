# libraries required for this script to work
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
import io
from PIL import Image
import pandas as pd

# Press Ctrl+Alt+N to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# path for Chrome web driver (CHANGE TO SUIT SYSTEM)
PATH = r'D:\ProjectsPython\WebScrapingExercises\drivers\chromedriver.exe'

# web driver (Chrome in this case)
wd = webdriver.Chrome()

# timeout (in seconds), so will stop request if no response in this amount of time
timeout = 5

# used to trick websites into identifying scraper as real user, common headers from:
#       https://oxylabs.io/blog/5-key-http-headers-for-web-scraping
headers = {
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0',
    'Accept-Language':'en-US',
    'Accept-Encoding':'gzip, deflate',
    'Accept':'text/html',
    'Referer':'http://www.google.com/',
}



def scrape_input(url = ''):
    # input options for scraping
    print('---[ Web Scraping Tools]---')
    while url == '':
        url = input('Please specify URL to scrape from: ')

    url = validate_url_end(url)
    print('\n--Tools--')
    print('1. Scrape images')
    print('2. Scrape external links')
    print('3. Scrape a specific element text')
    num = input('Which tool would you like to use? (1-3) ')
    while num not in ['1', '2', '3']:
        num = input('Please specify one of listed options: (1-3) ')
    num = int(num)
    # cases for which tool to use
    match num:
        case 1:
            scrape_images(url)
        case 2:
            scrape_external_links(url)
        case 3:
            scrape_element_text(url)
        case _:
            print('Invalid option, quitting program')


# ensures there is '/' after .com or .org, or whatever
def validate_url_end(url):
    if url.count('/') < 3:
        url += '/'
    return url

# checks with base url because some elements on site have links relative to webpage, so they are missing base url
# of https://.../ so we need to add it back in
#       e.g. instead of https://.../links/link_1 it may just be /links/link_1
#       so we need to add the address back in before the href link, if that is the case
def validate_url_https(base_url, url):
    if url is not None:
        # checks if url is a FULL website address URL, and NOT just relative to webpage
        if 'https://' not in url and url != '':
            # base url for links that drop it at start (so find the third /, BECAUSE: https://.../rest-of-site)
            count = i = 0
            while count < 3 and i < len(base_url):
                if base_url[i] == '/':
                    count += 1
                i += 1
            # this is actually NOT required because links automatically account for multiple / after .com,
            # for example https://www.google.com/search is same as https://www.google.com//////////search
            # BUT this simplifies the link by removing any extra slashes directly after the domain
            if base_url[i - 1] == '/' and url[0] == '/':
                i -= 1
            base_url = base_url[:i]
            url = base_url + url
        return url


# downloads a single image
def download_image(download_path, url, file_name, base_url):
    if url is not None:
        # parse the URL into its components:
        #   scheme:     'https'                 (the protocol)
        #   netloc:     'example.com'           (the domain or "net"work "loc"ation)
        #   path:       '/image.jpg'            (the path to the image)
        #   params:     ''                      (NOT the same as query parameters, seen below)
        #   query:      'size=100%&format=jpg'  (the query string)
        #   fragment:   ''                      (internal page reference e.g. #top in https://.../page#top)
        parsed_url = urlparse(url)
        # indexing above, grabbing the query as a dictionary
        query_params = parse_qs(parsed_url.query)
        # add/modify size
        query_params['size'] = ['100%']
        # rebuild query using new query parameters, doseq=True removes the padding of HTML [] around values
        new_query = urlencode(query_params, doseq=True)
        # rebuild url (the parsed one we have near the start of function) by replacing its old query with the new one
        new_url = parsed_url._replace(query=new_query)
        # convert (unparse) url back into a string
        url = urlunparse(new_url)

        # # OLD NAIVE WAY, this works for simple cases BUT is less robust BECAUSE if link already has parameter like:
        # #     ?format=jpg
        # # would result in:
        # #     ?format=jpg?size=100%
        # # which breaks link, should instead change to:
        # #     ?format=jpg&size=100%
        # # because ? already exists, so we are just adding on more query parameters
        # url += '?size=100%' # ensures image is at full HD capacity by adding size parameter

        # this is the main page url site, because some links do not include the 'https://.../', so this needs to be
        # re-added if doesnt exist in the current link
        url = validate_url_https(base_url, url)
        print(url)
        image_content = requests.get(url, headers=headers).content # get content at url, i.e. image content
        image_file = io.BytesIO(image_content) # storing binary data of image in memory

        # catches error that may occur if image binary data is unreadable
        try:
            image = Image.open(image_file) # convert data to an image so we can save it
            file_path = download_path + file_name # file path of downloaded image
            # open file with write bytes option
            with open(file_path, 'wb') as f:
                image.save(f, 'PNG') # save file in desired format

            print("Success!") # print if successful
        except:
            print(f'Image {image_file} not valid in memory')
    else:
        print(f'Invalid URL: {url}')



def scrape_images(url):
    if url == '':
        print('No URL specified')
    else:
        print("START")
        res = requests.get(url, headers=headers, timeout=timeout)
        print("request successful")
        print(res.headers['Content-Type'], '\n\n') # check content type (e.g. text, json, etc.)
        soup = BeautifulSoup(res.content, 'lxml')
        results = []
        for s in soup.find_all():
            name = s.find('img')
            if name is not None:
                if name.get('src') not in results:
                    results.append(name.get('src'))
        for i in range(len(results)):
            name = 'test_' + str(i) + '.png'
            download_image('img\\', results[i], name, url)

def scrape_external_links(url):
    if url == '':
        print('No URL specified')
    else:
        res = requests.get(url, headers=headers)
        print(res.headers['Content-Type'], '\n\n') # check content type (e.g. text, json, etc.)
        soup = BeautifulSoup(res.content, 'lxml')
        results = []
        for s in soup.find_all():
            name = s.find('a')
            if name is not None:
                # get href link from the hyperlink tag
                source = name.get('href')
                # the base_url needs to be added because the link may be missing the website address
                source = validate_url_https(url, source)
                if source not in results and source is not None:
                    results.append(source)
                    print(source)


# url is a string
def scrape_element_text(url):
    element = input('Specify element to scrape: \n(click enter to leave empty, will scrape text from ALL elements) ')
    res = requests.get(url, headers=headers)
    print(res.headers['Content-Type'], '\n\n') # check content type (e.g. text, json, etc.)
    soup = BeautifulSoup(res.content, 'lxml')

    # for i in soup.find_all():
    #     print(i.text)

    if element == '':
        for i in soup.find_all():
            print(i.text)
    else:
        for i in soup.find_all(element):
            print(i.text)


def scrape_json(url):
    if url == '':
        print('No URL specified')
    else:
        res = requests.get(url, headers=headers)
        # check if content type of link is json file
        if res.headers['Content-Type'] == 'application/json':
            print('JSON!!!')
            res = res.json() # converts json file to python dict, so we can work with it
            # converts to tabular format so we can represent data better
            records1 = pd.DataFrame.from_records(res['records'])
            print(records1)
            records1.to_csv("files/records1.csv")



            records = []
            chunk_size = 10
            offset = 0
            offset_cutoff = 500 # maximum we want offset to reach
            print(f'offset will cut off at: {offset_cutoff}')

            # the dataset is HUGE, so need to add offset cutoff
            while offset < offset_cutoff:
                param_values = {'load_amount': chunk_size, 'offset': offset}
                current_request = requests.get(url, params=param_values)
                # status code 200 means request was successful
                if current_request.status_code == 200:
                    # check if records key is in request
                    if 'records' in current_request.json():
                        fetched_records = current_request.json()['records']
                    else:
                        fetched_records = []
                    # if our list of records is empty
                    if fetched_records == []:
                        break
                    # append record data on end of current records
                    records.extend(fetched_records)
                    offset += chunk_size  # add 10 to offset (moving to next chunk)
                # otherwise was unsuccessful
                else:
                    print(f"Request failed with status code: {current_request.status_code}")
                    break
                print(f'offset: {offset}')
            # for offset in range(0, 50, 10):
            #     param_values = {'load_amount': 10, 'offset': offset}
            #     current_request = requests.get(url, params=param_values)
            #     records.extend(current_request.json()['records'])


            ## convert list of dicts to a `DataFrame`
            records_final = pd.DataFrame.from_records(records)

            # write the data to a file.
            records_final.to_csv("files/records_final.csv")

            print(records_final)
            # soup = BeautifulSoup(res.content, 'lxml')
            # results = []
            # for s in soup.find_all():
            #     name = s.find('a')
            #     if name is not None:
            #         # get href link from the hyperlink tag
            #         source = name.get('href')
            #         # the base_url needs to be added because the link may be missing the website address
            #         source = validate_url_https(url, source)
            #         if source not in results and source is not None:
            #             results.append(source)
            #             print(source)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # pass in site url (for this example using ancient rome article from history.com)
    my_url = 'https://www.history.com/topics/ancient-rome/ancient-rome'
    scrape_input(my_url) # if no input, function will ask for url input



    # json_url = 'https://www.sample.com'
    # scrape_json(json_url)


    print('\n\n\nEnd of main')
