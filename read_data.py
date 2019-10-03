"""
Yuchen Li
u6013787@anu.edu.au


"""




def is_float(s):
    """
    :param input a string, if it can be return to float then return float, otherwise return itself:
    :return: float or string

    str -> float or str
    """
    try:
        float(s)
        return float(s)

    except ValueError:
        return s

def read_file_flat(f):

    """
    :param path: the path of file AlignmentParmVals.dat and expt.in
    :return: dictionary of AF and Expt. Put them together

    path -> dict
    """



    df = {}


    multi_string = False
    name = None

    for line in f:
        if line == "\n" or line == "":
            print(line)
            continue
        if "BeginSection" in line:
            continue
        if "EndSection" in line:
            continue
        if "__start_multi_string__" in line:
            multi_string = True
            name = line.split()[0]
            df[name] = ""
            continue
        if "__end_multi_string__" in line:
            multi_string = False
            continue
        if multi_string:
            df[name] += line
            continue

        words = line.replace("\t", " ").split()

        if len(words) == 1:
            continue

        name = words[0]
        value = is_float(" ".join(words[1:]))
        df[name] = value

    return df