import sys
import logging
import argparse

####### I N I T #####################
# the BTB will be a dictionary with index determined from last 3 words of PC
# i.e. 400>1c4< -> 1*16^2 + 12+16 + 4 = 452 >> 2 (right-shift by 2 OR divide by 4)
#     ..>0001 1100 01<00
btb = dict()
cpc_tpc_pred_busy = dict()

logging.basicConfig(filename='cpts561_out.log', filemode='w', level=logging.DEBUG)

parser = argparse.ArgumentParser()
parser.add_argument("--codefile", help="provide the file path to file containing opcodes")
args = parser.parse_args()

####### F U N C T I O N S #####################
def get_entry_BTB(code):
    ''' assume input as hex'''
    total = 0
    last_three = code[3:6]
    # reverse them so math is easier
    last_three = "".join(reversed(last_three))
    for i in range(0, len(last_three)):
        total = total + int(last_three[i], 16) * (16**i)
        logging.debug("i {} -hex {} -dec {} -total {}".format(i, last_three[i], int(last_three[i], 16), total))
    
    # divide by 4
    entry = total >> 2
    logging.info("entry number for BTB: {}".format(entry))
    return entry

def make_BTB(entry, pc, tpc):
    btb[entry] = [pc, tpc]

def print_BTB():
    for entry in btb:
        print("{} --- PC {} - targetPC {}".format(entry, btb[entry][0], btb[entry][1]))

####### M A I N #####################
with open(args.codefile, "r") as f:
    code = f.readlines()

# strip out \n newline characters
code = [x.strip() for x in code]

for i in range(0, len(code)-2):
    icode_plus1 = int(code[i+1], 16)
    icode = int(code[i], 16)
    if icode_plus1 - icode == 4:
        # NOT a Branch
        continue
    else:
        logging.warning("FOUND a Branch for PC:{}".format(code[i]))
        entry = get_entry_BTB(code[i])
        # we know the Target PC is the next instruction hence i+1 or icode_plus1
        make_BTB(entry, pc=icode, tpc=icode_plus1)
    
print_BTB()
