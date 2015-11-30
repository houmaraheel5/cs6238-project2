import requests
import unittest
import os

BASEDIR  = os.path.dirname(os.path.realpath(__file__))
BASE_URL = "https://vps.kylekoza.com/"

class testAuthentication(unittest.TestCase):
    def testUnauthorized(self):
        r = requests.get(BASE_URL + "tlsauth/test/", verify=False)
        self.assertEqual(r.text, "NONE<br />")

    def testAuthorized(self):
        r = requests.get(BASE_URL + "tlsauth/test/", cert=(os.path.join(BASEDIR, "client.crt"), os.path.join(BASEDIR, "client.key")), verify=False)
        self.assertEqual(r.text, "SUCCESS<br />/C=US/ST=Georgia/L=Atlanta/O=testing/OU=Kyle/CN=Kyle")

if __name__ == "__main__":
    unittest.main()
