#!python3

from contextlib import contextmanager

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

    def get_query_params_obj(self):
        curr_coords = get_current_location()
        if curr_coords is None:
            print('Cannot get current location')

        # Get the station id of the closest station i.e. minimal distance between the current location and stations
        # in "STATIONS_DATA"
        closest_station_id = min(
            STATIONS_DATA,
            # Calculate the distance in meters between the current location and stations in "STATIONS_DATA"
            key=lambda station_id: geopy.distance.distance(curr_coords, STATIONS_DATA[station_id]['coordinates']).m)

        line_numbers = STATIONS_DATA[closest_station_id]['line_numbers']
        return dict(station_id=int(closest_station_id), line_numbers=line_numbers)

    def _make_eta_msg(self):
        msgs = []
        station_name = self.etas['station_name']
        station_city = self.etas['station_city']
        line1_padding = ' ' * 15
        line1_str = f'{line1_padding}{station_city} - {station_name}'
        msg_lines_padding = ' ' * (len(line1_str) // 2)
        line_number_2_etas = self.etas['line_number_2_etas']
        for line_number, etas in sorted(line_number_2_etas.items(), key=lambda item: item[0]):
            etas_str = ', '.join([str(eta) for eta in line_number_2_etas[line_number]])
            msg = f'{msg_lines_padding}🚌 {line_number}: {etas_str}'
            msgs.append(msg)

        if not msgs:
            return f'{NO_ETA_MESSAGE}'

        msgs_str = '\n'.join(msgs)
        return f'{line1_str}\n{msgs_str}'

    def send_notification(self):
        """
        Present ETAs in Pythonista's today widget
        """

        # FOO here we can blink an indicator exactly same internal as service query interval
        msg = self._make_eta_msg()

        # Configure the iOS today widget to present the text in dynamic view i.e. the size of the widget will be
        # dynamic and can be expanded when text can't feed the default widget size
        frame_size = (0, 0, 500, 500)  # x, y, width, height
        v = ui.View(frame=frame_size)
        label = ui.Label(frame=frame_size, flex='WHTB', alignment=ui.ALIGN_LEFT)
        label.font = ('Menlo', 15)
        label.number_of_lines = 0  # 0 means number of line is dynamic
        label.text = msg
        v.add_subview(label)
        appex.set_widget_view(v)


if __name__ == '__main__':
    my_notifier = MyEtaNotifier()
    my_notifier.run(DATA_REFRESH_INTERVAL)
