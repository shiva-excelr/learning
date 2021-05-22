#
# Copyright 2020 wu.com, Inc. or its affiliates. All Rights Reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import datetime
import json
import logging
import os
import urllib3
#import wu_helpers as helpers

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
http = urllib3.PoolManager()


def lambda_handler(event, context):
    logger.debug('<<western_union>> Lex event info = ' + json.dumps(event))
    session_attributes = event.get('sessionAttributes', None)
    if session_attributes is None:
        session_attributes = {}
    logger.debug('<<western_union>> lambda_handler: session_attributes = ' + json.dumps(session_attributes))
    return track_transfer_handler(event, session_attributes)


def track_transfer_handler(intent_request, session_attributes):
    slot_values = intent_request['currentIntent']['slots']
    input_transcript = intent_request.get('inputTranscript', None)
    logger.debug('<<western_union>> track_transfer_handler: slot_values = ' + json.dumps(slot_values))

    # Default response
    buttons = {"MAIN MENU": "MAIN MENU"}
    slot_to_elicit = 'tat_sender_country'
    response_string = 'To track your transfer, please tell me the name of the country the money was sent ' \
                      '<strong>from</strong>.'

    tat_sender_country = slot_values.get('tat_sender_country', None)
    tat_tracking_side = slot_values.get('tat_tracking_side', None)#im sender or im receiver
    tat_mtcn_number = slot_values.get('tat_mtcn_number', None)
    tat_confirm = slot_values.get('tat_confirm', None)
    tat_amount_type = slot_values.get('tat_amount_type', None)
    tat_amount = slot_values.get('tat_amount', None)

    if tat_confirm == 'Yes':
        response_string = 'Please type a question, or choose from the options below.'
        return helpers.custom_menu('wu_tat_intent', response_string,
                                   {"MAIN MENU": "MAIN MENU", "TRACK NEW TRANSFER": "TRACK NEW TRANSFER",
                                    "FIND LOCATIONS": "FIND LOCATIONS", "GIVE FEEDBACK": "GIVE FEEDBACK",
                                    "CHAT": "LIVE CHAT"})
    elif tat_confirm == 'No':
        response_string = 'Thank you! You may click the <strong>X</strong> to close this window, choose an option ' \
                          'below, or ask another question.'
        return helpers.custom_menu('wu_tat_intent', response_string,
                                   {"MAIN MENU": "MAIN MENU", "GIVE FEEDBACK": "GIVE FEEDBACK"})
    elif input_transcript and input_transcript.lower() == "don't have this information":
        response_string = 'Unfortunately without these details we can\'t track your transfer. Is there anything ' \
                          'else I can help with?'
        slot_to_elicit = 'tat_confirm'
        buttons_text = {"Yes": "Yes", "No": "No"}
        return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons_text, response_string)
    elif tat_amount is None and tat_amount_type is not None and input_transcript.lower() != "yes, send amount" and input_transcript.lower() != "yes, receive amount":
        response_string = 'Please enter the amount in the correct format e.g 250.50'
        slot_to_elicit = 'tat_amount'
        buttons = {"don't have this information": "don't have this information"}
        return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
    elif tat_mtcn_number is not None:
        if tat_mtcn_number == 'DON’T HAVE MTCN':
            return get_transaction_details(tat_sender_country, tat_tracking_side, session_attributes, slot_values)
        elif tat_mtcn_number == 'MAIN MENU' or tat_mtcn_number == 'ping':
            title = None
            response_string = 'You can select one of the commonly asked topics below, or type your own question.'
            buttons_text = {
                "Transfer Status": "Transfer Status",
                "How to Send": "How to Send",
                "Edit a Transfer": "Edit a Transfer",
                "Find Locations": "Find Locations",
                "COVID-19 Info": "COVID-19 Info"
            }
            return helpers.elicit_slot_with_choices(session_attributes,
                                                    'wu_q_and_a_intent',
                                                    'q_and_a_topic',
                                                    {'q_and_a_topic': None},
                                                    title,
                                                    buttons_text,
                                                    buttons_text,
                                                    {'contentType': 'PlainText', 'content': response_string}
                                                    )
        elif is_mtcn_input_valid(tat_mtcn_number) is False:
            response_string = '<table border="0"><tr><td>{0}</td><td>&nbsp;{1}</td></tr></table>'.format(
                get_error_image(),
                get_error_message('Invalid entry. Enter a 10-digit Tracking Number (MTCN).')
            )
            buttons = {"MAIN MENU": "MAIN MENU", "DON’T HAVE MTCN": "DON’T HAVE MTCN"}
            slot_to_elicit = 'tat_mtcn_number'
        else:
            response_string = find_status(tat_sender_country, tat_mtcn_number, {})
            buttons = {"Yes": "Yes", "No": "No"}
            slot_to_elicit = 'tat_confirm'
    elif tat_tracking_side is not None:
        response_string = 'Great! Please enter your 10-digit Tracking Number (MTCN). If you don’t have it, choose ' \
                          'an option below:'
        slot_to_elicit = 'tat_mtcn_number'
        buttons_text = {"MAIN MENU": "MAIN MENU", "DON’T HAVE MTCN": "DON’T HAVE MTCN"}
        return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons_text, response_string)
    elif tat_sender_country is not None:
        logger.debug('<<western_union>> track_transfer_handler: tat_sender_country = ' + tat_sender_country)
        tat_sender_country = get_country_code(tat_sender_country.lower())
        if tat_sender_country is not None:
            slot_values['tat_sender_country'] = tat_sender_country.lower()
            slot_to_elicit = 'tat_tracking_side'
            response_string = 'Are you the sender or receiver? '
            buttons = {"I'm the sender": "I'm the sender", "I'm the receiver": "I'm the receiver"}
            return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
        else:
            slot_to_elicit = 'tat_sender_country'
            response_string = 'The country you entered is not recognized. To track your transfer, please tell me the ' \
                              'name of the country the money was sent <strong>from</strong>.'

    return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)


def elicit_slot(session_attributes, slot_to_elicit, slot_values, response_string):
    return helpers.elicit_slot(
        session_attributes, 'wu_tat_intent', slot_to_elicit, slot_values,
        {'contentType': 'CustomPayload', 'content': response_string}
    )


def elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons_text, response_string):
    return helpers.elicit_slot_with_choices(
        session_attributes, 'wu_tat_intent', slot_to_elicit, slot_values, None, buttons_text, buttons_text,
        {'contentType': 'CustomPayload', 'content': response_string}
    )


def get_country_code(country):
    return next(
        (c for c in COUNTRY_CURRENCY_LIST if c["name"].lower() == country.lower()
         or c["code"].lower() == country
         or any(s.lower() == country.lower() for s in c["synonyms"])
         ),
        {}
    ).get('code', None)


def get_currency_code(country_code):
    return next(
        (c for c in COUNTRY_CURRENCY_LIST if c["code"].lower() == country_code.lower()),
        {'currencies': [None]}
    )['currencies'][0]


