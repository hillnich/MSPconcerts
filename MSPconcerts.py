from bs4 import BeautifulSoup
import requests
import time
import re

class concerts():

    """
   Attributes:
       btimes: the bands and times scraped from webpages
       bandlist: list of bands you're interested in finding shows for
       goodshows: the selection of available shows corresponding to bands you like
    """

    def __init__(self):

        """
        Creates attributes we fill with rest of methods
        """
        
        self.btimes = {}
        self.bandlist = ['adele', 'bon iver', 'andrew bird', 'little fevers',
                         'grimes', 'brandi carlisle']
        self.goodshows = []

    def ScrapeShows(self):

        """
        Executes each method corresponding to a scrape of a given
        concert venue
        """
        
        self.FirstAvenue()
        self.Amsterdam()

    def FindGoodsShows(self):

        """
        Cross-references all the 'good bands' against
        available shows and returns resulting list
        """
        
        for key in self.btimes.keys():
            
            for d in self.btimes[key]:
                
                for band in self.bandlist:
                    
                    try:
                        re.search(band, d, re.IGNORECASE).group(0)
                        self.goodshows.append(d)
                    except:
                        pass            
        
        
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
                bkey = "First-{:d}-{:02d}".format(years[i],  months[i])
                self.btimes[bkey] = ["{:s} - {:s}".format(datetime[j],
                                                          str(bands[j].encode('utf8')))
                                     for j, _ in enumerate(bands)]
            else:
                print "FIRST AVENUE SCRAPER IS BROKEN! FIX!"
                break
            
            # Wait before doing query as requested
            time.sleep(query_rate)


    def Amsterdam(self):

        """
        Scrapes from St. Paul's Amsterdam's events page
        for concerts
        """
  
      # Grab the one events page they have:
        page = "http://www.amsterdambarandhall.com/events-new/"

        print "Scraping:", page
        soup = BeautifulSoup(requests.get(page).text, 'html5lib')

        # Piece together the dates
        day = [d.string for d in soup('span', 'event-day')]
        month = [mon.string for mon in soup('span', 'event-month')]
        date = [d.string for d in soup('span', 'event-date')]                          
            
        if (len(day) == len(month) == len(date)):
            dates = ["{:s}, {:s} {:s}".format(day[i], month[i], date[i])
                     for i,_ in enumerate(day)]

        # Grab the bands/events, filtering out none types and ursl
        bands = [a.string
                 for div in soup('div', 'event-info-block')
                 for a in div('a')]
        bands = filter(None, bands)
        bands = [None
                 if re.match(".*http://.*", x)
                 else x
                 for x in bands]
        bands = filter(None, bands)
                 
                 
        self.btimes['Amsterdam'] = []

        if (len(bands) == len(dates)):
            for j, _ in enumerate(bands):
                
                self.btimes['Amsterdam'].append("{:s} - {:s}".
                                                format(dates[j],
                                                       str(bands[j].encode('utf8'))))
                
        else:
            print "AMSTERDAM SCRAPER IS BROKEN! FIX!"
            
            


if __name__ == '__main__':

    shows = concerts()
    shows.ScrapeShows()
    shows.FindGoodShows()




        
