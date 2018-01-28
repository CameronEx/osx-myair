import configparser
import logging
import os
import rumps
import requests


class MyAirTaskbar(rumps.App):

    def __init__(self):
        logger.debug("Initialising. Calling super.")
        super().__init__("MyAir")

        # Setup the config parser
        logger.debug("Setting up the config parser.")
        config = configparser.ConfigParser()
        config_dir = os.path.expanduser("~/.config/osx-myair/")
        config_file = config_dir + "config.ini"

        # Ensure the config directory and file exists, if not, create defaults
        logger.debug("Checking if the configuration directory exists.")
        if not os.path.exists(config_dir):
            logger.info("Configuration directory Does not exist. Creating it.")
            os.makedirs(config_dir)
        else:
            logger.debug("Configuration directory exists.")

        logger.debug("Checking if the configuration file exists.")
        if not config.read(config_file):
            logger.info("Configuration file did not exist, creating one with defaults.")
            default_config = { "server": "",
                               "port": 2025}
            logger.debug("Default config is: {}".format(default_config))
            config['DEFAULT'] = default_config
            with open(config_file, "w") as new_file:
                logger.debug("Saving configuration file to {}.".format(config_file))
                config.write(new_file)
        else:
            logger.debug("It does.")

        # Read the config file and set state
        # FIXME: Handle the event of missing configuration
        logger.info("Loading configuration.")
        self.server = config["DEFAULT"]["server"]
        logger.debug("Server IP: {}".format(self.server))
        self.port = config["DEFAULT"]["port"]
        logger.debug("API port: {}".format(self.port))

        self.current_state = {}
        self.base_target = "http://{}:{}/".format(self.server, self.port)
        logger.debug("Built base URL: {}".format(self.base_target))

        # Get the current state of the air conditioner
        logger.info("Getting initial state.")
        self.get_state()

    class ResponseError(Exception):
        pass

    @rumps.timer(30)
    def get_state(self):
        """
        Attempts to gather data from the AdvantageAir API.
        rumps decorator runs this every X seconds (as defined in config.ini)
        """

        if not self.server:
            logger.error("No server has been defined.")
            rumps.alert(title="Configuration Error", message="No host is configured.\nError 01")

        target = self.base_target + "getSystemData"
        logger.debug("Built target URL {}".format(target))
        self.current_state = self.send_command(target)

    @staticmethod
    def send_command(target):
        """
        Sends command to API. Handles responses.
        """

        logger.debug("Attempting to send command: {}".format(target))
        try:
            response = requests.get(target)
            if response.status_code == 200:
                logger.debug("Expected response received.\n Returning data:\n {}".format(response.json()))
                return response.json()
            else:
                logger.error("Unexpected response received.")
                raise ResponseError
        except ConnectionError as error:
            logging.error("Unable to connect to host.")
            return None
        except ResponseError:
            # FIXME: I don't work.
            logger.error("Status code was: {}".format(response.status_code))
            logger.debug("Body of response was:\n{}".format(response.text))
            return None

    @rumps.clicked("On/Off")
    def onoff(self, sender):
        """
        Turns aircon on or off. Checks state first.
        """
        logger.debug("Attempting to toggle AC state.")
        if self.current_state["ac1"]["info"]["state"] == "on":
            logger.debug("Last know state of AC was on.")
            logger.info("Turning AC off.")
            target = self.base_target + 'setAircon?json={"ac1":{"info":{"state":"off"}}}'
        else:
            logger.debug("Last know state of AC was off.")
            logger.info("Turning AC on.")
            target = self.base_target + 'setAircon?json={"ac1":{"info":{"state":"on"}}}'

        logger.debug("Built target URL {}".format(target))
        if self.send_command(target):
            self.get_state()
            if self.current_state["ac1"]["info"]["state"] == "on":
                rumps.notification(title="MyAir", message="AC turned on successfully")
            else:
                rumps.notification(title="MyAir", message="AC turned off successfully")

    @rumps.clicked("About")
    def about(self, _):
        rumps.alert(title="About OS X MyAir",
                    message="OS X MyAir Taskbar Application\n"
                    "Maintained at https://github.com/CameronEx/osx-myair"
                    "Not affiliated with Advantage Air.")


# Configure the logger
# FIXME: Log to file, for when program is compiled to .app
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

if __name__ == "__main__":
    MyAirTaskbar().run()
