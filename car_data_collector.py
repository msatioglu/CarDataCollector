import csv
from bs4 import BeautifulSoup
from requests import get
from collections import deque
import re
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

headers = ({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit\
/537.36 (XHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'})

pag_size = 50
base_page_url = "https://www.arabam.com"
search_page_base_url = "https://www.arabam.com/ikinci-el/otomobil/"
HTML_PARSER = 'html.parser'


def collect_car_brands():
    car_brand_names = []
    car_brand_counts = []

    response = get(search_page_base_url, headers=headers)
    html_soup = BeautifulSoup(response.text, HTML_PARSER)

    car_brands_content_list = html_soup.find_all('a', attrs={'class': 'list-item'})
    for car_brand_name in car_brands_content_list:
        car_brand_name = car_brand_name.text \
            .replace('\n\n\n', '') \
            .replace('\n\n', '') \
            .replace('\n', '') \
            .replace('\r\n', '') \
            .replace('\r', '') \
            .replace('-', '') \
            .replace(' ', '')

        if len(re.findall(r'[A-Z]', car_brand_name)) == 2:
            second_capital_letter_index = ''
            capital_letter_counter = 0
            current_char_index = 0
            for c in car_brand_name:
                if c.isupper():
                    capital_letter_counter = capital_letter_counter + 1
                    if capital_letter_counter == 2:
                        second_capital_letter_index = current_char_index
                current_char_index = current_char_index + 1
            car_brand_name = car_brand_name[:second_capital_letter_index] + '-' + car_brand_name[
                                                                                  second_capital_letter_index:]

        car_brand_name = car_brand_name.lower()
        car_brand_names.append(car_brand_name)

    car_brand_names.pop(0)  # pop the first unnecessary element
    car_brand_names.pop(0)  # pop the first unnecessary element

    car_brands_content_list = html_soup.find_all('span', attrs={'class': 'dib list-item-count pl4'})
    for car_brand_count in car_brands_content_list:
        car_brand_count = car_brand_count.text \
            .replace('\n\n\n', '') \
            .replace('\n\n', '') \
            .replace('\n', '') \
            .replace('\r\n', '') \
            .replace('\r', '') \
            .replace('(', '') \
            .replace(')', '') \
            .replace('.', '') \
            .replace(' ', '')

        car_brand_counts.append(int(car_brand_count))

    # put the car brands and car counts into a dictionary
    car_brand_count_dict = dict(zip(car_brand_names, car_brand_counts))
    # return a sorted list of top 10 items with key value pairs
    sorted_car_brand_count_dict = sorted(car_brand_count_dict.items(), key=lambda value: value[1], reverse=True)[:10]

    return sorted_car_brand_count_dict


car_brands = collect_car_brands()

global car_general_content_dict
car_general_content_dict = dict()

global car_all_info_combined_dict
global car_all_info_combined_list
car_all_info_combined_list = []


def process_url_and_extract_data(ad_url):
    browser = webdriver.Chrome('C:/PythonProjects/PythonCarDataCollector/chromedriver.exe')

    browser.get(ad_url)
    time.sleep(1)

    elem = browser.find_element_by_tag_name("body")

    no_of_page_downs = 8

    while no_of_page_downs:
        elem.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.3)
        no_of_page_downs -= 1

    html_soup = BeautifulSoup(browser.page_source, HTML_PARSER)

    car_general_content_list = html_soup.find_all('li', attrs={'class': 'bcd-list-item'})
    for car_general_content in car_general_content_list:
        car_general_content_dict[car_general_content.text.split(':')[0].strip()] = car_general_content.text.split(':')[
            1].strip()

    car_general_info_sections = []
    car_general_info_values = []

    car_general_info_sections_list = html_soup.find_all('span', attrs={'class': 'one-line-overflow font-default-minus'})
    for car_general_info in car_general_info_sections_list:
        car_general_info_sections.append(car_general_info.text)

    car_general_info_values_list = html_soup.find_all('span', attrs={'class': 'pl4 one-line-overflow'})
    for car_general_info in car_general_info_values_list:
        car_general_info_values.append(car_general_info.text)

    car_price_content_list = html_soup.find_all('p', attrs={'class': 'font-default-plusmore bold ls-03'})
    for car_price_content in car_price_content_list:
        car_general_content_dict["Fiyat"] = car_price_content.text.strip()

    car_general_info_combined_dict = dict(zip(car_general_info_sections, car_general_info_values))

    global car_all_info_combined_dict
    car_all_info_combined_dict = car_general_content_dict.copy()
    car_all_info_combined_dict.update(car_general_info_combined_dict)

    car_all_info_combined_list.append(car_all_info_combined_dict)

    browser.close()


def collect_ad_urls():
    # Data Structure for Advertisement URLs
    ad_urls = deque()

    car_select_counter = 0
    page_counter = 0

    while car_select_counter < 10:
        while page_counter < 10:
            search_page_url = search_page_base_url + car_brands.__getitem__(car_select_counter)[0] + "?" + \
                              "take=" + str(pag_size) + "&page=" + str(page_counter + 1)

            response = get(search_page_url, headers=headers)
            html_soup = BeautifulSoup(response.text, HTML_PARSER)

            # Collect the URLs in the page and put them to the data structure
            base_page_content_list = html_soup.find_all('div', attrs={'class': 'pr10 fade-out-content-wrapper'})
            for div in base_page_content_list:
                ad_urls.append(base_page_url + div.find('a')['href'])

            # increase the page count after retrieving the urls in the page
            page_counter = page_counter + 1
        car_select_counter = car_select_counter + 1
        page_counter = 0

    url_counter = 1
    url_section_counter = 1
    for ad_url in ad_urls:
        process_url_and_extract_data(ad_url)
        if url_counter % 500 == 0:
            print("Section " + str(url_section_counter) + " completed successfully.")
            url_section_counter = url_section_counter + 1
        print("URL " + str(url_counter) + " crawled successfully.")
        url_counter = url_counter + 1


collect_ad_urls()


def write_dict_data_to_csv():
    car_dateset_columns = ["İlan No", "İlan Tarihi", "Marka", "Seri", "Model",
                           "Yıl", "Yakıt Tipi", "Vites Tipi", "Motor Hacmi", "Motor Gücü",
                           "Kilometre", "Plaka", "Şasi Numarası", "Boya-değişen",
                           "Takasa Uygun", "Kimden", "Kasa Tipi", "Araç Türü", "Renk",
                           "Plaka Uyruğu", "Garantisi", "Aracın ilk sahibiyim",
                           "Yıllık MTV", "Şanzıman", "Çekiş", "Silindir Sayısı",
                           "Tork", "Maksimum Güç", "Minimum Güç", "Hızlanma (0-100)",
                           "Maksimum Hız", "Ortalama Yakıt Tüketimi",
                           "Şehir İçi Yakıt Tüketimi", "Şehir Dışı Yakıt Tüketimi",
                           "Yakıt Deposu", "Uzunluk", "Genişlik", "Yükseklik", "Ağırlık",
                           "Boş Ağırlığı", "Koltuk Sayısı", "Bagaj Hacmi",
                           "Ön Lastik", "Aks Aralığı", "Ekspertiz sonucu", "Fiyat"]
    car_dataset = open("car_dataset.csv", "w", encoding="UTF-8", newline='')

    writer = csv.DictWriter(car_dataset, fieldnames=car_dateset_columns)
    writer.writeheader()
    writer.writerows(car_all_info_combined_list)

    car_dataset.close()


write_dict_data_to_csv()
