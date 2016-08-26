#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup as bs
from IPython import embed
from requests_toolbelt.multipart.encoder import MultipartEncoder

def get_auth_payload(raw_resp):
    soup = bs(raw_resp.text, 'lxml')
    token = [n['value'] for n in soup.find_all('input') if n['name'] == 'authenticity_token'][0]
    login_payload = {
        'utf8': '&#x2713;',
        'user[login]': 'root',
        'user[password]': 'test_password',
        'user[remember_me]': '0',
        'authenticity_token': token,
    }
    return login_payload



#appearance_payload = {
    # 'utf8': '&#x2713;',
    # '_method': 'patch'
    # 'authenticity_token': '',
    # 'appearance[title]': 'GitLab Enterprise Edition',
    # 'appearance[description]': '### Open source software to collaborate on code\nManage git repositories with fine grained access controls that keep your code secure. Perform code reviews and enhance collaboration with merge requests. Each project can also have an issue tracker and a wiki.',
    # 'appearance[logo_cache]': None, # Empty field?
    # 'appearance[logo]': '', # ;filename=""
    # 'appearance[header_logo_cache]': None,
    # 'appearance[header_logo]': None, # ;filename="${FILENAME}", content-type image/png\r\n\r\n${IMG_DATA}
#}

def process_appearance_page(raw_resp):
    soup = bs(raw_resp.text, 'lxml')
    scraped_data = {x['name']: x['value'] for x in soup.find_all('input') if x['name'] in {'utf8', '_method', 'authenticity_token', 'appearance[title]'} }
    # got stupid utf8 tag, _method tag because it seems important
    # auth token, existing title
    # get current textbox value
    scraped_data['appearance[description]'] = [x for x in soup.find_all('textarea') if x['name'] == 'appearance[description]'][0].contents[0]
    # cool. That's really it for us.
    # the rest depends on what action we're performing
    return scraped_data


with requests.session() as s:
    login_page = s.get('http://192.168.52.131/users/sign_in')

    login_payload = get_auth_payload(login_page)

    login_responce = s.post('http://192.168.52.131/users/sign_in',
                            data=login_payload)

    appearance_page = s.get('http://192.168.52.131/admin/appearance')

    appearance_payload = process_appearance_page(appearance_page)

    # We COULD use python-magic and libmagic to get the mime type... or I can just make it png.
    # http://stackoverflow.com/a/2753385
    appearance_payload['appearance[header_logo]'] = ('FILENAME_HERE',open('img.png','rb'), 'image/png')

    print(appearance_payload)

    appearance_payload = MultipartEncoder(fields=appearance_payload)

    appearance_responce = s.post('http://192.168.52.131/admin/appearance',
                                 data=appearance_payload,
                                 headers={'Content-Type': appearance_payload.content_type})

    #page = bs(appearance_page.text, 'lxml')
    #embed()

