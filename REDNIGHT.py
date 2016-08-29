#!/usr/bin/env python3

import argparse
import logging
import requests
import yaml
from bs4 import BeautifulSoup as bs
from datetime import datetime
from pathlib import Path
from requests_toolbelt import sessions
from requests_toolbelt.multipart.encoder import MultipartEncoder
from threading import Event

username = 'root'
password = 'test_password'
address = 'http://192.168.52.131/'


def get_auth_payload(raw_resp):
    soup = bs(raw_resp.text, 'lxml')
    token = [n['value'] for n in soup.find_all('input') if n['name'] == 'authenticity_token'][0]
    return {
        'utf8': '&#x2713;',
        'user[login]': username,
        'user[password]': password,
        'user[remember_me]': '0',
        'authenticity_token': token,
    }


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


def set_image(image):
    with sessions.BaseUrlSession(base_url=address) as s:
        login_page = s.get('users/sign_in')

        login_payload = get_auth_payload(login_page)

        login_responce = s.post('users/sign_in',
                                data=login_payload)

        appearance_page = s.get('admin/appearance')

        appearance_payload = process_appearance_page(appearance_page)

        # We COULD use python-magic and libmagic to get the mime type... or I can just make it png.
        # http://stackoverflow.com/a/2753385
        appearance_payload['appearance[header_logo]'] = (image.name, image.open(mode='rb'), 'image/png')

        logging.info(image.name)

        appearance_payload = MultipartEncoder(fields=appearance_payload)

        appearance_responce = s.post('admin/appearance',
                                     data=appearance_payload,
                                     headers={'Content-Type': appearance_payload.content_type})


def reset_image():
    with sessions.BaseUrlSession(base_url=address) as s:
        login_page = s.get('users/sign_in')

        login_payload = get_auth_payload(login_page)

        login_responce = s.post('users/sign_in',
                                data=login_payload)

        appearance_page = s.get('admin/appearance')

        # We actually only need the auth token from it
        appearance_payload = process_appearance_page(appearance_page)

        appearance_payload = MultipartEncoder(fields={
            '_method': 'delete',
            'authenticity_token': appearance_payload['authenticity_token']
        })

        appearance_responce = s.post('admin/appearance/header_logos',
                                     data=appearance_payload,
                                     headers={'Content-Type': appearance_payload.content_type})


# silly hack to enforce value at argparse level
def enforce_positive(value):
    try:
        ivalue = int(value)
    except:
        raise argparse.ArgumentTypeError("{} is not an integer".format(value))
    if ivalue < 1:
        raise argparse.ArgumentTypeError("{} is not >= 1".format(value))
    return ivalue


def gen_datetime(value):
    try:
        if value == 'now':
            dt = datetime.now()
        else:
            dt = datetime.fromtimestamp(int(value))
    except Exception as err:
        raise argparse.ArgumentTypeError("Could not process {}! {}:{}".format(value, type(err).__name__, err))
    return dt


def cycle(image_list, time_delta):
    sleep_timer = Event()

    for image in image_list:
        set_image(image)
        sleep_timer.wait(time_delta)
    reset_image()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')

    parser.add_argument('begin', type=gen_datetime, default='now', help='Time to start, epoch or "now"')

    parser.add_argument('end', type=gen_datetime, help='Time to revert, epoch')

    # parser.add_argument('delay', type=enforce_positive, default=3600,
    #                    help="Time between changes (seconds)")

    parser.add_argument('--log', type=str, default='INFO', choices=['DEBUG', 'INFO', 'ERROR'], help="Logging level")

    args = parser.parse_args()

    params = vars(args)

    log_level = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }.get(params['log'], logging.INFO)  # super duper fallback to INFO if something breaks
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.debug("Log level set, arguments parsed")
    logging.debug(params)

    with open('config.yml', 'r') as f:
        config_data = yaml.safe_load(f)

    if any(x not in config_data for x in {'address', 'username', 'password'}):
        raise Exception('Missing config data!')

    username = config_data['username']
    password = config_data['password']
    address = config_data['address']

    images = sorted(Path('imgs/').glob('*.png'))

    if not params['begin'] < params['end']:
        raise Exception("Start time after end?")

    delta = (params['end'] - params['begin']).seconds / len(images)

    if datetime.now() < params['begin']:
        time_to_start = (params['begin'] - datetime.now()).seconds
        logging.info('Sleeping for %s seconds', time_to_start)
        Event().wait(timeout=time_to_start)

    logging.debug('%s', images)
    logging.debug('Delta: %s', delta)

    cycle(images, delta)
