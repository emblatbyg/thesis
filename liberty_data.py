from liberty.parser import parse_liberty
#spec = liberty.parser("liberty.parser", )
from pathlib import Path
import argparse
import numpy as np
import os,sys
import random
from datetime import datetime
import json
import re

path_to_libfile = sys.argv[1]
starttime = datetime.now()
path_to_calibration_file = sys.argv[2]
cells = ''
processed_library_path = "powerlib.txt"

#oneLogic_set = {"and2", "and3", "and4", "ao22", "ckand2", "cknand2", }

# input A1 or I (CP, E, S I0, I1, TE)
# output Z, Q, QN, ZN
input_set = {"A1", "I", "S", "I0", "TE", "CI", "CO", "A", "CDN", "D", "SDN"}
output_set = {"Z", "ZN", "Q", "QN", "ZN"}

def set_cells_and_environment(libfile):
    library = parse_liberty(open(libfile).read())
    #print("done parsing liberty after "+str((datetime.now()-starttime)/60)+" minutes")
    
    voltage_unit            = str(library.get("voltage_unit")        ).replace("\"", "")
    current_unit            = str(library.get("current_unit")        ).replace("\"", "")
    leakage_power_unit      = str(library.get("leakage_power_unit")  ).replace("\"", "")
    capacitive_load_unit    = str(library.get("capacitive_load_unit")).replace("\"", "")
    #what is unit of power in power templates?
    #also unit of leakage power
    
    cells = library.get_groups("cell")
    jsonstring = json.dumps([voltage_unit, current_unit, leakage_power_unit, capacitive_load_unit])
    fp = open(processed_library_path, "w")
    fp.write(jsonstring+"\n")
    for cell in cells:
        #print("Working")
        dynamic_current = cell.get_groups("dynamic_current")
        leakage_power   = cell.get_groups("leakage_power")
        pins            = cell.get_groups("pin")
        cellName = str(cell.args[0])
        occurences_in_calibration_file = count_occurence(cellName)
        leakagePower = str(leakage_power[-1].get("value"))
        #print("\tCell: "+str(cell.args))
        #print("\t\tleakage power value: "+str(leakagePower))
        footprint = cell.get("cell_footprint")

        #pinLists = []
        input_pins =[]
        output_pins = []
        for pin in pins:
            #pinList = []
            pinName = pin.args[0]
            direction = pin.get("direction")
            pinfuction = None
            intPwr_lists = []
            pin_cap = 0
            pwrPin = pin.get("related_power_pin")
            gndPin = pin.get("related_ground_pin")
            if (direction == "output"):
                pinfunction = pin.get("function")
            else:
                pin_cap = pin.get("capacitance")                
                #get internal power groups:
            internal_power_groups = pin.get_groups("internal_power")
            for intPwr in internal_power_groups:
                related_pin = intPwr.get("related_pin")
                when        = intPwr.get("when")
                risePwrGroup = intPwr.get_group("rise_power")
                fallPwrGroup = intPwr.get_group("fall_power")
                
                rise_arg = risePwrGroup.args[0]
                fall_arg = fallPwrGroup.args[0]

                if rise_arg != "scalar":
                    rise_i1 = risePwrGroup.get_array("index_1")
                    rise_values = risePwrGroup.get_array("values")
                if fall_arg != "scalar":
                    fall_i1     = fallPwrGroup.get_array("index_1")
                    fall_values = fallPwrGroup.get_array("values")
                fall_values_i = []
                rise_values_i = []
                fall_cap = []
                rise_cap = []
                powersum_list = []
                if direction == "output":
                    if fall_arg != "scalar":
                        fall_cap_np = fallPwrGroup.get_array("index_2")
                        fall_cap = fall_cap_np.tolist()[0]
                        for timeIndex in range(0, len(fall_i1[0])):
                            #print(fall_i1[0][timeIndex])
                            if str(fall_i1[0][timeIndex]) == "0.46":
                                fall_values_i = fall_values[timeIndex]
                                break
                        #for f in fall_values_i:
                        #    f = float(f)    
                        fall_values_i = fall_values_i.tolist()
                    if rise_arg != "scalar":
                        rise_cap_np = risePwrGroup.get_array("index_2")
                        rise_cap = rise_cap_np.tolist()[0]
                        for timeIndex in range(0, len(rise_i1[0])):
                            #print(rise_i1[0][timeIndex])
                            if str(rise_i1[0][timeIndex]) == "0.46":
                                rise_values_i = rise_values[timeIndex]
                                break
                        #for r in rise_values_i:
                        #    r = float(r)
                        rise_values_i = rise_values_i.tolist()
                    if rise_arg != 'scalar' and fall_arg != 'scalar':
                        powersum_list = sum_list(rise_values_i, fall_values_i)
                    elif rise_arg == 'scalar':
                        powersum_list = fall_values_i
                    elif fall_arg == 'scalar':
                        powersum_list = rise_values_i
                    else:
                        #both scalar
                        powersum_list = [float(0)]
                elif direction == "input":
                    if rise_arg != "scalar":
                        for timeIndex in range(0, len(rise_i1[0])):
                            #print(rise_i1[0][timeIndex])
                            if str(rise_i1[0][timeIndex]) == "0.46":
                                rise_values_i = rise_values[0][timeIndex]
                                break
                        rise_values_i = [float(rise_values_i)]
                    if fall_arg != "scalar":
                        for timeIndex in range(0, len(fall_i1[0])):
                            #print(fall_i1[0][timeIndex])
                            if str(fall_i1[0][timeIndex]) == "0.46":
                                fall_values_i = fall_values[0][timeIndex]
                                break
                        fall_values_i = [float(fall_values_i)]
                    if rise_arg != 'scalar' and fall_arg != 'scalar':
                            powersum_list = sum_list(rise_values_i, fall_values_i)
                    elif rise_arg == 'scalar':
                        powersum_list = fall_values_i
                    elif fall_arg == 'scalar':
                        powersum_list = rise_values_i
                    else:
                        #both scalar
                        powersum_list = [float(0)]

                # only append to list if desired pins
                # input A1 or I (CP, E, S I0, I1, TE)
                # output Z, Q, QN, ZN
                # only look at desired related pins: A1 or I ? 
                related_pin = str(related_pin).replace("\"","")
                when = str(when).replace("\"","")
                #make one for scalar as well so not that many empty lists?
                if (direction == "output" and (related_pin in input_set)):
                    intPwr_list = [related_pin, str(when).replace("\"",""), [rise_cap, powersum_list]] #[rise_cap, rise_values_i], [fall_cap, fall_values_i]]
                    intPwr_lists.append(intPwr_list)
                #inputs do not have related pins, remove them from list?
                elif (direction == "input"):
                    intPwr_list = powersum_list #[related_pin, str(when).replace("\"",""), powersum_list]#rise_values_i, fall_values_i]
                    intPwr_lists.append(intPwr_list)
    
            if direction == "output": #and (str(pinName) in output_set):
                output_pins.append([str(pinName), str(direction).replace("\"",""), str(pinfunction).replace("\"",""), str(pwrPin).replace("\"",""), str(gndPin).replace("\"",""), intPwr_lists ])
            else:# (str(pinName) in input_set):
                input_pins.append([str(pinName), str(direction).replace("\"",""), str(pin_cap), str(pwrPin).replace("\"",""), str(gndPin).replace("\"",""), intPwr_lists ])
            #print(pinLists)
        jsonstring = json.dumps([str(cellName),str(footprint).replace("\"",""),leakagePower,occurences_in_calibration_file, [input_pins, output_pins]], separators=(',', ':'))
        fp.write(jsonstring+"\n")
        
        #make json line with dumps
    fp.close()
    print("done extracting data after "+str((datetime.now()-starttime)/60)+" minutes")

