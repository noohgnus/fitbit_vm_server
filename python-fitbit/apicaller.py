import fitbit
import gather_keys_oauth2 as Oauth2
import pandas as pd 
import datetime
import urllib2


CLIENT_ID = '22CMWS'
CLIENT_SECRET = '83418e86bc034c4f162277e411144aaa'
implicit_url = 'https://www.fitbit.com/oauth2/authorize?response_type=token&client_id=22CMWS&redirect_uri=jhpro%3A%2F%2Ffinished&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'

def main():
    # r = requests.get('https://www.fitbit.com/oauth2/authorize?response_type=token&client_id=22CMWS&redirect_uri=jhpro%3A%2F%2Ffinished&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800')
    # print(r.text)
    print("START")
    authenticate()

def authenticate():
    server = Oauth2.OAuth2Server(CLIENT_ID, CLIENT_SECRET)
    server.browser_authorize()
    ACCESS_TOKEN = str(server.fitbit.client.session.token['access_token'])
    REFRESH_TOKEN = str(server.fitbit.client.session.token['refresh_token'])
    auth2_client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET, oauth2=True, access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)    
    auth2_client.sleep()
    
    yesterday = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d"))
    yesterday2 = str((datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    today = str(datetime.datetime.now().strftime("%Y%m%d"))

    fit_statsHR = auth2_client.intraday_time_series('activities/heart', base_date=yesterday2, detail_level='1sec')

    time_list = []
    val_list = []
    for i in fit_statsHR['activities-heart-intraday']['dataset']:
        val_list.append(i['value'])
        time_list.append(i['time'])
    heartdf = pd.DataFrame({'Heart Rate':val_list,'Time':time_list})

    heartdf.to_csv('/Users/anthony/Downloads/python-fitbit-master/Heart/heart'+ \
               yesterday+'.csv', \
               columns=['Time','Heart Rate'], header=True, \
               index = False)

if __name__ == "__main__":
    main()


    