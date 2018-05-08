import getpass
from common_tasks import set_data_mysql


class Device_object(object):
    """
    Author - Jonathan Steward
    Function - Device object that contains all the relevant information needed to poll/configure
    """
    def __init__(self, ip, username, password, enablePassword, vendor):
        """
        Author - Jonathan Steward
        Function -sets up device object
        Inputs - 
            ip - string
            username - string
            password - string
            vendor - string
        returns - n/a
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.enablePassword = enablePassword
        self.vendor = vendor
        self.configured = False


class ToolLog(object):
    """
    Author - Jonathan Steward
    Function - 
        Object to log all the details about a tool exectuion to allow for easy logging
        Currently doesn't store much information other than success or fail
    """
    def __init__(self, tool, variables):
        """
        Author - Jonathan Steward
        Function - Setup the tool log object takes in the name and the variables used
        Inputs - 
            tool - String
            variables - String
        """
        self.tool = tool
        self.variables = variables
        self.user = getpass.getuser()

    def set_tool_log(self, success=False, variables=""):
        """
        Author - Jonathan Steward
        Function - Take the details of the tools exectuion and sends it to the database
        Inputs - Success - Bool
        """
        if variables:
            self.variables = variables
        self.success = success
        command = """
        INSERT INTO `FYP Data`.`tool_log` (`tool`, `user`, `success`, `vars`)
         VALUES ("{}", "{}", "{}", "{}");
        """.format(self.tool, self.user, self.success, self.variables)
        print "logging the tool usage!"
        set_data_mysql(command)