def get_cells(filename):
    #cellLib = cell_library()
    cell_list = []
    #open file
    #read file line for line
    with open(filename, 'r') as svfile:
        line = svfile.readline()
        linenum = 1
        while line:
            #json loads on line to get all variables
            decoded_cell_line = json.loads(line)
            cell_list.append(decoded_cell_line)
            #print(decoded_cell_line[0])
            #print(decoded_cell_line[1]) #footprint
            line = svfile.readline()
    return cell_list

#set_cells()
def sum_list(l1, l2):
    returnlist = []
    if len(l1) == len(l2):
        for i in range(0, len(l1)):
            returnlist.append(float(l2[i])+float(l1[i]))
    else:
        print("trying to sum lists of different length")
    return returnlist

#sort cells in regs, mux and logic? 
def sort_cells(processed_library_path):
    cells = get_cells(processed_library_path)
    cell_environment = cells.pop(0)
    cell_list = []
    cellLib = cell_library()
    for c in cells:
        one_cell = cell(c, cellLib)
        cell_list.append(one_cell)
    cellLib.set_group_weights()

    #make groups handling select_op, add_op and comp_op
    adder = cell_group(['add_op'], 'adder')
    cellLib.combination_cells.append(adder)
    comp = cell_group(['comp_op'], 'comp')
    cellLib.combination_cells.append(comp)
    #selectoption = cellLib.find('ao22')
    #select = cell_group(['select_op'], 'select')
    #cellLib.combination_cells.append(select)
    
    mult = cell_group( ['mult_op'], 'mult')
    cellLib.combination_cells.append(mult)
    #cellLib.print_available_cells()
    return cellLib

