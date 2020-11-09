
import os
import scrapy
from scrapy_splash import SplashRequest, SplashFormRequest
from scrapy.shell import inspect_response
from scrapy.shell import Shell
import re
from bs4 import BeautifulSoup as bs
from PIL import Image, ImageFilter
from scipy.ndimage.filters import gaussian_filter
import numpy
import pytesseract
from urllib.parse import urlparse, urljoin
import requests
from io import BytesIO
import csv
import unicodedata
from .base_vars import SCRIPT, SCRIPT_FRAME, FIELDNAMES
from items import IconsoftCrawlerItem


class IconSoftwareCrawl(scrapy.Spider):

    name = 'icon_software_crawler'

    def __init__(self, *args, **kwargs):
        """Super of __init__ method in the Class after __dict__ 
        update.
        """

        self.__dict__.update(kwargs)
        super(IconSoftwareCrawl, self).__init__(*args, **kwargs)

        self.filename = kwargs['filename']
        self.url = kwargs.get('url')
        self.start_date = kwargs.get('start_date')
        self.end_date = kwargs.get('end_date')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.verbose = kwargs.get('verbose')
        self.reactor = kwargs.get('reactor')

        self.form_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': '',
            '__VIEWSTATEGENERATOR': '',
            '__VIEWSTATEENCRYPTED': '',
            '__EVENTVALIDATION': '',
            'tbCaseNumber': '',
            'tbPersonSearch': '',
            'tbSearch3': '',
            'tbSearch4': '',
            'tbFiledFrom': '',
            'tbFiledTo': '',
        }

    def start_requests(self):
        """Initial start request called by inherited 'Spider' Class.

        Yields:
            SplashRequest Class: request for the starting url.
        """

        yield SplashRequest(
            self.url,
            self.parse_initial,
            endpoint='render.json',
            args={'iframes': 1,
                  'html': 1,
                  'timeout': 90
                  }
        )

    def solve_captcha(self, captcha_url):
        """This method makes multiple attempts to solves the captcha 
        that is required for sign in. success rate is about 70%.

        Args:
            captcha_url (string): url for the captcha image.

        Returns:
            list: 'final' is cleaned and normalized captcha image.   
                  't' is the text translation of the cleaned image 
                  by pytesseract.'original' is the original captcha 
                  image.
        """

        th1 = 140
        th2 = 140  # threshold after blurring
        sig = 1.5  # the blurring sigma

        img_response = requests.get(captcha_url)
        b_img = BytesIO(img_response.content)
        original = Image.open(b_img)
        # reading the image from the request
        original.save("captcha_temp/original.png")
        black_and_white = original.convert(
            "L")  # converting to black and white
        black_and_white.save("captcha_temp/black_and_white.png")
        first_threshold = black_and_white.point(
            lambda p: p > th1 and 255)
        first_threshold.save("captcha_temp/first_threshold.png")
        blur = numpy.array(first_threshold)  # create an image array
        blurred = gaussian_filter(blur, sigma=sig)
        blurred = Image.fromarray(blurred)
        blurred.save("captcha_temp/blurred.png")
        final = blurred.point(lambda p: p > th2 and 255)
        final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
        final = final.filter(ImageFilter.SHARPEN)
        final.save("captcha_temp/final.png")
        text = pytesseract.image_to_string(
            Image.open('captcha_temp/final.png'))
        escapes = ''.join([chr(char) for char in range(1, 32)])
        translator = str.maketrans('', '', escapes)
        t = text.translate(translator)

        return [final, t.upper(), original]

    def _normalize_text(self, text):
        """Private method that normalizes text.

        Args:
            text (string): text to be normalized.

        Returns:
            string: normalized text.
        """

        return unicodedata.normalize("NFKD", text)

    def parse_initial(self, response):
        """Method for parsing the initial response, solving captcha, 
        and attempting to log in.

        Args:
            response (SplashRequest Object): A response with returned
            data from from the initial url.  


        Yields:
           SplashFormRequest Class : An http form request for login 
           and triggering Splash middlewear to render iframes in json 
           format.
        """

        soup = bs(response.data[
            'childFrames'][1]['html'], 'html.parser')

        captcha_url = self.url + \
            soup.find(id='RadCaptcha1_CaptchaImage').get('src')

        captcha_result = self.solve_captcha(captcha_url)
        captcha_text = captcha_result[1].replace(" ", "")
        cr = captcha_result[1]

        if self.verbose:
            print(f""" 
            __________________________

                --LOGGING IN --


                -- CAPTCHA RESULT -- 
                _                  _
                _    {cr}          _
                _                  _
            __________________________

            """)

        form_data = {}
        form_data['RadScriptManager1_TSM'] = soup.find(
            id='RadScriptManager1_TSM').get('value')
        form_data['__VIEWSTATE'] = soup.find(
            id='__VIEWSTATE').get('value'),
        form_data['__VIEWSTATEGENERATOR'] = soup.find(
            id='__VIEWSTATEGENERATOR').get('value'),
        form_data['__EVENTVALIDATION'] = soup.find(
            id='__EVENTVALIDATION').get('value'),
        form_data['UserName'] = self.username,
        form_data['Password'] = self.password,
        form_data['tbCaptchaEntry'] = captcha_text,
        form_data['btnLogIn.x'] = '39',
        form_data['btnLogIn.y'] = '15'

        yield SplashFormRequest(
            self.url+'webFormMenu.aspx?page=main',
            self.login_result,
            endpoint='execute',
            cache_args=['lua_source'],
            args={'lua_source': SCRIPT},
            formdata=form_data
        )

    def login_result(self, response):
        """Method for parsing the response from a successful login,
         and requesting response from the 'civil' court url.

        Args:
            response (SplashRequest Object): A response with returned 
            data from from the successful login.  

        Yields:
           SplashRequest Class :An http request for civil court url 
           and passing lua script to the Splash server for including 
           cookies in the request, and also to render the html from
           the <frameset> html tags.
        """

        yield SplashRequest(
            self.url+'webFormSearch.aspx?search=civil',
            self.civil_search,
            endpoint='execute',
            cache_args=['lua_source'],
            args={'lua_source': SCRIPT},
        )

    def civil_search(self, response):
        """Method for parsing the response from the civil court url, 
        and sending search results for the given 'self.start_date'
        and 'self.end_date']

        Args:
            response (SplashRequest Object): A response with returned 
            data from from the civil court url.

        Yields:
           SplashRequest Class : An http form request with form fields 
           for civil search url while passing lua script to the Splash
           server via middleware for including cookies in the request, 
           and also to render the html from the <frameset> html tags.
        """

        soup = bs(response.data['html'], 'html.parser')

        form_data = self.form_data.copy()

        form_data['__VIEWSTATE'] = soup.find(
            id='__VIEWSTATE').get('value')
        form_data['__VIEWSTATEGENERATOR'] = soup.find(
            id='__VIEWSTATEGENERATOR').get('value')
        form_data['__EVENTVALIDATION'] = soup.find(
            id='__EVENTVALIDATION').get('value')
        form_data['tbFiledFrom'] = self.start_date
        form_data['tbFiledTo'] = self.end_date
        form_data['btnSearch.x'] = '37'
        form_data['btnSearch.y'] = '19'

        yield SplashFormRequest(
            self.url+'webFormSearch.aspx?search=civil',
            self.civil_search_pages,
            endpoint='execute',
            cache_args=['lua_source'],
            args={'lua_source': SCRIPT},
            formdata=form_data
        )

    def row_data(self, bs):
        """Html parsing method for data in each row from the search
        results page.

        Args:
            bs (BeautifulSoup Object): Containing row data from the 
            search results page.

        Returns:
            dict: of data from a search row.
        """

        row_data = {}
        row_data['link_argument'] = bs.find_all('a')[0].get(
            'href').replace('(', "").replace(
                ')', "").split(',')[-1].replace("'", "")

        status = bs.find_all('td')[2].text.replace(" ", "")
        disp_date = bs.find_all('td')[3].text.replace(" ", "")
        disp_stage = bs.find_all('td')[4].text.replace(" ", "")
        disp_code = bs.find_all('td')[5].text.replace(" ", "")

        row_data['meta'] = {
            'cd': {
                'case_number': re.search(
                    '[a-zA-Z]', bs.find_all('td')[0].text).string,
                'status': self._normalize_text(status),
                'disp_date': self._normalize_text(disp_date),
                'disp_stage': self._normalize_text(disp_stage),
                'disp_code': self._normalize_text(disp_code)
            }
        }

        return row_data

    def civil_search_pages(self, response):
        """Method for parsing results from the filtered search, 
        looping through each result, parsing the data, navigating to
        the next page of results, and looping through requesting each
        result's case details page.

        Args:
            response (SplashRequest Object): A response with returned 
            data from from the search results form, or from itself.

        Yields:
           1) SplashFormRequest Class : An http form request with form 
           fields for the next paginated result including passing a 
           lua script to the Splash server via middleware for including 
           cookies in the request, and also to render the html from the 
           <frameset> html tags.
           2) SplashFormRequest Class : An http form request with form 
           fields for each case in the search results including passing 
           a lua script to the Splash server via middleware for 
           including cookies in the request and also to render the html 
           from the <frameset> html tags, and a metadata argument 
           containing scraped data from each result row. 
        """

        soup = bs(response.data['html'], 'html.parser')

        page_links = soup.select(
            '#CivilSearchGrid > tbody > \
            tr:nth-child(1) > td > table > tbody')[0].find_all('td')

        page_numbers = [l.findChild().get('href').split(
            "javascript:__doPostBack('CivilSearchGrid',")[1].replace(
                ')', '').replace("'", "") 
            if l.findChild().get('href') 
            else "NONE" for l in page_links]

        next_page = page_numbers[page_numbers.index('NONE')+1]

        form_data = self.form_data.copy()
        form_data['__EVENTTARGET'] = 'CivilSearchGrid'
        form_data['__EVENTARGUMENT'] = next_page
        form_data['__VIEWSTATE'] = soup.find(
            id='__VIEWSTATE').get('value')
        form_data['__VIEWSTATEGENERATOR'] = soup.find(
            id='__VIEWSTATEGENERATOR').get('value')
        form_data['__EVENTVALIDATION'] = soup.find(
            id='__EVENTVALIDATION').get('value')
        form_data['tbFiledFrom'] = '01/01/2020'
        form_data['tbFiledTo'] = '10/24/2020'
        if self.verbose:
            print("Navigating to ", next_page, '---------------')
        try:
            yield SplashFormRequest(
                self.url+'webFormSearch.aspx?search=civil',
                self.civil_search_pages,
                endpoint='execute',
                cache_args=['lua_source'],
                args={'lua_source': SCRIPT},
                formdata=form_data
            )
        except:
            pass

        row_data = [self.row_data(x) 
            for x in soup.select(
                '#CivilSearchGrid > tbody')[0].find_all('tr')[3:-2]
            if re.search('[a-zA-Z]', x.find('td').text)]

        for data in row_data:

            metadata = data['meta']

            form_data = self.form_data.copy()

            form_data['__EVENTTARGET'] = 'CivilSearchGrid'
            form_data['__EVENTARGUMENT'] = data['link_argument']
            form_data['__VIEWSTATE'] = soup.find(
                id='__VIEWSTATE').get('value')
            form_data['__VIEWSTATEGENERATOR'] = soup.find(
                id='__VIEWSTATEGENERATOR').get('value')
            form_data['__EVENTVALIDATION'] = soup.find(
                id='__EVENTVALIDATION').get('value')
            form_data['tbFiledFrom'] = '01/01/2020'
            form_data['tbFiledTo'] = '10/24/2020'

            yield SplashFormRequest(
                self.url+'webFormSearch.aspx?search=civil',
                self.parse_case_result,
                endpoint='execute',
                cache_args=['lua_source'],
                args={'lua_source': SCRIPT_FRAME},
                formdata=form_data,
                meta=metadata
            )

    def parse_case_result(self, response):
        """Method for parsing each case's details page. Technically,
        each page actually consists of three iframes each with its
        own <body>. Method stores all scraped data in the metadata  
        argument inside of the SplashFormRequest Class.

        Args:
            response (SplashRequest Object): A response with returned 
            data from from an individual case including metadata. 

        Yields:
           SplashRequest Class : An http request for each party of the
           case while passing lua script to the Splash server via 
           middleware for including cookies in the request, and also 
           to render the html from the <frameset> html tags.
        """

        cd = response.meta['cd']
        if self.verbose:
            print("GETTING DATA FROM CASE PAGE", cd['case_number'])

        frame1 = bs(response.data['frames']['frame_1'], 'html.parser')
        frame2 = bs(response.data['frames']['frame_2'], 'html.parser')
        frame3 = bs(response.data['frames']['frame_3'], 'html.parser')
        try:
            # Get data from frame1
            cd['type_of_case'] = frame1.select(
                '#ddTypeOfCase > option')[0].text
            cd['case_types'] = frame1.select(
                '#tbCaseTypes')[0].get('value')
            cd['style_of_case'] = frame1.select(
                '#tbCaseStyle')[0].get('value')
            cd['cause_of_action'] = frame1.select(
                '#tbCause')[0].get('value')
            cd['principal_claim'] = frame1.select(
                '#tbPrincipal')[0].get('value')
            cd['interest'] = frame1.select(
                '#tbInterest')[0].get('value')
            cd['interest_other'] = frame1.select(
                '#tbInterestOther')[0].get('value')
            cd['attorney_fees'] = frame1.select(
                '#tbAttorneyFees')[0].get('value')
            cd['filing_cost_serve'] = frame1.select(
                '#tbFilingCost')[0].get('value')
            cd['fi_fa_fee'] = frame1.select(
                '#tbFifaFee')[0].get('value')
            cd['totals'] = frame1.select(
                '#tbTotal')[0].get(
                'value').replace("$", "").replace(",", "")
            cd['fi_fa_notes'] = frame1.select(
                '#tbFifaNotes')[0].get('value')
            cd['types_on_this_case'] = frame1.select(
                '#lbCaseTypes')[0].get('value')
            cd['cse'] = frame1.select('#tbCSE')[0].get('value')
            cd['judge'] = frame1.select(
                '#ddJudge > option')[0].get('value')
            cd['case_status'] = frame1.select(
                '#ddCaseStatus > option')[0].get('value')
            cd['service_date'] = frame1.select(
                '#tbServiceDate')[0].get('value')
            cd['answer_date'] = frame1.select(
                '#tbAnswerDate')[0].get('value')
            cd['projected_default_date'] = frame1.select(
                '#tbProjDefaultDate')[0].get('value')
            cd['disposition_date'] = frame1.select(
                '#tbDispDate')[0].get('value')
            cd['stage_of_disposition'] = frame1.select(
                '#ddDispStage')[0].get('value')
            cd['disposition_code'] = frame1.select(
                '#ddDispCode')[0].get('value')
            cd['last_updated_by'] = frame1.select(
                '#Textbox16')[0].get('value')
            cd['updated_on'] = frame1.select(
                '#tbLastUp')[0].get('value')
        except:
            return

        links = [x for x in frame2.find_all(
            'a') if re.search('[a-zA-Z]', x.text)]
        text = [x.text for x in links if re.search('[a-zA-Z]', x.text)]
        parties = text.index('Parties')
        proceedings = text.index('Proceedings')
        proceeding_links = [x.text for x in links[proceedings+1:]]

        cd['plaintiff'] = [x.text for x in links[parties+1:proceedings]
                           if "P:" in x.text][0].split(": ")[1]

        for l in proceeding_links:

            if "served" in l.lower():
                cd['served_status'] = "Served"

            else:
                cd['served_status'] = "Not Served"

        for url in [(self.url+x.get('href'), 'D') if "D:" in x.text
                    else (self.url+x.get('href'), 'P') 
                    for x in links[parties+1:proceedings]]:

            yield SplashRequest(
                url[0],
                self.parse_defendant_contact_info,
                endpoint='execute',
                cache_args=['lua_source'],
                args={'lua_source': SCRIPT},
                meta={'cd': cd, 'party_status': url[1]}
            )

    def parse_defendant_contact_info(self, response):
        """Method for parsing each parties details page. The method
        unpacks the metadata object containing all the scraped data
        and assigns it to the IconSoftCrawlerItem Object for 
        processing in the item pipeline to be stored in the .csv 
        file.

        Args:
            response (SplashRequest Object): A response with returned 
            data from from a case's individual parties including data
            contained in the metadata object.

        Returns:
           IconsoftCrawlerItem Object inheriting a scrapy.Item Class:
           A Class for parsing scraped items to be passed to the item
           pipeline. 
        """

        cd = response.meta['cd']
        soup = bs(response.data['html'], 'html.parser')

        if response.meta['party_status'] == 'D':

            items = IconsoftCrawlerItem()

            items['filename'] = self.filename

            for key, value in cd.items():
                items[key] = value

            last = soup.select('#tbPartyLast')[0].get('value')
            first = soup.select('#tbPartyFirst')[0].get('value')
            middle = soup.select('#tbPartyMiddle')[0].get('value')
            suffix = soup.select('#ddPartySuffix > option')[0].text

            if last:
                items['last_name'] = soup.select('#tbPartyLast')[
                    0].get('value')
            else:
                items['last_name'] = 'no last'

            if first:
                items['first_name'] = soup.select(
                    '#tbPartyFirst')[0].get('value')
            else:
                items['first_name'] = 'no first'

            if middle:
                items['middle_name'] = soup.select('#tbPartyMiddle')[
                    0].get('value')
            else:
                items['middle_name'] = 'no middle'

            if suffix:
                items['suffix'] = soup.select(
                    '#ddPartySuffix > option')[0].text
            else:
                items['suffix'] = 'no suffix'

            items['full_name'] = f"{items['first_name']} \
                {items['middle_name']} {items['last_name']} \
                    {items['suffix']}"

            combined_name_hex = items['last_name'].encode(
                "utf-8").hex()+"-"+items[
                    'first_name'].encode("utf-8").hex()

            items['unique_case_number'] = items['case_number'] + \
                "-"+combined_name_hex

            items['street'] = soup.select(
                '#tbPartyAddr1')[0].get('value')
            items['street2'] = soup.select(
                '#tbPartyAddr2')[0].get('value')
            items['city'] = soup.select(
                '#tbPartyAddr1')[0].get('value')
            items['state'] = soup.select(
                '#ddPartyState > option')[0].text
            items['zip'] = soup.select(
                '#tbPartyZip')[0].get('value')

            items['home_phone'] = soup.select(
                '#tbPartyWPhone')[0].get('value')
            items['work_phone'] = soup.select(
                '#tbPartyWPhone')[0].get('value')
            items['email'] = soup.select(
                '#TextBox1')[0].get('value')
            items['party_type'] = soup.select(
                '#tbCivilPartyType')[0].get('value')
            items['service_date'] = soup.select(
                '#tbServiceDate')[0].get('value')
            items['answer_date'] = soup.select(
                '#tbAnswerDate')[0].get('value')
            items['service_type'] = soup.select(
                '#ddServiceType > option')[0].text
            if self.verbose:
                print("SAVING CASE DATA", "-------------\
                    ------------", "\n")
                print(cd, "\n")

            return items
