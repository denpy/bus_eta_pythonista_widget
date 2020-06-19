#### iOS Pythonista today widget that shows bus ETA.

The main idea is to have a widget that shows you ETA of buses you interested in for selected bus stations near your
current location.
It may be useful if you used to get to work and back home on a bus, so when you at home the widget will present an
information for station you take bus from to work and opposite when you a work.
   
##### TO DO: Add screenshots here
##### TO DO: Make installation script?

This will only work with [Pythonista 3](http://omz-software.com/pythonista/).

**Caution: Pythonista 2 is not supported!**

In order to make it work, you need to use [stash](https://github.com/ywangd/stash) 

Please for follow the instructions on [stash page](https://github.com/ywangd/stash) to have a working pip in
 Pythonista 3. 

You will have to allow Pythonista to use you location always.
On your iPhone follow the next steps: 
1. Go to "Settings"
2. Search for "Pythonista" or scroll down until you find it.
3. Tap Pythonista icon
4. Tap on "Location"
5. Select "Always"

You also need coordinates of bus stations you going to get information about. Refer to [Get the coordinates of a
 place](https://support.google.com/maps/answer/18539) section instructions to the exact coordinates.
 
Coordinates and line numbers need to be set in config.py, for example:
```python
# Please, set the bus stations data
# - "STATIONS_DATA" keys are bus station IDs
# - "line_numbers" is a list of integers and it holds line numbers you interested in, empty list means ETA for all lines
# will be returned
# - "coordinates" is a tuple of bus station coordinates, it will be used for detecting your current location relative
# to those coordinates in order to present the information relevant to the closest bus station
# - "label" is a string that will be presented with the bus station name (optional or can be empty)
STATIONS_DATA = {
    '12345': dict(line_numbers=[1, 2, 3], coordinates=(123.456789, 123.456789), label='🏡'),
    '54321': dict(line_numbers=[4, 5, 6], coordinates=(98.7654321, 98.7654321), label='🏙')
}

# How often to get info about arrival times
DATA_REFRESH_INTERVAL = 10

# Default messages, can be any text you want
NO_ETA_MESSAGE = '🤷🏾‍♂️'

``` 

Note: there is an issue the latest Pythonista 3.3 version which is described [here](https://www.reddit.com/r
/Pythonista/comments/fcqpl6/today_widget_doesnt_work/) it can prevent you from setting a custom today widget script.
