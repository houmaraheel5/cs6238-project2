import requests
import uuid
import unittest
import os
import tempfile

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
        r = requests.post(BASE_URL + "check_in/", verify=False, cert=cert, files={'file': upload.seek(0)})

        self.assertEqual(r.text, "CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name))

    def testUpdate(self):
        upload.write(os.urandom(64))
        upload.seek(0)

        r = requests.post(BASE_URL + "check_in/CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name) + "/", verify=False, files={'file': upload})

        self.assertEqual(r.text,"CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name)) 

class testCheckout(unittest.TestCase):
    def testCheckout(self):
        r = requests.post(BASE_URL + "check_out/CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name), verify=False, cert=cert, stream=True) 

        with open(tempfile.TemporaryFile(), "w+b") as f:
            for chunk in r.iter_content(16):
                f.write(chunk)
            f.seek(0)
            self.assertEqual(f.read(), upload.read())

    def testUnauthorized(self):
        r = requests.post(BASE_URL +  "check_out/CUS_STGeorgia_LAtlanta_Otesting_OUKyle_CNKyle" + os.path.basename(upload.name), verify=False, stream=True)

        self.assertEqual(r.text, "Access Denied")

if __name__ == "__main__":
    unittest.main()
