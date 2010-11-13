from lib.thirdparty import scrapemark
import urllib

class GoogleAPI:
    GOOGLE_SEARCH_URL = "http://www.google.com/search?"

    def __init__(self):
        pass

    def calc(self, expression):
        result = scrapemark.scrape("""
            <h2 class="r"><b>{{ answer }}</b></h2>
        """, url = GoogleAPI.GOOGLE_SEARCH_URL + urllib.urlencode({"q": expression}))

        if result:
            return result['answer']

    def search(self, searchterms):
        result = scrapemark.scrape("""
            <div id="ires">
                <ol>
                {*
                    <a class="l" href="{{ [results].link }}">{{ [results].title }}</a>
                *}
                </ol>
            </div>
        """, url = GoogleAPI.GOOGLE_SEARCH_URL + urllib.urlencode({"q": searchterms}))

        if result:
            return result['results']
