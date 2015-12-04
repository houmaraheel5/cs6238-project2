import requests
import uuid
import unittest
import os
import json
import tempfile
import hashlib
import datetime
import urllib
from werkzeug import secure_filename

BASEDIR  = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://vps.kylekoza.com/"

upload = tempfile.NamedTemporaryFile(suffix=".txt")
upload.write(os.urandom(128))
upload.seek(0)

cert = (os.path.join(BASEDIR, "client.crt"), os.path.join(BASEDIR, "client.key"))

class testAuthentication(unittest.TestCase):
    def testUnauthorized(self):
        r = requests.get(BASE_URL + "tlsauth/test/", verify=False)
        self.assertEqual(r.text, "NONE<br />")

    def testAuthorized(self):
        r = requests.get(BASE_URL + "tlsauth/test/", cert=cert, verify=False)
        self.assertEqual(r.text, "SUCCESS<br />/C=US/ST=Georgia/L=Atlanta/O=testing/OU=Kyle/CN=Kyle")

class testCheckin(unittest.TestCase):
    def testNewCheckin(self):
        upload.seek(0)
        r = requests.post(BASE_URL + "check_in/", verify=False, cert=cert, files={'file': upload})

        self.assertEqual(r.text, hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest())

    def testUpdate(self):
        upload.write(os.urandom(64))
        upload.seek(0)

        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()

        r = requests.post(BASE_URL + "check_in/" + document_id + "/", cert=cert, verify=False, files={'file': upload})

        self.assertEqual(r.text, hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest())

class testCheckout(unittest.TestCase):
    def testCheckout(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()

        r = requests.get(BASE_URL + "check_out/" + document_id, verify=False, cert=cert, stream=True)

        f = tempfile.TemporaryFile()
        for chunk in r.iter_content(16):
            f.write(chunk)
        f.seek(0)
        upload.seek(0)
        self.assertEqual(f.read(), upload.read())

    def testUnauthorized(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()

        r = requests.get(BASE_URL +  "check_out/" + document_id, verify=False, stream=True)

        self.assertEqual(r.text, "Access denied")

class Entitlements(unittest.TestCase):
    def testGetEntitlements(self):
        r = requests.get(BASE_URL + "get_entitlements/", cert=cert, verify=False)

        result = json.loads(r.text)

        self.assertEqual(result["status"], "success")

class yDelegation(unittest.TestCase):
    def testDelegateReadNoProagateNoTime(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()
        client_id = "C=US/CN=jimmy/L=Atlanta/O=CS6238/ST=Georgia/OU=Project2" # TODO

        payload = {"client": client_id, "permission": "READ", "propagate": False} 
        r = requests.post(BASE_URL + "delegate/" + document_id + "/", cert=cert, verify=False, json=payload)

        self.assertEqual(r.text, "Successfully delegated read access to {0} for {1}".format(document_id, client_id))

    def testDelegateReadProagateTime(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()
        client_id = "C=US/CN=jimmy/L=Atlanta/O=CS6238/ST=Georgia/OU=Project2" # TODO

        payload = {"client": client_id, "permission": "READ", "propagate": True, "until": str(datetime.datetime.utcnow() + datetime.timedelta(days=5))} 
        r = requests.post(BASE_URL + "delegate/" + document_id + "/", cert=cert, verify=False, json=payload)

        self.assertEqual(r.text, "Successfully delegated read access to {0} for {1}".format(document_id, client_id))

    def testDelegateWriteNoProagateNoTime(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()
        client_id = "C=US/CN=jimmy/L=Atlanta/O=CS6238/ST=Georgia/OU=Project2" # TODO

        payload = {"client": client_id, "permission": "WRITE", "propagate": False} 
        r = requests.post(BASE_URL + "delegate/" + document_id + "/", cert=cert, verify=False, json=payload)

        self.assertEqual(r.text, "Successfully delegated write access to {0} for {1}".format(document_id, client_id))

    def testDelegateWriteProagateTime(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()
        client_id = "C=US/CN=jimmy/L=Atlanta/O=CS6238/ST=Georgia/OU=Project2" # TODO

        payload = {"client": client_id, "permission": "WRITE", "propagate": True, "until": str(datetime.datetime.utcnow() + datetime.timedelta(days=5))} 
        r = requests.post(BASE_URL + "delegate/" + document_id + "/", cert=cert, verify=False, json=payload)

        self.assertEqual(r.text, "Successfully delegated write access to {0} for {1}".format(document_id, client_id))

class ztestDelete(unittest.TestCase):
    def testDelete(self):
        document_id = hashlib.sha1(secure_filename("CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))).hexdigest()

        r = requests.get(BASE_URL + "safe_delete/" + document_id, verify=False, cert=cert)

        self.assertEqual(r.text, "Document deleted")

if __name__ == "__main__":
   unittest.main()
