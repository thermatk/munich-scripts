import requests
import re
import json
import time
from time import gmtime, strftime

class Meta(type):
    def __repr__(cls):
        return cls.get_name()


class Buro(metaclass=Meta):
    """
    Base interface-like class for all departments providing appointments on ...muenchen.de/termin/index.php... page
    """

    @staticmethod
    def get_available_appointment_types():
        """
        :return: list of available appointment types
        """
        raise NotImplementedError

    @staticmethod
    def get_frame_url():
        """
        :return: URL with appointments form
        """
        raise NotImplementedError

    @staticmethod
    def _get_base_page():
        """
        :return: actual external web-page containing the frame. Not really needed for implementation, but may be useful
        for testing or debugging
        """
        raise NotImplementedError

    @staticmethod
    def get_name():
        """
        :return: human-readable name of the buro
        """
        raise NotImplementedError

class ForeignLabor(Buro):
    @staticmethod
    def get_name():
        return 'Ausländerbehörde'

    @staticmethod
    def _get_base_page():
        # Apparently there is no single page for all appointments publicly available
        return 'https://www.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Auslaenderwesen/Terminvereinbarung-.html'

    @staticmethod
    def get_frame_url():
        return 'https://www46.muenchen.de/termin/index.php?loc=ABH'

    @staticmethod
    def get_available_appointment_types():
        return [
            'Aufenthaltserlaubnis Blaue Karte EU',
            'Aufenthaltserlaubnis Blaue Karte EU (inländ. Hochschulabsolvent)',
            'Aufenthaltserlaubnis für Forschende',
            'Aufenthaltserlaubnis für Gastwissenschaftler, wissenschaftliche Mitarbeiter',
            'Aufenthaltserlaubnis zum Studium',
            'Aufenthaltserlaubnis zur Studienvorbereitung',
            'Aufenthaltserlaubnis für Doktoranden',
            'Fachrichtungswechsel',
            'Facharztausbildung',
            'Niederlassungserlaubnis allgemein',
            'Niederlassungserlaubnis Blaue Karte EU',
            'Aufenthaltserlaubnis zur Beschäftigung (Fachkräfte / Mangelberufe)',
            'Aufenthaltserlaubnis zur Arbeitsplatzsuche',
            'Selbständige und freiberufliche Erwerbstätigkeit',
            'Ehegattennachzug zum Drittstaatsangehörigen',
            'Eigenständiges Aufenthaltsrecht',
            'Aufenthaltserlaubnis für Kinder',
            'Familiennachzug in Ausnahmefällen',
            'Familiennachzug (SCIF)',
            'Familiennachzug (Stu)',
            'Verpflichtungserklärung (langfristige Aufenthalte)',
            'Verpflichtungserklärung (kurzfristige Aufenthalte)',
            'Erlöschen des Aufenthaltstitels, § 51 AufenthG',
            'Übertrag Aufenthaltstitel in neuen Pass',
            'Bescheinigung (Aufenthaltsstatus)',
            'Aufenthaltserlaubnis für langfristig Aufenthaltsberechtigte',
            'Niederlassungserlaubnis für Familienangehörige von Deutschen',
            'Niederlassungserlaubnis ab 16 Jahren',
            'Aufenthaltserlaubnis zur betrieblichen Ausbildung',
            'Aufenthaltserlaubnis zur Beschäftigung',
            'Niederlassungserlaubnis Asyl / int. Schutzberechtigte',
            'Familiennachzug zu EU-Staatsangehörigen',
            'Daueraufenthaltsbescheinigung',
            'Abholung elektronischer Aufenthaltstitel  (eAT)',
            'Abholung elektronischer Reiseausweis (eRA)',
            'Schülersammelliste',
            'Aufenthaltserlaubnis aus humanitären Gründen',
            'Medizinische Behandlung (Privatpatienten)',
            'Medizinische Behandlung (Botschaftspatienten)',
            'Werkverträge',
            'Firmenkunden',
            'Aufenthaltserlaubnis zur Arbeitsplatzsuche (16 V)',
            'Niederlassungserlaubnis für Hochqualifizierte',
            'Änderung der Nebenbestimmungen (AE)',
            'Niederlassungserlaubnis für Absolventen dt. Hochschulen',
            'Beratung allgemein',
            'Familiennachzug zu dt. Staatsangehörigen',
            'Aufenthaltserlaubnis zum Deutschintensivkurs',
        ]

