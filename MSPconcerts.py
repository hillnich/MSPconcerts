from bs4 import BeautifulSoup
import requests
import time
import re

class concerts():

    def __init__(self):

        self.btimes = {}
        self.bandlist = ['adele', 'bon iver', 'andrew bird']

    def ScrapeShows(self):

        self.FirstAvenue()
        self.Amsterdam()
        
    def FirstAvenue(self):

        """
        Scrapes from First Avenue's calendar pages
        out to 12 months in advance
        """
        
        query_rate = 10
        n_months = 12
        
        # Grab current date
        mon = int(time.strftime("%m"))
        year = int(time.strftime("%Y"))
        
        months = [x+mon for x in range(n_months) if (x+mon)<13] + \
                 [x+mon-12 for x in range(n_months) if (x+mon) > 12]
        
        years = [year for x in range(n_months) if (x+mon) < 13] + \
                [year + 1 for x in range(n_months) if (x+mon) > 12]
        
        # Loop through 12 months at time
        
        btimes = {}
        
        for i in range(n_months):
            
            cdates = []
            datetime = []
            page = "http://first-avenue.com/calendar/all/{:d}-{:02d}".format(years[i],
                                                                             months[i])
            print "Scraping:", page
            soup = BeautifulSoup(requests.get(page).text, 'html5lib')
            
            # Grab concert dates:
            dspans = [date.string for date in soup('span', 'date-display-single')]
            
            for d in dspans:
                
            # Try to grab a time
                try:
                    t = re.match("^[0-9].*", d).group(0)
                    datetime.append("{:s} - {:s}".format(cdates[-1], t))
                except:
                    cdates.append(d)
                    
            # Grab the band names
            bands = [h2span.string for h2span in soup('h2', 'node-title')]

            # Put the times and bands all together:

            if (len(datetime) == len(bands)):
                bkey = "{:d}-{:02d}".format(years[i],  months[i])
                self.btimes[bkey] = ["{:s} - {:s}".format(datetime[j],
                                                          str(bands[j].encode('utf8')))
                                     for j, _ in enumerate(bands)]
            else:
                print "FIRST AVENUE SCRAPER IS BROKEN! FIX!"
                break
            
            # Wait before doing query as requested
            time.sleep(query_rate)


    def Amsterdam():

        """
        Scrapes from Amsterdam for concerts
        """

        # Grab the one events page they have:
        page = "http://www.amsterdambarandhall.com/events-new/"
        soup = BeautifulSoup(requests.get(page).text, 'html5lib')

    
    

def find_good_concerts():

    first_ave = FirstAvenue()

    g = []
    for key in first_ave.keys():

        for d in first_ave[key]:

            for band in bandlist:

                try:
                    re.search(band, d, re.IGNORECASE).group(0)
                    g.append(d)
                except:
                    pass



    return g
        
