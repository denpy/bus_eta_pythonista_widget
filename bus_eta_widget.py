#!python3
#
# Written by denpy in 2020.
# https://github.com/denpy
#
from contextlib import contextmanager
from timeit import default_timer
import time
from itertools import cycle

# noinspection PyUnresolvedReferences
import appex  # Pythonista internal module
import geopy.distance
# noinspection PyUnresolvedReferences
import location  # Pythonista internal module
# noinspection PyUnresolvedReferences
import ui  # Pythonista internal module

# TODO: This should be changed to "config" when all is ready
from bus_eta_pythonista_widget.my_config import DATA_REFRESH_INTERVAL, NO_ETA_MESSAGE, STATIONS_DATA
from bus_notify.bus_eta_notifier import BusEtaNotifier


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


class MyEtaNotifier(BusEtaNotifier):

    def __init__(self):
        super(MyEtaNotifier, self).__init__()
        self.station_id = None

    def _get_station_data(self, station_id: int):
        start = default_timer()
        res_json = super(MyEtaNotifier, self)._get_station_data(self.station_id)
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
        station_name = self.etas['station_name']
        station_city = self.etas['station_city']

        # Pad messages with spaces so they will appear aligned in the middle of the widget
        widget_line_spaces = 45  # This number should work for iPhone
        station_label = STATIONS_DATA[self.station_id].get('label', '🚏')
        station_details_str = f'{station_city} - {station_name} {station_label} {status_label}'
        line1_str_len = len(station_details_str)
        line1_padding = (widget_line_spaces - line1_str_len) // 2 * ' '
        line1_str_padded = f'{line1_padding}{station_details_str}'

        # Pad lines with bus numbers and ETAs, we try to make line to be aligned in the middle of the widget for
        # esthetic purposes
        # This will make line to be in the middle of the widget
        eta_lines_padding = (line1_str_len // 2 + (len(line1_padding) - 5)) * ' '
        line_number_2_etas = self.etas['line_number_2_etas']
        for line_number, etas in sorted(line_number_2_etas.items(), key=lambda item: item[0]):  # sort by line number
            etas_str = ', '.join([str(eta) for eta in line_number_2_etas[line_number]])
            msg = f'{eta_lines_padding}🚌 {line_number}: {etas_str}'
            msgs.append(msg)

        if not msgs:
            return f'{NO_ETA_MESSAGE}'

        msgs_str = '\n'.join(msgs)
        return f'{line1_str_padded}\n{msgs_str}'

    def send_notification(self):
        """
        Present ETAs in Pythonista's today widget
        """
        # Configure the iOS today widget to present the text in dynamic view i.e. the size of the widget will be
        # dynamic and can be expanded when text can't fit the default widget size
        frame_size = (0, 0, 500, 500)  # x, y, width, height
        v = ui.View(frame=frame_size)
        label = ui.Label(frame=frame_size, flex='WHTB', alignment=ui.ALIGN_LEFT)
        label.font = ('Menlo', 15)
        label.number_of_lines = 0  # 0 means number of line is dynamic

        # We keep refresh the widget every one second to show that script is not stuck and running, since we refresh
        # every one second the number of refreshes will as a number of seconds we need to wait between Curlbus queries
        secs_until_widget_refresh = DATA_REFRESH_INTERVAL - self.get_station_data_elapsed
        for status_label in cycle(('⬆️', '⬇️')):
            secs_until_widget_refresh -= 1
            should_refresh = secs_until_widget_refresh == 0
            if should_refresh is True:
                status_label = '🔄'
            msg = self._make_eta_msg(status_label)
            label.text = msg
            v.add_subview(label)
            appex.set_widget_view(v)
            if should_refresh is True:
                break
            time.sleep(1)


if __name__ == '__main__':
    my_notifier = MyEtaNotifier()
    my_notifier.run(DATA_REFRESH_INTERVAL)