class cell:
    footprint       = ''
    name            = ''
    leakage_power   = 0
    #synthetic_gate_list = [] # litst containing equivalent synthetic gate list
    def __init__(self,def_list, cell_lib):
        self.synthetic_gate_list    = []
        self.footprint              = def_list[1]
        self.def_list               = def_list
        self.name                   = def_list[0]
        self.leakage_power          = def_list[2]
        self.calibration_count      = def_list[3]
        self.pin_list               = def_list[4]
        self.input_pins             = def_list[4][0]
        self.output_pins            = def_list[4][1]
        self.N_inputs               = len(self.input_pins)
        self.N_outputs              = len(self.output_pins)
        #look through dict and set syn gate sequence and name of cell.
        #dict corresponds to # inputs

        #need to append to correct list in cell_lib
        #check if mux, check if reg, else, check N_inputs
        match = False
        for key, l in rx_dict_reg_cells.items():
            #look for name match among registers    
            match = l[0].search(self.name)
            if match:
                self.synthetic_gate_list = l[1]
                #look through list in cell lib for cell_group with matching key,
                group = cell_lib.find_cell_group(cell_lib.regs, key)
                if group == None:
                    # make new cell group
                    group = cell_group(self.synthetic_gate_list, key)
                    #append cell to list in group
                    group.append_cell(self)
                    #append cell group to list in library
                    cell_lib.regs.append(group)
                else:
                    #else append cell to list in cell_group
                    group.append_cell(self)
                break
        if not match:
            for key, l in rx_dict_mux_cells.items():
                #look for name match among multiplexers
                match = l[0].search(self.name)
                if match:
                    self.synthetic_gate_list = l[1]
                    group = cell_lib.find_cell_group(cell_lib.muxes, key)
                    if group == None:
                        # make new cell group
                        group = cell_group(self.synthetic_gate_list, key)
                        #append cell to list in group
                        group.append_cell(self)
                        #append cell group to list in library
                        cell_lib.muxes.append(group)
                    else:
                        #else append cell to list in cell_group
                        group.append_cell(self)
                    break
        if not match:
            for key, l in rx_dict_sel_cells.items():
                #look for name match among multiplexers
                match = l[0].search(self.name)
                if match:
                    self.synthetic_gate_list = l[1]
                    group = cell_lib.find_cell_group(cell_lib.selects, key)
                    if group == None:
                        # make new cell group
                        group = cell_group(self.synthetic_gate_list, key)
                        #append cell to list in group
                        group.append_cell(self)
                        #append cell group to list in library
                        cell_lib.selects.append(group)
                    else:
                        #else append cell to list in cell_group
                        group.append_cell(self)
                    break
        #first look through mux dict and reg dict for matches, if none:
        if not match:
            dictionary = get_dict_N(self.N_inputs)
            for key, l in dictionary.items():
                match = l[0].search(self.name)
                if match:
                    #found regex, set list and break
                    self.synthetic_gate_list = l[1]
                    l = cell_lib.get_list(self.N_inputs)
                    group = cell_lib.find_cell_group(l, key)
                    if group == None:
                        # make new cell group
                        group = cell_group(self.synthetic_gate_list, key)
                        #append cell to list in group
                        group.append_cell(self)
                        #append cell group to list in library
                        l.append(group)
                    else:
                        #else append cell to list in cell_group
                        group.append_cell(self)
                    break

