# creates dict of ISO language names matched with their language code
# and a dict of codes matched with names
language_file = open("language_data", "r")

name_to_code = {} # all lowercase
code_to_name = {} # languages names are capitalized
for line in language_file:
    if (len(line.split()) == 2):
        name_to_code[line.split()[0].lower()] = line.split()[1].lower()
        code_to_name[line.split()[1]] = line.split()[0]
    else:
        name_to_code[line.split()[0].lower() + " " + line.split()[1].lower()] = line.split()[2].lower()
        code_to_name[line.split()[2]] = line.split()[0] + " " + line.split()[1]