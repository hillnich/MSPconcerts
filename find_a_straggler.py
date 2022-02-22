# Stuff for parsing the static html and sending emails
from bs4 import BeautifulSoup
import requests
import time
import re, os
import urllib.parse
import smtplib
from email.mime.text import MIMEText
import json

# All the selenium garbage so I can sizes that are dynamically loaded
# from the internal database
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# And for saving the 
from datetime import datetime
import pickle

class Bikes():

    """
    Attributes:
        page_base: the main URL to scrape from
        bikes_page: the predictate for the bike page to use for scraping 
                    inventory
    """

    def __init__(self, page_base=None, bikes_page=None):

        """
        Creates attributes we fill with rest of methods
        """
        if (page_base is None):
            self.page_base = "https://www.thehubbikecoop.org"
        else:
            self.page_base = page_base

        if (bikes_page is None):
            self.bikes_page = "product-list/commuter-urban-pg119/"
        else:
            self.bikes_page = bikes_page

        self.last_sent_email = 'last_sent_time.pkl'
        self.dt_max = 5


    def find_all_the_bikes(self):

        """
        Scrapes all the bikes currently available from the Hub's 
        Commuter/Urban bike pages
        """
        
        page = urllib.parse.urljoin(self.page_base, self.bikes_page)

        print("    Scraping:", page)
        soup = BeautifulSoup(requests.get(page).text, 'html5lib')
    
        # Figure out how many pages there are
        npages_html = soup.find_all("span", class_="sePaginationText")
        try:
            npages_txt = npages_html[0].string
            npages = max([int(val) for val in re.findall("[0-9]+", npages_txt)])
        except:
            os.sys.exit("Unable to figure out how many pages there are to skim")

        # Start looping through the pages getting the bike names
        self.bikes = []
        for page in range(1, npages+1):

            #Grab the list of the all the bikes on the page
            bikes_html = soup.find_all("a", class_="seProductAnchor")
            tmp = [{"name": bike["title"],"link": bike["href"]} for bike in bikes_html]

            _ = [self.bikes.append(bike) for bike in tmp]
            
            # Grab the next page
            if (page < npages):
                pages_html = soup.find("a", class_="sePaginationLink")
                next_page_suffix = pages_html['href']
                next_page = urllib.parse.urljoin(self.page_base, next_page_suffix)
                print("    Scraping page {0}: {1}".format(page+1, next_page))
                soup = BeautifulSoup(requests.get(next_page).text, 'html5lib')

        return self.bikes

    def find_my_bikes(self, all_the_bikes, bikes_i_want):

        """
        go through the bikes list and sanitize it and then compare
        it to my list of ones i want
        """
        
        # remove not alphabet characters and lowercase everything
        regex = re.compile("[^a-zA-Z0-9\s]")
        for bike in all_the_bikes:
            bike["clean_name"] = regex.sub("", bike["name"]).lower()


        # Go through and put together a short list of all my bikes
        clean_bike_list = [bike["clean_name"] for bike in all_the_bikes]

        self.my_bikes = []
        for bike in bikes_i_want:

            bike_tmp = [name_dict for name_dict in all_the_bikes
                                  if bike in name_dict["clean_name"]]

            _ = [self.my_bikes.append(bike_iter) for bike_iter in bike_tmp]

        return self.my_bikes

    def get_bike_sizes(self, bike_list):

        """
        Given a dict of bike names and links for those bikes' pages,
        go grab the available sizes and add those to the dict
        """

        # Open up the chrome driver, and just install the driver locally
        driver = webdriver.Chrome(ChromeDriverManager().install())

        # Start up a loop 
        delay = 10 # seconds
        for bike in bike_list:

            # Create a list to store data into for the bike
            bike["sizes"] = []
            # load the page
            page = urllib.parse.urljoin(self.page_base, bike['link'])
            driver.get(page)

            # Wait for the load to populate the dropdown menu
            try:
                myElem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.NAME, 'variation1')))
                print("Page is ready!")
            except TimeoutException:
                print("Loading took too much time!")

            # Get the dropdown values
            dropdown_element = driver.find_element(By.NAME, "variation1")
            s = Select(dropdown_element)
            
            # sleep long enough to let the hub query it's database and return
            # actual availability since it defaults to available until that
            # is done
            time.sleep(5)

            # Go through all the options grabbing only those that are
            # actually in stock
            for item in s.options:

                # Only get it if it's a selectable sizes, ie: not disabled
                if (item.get_property("disabled") is False):

                    # Don't get the select size string
                    if ("Select" not in item.text):
                        bike["sizes"].append(item.text)

        # Close the webdriver since we're done with this stuff now
        driver.close()

        return bike_list

    def email_bikes(self, bike_dict):

        """
        Email out any new bikes. If there hasn't been a daily update
        send out an email just so I know things are working
        correctly on at least a daily basis.
        """

        # Pull in email sender and login info
        sender = {}
        with open("email.from") as f:

            # Grab email
            try:
                (key, val) = f.readline().split(": ")
                sender['email'] = val.strip("\n")
            except:
                (key, val) = f.readline().split(":")
                sender['email'] = val.strip("\n")

            # Grab password
            try:
                (key, val) = f.readline().split(": ")
                sender['password'] = val.strip("\n")
            except:
                (key, val) = f.readline().split(":")
                sender['password'] = val.strip("\n")

        # Pull in list of recipients
        with open("email.to") as f:
            receivers = [x.strip('\n') for x in f.readlines()]

        # Start encrypted SMTP session
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender['email'], sender['password'])
 
        # Construct message
        html_preamble = """
        <html>
        <head></head>
        <body>
        <p><font face="monaco">
        """

        body = html_preamble
        body = body + "<br>NEW BIKES:"
        body = body + "<br>----------"

        for bike in bike_dict['new_results']:
            body = body + "<pre>" + json.dumps(bike, indent = 2) + "</pre>"


        body = body + "<br><br>MOST RECENT CACHED BIKE INVENTORY"
        body = body + "<br>---------------------------------"

        for bike in bike_dict['old_results']:
            body = body + "<pre>" + json.dumps(bike, indent = 2) + "</pre>"
 
        body = body + "</p></body></html>"

        msg = MIMEText(body, 'html')
        msg['Subject'] = "Hub Bike Update"
        msg['From'] = sender['email']
        msg['To'] = ", ".join(receivers)

        # Send message and end server session
        server.sendmail(sender['email'], receivers, msg.as_string())
        server.quit()

        # Cache the time so we can use it later to determine if we should send
        # one just as a regular reminder
        with open(self.last_sent_email, 'wb') as f:
            pickle.dump(datetime.now(), f)



    def check_cached_results(self, new_bikes_and_sizes, 
                             max_cached=3, cache_base=None):

        """ 
        Compare the current results against any of those that have
        been previously saved
        """

        if (cache_base is None):
            self.cache_base = "cached_bike_dict"
        else:
            self.cache_base = cache_base
  
        # Get a time string to date file

        # Get a list of the cached files
        cached_results = []
        for file in os.listdir(os.getcwd()):
            if file.startswith(self.cache_base):
                cached_results.append(file)

        # If there were results, sort them, and load the top
        old_bikes_and_sizes = None
        if (len(cached_results) != 0):
            cached_results.sort(reverse=True)

            with open(cached_results[0], 'rb') as f:
                old_bikes_and_sizes = pickle.load(f)

        # If we have stuff, compare it to what we currently have to
        # determine if there's a reason to email
        send_email = False
        old_results = []
        new_results = []
        if (old_bikes_and_sizes is not None):

            for old_bike in old_bikes_and_sizes:
                new_bike = next((nbike for i, nbike in enumerate(new_bikes_and_sizes) 
                                   if old_bike["name"] == nbike["name"]), None)

                # check to see if the new size is already in the old size
                if (new_bike is not None):

                    maybe_results = {}
                    for name, val in new_bike.items():
                        if (name != 'sizes'):
                            maybe_results[name] = val
                        else:
                            maybe_results['sizes'] = []


                    for new_size in new_bike['sizes']:
                        if (new_size not in old_bike['sizes']):
                            maybe_results['sizes'].append(new_bike['sizes'])

                    if (len(maybe_results['sizes']) > 0):
                        new_results.append(maybe_results)
                        send_email = True

            old_results = old_bikes_and_sizes

        # If we don't have anything cached we should definitely email
        # the current results
        else:
            send_email = True
            new_results = new_bikes_and_sizes
            old_results = []

        # Finally, save the current bike and list purge ones that are too old
        now = datetime.now()
        time_string = now.strftime("%Y.%m.%d_%H.%M.%S")
        new_cache_file = "{:s}-{:s}.{:s}".format(self.cache_base, time_string, "pkl")
        with open(new_cache_file, 'wb') as f:
            pickle.dump(new_bikes_and_sizes, f)

        if (len(cached_results) > 0):
            cached_results.insert(0, new_cache_file)
        else:
            cached_results.append(new_cache_file)

        _ = [os.remove(filename) for i, filename in enumerate(cached_results) 
                                 if i >= max_cached]

        # Lastly check the last sent email time. If enough
        # time has passed send the email now matter what 
        last_sent = None
        for file in os.listdir(os.getcwd()):
            if file == self.last_sent_email:
                with open(self.last_sent_email, 'rb') as f:
                    last_sent = pickle.load(f)


        if (last_sent is not None):
            dt = datetime.now() - last_sent
            if (dt.total_seconds() > self.dt_max):
                send_email = True
        # Put everything in a dict to return
        email_results = {"send_email": send_email,
                         "new_results": new_results,
                         "old_results": old_results}

        return email_results

if __name__ == '__main__':

    bikes_i_want = ["straggler", "crosscheck"]
    bikes = Bikes()
    all_the_bikes = bikes.find_all_the_bikes()
    my_bikes = bikes.find_my_bikes(all_the_bikes, bikes_i_want)
    bikes_and_sizes = bikes.get_bike_sizes(my_bikes)

    email_results = bikes.check_cached_results(bikes_and_sizes)

    if (email_results['send_email']):
        bikes.email_bikes(email_results)
        