#group together all cells with equivalent functionality
#if no cell_group matching "matching_key" is found, make new match group
#put cell groups in library instead of cells
class cell_group:
    matching_key = ''
    def __init__(self, sequence, matching_key):
        self.matching_key           = matching_key
        self.synthetic_gate_list    = sequence
        self.cells                  = []
        self.cellcounts             = []
        self.weights                = []
    def append_cell(self, cell):
        #N = count_occurence(cell.name)
        self.cellcounts.append(cell.calibration_count)
        self.cells.append(cell)
        #print("Appended cell "+cell.name)
        #print("Occurences: "+str(N))
    def get_weights(self):
        total_count = 0
        for i in self.cellcounts:
            total_count = total_count +i
        for i in range(0,len(self.cellcounts)):
            count = self.cellcounts[i]
            if total_count > 0:
                self.weights.append(round(count/total_count,2))
            else:
                self.weights.append(round(1/len(self.cellcounts), 2))
        for c in self.cells:
            print(c.name+", ", end='')
        print()
        print(self.weights)
#set_cells()
#get_cells()

def get_dict_N(N):
    if N == 1:
        return rx_dict_1_cells
    elif N == 2:
        return rx_dict_2_cells
    elif N == 3:
        return rx_dict_3_cells
    elif N == 4:
        return rx_dict_4_cells
    elif N == 5: 
        return rx_dict_5_cells
    else:
        return rx_dict_6_cells


