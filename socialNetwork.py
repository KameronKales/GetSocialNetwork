import urllib, urllib2, cookielib, re, json, math, os
from BeautifulSoup import BeautifulSoup
from pprint import pprint
import unicodedata


class SocialNetwork(object):
    def __init__(self, login, password, startURL, loginURL):
        self.login = login
        self.password = password
        self.cookieJar = cookielib.CookieJar()
        self.handler_list = [
            urllib2.HTTPCookieProcessor(self.cookieJar),
            urllib2.HTTPHandler(),
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPSHandler()
            ]
        self.header = [('User-Agent',('(Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36)'))]
        self.opener = urllib2.build_opener(*self.handler_list)
        self.opener.addheaders = self.header
        self.start_url = startURL
        self.login_url = loginURL

    def loadPage(self, url, data = None):
        try:
            if data is not None:
                data = urllib.urlencode(data)
                response = self.opener.open(url, data)

            else:
                response = self.opener.open(url)

            return str(response.read())

        except:
            raise IOError('{} is not accesable.'.fromat(url))


    def loginPage(self):
        """
        starts with the homepage to obtain the csrf, once its done logins using login, pass and csrf
        """
        loginPage = self.loadPage(self.start_url)
        soup = BeautifulSoup(loginPage)
        csrf = soup.find( id = "loginCsrfParam-login")['value']

        loginData = {'session_key'      : self.login,
                     'session_password' : self.password,
                     'loginCsrfParam'   : csrf}

        homePage = self.loadPage(self.login_url, loginData)

        return homePage


class LinkedIn(SocialNetwork):
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.startURL = "https://www.linkedin.com/"
        self.loginURL = "https://www.linkedin.com/uas/login-submit"
        self.con_url = "https://www.linkedin.com/contacts/api/contacts/?"
        super(LinkedIn, self).__init__(self.login, self.password, self.startURL, self.loginURL)
        self.homePage = self.loginPage()
        self.countryDict = self.loadCountryDict()
        self.num_con = self.getNumCons()
        self.conData = self.getConnections()
        self.companies = self.getCompanies() # TODO for speed sake I prolly need to take out this method.

    def getNumCons(self):
        numCon = re.search(r'\"numConnections\":\d+', self.homePage)
        number = numCon.group().split(':')[1]
        return number

    def _getCountryByCity(self, city):
        country = None
        city = unicodedata.normalize('NFKD', city).encode('ascii','ignore')
        city = re.sub(" Area", '', city)
        city = re.sub(" Metropolitan", '', city)
        city = re.sub(" Bay", '', city)
        city = re.sub("Greater ", '', city)
        city = re.sub(r" \(\w+\)", '', city) # takes out everything that is inside ().
        city = re.sub(r'\/[A-z ]*', '', city) # takes out everything that comes after /.

        for dictCountry in self.countryDict:
            for dictCity in self.countryDict[dictCountry]:
                cityMatch = re.compile(dictCity)
                match = cityMatch.match(city)

                if match:
                    match = match.group()
                    if len(match) == len(city):
                        country = dictCountry
                        return country
        else:
            return 'Unknown place'

    def loadCountryDict(self):
        script_dir = os.path.dirname(__file__)
        file_dir = 'countryCity.json'
        absolute_dir = os.path.join(script_dir,file_dir)
        f = file(absolute_dir,'r')
        countryDict = json.load(f)
        f.close()
        return countryDict


    def getConnections(self):
        """
        get the list of all connections
        """
        params = {'start' : 0,
                  'count' : self.num_con, #TODO replace with self.num_con
                  'fields': 'id,name,first_name,last_name,company,title,geo_location,tags,emails,sources,display_sources,last_interaction,secure_profile_image_url',
                  'sort'  : '-last_interaction',
                  '_'     : '1440213783954'}
        params = urllib.urlencode(params)
        connectionsPage = self.loadPage(self.con_url+params)
        conData = json.loads(connectionsPage)
        # for index in conData['contacts']:
        #     try:
        #         print '#first name:', index['first_name'], '# Title: ', index['title'], '#studio: ', index['company']['id']
        #     except:
        #         print 'profile skiped'

        return conData #return a dictionary

    def getCompanies(self):
        conData = self.conData
        companies = {}
        for person in conData['contacts']:

            if person['company']:

                if person['company']['id'] in companies:
                    continue

                else:
                    dataCompany = person['company']['id']
                    companies[dataCompany] = []

        return companies


    def getPeopleAtCompanies(self):
        companies = self.companies
        for company in self.companies:

            for person in self.conData['contacts']:

                if person['company']:

                    if person['company']['id'] == company:
                        companies[company].append(person['first_name']+" "+person['last_name'])

        return companies


    def getCountries(self):
        countries = {'Unspecified':{'unspecified city':[]} }

        count = 0
        for person in self.conData['contacts']:
            name = unicodedata.normalize('NFKD', person['first_name']).encode('ascii','ignore')
            lastname = unicodedata.normalize('NFKD', person['last_name']).encode('ascii','ignore')
            personNameLastName = '{} {}'.format(name, lastname)
            if person['geo_location']:
                location = person['geo_location']['name']
                location =  location.split(',')

                if location:
                    _city = location[0]
                    country = self._getCountryByCity(_city)

                    if country in countries:

                        if _city in countries[country]:
                            countries[country][_city].append(personNameLastName)

                        else: countries[country].update({_city: [ personNameLastName] } )

                    else:
                        countries[country]= {_city: [personNameLastName]}
            else:
                countries['Unspecified']['unspecified city'].append(personNameLastName)

        return countries
