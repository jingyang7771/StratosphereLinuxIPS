# Ths is a template module for you to copy and create your own slips module
# Instructions
# 1. Create a new folder on ./modules with the name of your template. Example:
#    mkdir modules/anomaly_detector
# 2. Copy this template file in that folder.
#    cp modules/template/template.py modules/anomaly_detector/anomaly_detector.py
# 3. Make it a module
#    touch modules/template/__init__.py
# 4. Change the name of the module, description and author in the variables
# 5. The file name of the python module (template.py) MUST be the same as the name of the folder (template)
# 6. The variable 'name' MUST have the public name of this module. This is used to ignore the module
# 7. The name of the class MUST be 'Module', do not change it.

# Must imports
from slips_files.common.abstracts import Module
import multiprocessing
from slips_files.core.database import __database__
import platform
import sys

# Your imports
import os
import shutil


class Module(Module, multiprocessing.Process):
    # Name: short name of the module. Do not use spaces
    name = 'blocking'
    description = 'Module to block IPs connecting to this device'
    authors = ['Sebastian Garcia']

    def __init__(self, outputqueue, config):
        multiprocessing.Process.__init__(self)
        # All the printing output should be sent to the outputqueue.
        # The outputqueue is connected to another process called OutputProcess
        self.outputqueue = outputqueue
        # In case you need to read the slips.conf configuration file for
        # your own configurations
        self.config = config
        # Start the DB
        __database__.start(self.config)
        # To which channels do you wnat to subscribe? When a message
        # arrives on the channel the module will wakeup
        # The options change, so the last list is on the
        # slips/core/database.py file. However common options are:
        # - new_ip
        # - tw_modified
        # - evidence_added
        self.c1 = __database__.subscribe('new_blocking')
        self.timeout = None

    def print(self, text, verbose=1, debug=0):
        """
        Function to use to print text using the outputqueue of slips.
        Slips then decides how, when and where to print this text by taking all the processes into account
        :param verbose:
            0 - don't print
            1 - basic operation/proof of work
            2 - log I/O operations and filenames
            3 - log database/profile/timewindow changes
        :param debug:
            0 - don't print
            1 - print exceptions
            2 - unsupported and unhandled types (cases that may cause errors)
            3 - red warnings that needs examination - developer warnings
        :param text: text to print. Can include format like 'Test {}'.format('here')
        """

        levels = f'{verbose}{debug}'
        self.outputqueue.put(f"{levels}|{self.name}|{text}")

    def determine_linux_firewall(self):
        """ Returns the currently installed firewall and installs one if none was found """
        if shutil.which('iptables'):
            return 'iptables'
        elif shutil.which('nftables'):
            return 'nftables'
        else:
            # If no firewall is found download and use iptables
            #TODO: maybe ask the user first?
            os.sys("sudo apt install iptables")
            return 'iptables'

    def initialize_chains_in_firewall(self):
        if self.platform_system == 'Linux':
            # Get the user's currently installed firewall
            self.firewall = self.determine_linux_firewall()
            if self.firewall == 'iptables':
                print('Executing "sudo iptables -N slipsBlocking"')
                # Add a new chain to iptables
                os.system('sudo iptables -N slipsBlocking')
                #TODO: determine which one to use OUTPUT INPUT or FORWARD

                # Redirect the traffic from all other chains to slipsBlocking so rules in any pre-existing chains dont override it
                # -I to insert slipsBlocking at the top of the INPUT, OUTPUT and FORWARD chains
                os.system('sudo iptables -I INPUT -j slipsBlocking')
                os.system('sudo iptables -I OUTPUT -j slipsBlocking')
                os.system('sudo iptables -I FORWARD -j slipsBlocking')

            elif self.firewall == 'nftables':
                print('Executing "sudo nft add table inet slipsBlocking"')
                # Add a new nft table that uses the inet family (ipv4,ipv6)
                os.system('sudo nft add table inet slipsBlocking')
                #TODO: HANDLE NFT TABLE

        elif self.platform_system == 'Darwin':
            self.print('Mac OS blocking is not supported yet.')

    def handle_stop_process_message(self, message):
        pass

    def block_ip(self,message):
       pass

    def run(self):
        #TODO: handle MacOS
        self.initialize_chains_in_firewall()
        try:
            # Main loop function
            while True:
                message = self.c1.get_message(timeout=self.timeout)
                # Check that the message is for you. Probably unnecessary...
                if message['data'] == 'stop_process':
                    self.handle_stop_process_message(message)
                    # Confirm that the module is done processing
                    __database__.publish('finished_modules', self.name)

                    return True

                if message['channel'] == 'new_blocking':
                   self.block_ip(message)

        except KeyboardInterrupt:
            return True
        except Exception as inst:
            exception_line = sys.exc_info()[2].tb_lineno
            self.print(f'Problem on the run() line {exception_line}', 0, 1)
            self.print(str(type(inst)), 0, 1)
            self.print(str(inst.args), 0, 1)
            self.print(str(inst), 0, 1)
            return True