rx_dict_1_cells = {
    'not' : [re.compile(r"INV"), ['gtech_not']],
}
rx_dict_2_cells = {
    'and2'  : [re.compile(r"AN2X?D"),   ['gtech_and2']],
    'ind2'  : [re.compile(r"IND2D"),    ['gtech_not', 'gtech_and2', 'gtech_not']],
    'nand2' : [re.compile(r"ND2D"),     ['gtech_and2', 'gtech_not']],
    'nor2'  : [re.compile(r"^NR2X?D"),  ['gtech_or2', 'gtech_not']],
    'xnor2' : [re.compile(r"XNR2"),     ['gtech_xor2', 'gtech_not']],
    'or2'   : [re.compile(r"^OR2X?D"),  ['gtech_or2']],
    'xor2'  : [re.compile(r"^XOR2"),    ['gtech_xor2']],
    'inor2' : [re.compile(r"INR2X?D"),  ['gtech_not','gtech_or2', 'gtech_not']],
    'andor22'  : [re.compile(r"AO22D"), ['select_op']], #duplicated here to be found when list are short
}
rx_dict_3_cells = {
    'and3'      : [re.compile(r"AN3X?D"),   ['gtech_and2','gtech_and2']],
    'nand3'     : [re.compile(r"^G?ND3D"),  ['gtech_and2','gtech_and2', 'gtech_not']],
    'inand3'    : [re.compile(r"^IND3D"),   ['gtech_not', 'gtech_and2','gtech_and2', 'gtech_not']],
    'nor3'      : [re.compile(r"^G?NR3"),   ['gtech_or2', 'gtech_or2','gtech_not']],
    'inor3'     : [re.compile(r"^INR3"),    ['gtech_not', 'gtech_or2', 'gtech_or2','gtech_not']],
    'iao21'     : [re.compile(r"^IAO21"),   ['gtech_or2', 'gtech_not','gtech_or2','gtech_not']],
    'or3'       : [re.compile(r"^OR3X?D"),  ['gtech_or2', 'gtech_or2']],
    'xor3'      : [re.compile(r"^XOR3"),    ['gtech_xor2', 'gtech_xor2']],
    'andori21'  : [re.compile(r"^G?AOI21D"),['gtech_and2', 'gtech_or2', 'gtech_not']],
    'orand21'   : [re.compile(r"OA21"),     ['gtech_or2', 'gtech_and2']],
    'xnor3'     : [re.compile(r"XNR3"),     ['gtech_xor2', 'gtech_xor2', 'gtech_not']],
    'iorand21'  : [re.compile(r"IOA21D"),   ['gtech_and', 'gtech_not','gtech_and', 'gtech_not']],
    'andori222' : [re.compile(r"MAOI222"),  ['gtech_and2', 'gtech_or2', 'gtech_or2', 'gtech_not']]
}
rx_dict_4_cells = {
    'and4'      : [re.compile(r"AN4X?D"),   ['gtech_and2','gtech_and2','gtech_and2']],
    'nor4'      : [re.compile(r"^NR4"),     ['gtech_or2','gtech_or2','gtech_or2','gtech_not']],
    'nand4'     : [re.compile(r"^ND4D"),    ['gtech_and2','gtech_and2','gtech_and2', 'gtech_not']],
    'xnor4'     : [re.compile(r"XNR4"),     ['gtech_xor2', 'gtech_xor2','gtech_xor2', 'gtech_not']],
    'xor4'      : [re.compile(r"^XOR4"),    ['gtech_xor2', 'gtech_xor2','gtech_xor2']],
    'orand211'  : [re.compile(r"OA211"),    ['gtech_or2', 'gtech_and2', 'gtech_and2']],
    'or4'       : [re.compile(r"^OR4X?D"),  ['gtech_or2', 'gtech_or2', 'gtech_or2']],
    'iinor4'    : [re.compile(r"IINR4"),    ['gtech_not', 'gtech_or2', 'gtech_or', 'gtech_or', 'gtech_not']],
    'andor211'  : [re.compile(r"AO211D"),   ['gtech_and2', 'gtech_or2', 'gtech_or2']],
    # identical to 21 'iandor22'  : [re.compile(r"IAO22D"),   ['gtech_or2','gtech_not', 'gtech_or2', 'gtech_not']],
    # identical to 21 'orandi22'  : [re.compile(r"OAI22D"),   ['gtech_and2','gtech_not', 'gtech_and2', 'gtech_not']],

    #'andor22'  : [re.compile(r"AO22D"), ['select_op']],
    'andori31'  : [re.compile(r"AOI31D"),   ['gtech_and2','gtech_and2', 'gtech_or2', 'gtech_not']],
    'andor31'  : [re.compile(r"AO31D"),     ['gtech_and2', 'gtech_and2','gtech_or2']],
    'ind4'     : [re.compile(r"IND4D"),     ['gtech_not', 'gtech_and2', 'gtech_and2', 'gtech_not']]
}
rx_dict_5_cells = {
    'and5'      : [re.compile(r"^G?AN5D"),  ['gtech_and2','gtech_and2','gtech_and2', 'gtech_and2']],
    'nor5'      : [re.compile(r"^G?NR5"),   ['gtech_or2','gtech_or2','gtech_or2', 'gtech_or2','gtech_not']],
    'or5'       : [re.compile(r"^OR5"),     ['gtech_or2','gtech_or2','gtech_or2', 'gtech_or2']],
    'xor5'      : [re.compile(r"XOR5D"),    ['gtech_xor2','gtech_xor2','gtech_xor2', 'gtech_xor2']],
    'xnor5'     : [re.compile(r"XNR5D"),    ['gtech_xor2','gtech_xor2','gtech_xor2', 'gtech_xor2', 'gtech_not']],
    'nand5'     : [re.compile(r"ND5D"),     ['gtech_and2','gtech_and2','gtech_and2', 'gtech_and2','gtech_not']],
    'oa221'     : [re.compile(r"OA221"),    ['gtech_or2', 'gtech_and2', 'gtech_and2']],
    'ao221'     : [re.compile(r"AO221"),    ['gtech_and2', 'gtech_or2', 'gtech_or']],
}
rx_dict_6_cells = {
    'and6'      : [re.compile(r"AN6D"),   ['gtech_and2','gtech_and2','gtech_and2', 'gtech_and2', 'gtech_and2']],
    'nand6'     : [re.compile(r"ND6D"),   ['gtech_and2','gtech_and2','gtech_and2', 'gtech_and2', 'gtech_and2', 'gtech_not']],
    'xnor6'     : [re.compile(r"XNR6"),   ['gtech_xor2','gtech_xor2','gtech_xor2', 'gtech_xor2', 'gtech_xor2', 'gtech_not']],
    'nor6'      : [re.compile(r"^NR6"),   ['gtech_or2','gtech_or2','gtech_or2', 'gtech_or2','gtech_or2', 'gtech_not']],
    'or6'       : [re.compile(r"^OR6"),   ['gtech_or2','gtech_or2','gtech_or2', 'gtech_or2','gtech_or2']],
    'xor6'      : [re.compile(r"XOR6"),   ['gtech_xor2','gtech_xor2','gtech_xor2', 'gtech_xor2', 'gtech_xor2']],
}
rx_dict_reg_cells = {
    'reg'   : [re.compile(r"DF[C|S|Q|N][N|D|C]"), ['reg']],
    'reg' : [re.compile(r"(L[H|N]Q)"), ['reg']]
}
rx_dict_mux_cells = {
    'mux2n' : [re.compile(r"MUX2N"), ['mux_op', 'gtech_not']],
    'mux2'  : [re.compile(r"MUX2"), ['mux_op']]
}
rx_dict_sel_cells = {
    'andor22'  : [re.compile(r"AO22D"), ['select_op']], #duplicated here to be found when list are short
}


