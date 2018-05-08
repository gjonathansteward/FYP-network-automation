from mysql import connector

#This is all from phase one for proof of concept

def get_data(query):
    DBconnection = connector.connect(user ="root", password="test", host="127.0.0.1", database="FYP Data")
    DBcursor = DBconnection.cursor()
    DBcursor.execute(query)
    database_return = DBcursor
    result = []
    for line in database_return:
        result.append(line)
    return result


def main():
    linebreak = "-" * 70

    DBconnection = connector.connect(user ="root", password="test", host="127.0.0.1", database="FYP Data")

    DBcursor = DBconnection.cursor()
    add_command =("SELECT dh.name, bt.`First line`, bt.City, bt.Postcode , bt.Country\n"
        "from `FYP Data`.`Data hall Table` dh INNER JOIN `FYP Data`.`Building Table` bt\n"
        "on dh.BuildingID = bt.BuildingID;")
    DBcursor.execute(add_command)

    database_return = DBcursor

    print"\nDatahall | Address\n{}".format(linebreak)
    for line in database_return:
        print line


if __name__ == "__main__":
    main()