if __name__ == '__main__':

    booked_none = True
    while True:        
        print("Another attempt, time: ", end='')
        print (strftime("%Y-%m-%d %H:%M:%S", gmtime()))

        # get appointments for Blaue Karte
        ##################################
        buro = ForeignLabor
        termin_type = 'Aufenthaltserlaubnis Blaue Karte EU'
            # Session is required to keep cookies between requests
        s = requests.Session()
        # First request to get and save cookies
        firstresponse = s.post(buro.get_frame_url())
        # get csrf token
        try:
            csrf = re.search('name="__ncforminfo" value="(.+?)"/>', firstresponse.text).group(1)
        except AttributeError:
            print('ERROR: cannot find csrf token in server\'s response. See log.txt for raw text')
            write_response_to_log(firstresponse.text)

        termin_data = {
            'CASETYPES[%s]' % termin_type: 1,
            'step': 'WEB_APPOINT_SEARCH_BY_CASETYPES',
            '__ncforminfo': csrf,
        }
        
        response = s.post(buro.get_frame_url(), termin_data)
        txt = response.text

        try:
            json_str = re.search('jsonAppoints = \'(.*?)\'', txt).group(1)
        except AttributeError:
            print('ERROR: cannot find termins data in server\'s response.')

        appointments = json.loads(json_str)
        ##################################

        if appointments:
            # booking
            ##################################
            if booked_none:
                for k, v in appointments.items():
                    caption = v['caption']
                    first_date = None
                    for date in v['appoints']:
                        if v['appoints'][date] and date == '2019-08-06':
                            print("Booking at %s" % date)
                            slot_data = {
                                'step': 'WEB_APPOINT_NEW_APPOINT',
                                'APPOINT': 'Termin+Wartezone+SCIF___%s___%s' % (date,v['appoints'][date][0]),
                            }
                            response_slot = s.post(buro.get_frame_url(), slot_data)
                            try:
                                csrfslot = re.search('name="__ncforminfo" value="(.+?)"/>', response_slot.text).group(1)
                            except AttributeError:
                                print('ERROR: cannot find csrf token in server\'s response.')

                            # last step
                            book_data = {
                                'step': 'WEB_APPOINT_SAVE_APPOINT',
                                'CONTACT[salutation]': 'Frau',
                                'CONTACT[name]': 'XXX',
                                'CONTACT[email]': 'XXX@gmail.com',
                                'CONTACT[privacy]': 1,
                                '__ncforminfo': csrfslot,
                            }

                            bookresponse = s.post(buro.get_frame_url(), book_data)

                            booked_boturl = 'https://api.telegram.org/botXXX:XXX/sendMessage'
                            booked_payload = {'chat_id': '-1001488103538', 'text': 'Booked %s %s' % (date,v['appoints'][date][0])}
                            requests.post(booked_boturl, data=booked_payload)
                            booked_none = False
            ##################################

            # posting to Telegram
            ##################################
            found_any = False

            for k, v in appointments.items():
                caption = v['caption']
                first_date = None
                for date in v['appoints']:
                    if v['appoints'][date]:
                        first_date = date
                        found_any = True
                        break
                if first_date:
                    print('The nearest appointments at %s are at %s:\n%s' % (caption, first_date, '\n'.join(v['appoints'][first_date])))
                    print("Full dump:")
                    print(json.dumps(appointments, sort_keys=True, indent=4, separators=(',', ': ')))

                    boturl = 'https://api.telegram.org/botXXX:XXX/sendMessage'
                    payload = {'chat_id': '-1001488103538', 'text': 'GO! https://www46.muenchen.de/termin/index.php?cts=1080627 \n Found nearest appointments at %s:\n%s' % (first_date,'\n'.join(v['appoints'][first_date]))}
                    requests.post(boturl, data=payload)
            if not found_any:
                print('Unfortunately, everything is booked.')
            ##################################

        time.sleep(50) # Delay for 50 seconds.