def get_transaction_details(tat_sender_country, tat_tracking_side, session_attributes, slot_values):
    tat_identifier_type = slot_values.get('tat_identifier_type', None)#sender phone or sender and reciever name
    tat_sender_phone_number = slot_values.get('tat_sender_phone_number', None)
    tat_sender_first_name = slot_values.get('tat_sender_first_name', None)
    tat_sender_last_name = slot_values.get('tat_sender_last_name', None)
    tat_receiver_first_name = slot_values.get('tat_receiver_first_name', None)
    tat_receiver_last_name = slot_values.get('tat_receiver_last_name', None)

    if tat_identifier_type is not None:
        if tat_identifier_type == 'Sender phone':
            additional_details = txn_additional_details(
                tat_sender_country, tat_tracking_side, tat_sender_phone_number,
                tat_sender_first_name, tat_sender_last_name, tat_receiver_first_name, tat_receiver_last_name,
                session_attributes, slot_values
            )
            if additional_details:
                return additional_details
            elif tat_sender_phone_number is not None and is_phone_number_valid(tat_sender_phone_number):
                response_string = 'Enter the name of the country the money was sent <strong>to</strong>.'
                slot_to_elicit = 'tat_receiver_country'
            else:
                response_string = 'Please enter the sender\'s phone number, without the country code, ' \
                                  'spaces or hyphens(-) e.g 8312238014'
                slot_to_elicit = 'tat_sender_phone_number'
            buttons = {"don't have this information": "don't have this information"}
            return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
        elif tat_identifier_type == 'Sender & Receiver Name':
            additional_details = txn_additional_details(
                tat_sender_country, tat_tracking_side, tat_sender_phone_number,
                tat_sender_first_name, tat_sender_last_name, tat_receiver_first_name, tat_receiver_last_name,
                session_attributes, slot_values
            )
            if additional_details:
                return additional_details
            elif tat_receiver_last_name is not None:
                response_string = 'Enter the name of the country the money was sent <strong>to</strong>.'
                slot_to_elicit = 'tat_receiver_country'
            elif tat_receiver_first_name is not None:
                response_string = 'Great! Now enter the Receiver\'s <strong>last name</strong>.'
                slot_to_elicit = 'tat_receiver_last_name'
            elif tat_sender_last_name is not None:
                response_string = 'Please enter the Receiver\'s <strong>first name</strong>.'
                slot_to_elicit = 'tat_receiver_first_name'
            elif tat_sender_first_name is not None:
                response_string = 'Great! Now enter the Sender\'s <strong>last name</strong>.'
                slot_to_elicit = 'tat_sender_last_name'
            else:
                response_string = 'Please enter the Sender\'s <strong>first name</strong>.'
                slot_to_elicit = 'tat_sender_first_name'
            buttons = {"don't have this information": "don't have this information"}
            return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
    else:
        response_string = 'No problem. Which one of the following can you share with us?'
        slot_to_elicit = 'tat_identifier_type'
        buttons_text = {"Sender's Phone Number": "Sender's Phone Number",
                        "Sender & Receiver Name": "Sender & Receiver Name",
                        "don't have this information": "don't have this information"}
        return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons_text, response_string)


def txn_additional_details(sender_country, tracking_side, sender_phone_number, tat_sender_first_name,
                           tat_sender_last_name, tat_receiver_first_name, tat_receiver_last_name,
                           session_attributes, slot_values):
    tat_receiver_country = slot_values.get('tat_receiver_country', None)
    tat_amount_type = slot_values.get('tat_amount_type', None)
    tat_amount = slot_values.get('tat_amount', None)
    tat_date = slot_values.get('tat_date', None)
    if tat_amount is not None or tat_date is not None:

        if tat_date is not None:
            try:
                datetime.datetime.strptime(tat_date, '%Y-%m-%d')
            except ValueError:
                response_string = 'Enter the date of transfer e.g today or October 12, 2020.'
                slot_to_elicit = 'tat_date'
                return elicit_slot(session_attributes, slot_to_elicit, slot_values, response_string)
        response_string = find_status_using_txn_details(
            sender_country,
            tracking_side,
            sender_phone_number,
            tat_sender_first_name, tat_sender_last_name, tat_receiver_first_name, tat_receiver_last_name,
            tat_receiver_country,
            tat_amount_type,
            round(float(tat_amount), 2),
            tat_date
        )
        if 'MULTIPLE TRANSACTIONS FOUND' in response_string and tat_date is None:
            response_string = 'Enter the date of transfer e.g today or October 12, 2020.'
            slot_to_elicit = 'tat_date'
        else:
            slot_to_elicit = 'tat_confirm'
        return elicit_slot(session_attributes, slot_to_elicit, slot_values, response_string)
    if tat_amount_type is not None:
        response_string = 'Please provide the amount {0}, in the following format e.g 100.00'.format(
            'sent' if tat_amount_type.lower() == 'send' else 'received',
            get_currency_code(sender_country if tat_amount_type.lower() == 'send' else tat_receiver_country)
        )
        slot_to_elicit = 'tat_amount'
        buttons = {"don't have this information": "don't have this information"}
        return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
    elif tat_receiver_country is not None:
        tat_receiver_country = get_country_code(tat_receiver_country.lower())
        if tat_receiver_country is not None:
            slot_values['tat_receiver_country'] = tat_receiver_country.lower()
            response_string = 'Do you know the transfer amount?'
            slot_to_elicit = 'tat_amount_type'
            buttons = {
                "Yes, send amount": "Yes, send amount",
                "Yes, receive amount": "Yes, receive amount",
                "don't have this information": "don't have this information"
            }
            return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
        else:
            response_string = 'Enter the name of the country the money was sent <strong>to</strong>.'
            slot_to_elicit = 'tat_receiver_country'
            buttons = {"don't have this information": "don't have this information"}
            return elicit_slot_with_choices(session_attributes, slot_to_elicit, slot_values, buttons, response_string)
    return None


def is_mtcn_input_valid(value):
    return value.isdigit() and len(value) == 10


def is_phone_number_valid(value):
    return value.isdigit() and 5 <= len(value) <= 15


def get_error_image():
    return '<img width="12" src="{0}" />'.format('{0}/icons/tat/invalid.png'.format(os.environ.get('cdn_url', '')))


def get_error_message(msg):
    return '<span style="color:red;">{0}<span/>'.format(msg)


def find_status_using_txn_details(sender_country, tracking_side, sender_phone, sender_first_name, sender_last_name,
                                  receiver_first_name, receiver_last_name, receiver_country, amount_type, amount, date):
    additional_info = {
        "sender": {"contact_phone": sender_phone},
        "receiver": {"address": {"country_iso_code": receiver_country.upper()}},
        "payment_details": {
            "destination": {
                "country_iso_code": receiver_country.upper(),
                "currency_iso_code": get_currency_code(receiver_country)
            },
            "origination": {
                "country_iso_code": sender_country.upper(),
                "currency_iso_code": get_currency_code(sender_country)
            }
        },
        "money_transfer_control": {},
        "query_params": {"param": [{"type": "TRACKING_SIDE", "value": tracking_side.upper()}]}
    }
    additional_info_names = {
        "sender": {"name": {"first_name": sender_first_name, "last_name": sender_last_name}},
        "receiver": {
            "address": {"country_iso_code": receiver_country.upper()},
            "name": {"first_name": receiver_first_name, "last_name": receiver_last_name}
        }
    }
    if date is not None:
        additional_info['money_transfer_control']['date'] = date
    if sender_phone is None:
        additional_info.update(additional_info_names)
    if amount_type.lower() == 'send':
        additional_info['payment_details']['origination']['principal_amount'] = amount * 100
    else:
        additional_info['payment_details']['destination']['expected_payout_amount'] = amount * 100
    return find_status(sender_country, None, additional_info)#######NO  MTCN


