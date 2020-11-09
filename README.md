# Iconsoftware Crawler
   This web crawler leverages [scrapy](https://github.com/scrapy/scrapy) and [scrapy-splash](https://github.com/scrapy-plugins/scrapy-splash) for crawling IconSoftware websites. These websites are typically used by U.S state and county court systems for the purpose of hosting access of public records. They are built on the .NET framework and are easily some of the most difficult websites to scrape. This is due to its heavy use of `<frameset>` HTML, image captchas, and javascript `<href>` links. 
  
  ** __You will need a valid username and password. This program will in no way help you bypass credentialed authentication__ **



## Installation
1. Install packages with requirements.txt:

       $ pip install -r requirements.txt

2. ** This crawler uses [Splash](https://github.com/scrapinghub/splash) HTTP API, so you also need a Splash instance. Usually to install & run Splash, something like this is enough:
 
       $ docker run -it -p 8050:8050 --rm scrapinghub/splash
       
    If you need further help setting up Splash, check out the [install docs](https://splash.readthedocs.io/en/latest/install.html)

## Configuration & Usage Examples

This program is best used via the command line. 

1) Basic operation
   
    * required arguments:
      * -url URL       the url to be crawled
      * -u username    the username of the account that will be logged in
      * -p password    the password of the account that will be logged in
      
    Start the crawler by running:
      
       $ python iconsoft_crawler/i_crawl.py -url http://example-site1.com -u example_user -p example_password
       
2) Additional Arguments

     Multiple websites can be assigned to the crawler by passing the `-url` argument multiple times.
     
       $ python iconsoft_crawler/i_crawl.py -url http://example-site1.com -url http://example-site2 ...
       
      
    * optional arguments:
      * -h, --help     show this help message and exit
      * -s start_date  the start date for cases to be crawled - Default will be 12 earlier
      * -e end_date    the end date for cases to be crawled - Default will be current date
      * -v verbose     if True, will print debug data
      * -f filename    .csv filename for crawled data to be saved - Default will be (random-date.csv)   
        
    Notes:

      When Passing multiple `-url` arguments, username and password will need to be the same for all urls.
      
 3) Output 
 
    All scraped data will be saved as a .csv file in the _'crawl_saves'_ directory.
    
        iconsoft_crawler > crawl_saves > example_save.csv
