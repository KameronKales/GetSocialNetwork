import json, pprint, unicodedata, os
from socialNetwork import LinkedIn


class LinkedInStats(object):
    """ A class which outputs all the data as a .txt file for future use in Microsoft Excel app. """
    def __init__(self, login, password):

        self.link = LinkedIn(login, password)
        self.selfDir = os.path.dirname(__file__)

        self.companyStatsDir = os.path.join(self.selfDir, "companies stats.txt")
        self.countriesStatDir = os.path.join(self.selfDir, "countries stats.txt")
        self.positionStats = os.path.join(self.selfDir, "position stats.txt")

    @staticmethod
    def _write(fileName,*args):
        flatList = []

        for arg in args:
            if hasattr(arg,'__iter__'):
                flatList.extend(arg)
            else:
                flatList.append(arg)
        newList =  []

        for item in flatList:

            if not isinstance(item, int) and not isinstance(item, str):
                item = unicodedata.normalize('NFKD', item).encode('ascii', 'ignore')

            newList.append(item)

        flatList = newList
        title = flatList[0]+":"
        stringValue = ', '.join(map(str,flatList[1:]))
        fileName.write(title+' '+stringValue+'\n')


    def companyStats(self):
        """ A function outputs a .txt file with a list of companies and people working in them. """
        companies_people =  self.link.getPeopleAtCompanies()
        all_companies = float(len(companies_people))
        d = {}

        for company in companies_people:
            accurance = len(companies_people[company])
            d[company] = accurance

        with open(self.companyStatsDir,'w') as f:
            f.write("total companies in profile: %s\n" %(all_companies))
            f.write("\n")
            f.write('company name and the number of people working at the company\n')
            f.write("\n")
            for company, value in sorted(d.items(),key=lambda x: x[1], reverse=True):
                names = companies_people[company]
                company = company[3:]
                self._write(f,company,value,names)

    def locationStats(self):
        """ A fuction outputs a .txt file with countries and number of people living in the countries. """
        locations = self.link.getCountries()
        totalLocations = len(locations)
        countryCount = {}
        globalCount = 0

        for country in locations:
            count = 0

            for city in locations[country]:
                size = len(locations[country][city])
                count+=size
            countryCount[country] = count
            globalCount+=count

        with open(self.countriesStatDir,'w') as f:
            f.write("total locations in profile: %s\n" %(totalLocations))
            f.write("\n")
            for country, cities in sorted(locations.items(), key = lambda x:len(x[1]), reverse=True):
                self._write(f, country, countryCount[country], cities)

            f.write('\n')

    def workStats(self):
        """ A function which sorts the job titles into a list of positions and outputs a .txt file. """
        positionCount = {}
        positions = self.link.getPosition()

        for position in positions:
            count = len(positions[position])
            positionCount[position] = count

        with open(self.positionStats,'w') as f:
            for position in positions:
                self._write(f, position, positionCount[position], positions[position])
