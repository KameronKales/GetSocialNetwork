import urllib, urllib2, cookielib, re, json, math, os, sys, time, random
from pprint import pprint
import unicodedata


class SocialNetwork(object):
    """ A base class to login and load pages """
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

    def loadPage(self, url, data = None, tryAgain = 2):

        if tryAgain <= 0:
            raise IOError('{} {} is not accesable.'.format(url, data) )

        tryAgain-=1
        try:
            if data is not None:
                data = urllib.urlencode(data)
                response = self.opener.open(url, data)

            else:
                response = self.opener.open(url)

            return str(response.read())

        except:
            self.loadPage(url, data, tryAgain)


    def loginPage(self):
        """
        starts with the homepage to obtain the csrf, once its done logins using login, pass and csrf
        """
        loginPage = self.loadPage(self.start_url)
        csrfMatch = re.compile(r'(?<=id="loginCsrfParam-login" type="hidden" value=")[A-z,0-9,-]+')
        csrf = csrfMatch.search(loginPage).group()
        loginData = {'session_key'      : self.login,
                     'session_password' : self.password,
                     'loginCsrfParam'   : csrf }

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

    def getNumCons(self):
        numCon = re.search(r'\"numConnections\":\d+', self.homePage)
        number = numCon.group().split(':')[1]
        return number

    def _getCountryByCity(self, city):
        country = None
        # city = unicodedata.normalize('NFKD', city).encode('ascii','ignore')
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
            return 'Unresolved place'

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

    def getPeopleAtCompanies(self):
        conData = self.conData
        companies = {}
        for person in conData['contacts']:

            if person['company']:
                company = person['company']['id']
                if company in companies:
                    companies[company].append(person['first_name']+' '+person['last_name'])

                else:
                    companies[company] = [person['first_name']+' '+person['last_name']]

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

    def _getCountry(self, location):
        """ The method takes a profile['geo_location']['name'] dictionary value and outputs the country index. """
        location =  location.split(',')
        _city = location[0]
        country = self._getCountryByCity(_city)
        return country





    def getPosition(self):

        def _positionMatch(extendedTitle, positions):
            if not isinstance(extendedTitle, list):
                raise TypeError('{} is not a list'.format(extendedTitle) )

            for word in extendedTitle:
                for position in positions:

                    if word == position:
                        return position

            else:
                return 'other'

        positions = {'manager':[], 'animator':[], 'ceo':[], 'cto':[], 'owner':[], 'professor':[],
                    'supervisor':[], 'recruiter':[], 'producer':[], 'artist':[], 'marketing':[], 'designer':[],
                    'developer':[], 'strategist':[], 'td': [],'scientist':[], 'freelance':[], 'compositor':[],
                    'artist':[], 'generalist':[], 'founder':[], 'coordinator':[], 'creative':[], 'lighter':[],
                    'director':[], 'technical director':[], 'engineer':[], 'senior':[], 'software':[],
                    'junior':[], 'other':[], 'lead': [] }


        for person in self.conData['contacts']:
            n = unicodedata.normalize('NFKD',person['first_name']).encode('ascii','ignore')
            l = unicodedata.normalize('NFKD',person['last_name']).encode('ascii','ignore')
            personNameLastname = n+' '+l
            if person['title']:
                title = unicodedata.normalize('NFKD',person['title']).encode('ascii','ignore')
                title = title.split(' ')
                extendedTitle = []
                for word in title:
                    word = word.lower().split('/')
                    extendedTitle.extend(word)

                if 'owner' in extendedTitle:
                    positions['owner'].append(personNameLastname)
                    continue
                elif 'supervisor' in extendedTitle:
                    positions['supervisor'].append(personNameLastname)
                    continue
                elif 'senior' in extendedTitle:
                    positions['senior'].append(personNameLastname)
                    continue
                elif 'lead' in extendedTitle:
                    positions['lead'].append(personNameLastname)
                    continue
                else:
                    position = _positionMatch(extendedTitle, positions)
                    positions[position].append(personNameLastname)

            else:
                continue

        return positions


    def _getProfileConnections(self, profileID, depth, maxcount, minSleep = 2):
        depth -= 1
        profileConDataURL = 'https://www.linkedin.com/profile/profile-v2-connections?'
        x = 0
        size = 10
        offset = 0
        conData = []
        deepContacts = {}
        contatcs = {}

        while(True):
            sleepTime = random.uniform(minSleep, minSleep*2)
            time.sleep(sleepTime)
            paramsConnections = {'id': profileID, 'offset': offset, 'count': 10, 'distance': 1, 'type': 'ALL', '_': x }
            try:
                profileConData = self.loadPage(profileConDataURL, paramsConnections)
                profileConData = json.loads(profileConData)

            except:
                print 'Can not load #profileID', profileID, '#offset', offset, '#x', x
                break

            if 'connections' not in profileConData['content'] or 'connections' not in profileConData['content']['connections']:
                break

            listCons = profileConData['content']['connections']['connections']
            conData.extend(listCons)
            offset += 10
            x+=1

            if offset >= maxcount and maxcount != -1:
                break

        for dic in conData:
            name = dic['fmt__full_name'].split(" ")
            memberID = dic['memberID']

            if depth > 0:
                deepContacts = self._getProfileConnections(memberID, depth, maxcount, minSleep)

            if len(name)==1:
                contact = {'first_name': name[0], 'last_name': '', 'id': memberID, 'profile connections': deepContacts }
            else:
                contact = {'first_name': name[0], 'last_name': name[1], 'id': memberID, 'profile connections': deepContacts }

            # nameLastname = '{} {}'.format(contact['first_name'], contact['last_name'])
            nameLastname = contact['first_name'] + ' ' + contact['last_name']
            contatcs[nameLastname] = contact

        return contatcs


    def _getProfileID(self, name, lastname):
        if not isinstance(name, basestring) or not isinstance(lastname, basestring):
            raise TypeError('{} or {} is not a string'.format(name, lastname) )

        profileID = 0
        for profile in self.conData['contacts']:

            if name == profile['first_name'] and lastname == profile['last_name']:
                profileID = profile['id']
                profileID = profileID[3:]
                return profileID

        else:
            raise ValueError('{} {} is not in the contacts.'.format(name, lastname) )


    def getProfileConnections(self, name, lastname, fileDir, depth=0, maxcount=-1, minSleep = 2):
        nameLastname = name + ' ' + lastname
        profileID = self._getProfileID(name, lastname)
        profileConData = {nameLastname: {'first_name': name, 'last_name': lastname, 'id': profileID, 'connections':{} } }
        profileConData[nameLastname]['connections'] = self._getProfileConnections(profileID, depth, maxcount, minSleep)

        with open(fileDir, 'w') as f:
            json.dump(profileConData, f, indent=4, sort_keys=True)

        return profileConData


    def getAllConnections(self, fileDir, depth=0, maxcount=-1, minSleep = 2):
        if not isinstance(fileDir, basestring):
            raise TypeError('{} is not a string.'.format(fileDir) )
        if not isinstance(depth, int):
            raise TypeError('{} is not an integer'.format(depth) )

        connectionsTree = {}
        for profile in self.conData['contacts']:
            profileID = profile['id'][3:]
            # nameLastname = '{} {}'.format(profile['first_name'], profile['last_name'])
            nameLastname = profile['first_name'] + ' ' + profile['last_name']
            connections = self._getProfileConnections(profileID, depth, maxcount, minSleep)
            profile['connections'] = connections
            profile['num_cons'] = len(connections)
            profile.pop('tags')
            profile.pop('emails')
            profile.pop('sources')
            profile.pop('display_sources')
            connectionsTree[nameLastname] = profile

        with open(fileDir, 'w') as f:
            json.dump(connectionsTree, f, indent=4, sort_keys=True)

        return connectionsTree

    def _getProfileData(self, profileID):

        profileURL = 'https://www.linkedin.com/profile/view?trk=contacts-contacts-list-contact_name-0&id='+str(profileID)
        profilePage = self.loadPage(profileURL)
        # profileConData = {nameLastname: {'first_name': name, 'last_name': lastname, 'id': profileID, 'connections':{}, 'workExperience':{} } }
        country = None
        locationPattern = re.compile(r'(?<=name=\'location\' title=\"Find other members in )[ A-z,0-9,.]+')
        location = locationPattern.search(profilePage)
        if location:
            print '######location found'
            location = location.group()
            country = self._getCountry(location)

        profilePicturePattern = re.compile(r'(?<=<div class=\"profile-picture\"> <img src=\')[A-z0-9.:/]+')
        profilePicture = profilePicturePattern.search(profilePage)
        if profilePicture:
            profilePicture = profilePicture.group()

        titlePattern = re.compile(r'(?<=title=\"Learn more about this title\">)[ &#39,A-z,0-9]+')
        titles = titlePattern.findall(profilePage)

        startTimePattern = re.compile(r'(?<=<span class=\"experience-date-locale\"><time>)[ A-z,0-9]+')
        startTimes = startTimePattern.findall(profilePage)

        endTimePattern = re.compile(r'(?<=</time> &#8211; <time>)[ A-z,0-9]+')
        endTimes = endTimePattern.findall(profilePage)

        endTimesSize = len(endTimes)
        startTimesSize = len(startTimes)
        startEndDifference = startTimesSize - endTimesSize
        workExp = {}
        for i in range(startEndDifference):
            endTimes.insert(i, 'Present')

        for x in range(startTimesSize):
            start = startTimes[startTimesSize-1-x]
            end = endTimes[startTimesSize-1-x]
            title = titles[startTimesSize-1-x]
            durationPattern = re.compile(r'(?<='+ end + r'</time> \()[ A-z,0-9,|,/]+')
            duration = durationPattern.search(profilePage)

            if duration: duration = duration.group()

            if end == 'Present':

                durationPattern = re.compile(r'(?<=&#8211; Present \()[ A-z,0-9]+')
                duration = durationPattern.search(profilePage)
                if duration: duration = duration.group()

            companyPattern = re.compile(r'[ A-z,0-9,.,/]+(?=</a></strong></span></h5></header><span class=\"experience-date-locale\"><time>' + start + r')')
            company = companyPattern.search(profilePage)

            if not company:
                companyPattern = re.compile(r'[ A-z,0-9,.,/]+(?=</a></h5></header><span class=\"experience-date-locale\"><time>' + start + r')')
                company = companyPattern.search(profilePage)

            if company: company = company.group()

            workExp[company] = {'start': start, 'end': end, 'duration': duration, 'title': title}

        return workExp, country, profilePicture


    def getProfileData(self, name, lastname):
        profileId = self._getProfileID(name, lastname)
        workExp, country, profilePic = self._getProfileData(profileId)
        return workExp, country, profilePic


    def getAllData(self, fileDir, numberProfiles = 199, minSleepTime = 4):

        workExp = {}
        count = 0
        profilesExp = {'skipped profiles': []}
        # if the the there was previous use of the method, the method will look for a file to update the initial dict
        if os.path.exists(fileDir):
            with open(fileDir,'r') as f:
                profilesExp = json.load(f)
                profilesExp['skipped profiles'] = []

        userBehaviorUrls = ['https://www.linkedin.com/contacts/?filter=recent&trk=nav_responsive_tab_network#?filter=recent&trk=nav_responsive_tab_network',
                            'https://www.linkedin.com/profile/view?id=AAIAAA_doisB8NJHxZBU_a3qUco4QCK7JGgrVFA&trk=nav_responsive_tab_profile_pic',
                            'https://www.linkedin.com/home?trk=nav_responsive_tab_home',
                            'https://www.linkedin.com/people/pymk/hub?trk=hp-identity-connections',
                            'https://www.linkedin.com/job/home?trk=nav_responsive_sub_nav_jobs',
                            'https://www.linkedin.com/profile/preview?locale=ru_RU&trk=prof-0-sb-preview-primary-button',
                            'https://www.linkedin.com/vsearch/p?company=FRAME+ONE+ANIMATION&trk=prof-exp-company-name',
                            'https://www.linkedin.com/messaging/thread/6029330728980930560',
                            'https://www.linkedin.com/wvmx/profile?trk=nav_responsive_sub_nav_wvmp',
                            'https://www.linkedin.com/edu/school?id=20946&trk=prof-following-school-logo']

        for profile in self.conData['contacts']:

            if count >= numberProfiles:
                break

            profileId = int(profile['id'][3:])
            nameLastname = profile['first_name'] + ' ' + profile['last_name']
            #skip the profiles which are in the dictionary profilesExp
            if nameLastname in profilesExp:
                print 'skiping profile', profilesExp[nameLastname]['id']
                continue

            sleepTime = random.uniform(minSleepTime, minSleepTime*2)
            time.sleep(sleepTime)
            print sleepTime
            randomPage = random.choice(userBehaviorUrls)

            print 'visiting rand page'
            self.loadPage(randomPage)

            sleepTime = random.uniform(minSleepTime, minSleepTime*2)
            time.sleep(sleepTime)
            try:
                try:
                    print 'getting the profile exp', profileId
                    workExp, country, profilePic = self._getProfileData(profileId)
                    profilesExp[nameLastname] = {'workExp': workExp, 'id': profileId, 'country': country, 'profilePic': profilePic}
                    print 'ok'
                    print '### count:', count
                    count +=1
                except IOError:
                    print 'could not get the profile exp', profileId
                    print '!!! count', count
                    break
            except:
                profilesExp['skipped profiles'].append(profileId)
                print '____ skipping profile', profileId
                continue

        with open(fileDir,'w') as f:
            json.dump(profilesExp, f, indent=4, sort_keys=True)

        return workExp
