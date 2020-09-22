#!python3
#
# Written by denpy in 2020.
# https://github.com/denpy
#
import logging
import time
from contextlib import contextmanager
from itertools import cycle
from timeit import default_timer

# Pythonista internal modules
# noinspection PyUnresolvedReferences
import appex
import geopy.distance
# noinspection PyUnresolvedReferences
import location
# noinspection PyUnresolvedReferences
import ui

# TODO: This should be changed to "config" when all is ready
from bus_eta_pythonista_widget.my_config import DATA_REFRESH_INTERVAL, NO_ETA_MESSAGE, STATIONS_DATA, STATUS_LABELS
from bus_notify.bus_arrivals_notifier import BusArrivalsNotifier

# Set level for urllib3 logger so we will not see any messages on widget, otherwise its logs will appear on the widget
# background
logging.getLogger("urllib3").setLevel(logging.ERROR)


def get_current_location():
    """
    Retrieves the current location latitude and longitude from the iOS
    :return: latitude and longitude
    :rtype: tuple[float, float]
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

        return curr_loc['latitude'], curr_loc['longitude']


class DummyLogger(object):
    """
    An object which does nothing, we pass it as logger so nothing will be printed to the widget, we don't want log
    messages in the widget
    """
    def __getattr__(self, name):
        return lambda *x: None


class MyArrivalsNotifier(BusArrivalsNotifier):

    def __init__(self):
        dl = DummyLogger()
        super(MyArrivalsNotifier, self).__init__(dl)
        self.station_id = None

    def _get_station_info(self, station_id: int):
        start = default_timer()
        res_json = super(MyArrivalsNotifier, self)._get_station_info(self.station_id)
        self.get_station_data_elapsed = round(default_timer() - start)
        return res_json

    def get_query_params_obj(self):
        curr_coords = get_current_location()
        if curr_coords is None:
            self.logger.error('Cannot get current location')

        # Get the station id of the closest station i.e. minimal distance between the current location and stations
        # in "STATIONS_DATA"
        closest_station_id = min(
            STATIONS_DATA,
            # Calculate the distance in meters between the current location and stations in "STATIONS_DATA"
            key=lambda station_id: geopy.distance.distance(curr_coords, STATIONS_DATA[station_id]['coordinates']).m)
        self.station_id = closest_station_id
        line_numbers = STATIONS_DATA[closest_station_id]['line_numbers']
        return dict(station_id=int(closest_station_id), line_numbers=line_numbers)

    def _make_eta_msg(self, status_label):
        msgs = []

        # Bus station details
        station_city = self.arrivals['station_city']
        station_label = STATIONS_DATA[self.station_id].get('label')
        station_name = self.arrivals['station_name'] if station_label is None else station_label
        station_details_str = f'{station_city} - {station_name} {status_label}'.center(42, ' ')

        # ETAs text
        line_number_2_etas = self.arrivals['line_num_2_mins_remained']
        for line_number, etas in sorted(line_number_2_etas.items(), key=lambda item: item[0]):  # sort by line number
            etas_str = ', '.join([str(eta) if eta > 0 else 'Now' for eta in line_number_2_etas[line_number]])
            msg = f'🚌 {line_number}: {etas_str}'

            # TODO: Currently the alignment will work with iPhone X and later. Make it work with any iPhone model
            #  with no relation to the screen size
            # Align text, so it will appear in the middle of of the widget
            msg = f'{msg: <25}'.center(60, ' ')
            msgs.append(msg)

        if not msgs:
            msgs = [f'{NO_ETA_MESSAGE: <25}'.center(60, ' ')]

        msgs_str = '\n'.join(msgs)
        return f'{station_details_str}\n{msgs_str}'

    def send_notification(self):
        """
        Present bus arrivals in Pythonista's today widget
        """
        # Configure the iOS today widget to present the text in dynamic view i.e. the size of the widget will be
        # dynamic and can be expanded when text can't fit the default widget size
        frame_size = (0, 0, 500, 500)  # x, y, width, height
        v = ui.View(frame=frame_size)
        label = ui.Label(frame=frame_size, flex='WHTB', alignment=ui.ALIGN_LEFT)
        label.font = ('Menlo', 15)
        label.number_of_lines = 0  # 0 means number of line is dynamic

        # We keep refresh the widget every one second to show that script is not stuck and running, since we refresh
        # every one second the number of refreshes will as a number of seconds we need to wait between Curlbus
        # data requests
        widget_refresh_count = DATA_REFRESH_INTERVAL - self.get_station_data_elapsed
        for status_label in cycle(STATUS_LABELS):
            widget_refresh_count -= 1
            should_request_etas = widget_refresh_count == 0

            # When it's time to query Curlbus again we change the status label so it will show that data query is
            # performed
            if should_request_etas is True:
                status_label = '🔄'
            msg = self._make_eta_msg(status_label)
            label.text = msg
            v.add_subview(label)
            appex.set_widget_view(v)

            # Check if we need to exit the loop for requesting new data from Curlbus
            if should_request_etas is True:
                return
            time.sleep(1)


if __name__ == '__main__':
    my_notifier = MyArrivalsNotifier()
    my_notifier.run(DATA_REFRESH_INTERVAL)
