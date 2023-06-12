import pprint
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Turn off warnings about invalid certificates
#
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pp = pprint.PrettyPrinter(indent=4)


class ISE(object):

    iseSession = None
    groupCache = {}
    userCache = {}

    def __init__(self, host, port, username, password):
        self.username = username
        self.password = password
        self.baseurl = "https://" + host + ":" + port + "/ers/config/"

    def join_errors(self, messages):
        m = ""
        for message in messages:
            m = m + ":" + message["title"]

        return m

    def connect(self):

        self.iseSession = requests.Session()
        self.iseSession.auth = (self.username, self.password)
        self.iseSession.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def close(self):
        self.iseSession.close()

    def getUserList(self, page, filter):
        return self.getPage("internaluser", page, filter)

    def getUserByID(self, id, resolveGroups=False):
        userRecord = self.getByID("internaluser", id)

        if "InternalUser" in userRecord:
            userRecord = userRecord["InternalUser"]

        if resolveGroups:
            if userRecord["identityGroups"]:
                resolvedGroups = []
                resolvedGroupsAll = []
                for Group in userRecord["identityGroups"].split(","):
                    idGroups = self.getGroupByID(Group)
                    resolvedGroups.append({"name": idGroups["name"], "id": idGroups["id"]})
                    resolvedGroupsAll.append(idGroups["name"])

                userRecord["idenityGroupDetail"] = resolvedGroups
                userRecord["idenityGroupNames"] = ";".join(resolvedGroupsAll)

        return userRecord

    def updateUserByID(self, id, userRecord):

        if "InternalUser" not in userRecord:
            newRecord = {"InternalUser": userRecord}

        response = self.updateByID("internaluser", id, newRecord)
        return response

    def getGroupList(self, page, filter):
        return self.getPage("identitygroup", page, filter)

    def getGroupByID(self, id):
        if id not in self.groupCache:
            groupRecord = self.getByID("identitygroup", id)
            if "IdentityGroup" in groupRecord:
                groupRecord = groupRecord["IdentityGroup"]

            self.groupCache[id] = groupRecord

        return self.groupCache[id]

    def getPage(self, path, page, filter):
        url = self.baseurl + path

        params = {"page": page, "size": 100}

        if filter:
            params["filter"] = filter

        resp = self.iseSession.get(url, verify=False, params=params)

        if resp.status_code in (401, 403):
          raise Exception('User not authorised')

        if resp.status_code != 200:
            result = resp.json()
            error = self.join_errors(result["ERSResponse"]["messages"])
            raise Exception("getPage: {} {}".format(resp.status_code, error))

        return resp.json()["SearchResult"]

    def getByID(self, path, id):
        idurl = self.baseurl + path + "/" + id

        resp = self.iseSession.get(idurl, verify=False)

        if resp.status_code != 200:
            result = resp.json()
            error = self.join_errors(result["ERSResponse"]["messages"])
            raise Exception("getByID: {} {}".format(resp.status_code, error))

        return resp.json()

    def updateByID(self, path, id, record):
        idurl = self.baseurl + path + "/" + id

        resp = self.iseSession.put(idurl, verify=False, json=record)

        if resp.status_code != 200:
            result = resp.json()
            error = self.join_errors(result["ERSResponse"]["messages"])
            raise Exception("updateByID: {} {}".format(resp.status_code, error))

        return resp.json()
