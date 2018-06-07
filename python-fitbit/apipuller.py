import sys
import json
import base64
try: 
  import urllib.request as urllib2
except ImportError:
  import urllib2
import urllib
try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

#These are the secrets etc from Fitbit developer
OAuthTwoClientID = "22CMWS"
ClientOrConsumerSecret = "83418e86bc034c4f162277e411144aaa"

#This is the Fitbit URL
TokenURL = "https://api.fitbit.com/oauth2/token"

#I got this from the first verifier part when authorising my application
AuthorisationCode = sys.argv[1]

#Form the data payload
BodyText = {'code' : AuthorisationCode,
            'redirect_uri' : 'https://jhprohealth.app/callback',
            'client_id' : OAuthTwoClientID,
            'grant_type' : 'authorization_code'}

BodyURLEncoded = urllib.urlencode(BodyText)
print (BodyURLEncoded)

#Start the request
req = urllib2.Request(TokenURL,BodyURLEncoded)

#Add the headers, first we base64 encode the client id and client secret with a : inbetween and create the authorisation header
req.add_header('Authorization', 'Basic ' + base64.b64encode(OAuthTwoClientID + ":" + ClientOrConsumerSecret))
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

#Fire off the request
try:
  response = urllib2.urlopen(req)

  FullResponse = response.read()

  print ("Output >>> " + FullResponse)
  file_obj = open("token.json", 'wb')
  file_obj.write(FullResponse)
except urllib2.URLError as e:
  print (e.code)
  print (e.read())
