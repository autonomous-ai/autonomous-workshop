from cybercab_lib import body, print_part, Rot
PRINTABLE = True
def gen_step():
    return print_part(Rot(0,90,0)*body())