def find_status(tat_sender_country, tat_mtcn_number, additional_info):
    status = track_transfer(tat_sender_country, tat_mtcn_number, additional_info)
    logger.debug('<<western_union>> lambda_handler: find_status status = ' + json.dumps(status))

    image_tick = '<img width="15" style="vertical-align:middle;" src="{0}"/>'.format(
        '{0}/icons/tat/tick.svg'.format(os.environ.get('cdn_url', ''))
    )
    image_current = '<img width="15" style="vertical-align:middle;" src="{0}"/>'.format(
        '{0}/icons/tat/current.svg'.format(os.environ.get('cdn_url', ''))
    )
    image_future = '<img width="12" style="vertical-align:middle;" src="{0}"/>'.format(
        '{0}/icons/tat/future.svg'.format(os.environ.get('cdn_url', ''))
    )

    image = '<table border="0">'
    for i in range(1, status['progress_indicator']):
        status_message = PROGRESS_INDICATOR_MAPPING.get(str(i), 'Unknown')
        image = image + '<tr><td>{0}</td><td>&nbsp;{1}</td></tr>'.format(
            image_tick, status_message
        )

    image = image + '<tr><td>{0}</td><td>&nbsp;<strong>{1}</strong></td></tr>'.format(
        get_error_image() if status['progress_indicator'] == -1 else image_current,
        get_error_message(status['message']) if status['progress_indicator'] == -1 else status['status_label']
    )
    #status is in progress
    if 1 <= status['progress_indicator'] <= 3 and \
            status['status_label'].lower() not in ['canceled', 'declined', 'delivered', 'refunded']:
        image = image + '<tr><td style="text-align: center;">{0}</td><td>&nbsp;<span style="color: #6B6B6B;">{1}' \
                        '</span></td></tr>'.format(
            image_future,
            'Paid' if status['status_label'].lower() == 'paid' else 'Received')
    image = image + '</table>'

    return '{0}{1}{2}<br/>{3}'.format(
        'Tracking # (MTCN): <strong>{0}</strong>'.format(tat_mtcn_number) if tat_mtcn_number else '',
        image,
        '' if status['progress_indicator'] == -1 else '<strong>' + status['message'] + '</strong>',
        'Is there anything else I can help with?'
    )


def track_transfer(tat_sender_country, mtcn, additional_info):
    create_session_request = {
        "device": {
            "type": "WEB"
        },
        "channel": {
            "name": "Western Union",
            "type": "WEB",
            "version": "9Z00",
            "device_identifier": "RESPONSIVE_WEB"
        },
        "external_reference_no": "1",
        "locale": {
            "country_code": tat_sender_country,
            "language_code": "en"
        }
    }
    create_session_response = call_cs_api('GwpCreateSession', create_session_request)
    create_session_error = create_session_response.get('error', None)

    if create_session_error is None:
        track_transfer_request = {
            "channel": {"name": "Western Union", "type": "WEB", "version": "9Z00"},
            "security": {
                "session": {
                    "id": create_session_response['security']['session']['id']
                },
                "version": "3"
            },
            "money_transfer_control": {"mtcn": mtcn},
            "inquiry_type": "MONEY_TRANSFER",
            "bashPath": "/{0}/en".format(tat_sender_country)
        }
        track_transfer_request.update(additional_info)
        if mtcn is None:
            del track_transfer_request['inquiry_type']
        track_transfer_response = call_cs_api('GwpTransactionInquiry', track_transfer_request)
        track_transfer_error = track_transfer_response.get('error', None)
        if track_transfer_error is None:
            return {
                'message': track_transfer_response['status_details']['message'],
                'status_label': track_transfer_response['status_details']['status_label'],
                'progress_indicator': int(track_transfer_response['status_details']['progress_indicator'])
            }
        else:
            message = 'Something went wrong, please try again later.' if type(track_transfer_error) == str else \
                track_transfer_error.get('message', 'Something went wrong, please try again later.')
            return {
                'message': message,
                'progress_indicator': -1
            }
    return {
        'message': 'Unable to track you transfer at this moment, please try again later.',
        'progress_indicator': -1
    }


def call_cs_api(api_function, request_body):
    logger.debug('<<western_union>> lambda_handler: call_cs_api function = ' + api_function)
    logger.debug('<<western_union>> lambda_handler: call_cs_api request = ' + json.dumps(request_body))
    cs_api_endpoint = 'https://{0}/wudgtsrvs/mobiliser/rest/channel/'.format('www.westernunion.com')
    request = http.request(
        'POST',
        '{0}{1}'.format(cs_api_endpoint, api_function),
        headers={'Content-Type': 'application/json', 'wuchatbot': 'true','User-Agent':'wuchatbot v1.0'},
        body=json.dumps(request_body)
    )

    logger.debug('<<western_union>> lambda_handler: call_cs_api response code = ' + str(request.status))
    response = json.loads(request.data)
    logger.debug('<<western_union>> lambda_handler: call_cs_api response = ' + json.dumps(response))
    return response


PROGRESS_INDICATOR_MAPPING = {
    '1': 'Sent',
    '2': 'In progress',
    '3': 'Delivered'
}