class cell_library:
    def __init__(self):
        self.cells_6 = []
        self.cells_5 = []
        self.cells_4 = []
        self.cells_3 = []
        self.cells_2 = []
        self.cells_1 = []
        self.muxes   = []
        self.regs    = []
        self.selects = []
        self.combination_cells = []
        self.group_lists = [self.cells_6, self.cells_5, self.cells_4, self.cells_3, self.cells_2, self.cells_1, self.muxes, self.regs]
    def get_list(self, N):
        list_dict = {
            1 : self.cells_1,
            2 : self.cells_2,
            3 : self.cells_3,
            4 : self.cells_4,
            5 : self.cells_5,
            6 : self.cells_6
        }
        l = list_dict.get(N, lambda: None)
        if l == None:
            print("could not get list, no corresponding N")
            return l
        else:
            return l
    def find_cell_group(self, l, group_key):
        for g in l:
            if g.matching_key == group_key:
                #found, return group
                return g
        #not found, return none
        #if none make new group outside function
        return None
    def set_group_weights(self):
        for l in self.group_lists:
            for g in l:
                g.get_weights()
    def print_available_cells(self):
        print("6 input")
        for c in self.cells_6:
            print("\t"+c.matching_key)
        print("5 input")
        for c in self.cells_5:
            print("\t"+c.matching_key)
        print("4 input")
        for c in self.cells_4:
            print("\t"+c.matching_key)
        print("3 input")
        for c in self.cells_3:
            print("\t"+c.matching_key)
        print("2 input")
        for c in self.cells_2:
            print("\t"+c.matching_key)
        print("1 input")
        for c in self.cells_1:
            print("\t"+c.matching_key)
        print("registers")
        for c in self.regs:
            print("\t"+c.matching_key)
        print("muxes")
        for c in self.muxes:
            print("\t"+c.matching_key)

