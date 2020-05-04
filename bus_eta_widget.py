#!python3

import os
import time
from textwrap import dedent
from contextlib import contextmanager

# noinspection PyUnresolvedReferences
import appex  # Pythonista module
# noinspection PyUnresolvedReferences
import location  # Pythonista module
# noinspection PyUnresolvedReferences
import ui  # Pythonista module

from bus_notify.bus_eta_notifier import BusEtaNotifier

# TODO: This should be changed to "config" when all is ready
from .my_config import (
    BUS_LINE_NUMBERS, DATA_REFRESH_INTERVAL, HOME_BUS_STOP_ID, HOME_COORDINATES, WORK_BUS_STOP_ID, WORK_COORDINATES,
    ETA_MESSAGE, NO_ETA_MESSAGE, NOTHING_TO_DO_MESSAGE)

# URLs
BASE_URL = 'http://curlbus.app/'
URL_TO_HOME = os.path.join(BASE_URL, WORK_BUS_STOP_ID)
URL_TO_WORK = os.path.join(BASE_URL, HOME_BUS_STOP_ID)


def get_location_city(coordinates):
    """
    FOO
    :param coordinates:
    :return:
    """
    # noinspection PyBroadException
    try:
        return location.reverse_geocode(coordinates)[0]['SubLocality']
    except Exception:
        return


def get_current_location():
    """
    FOO
    :return:
    """

    @contextmanager
    def location_updates():
        # Start getting location data from iOS
        location.start_updates()
        try:
            yield location.get_location()
        finally:
            # Stop getting location data from iOS
            location.stop_updates()

    with location_updates() as curr_loc:
        if curr_loc is None:
            return

        return get_location_city(dict(latitude=curr_loc['latitude'], longitude=curr_loc['longitude']))


@contextmanager
def widget_label():
    # Create a label which will be presented as text box in the NC widget
    label = ui.Label(font=('Menlo', 15), alignment=ui.ALIGN_CENTER)
    label.number_of_lines = 0  # Make widget adjust the size to the number of lines
    yield label


class MyEtaNotifier(BusEtaNotifier):

    def __init__(self):
        super(BusEtaNotifier, self).__init__()

    def get_service_query_obj(self):
        # FOO how do I understand what ORIGIN is???
        return dict(station_id=ORIGIN, line_numbers=BUS_LINE_NUMBERS)

    def send_notification(self):
        msg = NO_ETA_MESSAGE
        if self.etas:
            msg = ETA_MESSAGE.format(
                current_location=get_current_location(), station_name=self.etas['station_name'], etas_str=self.etas)

        # FOO here we can bink an indicator exactly same internal as service query interval
        for x in range(self.service_query_interval + 1):
            # Refresh the widget every 1 second between service queries
            with widget_label() as label:
                label.text = dedent(f'Updated {x} sec ago\n{msg}')  # Maximum 7 lines
                appex.set_widget_view(label)
            time.sleep(1)


if __name__ == '__main__':
    ORIGIN = None
    MESSAGE = None
    HOME_LOCATION_CITY = get_location_city(HOME_COORDINATES)
    WORK_LOCATION_CITY = get_location_city(WORK_COORDINATES)

    my_notifier = MyEtaNotifier()
    my_notifier.run(service_query_interval=10)