COUNTRY_CURRENCY_LIST = [
    {
        "name": "Afghanistan",
        "code": "AF",
        "currencies": [
            "AFN",
            "USD"
        ],
        "synonyms": [
            "afg",
            "afgh",
            "afghan",
            "Islamic Republic of Afghanistan"
        ]
    },
    {
        "name": "American Samoa",
        "code": "AS",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Aruba",
        "code": "AW",
        "currencies": [
            "AWG"
        ],
        "synonyms": []
    },
    {
        "name": "Bermuda",
        "code": "BM",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "the Islands of Bermuda",
            "Islands of Bermuda"
        ]
    },
    {
        "name": "Belarus",
        "code": "BY",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Byelorussia",
            "Belorussia",
            "Republic of Belarus"
        ]
    },
    {
        "name": "Cayman Islands",
        "code": "KY",
        "currencies": [
            "KYD",
            "USD"
        ],
        "synonyms": [
            "The Cayman Islands"
        ]
    },
    {
        "name": "Eritrea",
        "code": "ER",
        "currencies": [
            "ERN"
        ],
        "synonyms": [
            "the State of Eritrea",
            "State of Eritrea"
        ]
    },
    {
        "name": "Fiji",
        "code": "FJ",
        "currencies": [
            "FJD"
        ],
        "synonyms": []
    },
    {
        "name": "Falkland Islands (Malvinas)",
        "code": "FK",
        "currencies": [
            "FKP",
            "USD"
        ],
        "synonyms": [
            "Malvinas",
            "Falklands",
            "The Falkland Islands",
            "Falkland Islands"
        ]
    },
    {
        "name": "Grenada",
        "code": "GD",
        "currencies": [
            "XCD"
        ],
        "synonyms": []
    },
    {
        "name": "Equatorial Guinea",
        "code": "GQ",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "Republic of Equatorial Guinea",
            "The Republic of Equatorial Guinea"
        ]
    },
    {
        "name": "Jamaica",
        "code": "JM",
        "currencies": [
            "JMD"
        ],
        "synonyms": []
    },
    {
        "name": "Kosovo",
        "code": "K1",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "the Republic of Kosovo",
            "Republic of Kosovo"
        ]
    },
    {
        "name": "Lithuania",
        "code": "LT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Lithuania",
            "The Republic of Lithuania"
        ]
    },
    {
        "name": "Madagascar",
        "code": "MG",
        "currencies": [
            "MGA"
        ],
        "synonyms": [
            "Republic of Madagascar",
            "The Republic of Madagascar"
        ]
    },
    {
        "name": "Mongolia",
        "code": "MN",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Malawi",
        "code": "MW",
        "currencies": [
            "MWK"
        ],
        "synonyms": [
            "the Republic of Malawi",
            "Republic of Malawi"
        ]
    },
    {
        "name": "New Zealand",
        "code": "NZ",
        "currencies": [
            "NZD"
        ],
        "synonyms": [
            "NewZealand"
        ]
    },
    {
        "name": "Solomon Islands",
        "code": "SB",
        "currencies": [
            "SBD"
        ],
        "synonyms": [
            "The Solomon Islands"
        ]
    },
    {
        "name": "Singapore",
        "code": "SG",
        "currencies": [
            "SGD"
        ],
        "synonyms": [
            "The Republic of Singapore",
            "Republic of Singapore"
        ]
    },
    {
        "name": "Sudan",
        "code": "SD",
        "currencies": [
            "SDG"
        ],
        "synonyms": [
            "the Republic of the Sudan",
            "Republic of the Sudan"
        ]
    },
    {
        "name": "South Sudan",
        "code": "SS",
        "currencies": [
            "SSP"
        ],
        "synonyms": [
            "the Republic of South Sudan",
            "Republic of South Sudan"
        ]
    },
    {
        "name": "Slovenia",
        "code": "SI",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "the People's Republic of Slovenia",
            "People's Republic of Slovenia",
            "the Peoples Republic of Slovenia",
            "Peoples Republic of Slovenia",
            "Republic of Slovenia",
            "Socialist Republic of Slovenia"
        ]
    },
    {
        "name": "Senegal",
        "code": "SN",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "the Republic of Senegal",
            "Republic of Senegal"
        ]
    },
    {
        "name": "Suriname",
        "code": "SR",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Dutch Guiana",
            "Republic of Suriname",
            "The Republic of Suriname",
            "Netherlands Guiana"
        ]
    },
    {
        "name": "Turkey",
        "code": "TR",
        "currencies": [
            "TRY",
            "USD"
        ],
        "synonyms": [
            "Republic of Turkey",
            "The Republic of Turkey"
        ]
    },
    {
        "name": "Taiwan",
        "code": "TW",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Separate Customs Territory of Taiwan",
            "Separate Customs Territory of Taiwan",
            "Nationalist China",
            "Zhongguo"
        ]
    },
    {
        "name": "United States",
        "code": "US",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "United States of America",
            "The United States of America",
            "US",
            "U.S",
            "U.S.",
            "U.S.A",
            "U.S.A.",
            "USA",
            "America",
            "The US",
            "The U.S",
            "The U.S.",
            "The USA",
            "The U.S.A",
            "The U.S.A.",
            "the States"
        ]
    },
    {
        "name": "Mayotte",
        "code": "YT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "the Department of Mayotte",
            "Department of Mayotte"
        ]
    },
    {
        "name": "United Arab Emirates",
        "code": "AE",
        "currencies": [
            "AED"
        ],
        "synonyms": [
            "UAE",
            "U.A.E",
            "U.A.E.",
            "Arab Emirates",
            "The Emirates"
        ]
    },
    {
        "name": "Albania",
        "code": "AL",
        "currencies": [
            "ALL",
            "EUR"
        ],
        "synonyms": [
            "Republic of Albania",
            "The Republic of Albania",
            "Arbanon"
        ]
    },
    {
        "name": "Burkina Faso",
        "code": "BF",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "Burkina",
            "Upper Volta"
        ]
    },
    {
        "name": "Bahrain",
        "code": "BH",
        "currencies": [
            "BHD"
        ],
        "synonyms": [
            "Kingdom of Bahrain",
            "State of Bahrain",
            "Pearl of the Gulf"
        ]
    },
    {
        "name": "Bolivia",
        "code": "BO",
        "currencies": [
            "BOB",
            "USD"
        ],
        "synonyms": [
            "Plurinational State of Bolivia",
            "Republic of Bolivar",
            "Republic of Bolivia",
            "The Republic of Bolivia"
        ]
    },
    {
        "name": "Cyprus (Northern)",
        "code": "C2",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Cyprus",
            "The Republic of Cyprus"
        ]
    },
    {
        "name": "Canada",
        "code": "CA",
        "currencies": [
            "CAD"
        ],
        "synonyms": [
            "Dominion of Canada",
            "CN",
            "CAN"
        ]
    },
    {
        "name": "Switzerland",
        "code": "CH",
        "currencies": [
            "CHF"
        ],
        "synonyms": [
            "Swiss Confederation"
        ]
    },
    {
        "name": "Czech Republic",
        "code": "CZ",
        "currencies": [
            "CZK"
        ],
        "synonyms": [
            "Czechia",
            "Czech",
            "Czechland",
            "Czech lands",
            "Bohemian lands"
        ]
    },
    {
        "name": "Egypt",
        "code": "EG",
        "currencies": [
            "EGP",
            "USD"
        ],
        "synonyms": [
            "Arab Republic of Egypt"
        ]
    },
    {
        "name": "Spain",
        "code": "ES",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Kingdom of Spain"
        ]
    },
    {
        "name": "Georgia",
        "code": "GE",
        "currencies": [
            "GEL",
            "USD"
        ],
        "synonyms": [
            "Iberia",
            "Iberia",
            "Republic of Georgia"
        ]
    },
    {
        "name": "French Guiana",
        "code": "GF",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Department of French Guiana"
        ]
    },
    {
        "name": "Gibraltar",
        "code": "GI",
        "currencies": [
            "GBP"
        ],
        "synonyms": []
    },
    {
        "name": "Haiti",
        "code": "HT",
        "currencies": [
            "HTG"
        ],
        "synonyms": [
            "Republic of Haiti",
            "Hayti"
        ]
    },
    {
        "name": "Iceland",
        "code": "IS",
        "currencies": [
            "ISK",
            "EUR"
        ],
        "synonyms": [
            "Republic of Iceland",
            "Republic of Ice land",
            "Ice land",
            "Rep of Iceland"
        ]
    },
    {
        "name": "Kenya",
        "code": "KE",
        "currencies": [
            "KES"
        ],
        "synonyms": [
            "Republic of Kenya"
        ]
    },
    {
        "name": "Saint Kitts and Nevis",
        "code": "KN",
        "currencies": [
            "XCD",
            "USD"
        ],
        "synonyms": [
            "Federation of Saint Kitts and Nevis",
            "Saint Kitts",
            "Saint Christopher and Nevis",
            "St Kitts",
            "St Kitts-Nevis"
        ]
    },
    {
        "name": "Liberia",
        "code": "LR",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "the Republic of Liberia",
            "Republic of Liberia"
        ]
    },
    {
        "name": "Marshall Islands",
        "code": "MH",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of the Marshall Islands",
            "The Republic of the Marshall Islands"
        ]
    },
    {
        "name": "Maldives",
        "code": "MV",
        "currencies": [
            "MVR"
        ],
        "synonyms": [
            "Republic of the Maldives",
            "The Maldive Islands",
            "The Maldive Island",
            "The Maldives Islands"
        ]
    },
    {
        "name": "Nigeria",
        "code": "NG",
        "currencies": [
            "NGN"
        ],
        "synonyms": [
            "Federal Republic of Nigeria",
            "Naija",
            "Republic of Nigeria"
        ]
    },
    {
        "name": "Niue",
        "code": "NU",
        "currencies": [
            "NZD"
        ],
        "synonyms": [
            "the Republic of Niue"
        ]
    },
    {
        "name": "Philippines",
        "code": "PH",
        "currencies": [
            "PHP",
            "USD"
        ],
        "synonyms": [
            "Republic of the Philippines",
            "Pilipinas",
            "Felipinas"
        ]
    },
    {
        "name": "Pakistan",
        "code": "PK",
        "currencies": [
            "PKR"
        ],
        "synonyms": [
            "Islamic Republic of Pakistan",
            "Pak",
            "Federation of Pakistan"
        ]
    },
    {
        "name": "Puerto Rico",
        "code": "PR",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Commonwealth of Puerto Rico",
            "PuertoRico",
            "Puerto",
            "Porto Rico",
            "PortoRico"
        ]
    },
    {
        "name": "Reunion Island",
        "code": "RE",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Reunion",
            "Reunio"
        ]
    },
    {
        "name": "",
        "code": "XZ",
        "currencies": [
            "GBP"
        ],
        "synonyms": []
    },
    {
        "name": "Argentina",
        "code": "AR",
        "currencies": [
            "ARS"
        ],
        "synonyms": [
            "Argentine Republic",
            "Argentine Republic",
            "the Argentine",
            "Argentine Nation",
            "Argentine"
        ]
    },
    {
        "name": "Barbados",
        "code": "BB",
        "currencies": [
            "BBD"
        ],
        "synonyms": [
            "Bim",
            "Bimshire"
        ]
    },
    {
        "name": "Belgium",
        "code": "BE",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Kingdom of Belgium",
            "The Kingdom of Belgium",
            "Bel gium"
        ]
    },
    {
        "name": "Bhutan",
        "code": "BT",
        "currencies": [
            "BTN"
        ],
        "synonyms": [
            "Kingdom of Bhutan",
            "The Kingdom of Bhutan"
        ]
    },
    {
        "name": "Central African Republic",
        "code": "CF",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "Ubangi-Shari",
            "Central African Empire"
        ]
    },
    {
        "name": "Algeria",
        "code": "DZ",
        "currencies": [
            "DZD"
        ],
        "synonyms": [
            "People's Democratic Republic of Algeria",
            "Peoples Democratic Republic of Algeria",
            "Democratic Republic of Algeria",
            "Republic of Algeria",
            "al-Jazair",
            "al jazair",
            "Jazair"
        ]
    },
    {
        "name": "Estonia",
        "code": "EE",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Estland",
            "Eesti",
            "Estland"
        ]
    },
    {
        "name": "France",
        "code": "FR",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "French Republic",
            "French",
            "Gaul"
        ]
    },
    {
        "name": "Guinea",
        "code": "GN",
        "currencies": [
            "GNF"
        ],
        "synonyms": [
            "Republic of Guinea-Bissau",
            "Guinea-Bissau",
            "Bissau"
        ]
    },
    {
        "name": "Iraq",
        "code": "IQ",
        "currencies": [
            "IQD"
        ],
        "synonyms": [
            "Republic of Iraq"
        ]
    },
    {
        "name": "Italy",
        "code": "IT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Repubblica Italiana",
            "Italiana",
            "Italia"
        ]
    },
    {
        "name": "Kyrghyz Republic",
        "code": "KG",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Kyrgyzstan",
            "Republic of Kyrgyzstan"
        ]
    },
    {
        "name": "Kiribati",
        "code": "KI",
        "currencies": [
            "AUD"
        ],
        "synonyms": [
            "Republic of Kiribati"
        ]
    },
    {
        "name": "Luxembourg",
        "code": "LU",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Grand Duchy of Luxembourg",
            "Grand Duchy",
            "Luxemburgo",
            "Lussemburgo"
        ]
    },
    {
        "name": "Morocco",
        "code": "MA",
        "currencies": [
            "MAD"
        ],
        "synonyms": [
            "Kingdom of Morocco",
            "Marrakesh"
        ]
    },
    {
        "name": "Mexico",
        "code": "MX",
        "currencies": [
            "MXN"
        ],
        "synonyms": [
            "United Mexican States",
            "Maxico",
            "MEX",
            "Mexicana"
        ]
    },
    {
        "name": "Mozambique",
        "code": "MZ",
        "currencies": [
            "MZN"
        ],
        "synonyms": [
            "Republic of Mozambique"
        ]
    },
    {
        "name": "Nicaragua",
        "code": "NI",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Nicaragua"
        ]
    },
    {
        "name": "Nepal",
        "code": "NP",
        "currencies": [
            "NPR"
        ],
        "synonyms": [
            "Federal Democratic Republic Of Nepal",
            "NPL"
        ]
    },
    {
        "name": "Peru",
        "code": "PE",
        "currencies": [
            "PEN",
            "USD"
        ],
        "synonyms": [
            "Republic of Peru",
            "Peruana",
            "Peru"
        ]
    },
    {
        "name": "French Polynesia",
        "code": "PF",
        "currencies": [
            "XPF"
        ],
        "synonyms": []
    },
    {
        "name": "Qatar",
        "code": "QA",
        "currencies": [
            "QAR"
        ],
        "synonyms": [
            "State of Qatar"
        ]
    },
    {
        "name": "Somalia",
        "code": "SO",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Federal Republic of Somalia",
            "Soomaaliya"
        ]
    },
    {
        "name": "Chad",
        "code": "TD",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "Republic of Chad",
            "Tchad"
        ]
    },
    {
        "name": "Togo",
        "code": "TG",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "Togolese Republic"
        ]
    },
    {
        "name": "Vietnam",
        "code": "VN",
        "currencies": [
            "VND",
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Cyprus",
        "code": "CY",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Cyprus"
        ]
    },
    {
        "name": "Finland",
        "code": "FI",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Finland"
        ]
    },
    {
        "name": "Micronesia",
        "code": "FM",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Greece",
        "code": "GR",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Hellas",
            "Hellenic Republic",
            "Yavan"
        ]
    },
    {
        "name": "Guatemala",
        "code": "GT",
        "currencies": [
            "GTQ"
        ],
        "synonyms": [
            "Republic of Guatemala"
        ]
    },
    {
        "name": "Croatia",
        "code": "HR",
        "currencies": [
            "HRK"
        ],
        "synonyms": [
            "Republic of Montenegro"
        ]
    },
    {
        "name": "Jordan",
        "code": "JO",
        "currencies": [
            "JOD"
        ],
        "synonyms": [
            "Hashemite Kingdom of Jordan"
        ]
    },
    {
        "name": "Cambodia",
        "code": "KH",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Kingdom of Cambodia",
            "State of Cambodia"
        ]
    },
    {
        "name": "Comoros",
        "code": "KM",
        "currencies": [
            "KMF"
        ],
        "synonyms": [
            "Union of the Comoros",
            "United Republic of the Commoros",
            "Commoros"
        ]
    },
    {
        "name": "Korea, Republic of",
        "code": "KR",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Korea",
            "South Korea"
        ]
    },
    {
        "name": "Kuwait",
        "code": "KW",
        "currencies": [
            "KWD"
        ],
        "synonyms": [
            "State of Kuwait"
        ]
    },
    {
        "name": "Saint Lucia",
        "code": "LC",
        "currencies": [
            "XCD"
        ],
        "synonyms": [
            "St. Lucia"
        ]
    },
    {
        "name": "Moldova, Republic of",
        "code": "MD",
        "currencies": [
            "MDL",
            "EUR",
            "USD"
        ],
        "synonyms": [
            "Republic of Moldova",
            "Moldova",
            "Moldavia"
        ]
    },
    {
        "name": "Mauritania",
        "code": "MR",
        "currencies": [
            "MRU"
        ],
        "synonyms": [
            "Islamic Republic of Mauritania",
            "Republic of Mauritania",
            "Mauritanie"
        ]
    },
    {
        "name": "Malaysia",
        "code": "MY",
        "currencies": [
            "MYR"
        ],
        "synonyms": [
            "Malaya",
            "Malesiya"
        ]
    },
    {
        "name": "Niger",
        "code": "NE",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "The Niger",
            "Republic of the Niger"
        ]
    },
    {
        "name": "Oman",
        "code": "OM",
        "currencies": [
            "OMR"
        ],
        "synonyms": [
            "Sultanate of Oman"
        ]
    },
    {
        "name": "Tajikistan",
        "code": "TJ",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Tajikistan"
        ]
    },
    {
        "name": "Tunisia",
        "code": "TN",
        "currencies": [
            "TND"
        ],
        "synonyms": [
            "Republic of Tunisia"
        ]
    },
    {
        "name": "Tanzania",
        "code": "TZ",
        "currencies": [
            "TZS"
        ],
        "synonyms": [
            "United Republic of Tanzania",
            "United Republic of Tanganyika and Zanzibar",
            "Tanganyika",
            "Zanzibar"
        ]
    },
    {
        "name": "Virgin Islands, U.S.",
        "code": "VI",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "United States Virgin Islands",
            "U.S. Virgin Islands"
        ]
    },
    {
        "name": "Curacao",
        "code": "AN",
        "currencies": [
            "ANG"
        ],
        "synonyms": []
    },
    {
        "name": "Saint Barthelemy",
        "code": "BL",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Saint-Barthelemy",
            "St.  Barthelemy",
            "St  Barthelemy",
            "Barthelemy"
        ]
    },
    {
        "name": "Belize",
        "code": "BZ",
        "currencies": [
            "BZD"
        ],
        "synonyms": [
            "British Honduras"
        ]
    },
    {
        "name": "Congo (DRC)",
        "code": "CD",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Democratic Republic of Congo",
            "DRC"
        ]
    },
    {
        "name": "Congo",
        "code": "CG",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "The Republic of the Congo",
            "Republic of the Congo",
            "Congo-Brazzaville",
            "Congo Republic"
        ]
    },
    {
        "name": "Cook Islands",
        "code": "CK",
        "currencies": [
            "NZD"
        ],
        "synonyms": [
            "The Cook Islands"
        ]
    },
    {
        "name": "Chile",
        "code": "CL",
        "currencies": [
            "CLP"
        ],
        "synonyms": [
            "Republic of Chile",
            "Republic of Chile",
            "Chile",
            "Chilli"
        ]
    },
    {
        "name": "Denmark",
        "code": "DK",
        "currencies": [
            "DKK"
        ],
        "synonyms": [
            "Kingdom of Denmark",
            "Danmark"
        ]
    },
    {
        "name": "Dominica",
        "code": "DM",
        "currencies": [
            "XCD"
        ],
        "synonyms": [
            "Commonwealth of Dominica"
        ]
    },
    {
        "name": "Gabon",
        "code": "GA",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "Gabonese Republic",
            "Gabonese"
        ]
    },
    {
        "name": "Guadeloupe",
        "code": "GP",
        "currencies": [
            "EUR"
        ],
        "synonyms": []
    },
    {
        "name": "Guam",
        "code": "GU",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Guyana",
        "code": "GY",
        "currencies": [
            "GYD"
        ],
        "synonyms": [
            "Cooperative Republic of Guyana",
            "Republic of Guyana"
        ]
    },
    {
        "name": "Hungary",
        "code": "HU",
        "currencies": [
            "HUF",
            "USD"
        ],
        "synonyms": [
            "Republic of Hungary",
            "Hungaria"
        ]
    },
    {
        "name": "Ireland",
        "code": "IE",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Ireland",
            "Aire"
        ]
    },
    {
        "name": "Israel",
        "code": "IL",
        "currencies": [
            "ILS"
        ],
        "synonyms": [
            "State of Israel"
        ]
    },
    {
        "name": "Lebanon",
        "code": "LB",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "The Lebanese Republic",
            "Lebnan",
            "Lubnan"
        ]
    },
    {
        "name": "Latvia",
        "code": "LV",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Latvija"
        ]
    },
    {
        "name": "Monaco",
        "code": "MC",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Principality of Monaco"
        ]
    },
    {
        "name": "Montenegro",
        "code": "ME",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Montenegro",
            "Crna Gora"
        ]
    },
    {
        "name": "Myanmar",
        "code": "MM",
        "currencies": [
            "MMK"
        ],
        "synonyms": [
            "Republic of the Union of Myanmar"
        ]
    },
    {
        "name": "Norway",
        "code": "NO",
        "currencies": [
            "NOK"
        ],
        "synonyms": [
            "Kingdom of Norway"
        ]
    },
    {
        "name": "Nauru",
        "code": "NR",
        "currencies": [
            "AUD"
        ],
        "synonyms": [
            "Republic of Nauru"
        ]
    },
    {
        "name": "Papua New Guinea",
        "code": "PG",
        "currencies": [
            "PGK"
        ],
        "synonyms": [
            "Independent State of Papua New Guinea",
            "New Guinea",
            "Papua New Guinea"
        ]
    },
    {
        "name": "Portugal",
        "code": "PT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Portuguese Republic",
            "Lusitania"
        ]
    },
    {
        "name": "Sweden",
        "code": "SE",
        "currencies": [
            "SEK"
        ],
        "synonyms": [
            "Kingdom of Sweden"
        ]
    },
    {
        "name": "Trinidad and Tobago",
        "code": "TT",
        "currencies": [
            "TTD"
        ],
        "synonyms": [
            "Republic of Trinidad and Tobago",
            "Trinbago"
        ]
    },
    {
        "name": "Virgin Islands, British",
        "code": "VG",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "The British Virgin Islands",
            "BVI",
            "the Virgin Islands",
            "Virgin Islands"
        ]
    },
    {
        "name": "South Africa",
        "code": "ZA",
        "currencies": [
            "ZAR"
        ],
        "synonyms": [
            "S Africa"
        ]
    },
    {
        "name": "Zambia",
        "code": "ZM",
        "currencies": [
            "ZMW"
        ],
        "synonyms": [
            "Republic of Zambia",
            "Northern Rhodesia",
            "The Republic of Zambia"
        ]
    },
    {
        "name": "Zimbabwe",
        "code": "ZW",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Zimbabwe"
        ]
    },
    {
        "name": "Austria",
        "code": "AT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of Austria"
        ]
    },
    {
        "name": "Bosnia and Herzegovina",
        "code": "BA",
        "currencies": [
            "BAM"
        ],
        "synonyms": [
            "Bosnia",
            "Herzegovina"
        ]
    },
    {
        "name": "Bulgaria",
        "code": "BG",
        "currencies": [
            "BGN",
            "EUR"
        ],
        "synonyms": [
            "Republic of Bulgaria",
            "Republic of Bulgaria"
        ]
    },
    {
        "name": "Benin",
        "code": "BJ",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "Republic of Benin"
        ]
    },
    {
        "name": "Cameroon",
        "code": "CM",
        "currencies": [
            "XAF"
        ],
        "synonyms": [
            "Republic of Cameroon"
        ]
    },
    {
        "name": "China",
        "code": "CN",
        "currencies": [
            "CNY",
            "USD"
        ],
        "synonyms": [
            "People's Republic of China",
            "Peoples Republic of China"
        ]
    },
    {
        "name": "Colombia",
        "code": "CO",
        "currencies": [
            "COP"
        ],
        "synonyms": [
            "Republic of Colombia"
        ]
    },
    {
        "name": "Cape Verde",
        "code": "CV",
        "currencies": [
            "CVE"
        ],
        "synonyms": [
            "Cabo Verde"
        ]
    },
    {
        "name": "Germany",
        "code": "DE",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Federal Republic of Germany",
            "Deutschland"
        ]
    },
    {
        "name": "United Kingdom",
        "code": "GB",
        "currencies": [
            "GBP"
        ],
        "synonyms": [
            "United Kingdom of Great Britain and Northern Ireland",
            "U.K",
            "U.K.",
            "UK",
            "Great Britain",
            "G.B.",
            "G.B",
            "Britain"
        ]
    },
    {
        "name": "Gambia",
        "code": "GM",
        "currencies": [
            "GMD"
        ],
        "synonyms": [
            "The Gambia"
        ]
    },
    {
        "name": "Hong Kong",
        "code": "HK",
        "currencies": [
            "HKD",
            "USD"
        ],
        "synonyms": [
            "HonKong"
        ]
    },
    {
        "name": "Liechtenstein",
        "code": "LI",
        "currencies": [
            "CHF"
        ],
        "synonyms": [
            "Principality of Liechtenstein"
        ]
    },
    {
        "name": "Macedonia",
        "code": "MK",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Republic of North Macedonia"
        ]
    },
    {
        "name": "Malta",
        "code": "MT",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            " the Republic of Malta"
        ]
    },
    {
        "name": "Palau",
        "code": "PW",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Palau"
        ]
    },
    {
        "name": "Romania",
        "code": "RO",
        "currencies": [
            "RON",
            "EUR"
        ],
        "synonyms": [
            "Rumania",
            "Roumania"
        ]
    },
    {
        "name": "Russian Federation",
        "code": "RU",
        "currencies": [
            "RUB"
        ],
        "synonyms": [
            "Russia",
            "Soviet Union"
        ]
    },
    {
        "name": "Seychelles",
        "code": "SC",
        "currencies": [
            "SCR"
        ],
        "synonyms": [
            "Republic of Seychelles"
        ]
    },
    {
        "name": "El Salvador",
        "code": "SV",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Uganda",
        "code": "UG",
        "currencies": [
            "UGX"
        ],
        "synonyms": [
            "Republic of Uganda"
        ]
    },
    {
        "name": "Uruguay",
        "code": "UY",
        "currencies": [
            "UYU",
            "USD"
        ],
        "synonyms": [
            "Oriental Republic of Uruguay"
        ]
    },
    {
        "name": "Uzbekistan",
        "code": "UZ",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Uzbekistan"
        ]
    },
    {
        "name": "Vanuatu",
        "code": "VU",
        "currencies": [
            "VUV"
        ],
        "synonyms": []
    },
    {
        "name": "Serbia",
        "code": "YU",
        "currencies": [
            "RSD",
            "EUR"
        ],
        "synonyms": [
            "the Republic of Serbia"
        ]
    },
    {
        "name": "Australia",
        "code": "AU",
        "currencies": [
            "AUD"
        ],
        "synonyms": [
            "Commonwealth of Australia",
            "AUS"
        ]
    },
    {
        "name": "Bangladesh",
        "code": "BD",
        "currencies": [
            "BDT"
        ],
        "synonyms": [
            "People's Republic of Bangladesh",
            "Peoples Republic of Bangladesh",
            "Bangla"
        ]
    },
    {
        "name": "Burundi",
        "code": "BI",
        "currencies": [
            "BIF",
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Brunei",
        "code": "BN",
        "currencies": [
            "BND"
        ],
        "synonyms": [
            "Republic of Burundi"
        ]
    },
    {
        "name": "Brazil",
        "code": "BR",
        "currencies": [
            "BRL"
        ],
        "synonyms": [
            "Federative Republic of Brazil",
            "Brasil"
        ]
    },
    {
        "name": "Botswana",
        "code": "BW",
        "currencies": [
            "BWP"
        ],
        "synonyms": [
            "Republic of Botswana"
        ]
    },
    {
        "name": "Ivory Coast",
        "code": "CI",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "the Ivory Coast",
            "Republic of Cate d'Ivoire",
            "cote d'ivoire"
        ]
    },
    {
        "name": "Cuba",
        "code": "CU",
        "currencies": [
            "CUC"
        ],
        "synonyms": [
            "Republic of Cuba "
        ]
    },
    {
        "name": "Dominican Republic",
        "code": "DO",
        "currencies": [
            "DOP",
            "USD"
        ],
        "synonyms": [
            "Dominicana"
        ]
    },
    {
        "name": "Honduras",
        "code": "HN",
        "currencies": [
            "HNL"
        ],
        "synonyms": [
            "Republic of Honduras"
        ]
    },
    {
        "name": "Indonesia",
        "code": "ID",
        "currencies": [
            "IDR"
        ],
        "synonyms": [
            "Republic of Indonesia"
        ]
    },
    {
        "name": "India",
        "code": "IN",
        "currencies": [
            "INR"
        ],
        "synonyms": [
            "Bharat",
            "Hindustan",
            "Republic of India"
        ]
    },
    {
        "name": "Japan",
        "code": "JP",
        "currencies": [
            "JPY"
        ],
        "synonyms": [
            "Nippon",
            "JPN"
        ]
    },
    {
        "name": "Laos",
        "code": "LA",
        "currencies": [
            "LAK"
        ],
        "synonyms": [
            "Lao People's Democratic Republic",
            "Lao Peoples Democratic Republic"
        ]
    },
    {
        "name": "Macao",
        "code": "MO",
        "currencies": [
            "MOP"
        ],
        "synonyms": []
    },
    {
        "name": "Martinique",
        "code": "MQ",
        "currencies": [
            "EUR"
        ],
        "synonyms": []
    },
    {
        "name": "Montserrat",
        "code": "MS",
        "currencies": [
            "XCD"
        ],
        "synonyms": []
    },
    {
        "name": "Poland",
        "code": "PL",
        "currencies": [
            "PLN",
            "USD"
        ],
        "synonyms": [
            "Republic of Poland",
            "Polska"
        ]
    },
    {
        "name": "New Caledonia",
        "code": "NC",
        "currencies": [
            "XPF",
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Paraguay",
        "code": "PY",
        "currencies": [
            "PYG",
            "USD"
        ],
        "synonyms": [
            "Republic of Paraguay"
        ]
    },
    {
        "name": "St. Maarten",
        "code": "S1",
        "currencies": [
            "ANG",
            "USD"
        ],
        "synonyms": [
            "Sint Maarten",
            "Sint. Maarten"
        ]
    },
    {
        "name": "St. Martin",
        "code": "MF",
        "currencies": [
            "ANG",
            "USD"
        ],
        "synonyms": [
            "Saint Martin"
        ]
    },
    {
        "name": "Saudi Arabia",
        "code": "SA",
        "currencies": [
            "SAR"
        ],
        "synonyms": [
            "Kingdom of Saudi Arabia",
            "KSA",
            "Saudia",
            "Saudi"
        ]
    },
    {
        "name": "Sierra Leone",
        "code": "SL",
        "currencies": [
            "SLL"
        ],
        "synonyms": [
            "Republic of Sierra Leone",
            "Salone"
        ]
    },
    {
        "name": "Thailand",
        "code": "TH",
        "currencies": [
            "THB"
        ],
        "synonyms": [
            "Kingdom of Thailand",
            "Thai"
        ]
    },
    {
        "name": "Turkmenistan",
        "code": "TM",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Turkmenistan"
        ]
    },
    {
        "name": "Tonga",
        "code": "TO",
        "currencies": [
            "TOP"
        ],
        "synonyms": [
            "Kingdom of Tonga",
            "The Kingdom of Tonga"
        ]
    },
    {
        "name": "Ukraine",
        "code": "UA",
        "currencies": [
            "UAH",
            "USD"
        ],
        "synonyms": [
            "UKR"
        ]
    },
    {
        "name": "Saint Vincent and the Grenadines",
        "code": "VC",
        "currencies": [
            "XCD"
        ],
        "synonyms": [
            "Saint Vincent",
            "St. Vincent",
            "St Vincent"
        ]
    },
    {
        "name": "Northern Mariana Islands",
        "code": "MP",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Antigua and Barbuda",
        "code": "AG",
        "currencies": [
            "XCD"
        ],
        "synonyms": []
    },
    {
        "name": "Anguilla",
        "code": "AI",
        "currencies": [
            "XCD",
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Andorra",
        "code": "AD",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "the Principality of Andorra "
        ]
    },
    {
        "name": "Angola",
        "code": "AO",
        "currencies": [
            "AOA"
        ],
        "synonyms": [
            "Republic of Angola"
        ]
    },
    {
        "name": "Azerbaijan",
        "code": "AZ",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Azerbaijan"
        ]
    },
    {
        "name": "Costa Rica",
        "code": "CR",
        "currencies": [
            "CRC",
            "USD"
        ],
        "synonyms": [
            "Republic of Costa Rica"
        ]
    },
    {
        "name": "Djibouti",
        "code": "DJ",
        "currencies": [
            "DJF"
        ],
        "synonyms": [
            "Republic of Djibouti"
        ]
    },
    {
        "name": "Ecuador",
        "code": "EC",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "Republic of Ecuador"
        ]
    },
    {
        "name": "Ethiopia",
        "code": "ET",
        "currencies": [
            "ETB"
        ],
        "synonyms": [
            "Federal Democratic Republic of Ethiopia"
        ]
    },
    {
        "name": "Ghana",
        "code": "GH",
        "currencies": [
            "GHS"
        ],
        "synonyms": [
            "United Gold Coast Convention",
            "UGCC",
            "Gaana"
        ]
    },
    {
        "name": "Guinea-Bissau",
        "code": "GW",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "Portuguese Guinea",
            "Republic of Guinea-Bissau",
            "Guinea Bissau",
            "Guinea"
        ]
    },
    {
        "name": "Kazakhstan",
        "code": "KZ",
        "currencies": [
            "KZT",
            "USD"
        ],
        "synonyms": [
            "Republic of Kazakhstan",
            "Qazaqstan"
        ]
    },
    {
        "name": "Sri Lanka",
        "code": "LK",
        "currencies": [
            "LKR"
        ],
        "synonyms": [
            "Democratic Socialist Republic of Sri Lanka",
            "Srilanka"
        ]
    },
    {
        "name": "Mali",
        "code": "ML",
        "currencies": [
            "XOF"
        ],
        "synonyms": [
            "Republic of Mali"
        ]
    },
    {
        "name": "Mauritius",
        "code": "MU",
        "currencies": [
            "MUR"
        ],
        "synonyms": [
            "Republic of Mauritius"
        ]
    },
    {
        "name": "Netherlands",
        "code": "NL",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Kingdom of the Netherlands",
            "Holland",
            "Nederland"
        ]
    },
    {
        "name": "Panama",
        "code": "PA",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "the Republic of Panama"
        ]
    },
    {
        "name": "Rwanda",
        "code": "RW",
        "currencies": [
            "RWF",
            "USD"
        ],
        "synonyms": [
            "Rwandese Republic",
            "Republic of Rwanda"
        ]
    },
    {
        "name": "Slovakia",
        "code": "SK",
        "currencies": [
            "EUR"
        ],
        "synonyms": [
            "Slovak Republic",
            "Slovensko",
            "SVK"
        ]
    },
    {
        "name": "Sao Tome and Principe",
        "code": "ST",
        "currencies": [
            "STD"
        ],
        "synonyms": [
            "Democratic Republic of Sao Tome and Principe"
        ]
    },
    {
        "name": "East Timor",
        "code": "TP",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "TLS",
            "Timor-Leste",
            "Democratic Republic of Timor-Leste",
            "Timor-Leste"
        ]
    },
    {
        "name": "Tuvalu",
        "code": "TV",
        "currencies": [
            "AUD"
        ],
        "synonyms": [
            "TUV"
        ]
    },
    {
        "name": "Venezuela",
        "code": "VE",
        "currencies": [
            "VEF"
        ],
        "synonyms": [
            "VEN",
            "Bolivarian Republic of Venezuela"
        ]
    },
    {
        "name": "Samoa",
        "code": "WS",
        "currencies": [
            "WST"
        ],
        "synonyms": [
            "Independent State of Samoa"
        ]
    },
    {
        "name": "Lesotho",
        "code": "LS",
        "currencies": [
            "LSL"
        ],
        "synonyms": [
            "LSO",
            "Kingdom of Lesotho"
        ]
    },
    {
        "name": "Namibia",
        "code": "NA",
        "currencies": [
            "NAD"
        ],
        "synonyms": [
            "Republic of Namibia"
        ]
    },
    {
        "name": "Yemen",
        "code": "YE",
        "currencies": [
            "USD"
        ],
        "synonyms": [
            "YEM",
            "Republic of Yemen"
        ]
    },
    {
        "name": "Syria",
        "code": "SY",
        "currencies": [
            "SYP"
        ],
        "synonyms": [
            "the Syrian Arab Republic",
            "SYR"
        ]
    },
    {
        "name": "Palestinian Authority",
        "code": "PS",
        "currencies": [
            "ILS",
            "JOD",
            "USD"
        ],
        "synonyms": [
            "State of Palestine",
            "PSE"
        ]
    },
    {
        "name": "Afghanistan US Military Base",
        "code": "XP",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Belgium US Military Base",
        "code": "QQ",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Cuba US Military Base",
        "code": "QS",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Djibouti US Military Base",
        "code": "QV",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Germany  US Military Base",
        "code": "QO",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Greece US Military Base",
        "code": "QZ",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Guam US Military Base",
        "code": "XY",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Turks and Caicos Islands",
        "code": "TC",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Honduras US Military Base",
        "code": "QR",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Iraq US Military Base",
        "code": "QX",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Italy US Military Base",
        "code": "QP",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Japan US Military Base",
        "code": "QM",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Korea US Military Base",
        "code": "QN",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Kosovo US Military Base",
        "code": "XF",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Kuwait US Military Base",
        "code": "QU",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Netherlands US Military Base",
        "code": "QT",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Portugal US Military Base",
        "code": "XT",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Qatar US Military Base",
        "code": "QY",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Spain US Military Base",
        "code": "AB",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Turkey US Military Base",
        "code": "XN",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    },
    {
        "name": "Bahamas",
        "code": "BS",
        "currencies": [
            "BSD"
        ],
        "synonyms": [
            "The Bahamas"
        ]
    },
    {
        "name": "United Kingdom US Military Base",
        "code": "QW",
        "currencies": [
            "USD"
        ],
        "synonyms": []
    }
]