# find cell group in list of cell groups
def find_cell(key, l):
    for cell_group in l:
        if key == cell_group.matching_key:
            return cell_group
    return None

# count occurence of a word in a file
def count_occurence(word):
    path = path_to_calibration_file
    fp = open(path, "r")
    f = fp.read()
    return f.count(word)

#sort_cells(processed_library_path)

#make list of synthetic cells into list of cells from cell library
def transform_list(cell_lib, to_transform):
    if len(to_transform) < 6:
        i = len(to_transform)+1#6
    else:
        i = 6
    #make list of index structs, sort list, then go through list and append
    ind = []
    templist = list(to_transform)
    #look for regs
    regindexes = find_sequence(templist, cell_lib.regs[0])
    if regindexes != []: 
        for r in regindexes:
            ind.append(r)
            templist[r[0]] = 0
    selindexes = find_sequence(templist, cell_lib.selects[0])
    if selindexes != []: 
        for r in selindexes:
            ind.append(r)
            templist[r[0]] = 0
        #print("found regindex")
    #for ind in regindexes:
    #    # make new list? or what... length of sequences vary.... 
    #    # gonna fuck up if i start modifying original
    #    #okey with muxes and registers but not with logic
    #    to_transform[ind[0]:ind[1]]
    #look for muxes
    muxindexes = find_sequence(templist, cell_lib.muxes[0])
    #for mux in muxindexes:
    if muxindexes != []: 
        for m in muxindexes:
            ind.append(m)
            templist[m[0]] = 0
    l = cell_lib.combination_cells
    for element in l:
        indexes = find_sequence(templist, element)
        if indexes != []: 
                for k in indexes:
                    ind.append(k)
                #print(indexes)
                #print("Found "+str(element.synthetic_gate_list)+" in "+str(to_transform))
                for ii in indexes:
                    for r in range(ii[0], ii[1]):
                        #print(r)
                        #templist.pop(r)
                        templist[r] = 0
    #look through lists looking for matches to replace sequences
    while i != 0:
        #print(i)
        l = cell_lib.get_list(i)
        #print("called cell_lib.get_list "+str(i))
        #go through dict with that many inputs:
        #need to relate this list to cell group somehow as well to have power info available
        for element in l:
            #print("looking for "+str(element.synthetic_gate_list)+" in "+str(to_transform))
            indexes = find_sequence(templist, element) #need element as well in list, not only indexes
            #print("syn_gate_list")
            #print(element.synthetic_gate_list)
            if indexes != []: 
                for k in indexes:
                    ind.append(k)
                #print(indexes)
                #print("Found "+str(element.synthetic_gate_list)+" in "+str(to_transform))
                for ii in indexes:
                    for r in range(ii[0], ii[1]):
                        #print(r)
                        templist[r] = 0
                        #templist.pop(r)
        i = i-1
    #replace found indexes when they are found so they cannot be found again
    ind.sort()
    elementlist = []
    #print(ind)
    for indexelement in ind:
        #print(i[0][2].matching_key)
        elementlist.append(indexelement[2])
    #print(elementlist)
    return elementlist

# returns none if indexes not in list or list of (startindex, stopindex) for each occurence
# also returns the index(es) it found
def find_sequence(to_find, element):
    l = element.synthetic_gate_list
    indexes = []
    temp = list(to_find)
    #print("list from structure: "+str(to_find))
    #print("looking for: "+str(l))
    #print("looking for l: "+str(l))
    for i in range(len(temp)):
        #print(to_find[i:i+len(l)])
        if temp[i:i+len(l)] == l:
            temp[i:i+len(l)] = [0]*len(l)
            #print(l[i:i+len(to_find)])
            #print("found: "+str(l))
            #print(to_find[i:i+len(l)])
            indexes.append((i, i+len(l), element))
    return indexes
