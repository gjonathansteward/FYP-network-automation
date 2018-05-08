from mysql import connector

#Used for phase one implementation

DBconnection = connector.connect(user ="root", password="test", host="127.0.0.1", database="FYP Data")

DBcursor = DBconnection.cursor()
add_command =("INSERT INTO `FYP Data`.`syslog event` (`syslog detail`) VALUES ('{}');").format("line")
DBcursor.execute(add_command)
DBconnection.commit()
print "added"

