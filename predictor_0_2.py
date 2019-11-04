import sys
import logging
import argparse

####### I N I T #####################
# the BTB will be a dictionary with index determined from last 3 words of PC
# i.e. 400>1c4< -> 1*16^2 + 12+16 + 4 = 452 >> 2 (right-shift by 2 OR divide by 4)
#     ..>0001 1100 01<00
btb = dict()
TAKEN = 1
NOT_TAKEN = 0

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
        logging.debug("i {} -hex {} -dec {} -total {}".format(i, 
                                                        last_three[i], 
                                                        int(last_three[i], 16), total))
    
    # divide by 4
    entry = total >> 2
    logging.info("entry number for BTB: {}".format(entry))
    return entry

def update_BTB(entry, pc, tpc, local_pred):
    # mod so we only have 1024 entries
    btb[entry % 1024] = [pc, tpc, local_pred]

def print_BTB():
    for entry in btb:
        print("{} --- PC {} - targetPC {} - local_pred {}".format(entry, 
                                                    btb[entry][0], 
                                                    btb[entry][1],
                                                    btb[entry][2]))

def in_BTB(entry, pc):
    if entry in btb:
        logging.debug("entry in BTB!")
        if pc == btb[entry][0]:
            logging.debug("PC found in BTB!")
            logging.debug("BTB entry {} --- PC {} - targetPC {} - local_pred {}".
                                                    format(entry, 
                                                    btb[entry][0], 
                                                    btb[entry][1],
                                                    btb[entry][2]))
            return True
        else:
            logging.debug("PC {} not in BTB, compared to {}".format(
                                                            pc,
                                                            btb[entry][0]))
            return False
    else:
        logging.debug("PC {} not in BTB".format(pc))
        return False

def update_pred(prev_pred, t_nt):
    # implement 2-bit prdictor state-machine
    # input1: previous prediction (in [x,x] format)
    # input2: current branch TAKEN(=1) or NOT_TAKEN(=0)

    # if previous Strong Taken and actual branch TAKEN
    if (((prev_pred[0] == TAKEN) and (prev_pred[1] == TAKEN))
         and (t_nt == TAKEN)):
        # stay in Strong Taken
        new_pred = [1,1]
    # if previous Strong Taken and actual branch NOT_TAKEN
    elif (((prev_pred[0] == TAKEN) and (prev_pred[1] == TAKEN))
         and (t_nt == NOT_TAKEN)):
        # transition to Weak Taken
        new_pred = [1,0]
    # if previous Weak Taken and actual branch TAKEN
    elif (((prev_pred[0] == TAKEN) and (prev_pred[1] == NOT_TAKEN))
         and (t_nt == TAKEN)):
        # transition to Strong Taken
        new_pred = [1,1]
    # if previous Weak Taken and actual branch NOT_TAKEN
    elif (((prev_pred[0] == TAKEN) and (prev_pred[1] == NOT_TAKEN))
         and (t_nt == NOT_TAKEN)):
        # transition to Strong Not Taken
        new_pred = [0,0]
    # if previous Strong Not Taken and actual branch NOT_TAKEN
    elif (((prev_pred[0] == NOT_TAKEN) and (prev_pred[1] == NOT_TAKEN))
         and (t_nt == NOT_TAKEN)):
        # stay in Strong Not Taken
        new_pred = [0,0]
    # if previous Strong Not Taken and actual branch TAKEN
    elif (((prev_pred[0] == NOT_TAKEN) and (prev_pred[1] == NOT_TAKEN))
         and (t_nt == TAKEN)):
        # transition to Weak Not Taken
        new_pred = [0,1]
    # if previous Weak Not Taken and actual branch TAKEN
    elif (((prev_pred[0] == NOT_TAKEN) and (prev_pred[1] == TAKEN))
         and (t_nt == TAKEN)):
        # transition to Strong Taken
        new_pred = [1,1]
    # if previous Weak Not Taken and actual branch NOT_TAKEN
    elif (((prev_pred[0] == NOT_TAKEN) and (prev_pred[1] == TAKEN))
         and (t_nt == NOT_TAKEN)):
        # transition to Strong Not Taken
        new_pred = [0,0]
    
    return new_pred

####### M A I N #####################
with open(args.codefile, "r") as f:
    code = f.readlines()

# strip out \n newline characters
code = [x.strip() for x in code]

for i in range(0, len(code)-2):
    hex_pc_plus1 = code[i+1]
    pc_plus1 = int(code[i+1], 16)
    hex_pc = code[i]
    pc = int(code[i], 16)
    # compute the entry number in BTB
    entry = get_entry_BTB(hex_pc)

    if pc_plus1 - pc == 4:
        # NOT a Branch but if pc in BTB we have NOT TAKEN it
        if in_BTB(entry, hex_pc) == True:
            pred = update_pred(prev_pred=btb[entry][2], t_nt=NOT_TAKEN)
            update_BTB(entry, pc=hex_pc, tpc=hex_pc_plus1, local_pred=pred)
    else:
        # FOUND a Branch hence TAKEN
        logging.warning("FOUND a Branch for PC:{}".format(code[i]))
        
        # see if PC exists in current BTB
        if in_BTB(entry, hex_pc) == True:
            # TODO?: add functionality to see if the target PC is same as in BTB
            # if not then update BTB target address to the new
            # THIS IS ALREADY BEING DONE as we update target PC every iteration

            # update prediction according to state machine
            pred = update_pred(prev_pred=btb[entry][2], t_nt=TAKEN)
            # we know the Target PC is the next instruction hence code[i+1]
            update_BTB(entry, pc=hex_pc, tpc=hex_pc_plus1, local_pred=pred)
        else:
            # by default we'll assume Strong Taken
            update_BTB(entry, pc=hex_pc, tpc=hex_pc_plus1, local_pred=[1,1])
        

# printing final state of BTB
print_BTB()