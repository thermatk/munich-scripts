import requests
import re
import json
from time import gmtime, strftime, sleep

frame_url = 'https://www46.muenchen.de/termin/index.php?loc=ABH'
termin_type = 'Aufenthaltserlaubnis Blaue Karte EU'

blessed_day = '2019-08-06'

con_salutation = 'FILL'
con_name = 'FILL'
con_email = 'FILL'

tg_bottoken = 'FILL'
tg_chatid = 'FILL'

def tg_bot_post_chat(msg):
    boturl = 'https://api.telegram.org/bot'+ tg_bottoken +'/sendMessage'
    payload = {'chat_id': tg_chatid, 'text': msg,}
    requests.post(boturl, data=payload)

### MAIN
# book only once
booked_none = True
while True:        
    print("Another attempt, time: ", end='')
    print (strftime("%Y-%m-%d %H:%M:%S", gmtime()))

    # Session is required to keep cookies between requests
    s = requests.Session()
    # STEP 1
    # First request to get cookies and token
    firstresponse = s.post(frame_url)
    # get csrf token
    try:
        csrf = re.search('name="__ncforminfo" value="(.+?)"/>', firstresponse.text).group(1)
    except AttributeError:
        print('ERROR: cannot find csrf token in server\'s response.')

    # STEP 2 
    # Get appointments
    termin_data = {
        'CASETYPES[%s]' % termin_type: 1,
        'step': 'WEB_APPOINT_SEARCH_BY_CASETYPES',
        '__ncforminfo': csrf,
    }    
    response = s.post(frame_url, termin_data)
    txt = response.text
    # get json with appointments list
    try:
        json_str = re.search('jsonAppoints = \'(.*?)\'', txt).group(1)
    except AttributeError:
        print('ERROR: cannot find termins data in server\'s response.')

    # Step 3
    # If there are appointments, notify and book as required 
    appointments = json.loads(json_str)
    if appointments:
        # booking
        ##################################
        # book only once
        if booked_none:
            for k, v in appointments.items():
                caption = v['caption']
                first_date = None
                for date in v['appoints']:
                    # check appointment day
                    if v['appoints'][date] and date == blessed_day:
                        # Step 4a
                        # take the first one on this day
                        print("Booking at %s" % date)
                        slot_data = {
                            'step': 'WEB_APPOINT_NEW_APPOINT',
                            'APPOINT': 'Termin+Wartezone+SCIF___%s___%s' % (date,v['appoints'][date][0]),
                        }
                        response_slot = s.post(frame_url, slot_data)
                        try:
                            csrfslot = re.search('name="__ncforminfo" value="(.+?)"/>', response_slot.text).group(1)
                        except AttributeError:
                            print('ERROR: cannot find csrf token in server\'s response.')
                        # Step 4b
                        # last step, book it
                        book_data = {
                            'step': 'WEB_APPOINT_SAVE_APPOINT',
                            'CONTACT[salutation]': con_salutation,
                            'CONTACT[name]': con_name,
                            'CONTACT[email]': con_email,
                            'CONTACT[privacy]': 1,
                            '__ncforminfo': csrfslot,
                        }
                        bookresponse = s.post(frame_url, book_data)
                        print(bookresponse.text)
                        # notify in Telegram about booking
                        tg_bot_post_chat('Booked %s %s' % (date,v['appoints'][date][0]))
                        # book only once
                        booked_none = False
                        break
        ##################################

        # logging/posting to Telegram
        ##################################
        found_any = False
        tg_msg = 'Go book! https://www46.muenchen.de/termin/index.php?cts=1080627 '
        for k, v in appointments.items():
            caption = v['caption']
            for date in v['appoints']:
                if v['appoints'][date]:
                    found_any = True
                    msg_addition = '\nAppointments at %s on %s:\n%s'  % (caption, date, '\n'.join(v['appoints'][date]))
                    tg_msg = tg_msg + msg_addition
        if found_any:
            print("Full dump:")
            print(json.dumps(appointments, sort_keys=True, indent=4, separators=(',', ': ')))
            # post to Telegram
            tg_bot_post_chat(tg_msg)
        # nothing there
        else:
            print('Unfortunately, everything is booked.')
        ##################################

    sleep(50) # Delay for 50 seconds.
