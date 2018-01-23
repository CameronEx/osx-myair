import configparser
import os
import rumps
import requests

class MyAirTaskbar(rumps.App):

    def __init__(self):
        # Setup the config parser
        config = configparser.ConfigParser()
        config_dir = os.path.expandpath("~/.config/osx-myair/")
        config_file = config_dir + "config.ini"

        # Ensure the config directory and file exists, if not, create defaults
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if not config.read(config_dir + config_file):
            self.config['DEFAULT'] = { "pollInterval": "30",
                                "server": "",
                                "port": 2025}
            with open(config_file, "w") as new_file:
                self.config.write(new_file)

        # Read the config file and set state
        self.poll_int = config['DEFAULT']['pollInterval']
        self.server = self.config['DEFAULT']['server']
        self.port = self.config['DEFAULT']['port']

        self.current_state = {}
        self.base_target = "http://{server}:{port}/".format(**self)

        # Get the current state of the air conditioner
        get_state()

    class ResponseError(Exception):
        pass

    @rumps.timer(self.poll_int)
    def get_state(self):
        """
        Attempts to gather data from the AdvantageAir API.
        rumps decorator runs this every X seconds (as defined in config.ini)
        """

        if not self.server:
            rumps.alert(title="Configuration Error", message="No host is configured.\nError 01")
        target = self.base_target + "getSystemData"
        self.current_state = send_command(target)

    def send_command(self, target):
        """
        Sends command to API. Handles responses.
        """
        try:
            response = requests.get(target)
            if response.status_code == 200:
                return response.json()
            else:
                raise ResponseError
        except ConnectionError as error:
            # FIXME This will be super annoying, change it to logging
            # rumps.alert(title="Connection Error!", message="Unable to connect to host.\nError 02")
            return None
        except ResponseError:
            # FIXME Log the issue
            return None

    @rumps.clicked("On/Off")
    def onoff(self, sender):
        """
        Turns aircon on or off. Checks state first.
        """
        if self.current_state["ac1"]["info"]["state"] == on:
            target = self.base_target + 'setAircon?json={"ac1":{"info":{"state":"off"}}}'
        else:
            target = self.base_target + 'setAircon?json={"ac1":{"info":{"state":"on"}}}'

        send_command(target)
        # FIXME If successful, pop a notification
        rumps.notification(title="MyAir", message="AC1 turned on successfully")

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(title="About OS X MyAir",
                    message="OS X MyAir Taskbar Application\n"
                    "Maintained at https://github.com/CameronEx/osx-myair"
                    "Not affiliated with Advantage Air.")


if __name__ == "__main__":
    MyAirTaskbar("MyAir").run()
