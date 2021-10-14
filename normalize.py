import csv

def normalizeCsv(file):
    with open(file, 'r') as infile, open('out.csv', 'w', newline='') as outfile:
        data = csv.reader(infile)
        temp = []
        for row in data:
            tempRow = []
            for field in row:
                tempRow.append(field.strip())
            temp.append(tempRow)
        writer = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerows(temp)