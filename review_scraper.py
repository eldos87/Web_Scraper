from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from flask import Flask, request
import pandas as pd
import sys

app = Flask(__name__)


@app.route('/review', methods=['GET', 'POST'])
def get_reviews():
    if request.method == 'POST':
        try:
            search_string = request.json['item']
            t1 = str(search_string).upper().replace(' ', '-')
            t2 = str(search_string).lower().replace(' ', '+')

            # hit Qoo10 url with search string and reading page
            webpage = "https://www.qoo10.sg/s/{}?keyword={}&keyword_auto_change=".format(t1, t2)
            uClient = urlopen(webpage)
            page = uClient.read()
            uClient.close()

            # parsing html data with beautiful soup
            data = bs(page, "html.parser")

            try:
                # getting the big box which contain products
                Bigbox = data.findAll("div", {"class": "bd_lst_item", "id": "div_search_result_list"})

                # getting the list of products
                boxes = Bigbox[0].table.tbody.findAll("tr")

            except Exception as e:
                print("Exception occurred due to no such item in Q0010")
                raise e

            # dataframe to store data
            df = pd.DataFrame()

            # Looping through first 50 boxes
            for i in range(50):

                # getting hyperlink to navigate to individual product page
                weblink = boxes[i].findAll("div", {'class': 'inner'})[1].a['href']
                page = urlopen(weblink)
                page_data = page.read()
                data = bs(page_data, "html.parser")

                # locating customer review area in product page
                rev_boxes = data.findAll("div", {"class": "sec_review"})

                if len(rev_boxes) == 2:           # for products with photo review & text review, go to text review
                    try:
                        reviews_per_page = rev_boxes[1].table.tbody.findAll("tr")
                    except:
                        continue
                elif len(rev_boxes) == 1:         # for products with only text review
                    try:
                        reviews_per_page = rev_boxes[0].table.tbody.findAll("tr")
                    except:
                        continue
                else:                          # if no review for the product, continue with next product
                    continue

                # looping through reviews
                for j in reviews_per_page:
                    Item = j.div.p.text
                    Rating = j.td.text
                    user = j.findAll("td")[3].text
                    user = user.replace('\n', '')
                    user = user.replace('\t', '')
                    Date = j.findAll("td")[2].text
                    Comments = j.div.a.text
                    df = df.append({'Search': search_string, 'Item': Item, 'Date': Date, 'Customer': user,
                                    'Rating': Rating, 'Comments': Comments}, ignore_index=True)

            df = df[['Search', 'Item', 'Date', 'Rating', 'Customer', 'Comments']]
            df.to_csv(search_string + '_df.csv')
            return f"{df.shape[0]} reviews scraped from Q0010 for {search_string} product"

        except Exception as e:
            print("Exception : {} in line number {}".format(e, sys.exc_info()[2].tb_lineno ))
            return "Something went wrong or no such item in Q0010"


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=True)
