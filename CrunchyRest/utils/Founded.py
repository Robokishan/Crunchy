from datetime import datetime
import argparse


class FoundedToDate:

    def getDateFromFounded(self, founded):
        '''
        format 1: Nov30,2016
        format 2: 2018
        format 3: Aug2015
        format 4: Jan1,2015
        '''
        if founded is None:
            return None
        founded = founded.strip()
        if founded == "":
            return None
        try:
            if founded.isdigit():
                return datetime.strptime(founded, "%Y")
            if founded[0].isdigit():
                if len(founded) == 4:
                    return datetime.strptime(founded, "%Y")
                else:
                    return datetime.strptime(founded, "%b%d,%Y")
            else:
                if len(founded) == 8:
                    return datetime.strptime(founded, "%b%Y")
                elif ',' in founded:
                    return datetime.strptime(founded, "%b%d,%Y")
                else:
                    return datetime.strptime(founded, "%b%Y")
        except ValueError:
            return None


if __name__ == "__main__":
    import os
    import csv

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--filename', type=str,
                        help='The name of the file to process', required=True)
    args = parser.parse_args()

    founded = FoundedToDate()
    if not args.filename.lower().endswith('.csv'):
        raise "The file is not a CSV file"
    else:
        if not os.path.exists(args.filename):
            raise "The file does not exist."
        else:
            try:
                with open(args.filename, newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    if 'founded' not in reader.fieldnames:
                        raise Exception(
                            "The 'founded' column does not exist in the CSV file.")
                    for row in reader:
                        founded_value = row['founded']
                        date = founded.getDateFromFounded(founded_value)
                        if date is None:
                            print(
                                f"Founded: {founded_value}, Date: {date}")
            except Exception as e:
                raise f"An error occurred while reading the file: {e}"
