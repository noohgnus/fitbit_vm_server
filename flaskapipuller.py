from flask import Flask
app = Flask(__name__)
implicit_url = 'https://www.fitbit.com/oauth2/authorize?response_type=token&client_id=22CMWS&redirect_uri=jhpro%3A%2F%2Ffinished&scope=activity%20heartrate%20location%20nutrition%20profile%20settings%20sleep%20social%20weight&expires_in=604800'

@app.route('/')
def scrape_and_reformat():
    # call your scraping code here
    # return '<html><body> ... generated html string ... </body></html>'
    return implicit_url

if __name__ == '__main__':
    app.run()