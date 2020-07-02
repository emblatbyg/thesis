# File for parsing .elab files made by synopsys compiler

import numpy as np
import re 
import pandas as pd
import sys

#list of module objects
modules = []
#list of structure trees
top_level_parents = []

#lists setting module environment
regs            = np.array([])
nots            = np.array([])
bufs            = np.array([])
and2s           = np.array([])
or2s            = np.array([])
muxes           = np.array([])
selects         = np.array([])
connects        = np.array([])
inputs          = np.array([])
outputs         = np.array([])
dependencies    = np.array([])
shifters        = np.array([])
comparators     = np.array([])
xor2s           = np.array([])
multipliers     = np.array([])
subtractors     = np.array([])
b_shifters      = np.array([])
adders          = np.array([])
shift_adders    = np.array([])
divisors        = np.array([])
assigns         = np.array([])

#gate counts
reg_n        = 0
not_n        = 0
buf_n        = 0
and2_n       = 0
or2_n        = 0
mux_n        = 0
select_n     = 0
shift_n      = 0
comp_n       = 0
xor2_n       = 0
mult_n       = 0
sub_n        = 0
b_shift_n    = 0
add_n        = 0
shift_add_n  = 0
div_n        = 0

#empty global lists relating to a module environment
def empty_global_lists():
    global regs      
    global nots      
    global bufs      
    global and2s     
    global or2s      
    global muxes     
    global selects   
    global connects  
    global inputs    
    global outputs   
    global dependencies
    global shifters
    global comparators
    global xor2s
    global multipliers
    global subtractors
    global b_shifters 
    global adders     
    global shift_adders
    global divisors  
    global assigns

    regs        = np.array([])
    nots        = np.array([])
    bufs        = np.array([])
    and2s       = np.array([])
    or2s        = np.array([])
    muxes       = np.array([])
    selects     = np.array([])
    connects    = np.array([])
    inputs      = np.array([])
    outputs     = np.array([])
    dependencies = np.array([])
    shifters    = np.array([])
    comparators = np.array([])
    xor2s       = np.array([])
    multipliers = np.array([])
    subtractors = np.array([])
    b_shifters = np.array([])
    adders      = np.array([])
    shift_adders  = np.array([])
    divisors    = np.array([])
    assigns = np.array([])

#set global lists relating to a module environment
def set_global_lists(module):
    global regs      
    global nots      
    global bufs      
    global and2s     
    global or2s      
    global muxes     
    global selects   
    global connects  
    global inputs    
    global outputs   
    global dependencies
    global shifters
    global comparators
    global xor2s
    global multipliers
    global subtractors
    global b_shifters 
    global adders     
    global shift_adders
    global divisors  
    global assigns

    regs            = module.regs        
    nots            = module.nots        
    bufs            = module.bufs        
    and2s           = module.and2s       
    or2s            = module.or2s        
    muxes           = module.muxes       
    selects         = module.selects     
    connects        = module.connects    
    inputs          = module.inputs      
    outputs         = module.outputs     
    dependencies    = module.dependencies
    shifters        = module.shifters    
    comparators     = module.comparators 
    xor2s           = module.xor2s       
    multipliers     = module.multipliers 
    subtractors     = module.subtractors 
    b_shifters      = module.b_shifters  
    adders          = module.adders      
    shift_adders    = module.shift_adders
    divisors        = module.divisors
    assigns         = module.assigns

#go through elaborated systemverilog file line by line
def parse_file(path):
    #make lists and treat lists to make objs later
    print ("Parsing file:" + path )
    
    #SEARCH FOR START OF OBJECT
    object_handle   = 'false'
    objectstring    = ""
    bitwidth = 0
    modulename = ''
    in_module = False
    moduleline = ''
    with open(path, 'r') as svfile:
        line = svfile.readline()
        linenum = 1
        while line:
            #search for start of module 
            if (in_module):
                #handle end of module
                if (find_endmodule(line)):
                    global modules
                    in_module = False
                    module_handle = module(modulename)
                    module_handle.set_lists()
                    module_handle.connection_point_string = moduleline 
                    connect_assigns()
                    empty_global_lists()
                    modules.append(module_handle)
                #search for start of object
                else:
                    key, match = parse_line(line, 'false')
            else:
                #search for start of module
                modulename, in_module = find_module(line)
                #print("Started module: "+modulename)
                match = False
                module_declaration_ongoing = True
                #get lines until end of module declaration and catch things in regex
                while module_declaration_ongoing:
                    for k, rx in rx_dict_end.items():
                            objectstring = objectstring+line
                            #print("objectstring to search for end: \n\t"+objectstring)
                            match = rx.search(line)
                            if match:
                                # found end, leave while loop
                                module_declaration_ongoing = False
                                moduleline = objectstring
                                #print(moduleline)
                            else:
                                # read new line until end is found
                                line = svfile.readline()
                                linenum = linenum +1
                objectstring = ''
                match = False
        
            if match and in_module:
                #if connection split items by comma and make objects of all
                offset = 0
                if match.group(1) == 'input' or match.group(1) == 'output' or match.group(1) == 'wire':
                    
                    if match.group(2) != None:
                        bitwidth = int(match.group(2)) - int(match.group(3)) + 1
                        line = " ".join(line.split()[2:])
                        offset = int(match.group(3))
                    else:
                        bitwidth = None
                        line = " ".join(line.split()[1:])
                #else prepare for finding attributes of single object
                else:
                    #object_handle = make_object(match.group(1), key)
                    if(key == 'dep'): 
                        object_handle = make_object(match.group(2), key)
                        object_handle.modulename = match.group(1)
                        #print("made dep: "+match.group(2)+" of module "+match.group(1))
                    else:
                        object_handle = make_object(match.group(1), key)
                # while taking in list of equally attributed connections or single item
                # get new lines until all of object(s) is in one string
                in_object = True
                while in_object:
                    #merge lines until end of regster is found
                    #print ("looking for end of object")
                    for k, rx in rx_dict_end.items():
                        objectstring = objectstring+line
                        #print("objectstring to search for end: \n\t"+objectstring)
                        match = rx.search(line)
                        if match:
                            # found end, leave while loop
                            in_object = False
                        else:
                            # read new line until end is found
                            line = svfile.readline()
                            linenum = linenum +1
                
                #make single object or make several connect objects
                objectstring = "".join(objectstring.split())
                if (key == 'input' or key == 'output' or key == 'wire'):
                    objectstring = objectstring.strip(";")
                    
                    objectstring = objectstring.translate({ord(i): None for i in '}{ '})
                    
                    objectlist = objectstring.split(',')
                    for name in objectlist:
                        object_handle = make_object(name, key)
                        #if (object_handle != None):
                        if (bitwidth != None): 
                            object_handle.width = bitwidth
                            object_handle.widthoffset = offset
                            object_handle.init_connection_nodes()
                        #print ("made new connection object with name "+name+"\nand width "+ str(bitwidth))
                else:
                    # add connection node info to object                
                    parse_line(objectstring, object_handle)
                # when done with an object, empty object string
                objectstring = ""

            line = svfile.readline()
            linenum = linenum + 1

# create object
def make_object(line, name):
    #print("Making object: "+name)
    
    line = line.translate({ord(i): None for i in '}{\ '}) 
   
    i1, i2, object_name, index_type = find_indexes(line)
    if ((i1 != -1) or (i2 != -1)) and name != 'register' and name != 'assign':
        object_handle = None
        foundbool = False
        if name == 'input':
            object_handle, foundbool = search_list(inputs, object_name)
        elif name == 'output':
            object_handle, foundbool = search_list(outputs, object_name)
        elif name == 'wire':
            object_handle, foundbool = search_list(connects, object_name)
        if (foundbool):
            #print("Found object in already existing connetion object")
            if (object_handle.width <= i1): object_handle.width = i1+1
            if (object_handle.depth <= i2): object_handle.depth = i2+1

        else:
            object_handle = create_object(name)
            object_handle.name = object_name
            if i1 != -1: object_handle.width = i1+1
            if i2 != -1: object_handle.depth = i2+1
            object_handle.init_connection_nodes()
    else:
        object_handle = create_object(name)
        object_handle.name = line
        if(name == 'input' or name == 'output' or name == 'wire'):
            object_handle.init_connection_nodes()
        if(name == 'assign'):
            #print("making fancy assign")
            object_handle.i1 = i1
            if i2 != -1: object_handle.i2 = i2
            foundbool = False
            connected_handle, foundbool = search_list(outputs, object_name)
            if foundbool != True:
                connected_handle, foundbool = search_list(inputs, object_name)
                if foundbool != True: 
                    connected_handle, foundbool = search_list(connects, object_name)
            if foundbool:
                object_handle.lhs = connected_handle
                
    return object_handle

#looks for indexes at end of string, returns i1, i2, str(w/o)indexes
def find_indexes(string):
    i1 = -1
    i2 = -1
    index_type = ''
    indexes = re.compile(r"(?:\[(\d{1,4})\])(?:\[(\d{1,4})\])?$")
    slices = re.compile(r"(?:\[(\d{1,4})\:(\d{1,4})\])$")
    indexfind = indexes.search(string)
    newline = indexes.sub("",string)
    if indexfind != None:
        index_type  = 'index'
        if indexfind.group(1) != None:
            i1 = int(indexfind.group(1))
            if indexfind.group(2) != None:
                i2 = int(indexfind.group(2))
    else:
        slicefind = slices.search(string)
        if slicefind != None:
            index_type = 'slice'
            i1 = int(slicefind.group(1))
            i2 = int(slicefind.group(2))
            newline = slices.sub("", string)
            #print("found a slice")
    return i1, i2, newline, index_type

#create an object of a class specified by objectname
def create_object(objectname):
    objectselect = {
        'wire'      : connection,
        'input'     : input_obj,
        'output'    : output_obj,
        'SELECT_OP' : select_op,
        'MUX_OP'    : mux_op,
        'GTECH_NOT' : gtech_not,
        'GTECH_BUF' : gtech_buf,
        'GTECH_AND2': gtech_and2,
        'GTECH_OR2' : gtech_or2,
        'GTECH_XOR2': gtech_xor2,
        'register'  : register,
        'dep'       : dependency,
        'COMP_OP'   : comp_op,
        'SHIFT_OP'  : shift_op,
        'SUB_OP'    : sub_op,
        'ADD_OP'    : add_op,
        'MULT_OP'   : mult_op,
        'DIV_OP'    : div_op,
        'B_SHIFT_OP'   : b_shift_op,
        'SHIFT_ADD_OP': shift_add_op,
        'DIV_OP'    : div_op,
        'assign'    : assign
        
    }
    #get function
    #print("making object: "+objectname)
    func = objectselect.get(objectname, lambda: None)
    if func == None:
        print("found no object with objectname: "+str(objectname))
        return None
    else:
        #print("lookup successful, func = "+ str(func))
        retval = func()
        return retval

#return true if module declaration is on line
def find_module(line):
    module_start = re.compile(r"module\s+(\S+)\s?\(")
    match = module_start.search(line)
    if (match):
        return match.group(1), True
    else:
        return None, False

#return true if line contains endmodule
def find_endmodule(line):
    module_end = re.compile(r"endmodule")
    match = module_end.search(line)
    if (match):
        return True
    else:
        return False

#look for object with name objectname in a list of objects. return handle if match, None otherwise
def find_object(objectlist, objectname):
    for i in range(0, len(objectlist)-1):
        if objectlist[i].name == objectname:
            return objectlist[i]
    return None

# parse one line, looking for start of object or internal parameters of object
def parse_line(line, object_handle):
    # print ("parsing line: \n"+ line + "\n in object:\n" + str(object_handle))
    key = ""
    match = ""
    if (object_handle == 'false'):
        for key, rx in rx_dict_start.items():
            #look for start of object to determine object type
            match = rx.search(line)
            if match:
                return key, match  
    #look for connect objects in non-connect objects? 
    elif (object_handle.id == 'reg'):
        #look for objects inside register dict and end
        for key, rx in rx_dict_reg.items():
            match = rx.search(line)
            #print("line: " + line)
            #print ("found match for: " + key +" group captured: " +  match.group(1) )
            if (key == 'clear'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.clear = match.group(1)
            elif (key == 'preset'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.preset = match.group(1)
            elif (key == 'next_state'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.next_state = match.group(1)
            elif (key == 'clocked_on'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.clocked_on = match.group(1)
            elif (key == 'data_in'):
                process_match([match.group(1)], object_handle, 'input', key)
                object_handle.data_in = match.group(1)
            elif (key == 'enable'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.enable = match.group(1)
            elif (key == 'Q'):
                process_match([match.group(1)], object_handle, 'output', key)
                object_handle.Q = match.group(1)
            elif (key == 'QN'):
                process_match([match.group(1)], object_handle, 'output', key)
                object_handle.QN = match.group(1)
            elif (key == 'synch_clear'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.synch_clear = match.group(1)
            elif (key == 'synch_preset'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.synch_preset = match.group(1)
            elif (key == 'synch_toggle'):
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.synch_toggle = match.group(1)
            elif key == 'synch_enable':
                process_match([match.group(1)], object_handle, 'control', key)
                object_handle.synch_enable = match.group(1)
            else:
                print ("no matching key: " + key + " in register " + object_handle)
        #look for end
        for key, rx in rx_dict_end.items():
            match = rx.search(line)
    elif object_handle.id == 'gtech_or2' or object_handle.id == 'gtech_and2' or object_handle.id == 'gtech_xor2':
        for key, rx in rx_dict_AND2.items():
            match = rx.search(line)
            if (key == 'A' and match):
                process_match([match.group(1)], object_handle, 'input', key)
                object_handle.A = match.group(1)
            elif (key == 'B' and match):
                process_match([match.group(1)], object_handle, 'input', key)
                object_handle.B = match.group(1)
            elif (key == 'Z' and match):
                process_match([match.group(1)], object_handle, 'output', key)
                object_handle.Z = match.group(1)
            else:
                print ("\nNo attribute of object " + str(object_handle) + " matches key " + key)
                print("from line: "+line+"\n")
        for key, rx in rx_dict_end.items():
            match = rx.search(line)
            if (match == False):
                print ("looked for end in "+ object_handle + " could not find it..." )
    elif object_handle.id == 'gtech_not' or object_handle.id == 'gtech_buf':
        for key, rx in rx_dict_BUF.items():
            match = rx.search(line)
            if (key == 'A' and match):
                process_match([match.group(1)], object_handle, 'input', key)
                object_handle.A = match.group(1)
            elif (key == 'Z' and match):
                process_match([match.group(1)], object_handle, 'output', key)
                object_handle.Z = match.group(1)
            else:
                print ("No attribute of object " + str(object_handle) + " matches key " + key)  
            #look for end
        for key, rx in rx_dict_end.items():
            match = rx.search(line)
            if (match == False):
                print ("looked for end in "+ str(object_handle) + " could not find it..." )
                return key, False
        return key, match
    elif object_handle.id == 'mux_op':
        for key, rx in rx_dict_MUX.items():
            match = rx.findall(line)
            if (key == 'D' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'input', key)
 
                object_handle.datawidth = datawidth
                object_handle.D = matchlist
                for i in range(0,len(match)):
                    object_handle.D[i] = matchlist
            elif (key == 'S' and match):
                process_match(match, object_handle, 'control', key) 
                #number of selects is length of match, only one bit widths.
                object_handle.S = np.append(object_handle.S, match)
                #if match is list of matches to key
            elif (key == 'Z' and match):
                #print( "Added Z to mux")
                process_match(match, object_handle, 'output', key)
                #will have same datawidth as D.
                object_handle.Z = match

            else: 
                print("did not find attributes of object: "+ object_handle.name)        
    elif object_handle.id == 'select_op':
        for key, rx in rx_dict_SELECT.items():
            #returning everything matching given key in a list
            match = rx.findall(line)
            if (key == 'DATA' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'input', key)
                object_handle.datawidth = datawidth
                object_handle.D = matchlist
            elif (key == 'CONTROL' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'control',key)
                object_handle.datawidth = datawidth
            elif (key == 'Z' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'output', key)
                object_handle.Z = matchlist
            else:
                print("did not find attributes of object: "+ object_handle.name)
    elif object_handle.id == 'comp_op' or object_handle.id == 'add_op' or object_handle.id == 'sub_op' or object_handle.id == "mult_op" or object_handle.id == "div_op":
        for key, rx in rx_dict_SUB_ADD_MULT.items():
            match = rx.findall(line)
            if (key == 'A' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'input', key)
                object_handle.a_width = datawidth
                object_handle.A = matchlist
            elif (key == 'B' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'input', key)
                object_handle.b_width = datawidth
                object_handle.B = matchlist
            elif (key == 'Z' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'output', key)
                object_handle.z_width = datawidth
                object_handle.Z = matchlist
            else: 
                print("did not find attributes of object: "+ object_handle.name) 
    elif object_handle.id == 'shift_op' or object_handle.id == 'b_shift_op':
        for key, rx in rx_dict_shift.items():
            match = rx.findall(line)
            if (key == 'A' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'input', key)
                object_handle.a_width = datawidth
                object_handle.A = matchlist
            elif (key == 'SH' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'control', key)
                object_handle.sh_width = datawidth
                object_handle.SH = matchlist
            elif (key == 'Z' and match):
                dataN, datawidth, matchlist = process_match(match, object_handle, 'output', key)
                object_handle.z_width = datawidth
                object_handle.Z = matchlist
            else: 
                print("did not find attributes of object: "+ object_handle.name)  
    elif(object_handle.id == 'dep'):
        #look for dep objects and add them to list
        for key, rx in rx_dict_dep_internals.items():
            match = rx.findall(line)
            if match:
                object_handle.add_connections(match)
    elif(object_handle.id == 'assign'):
        #print("Assign statement")
        for key, rx in rx_dict_assign.items():
            match = rx.search(line)
            if key == 'rhs':
                rhsline = match.group(1)
                rhsline = rhsline.translate({ord(i): None for i in '}{\ '})
                if rhsline == "1'b0" or rhsline == "1'b1":
                    object_handle.rhs = "constant"
                else: 
                    i1, i2, new_rhsline, indextype = find_indexes(rhsline)
                    object_handle.rhs_i1 = i1
                    #look for new_rhsline in connections.
                    if (i2 != -1): object_handle.rhs_i2 = i2

                    element, foundbool = search_list(outputs, new_rhsline)
                    
                    if foundbool == False:
                        element, foundbool = search_list(inputs, new_rhsline)
                        if foundbool == False:
                            element, foundbool = search_list(connects, new_rhsline)
                    if foundbool:
                        object_handle.rhs = element
                    else:
                        print("Did not find match of rhs in assign")
                        print(new_rhsline)
    else: 
        print (" No match found for object handle id: "+ object_handle.id)
    return key, match

#if signal is not constant, find out what it is connected to and the width and register connection
def process_match(match, object_handle, connection_type, port_name):
    #print("Running process match for object " + str(object_handle.name)) 
    dataN = len(match)
    processed_matchlist = []
    if match[0] == "":
        return 0, 0, []
    for i in range(0, len(match)):
        match[i] = match[i].translate({ord(i): None for i in '}{\ '}) 
        datawidth = match[i].count(',')+1
        matchlist = match[i].split(',')
        processed_matchlist.append(matchlist)
        datawidth_set = {'sub_op','select_op', 'mux_op', 'shift_op', 'add_op', 'mult_op', 'comp_op', 'div_op', 'b_shift_op', 'shift_add_op'}
        if(connection_type == 'output'):
            if (object_handle.id in datawidth_set):
                if(object_handle.output_nodes ==[]):
                    #declare output_nodes
                    if object_handle.id == 'mux_op' or object_handle.id == 'select_op':
                        object_handle.output_nodes = [None]*datawidth
                    else:
                        object_handle.output_nodes = [None]*datawidth
        j_increment = 0
        for j in range(0, len(matchlist)): #j is i1
            if matchlist[j] == '1\'b1' or matchlist[j] == '1\'b0':
                datawidth = 1
            else:
                found = False
                if(port_name == 'dep'):
                    to_append = [object_handle, port_name, object_handle.id, connection_type, j+j_increment, i] #0]
                else:
                    to_append = [object_handle, port_name, object_handle.id, connection_type, j+j_increment]
                #print("j = "+str(j))
                if (connection_type == 'input' or connection_type == 'control'): #or connection_type == 'control'):
                    i1, i2, matchobj, index_type = find_indexes(matchlist[j])
                    element, found = search_list(inputs, matchobj)
                    
                    if found:
                        element.add_node_input_connection(i1, i2, to_append, index_type)
                    else:
                        element, found = search_list(connects, matchobj)
                        if found:
                            element.add_node_input_connection(i1, i2, to_append, index_type)
                        else: 
                            element, found = search_list(outputs, matchobj)
                            if found:
                                element.add_node_input_connection(i1, i2, to_append, index_type)
                               
                            else:
                                print("Did not find: "+matchobj)
                                print("["+str(object_handle.name)+" , "+str(port_name)+" , "+str(object_handle.id)+"]")
                    if found:
                        if index_type == '':
                            #whole signal width-1 added to j
                            j_increment = j_increment + element.width -1
                        elif index_type == 'slice':
                            #add width of slice to j'
                            j_increment = j_increment+ i1-i2
                        #print("j_increment: "+str(j_increment))

                elif (connection_type == 'output'):
                    i1, i2, matchobj, index_type = find_indexes(matchlist[j])
                    element, found = search_list(outputs, matchobj)
                    if found:
                        if(i1 == -1 and i2 == -1):
                            #print("Element width: "+str(element.width))
                            if element.width > 1 and (element.width != len(object_handle.output_nodes)):
                            #redefine output
                                if (object_handle.id in datawidth_set):
                                    for i in range(element.width-1):
                                        object_handle.output_nodes.append(None)
                                    #print(len(object_handle.output_nodes))
                        if element.width == 1 and index_type == '':
                            index_type = 'bit'
                        element.add_node_output_connection(i1, i2, to_append, index_type,j+j_increment)
                    else:
                        element, found = search_list(connects, matchobj)
                        if found:
                            if(i1 == -1 and i2 == -1):
                                #print("Element width: "+str(element.width))
                                if element.width > 1 and (element.width != len(object_handle.output_nodes)):
                                #redefine output
                                    if (object_handle.id in datawidth_set):
                                        for i in range(element.width-1):
                                            object_handle.output_nodes.append(None)                            
            
                            if element.width == 1 and index_type == '':
                                index_type = 'bit'
                            #print("calling add_node_output_connection i1="+str(i1)+" i2: "+str(i2)+" j: "+str(j))
                            element.add_node_output_connection(i1, i2, to_append, index_type,j+j_increment)
                            
                        else: 
                            print("Did not find: "+matchobj)
                            print(str(object_handle)+" "+str(port_name)+" "+str(object_handle.id))
                    if found:
                        #print("j = "+str(j))
                        if index_type == '':
                            #whole signal width-1 added to j
                            #print("Modified j_increment")
                            j_increment = j_increment + element.width -1
                        elif index_type == 'slice':
                            #add width of slice to j'
                            #print("Modified j_increment")
                            j_increment = j_increment+ i1-i2
                        #print("j_increment: "+str(j_increment))
                else:
                    print("Did not find\t"+str(matchlist[j])+"\tANYWHERE")
        
    #print("\nFinished matchlist for: "+object_handle.name+"\nwidth: "+str(datawidth)+"\nN:" +str(dataN)+"\nMatchlist:" + str(processed_matchlist)+"\n")
    return dataN, datawidth,  processed_matchlist

#return object in list with name matching searchstring or None, False
def search_list(list, searchstring):
    element = None
    for element in list:
        if (element.name == searchstring):
            #if searchstring[0] == 'e': print("FOUND: "+searchstring)
            return element, True
    return element, False

#set nodes involved in assign statements equal to each other
def connect_assigns():
    #print("RUNNING CONNECT ASSIGNS")
    #print(assigns)
    for a in assigns:
        #print(a.name)
        #print(a.lhs.name+" "+str(a.lhs))
        #print(a.rhs)
        #print(a.i1)
        #print(a.i2)
        if(a.i1 != -1):
            #print(a.lhs.connection_nodes)
            lhs_node = a.lhs.connection_nodes[a.i1-a.lhs.widthoffset][a.i2]
        else: 
            #print("should connect whole signal")
            pass
        if a.rhs != None and a.rhs !="constant":
            #print(a.rhs.connection_nodes)
            rhs_node = a.rhs.connection_nodes[a.rhs_i1-a.rhs.widthoffset][a.rhs_i2]
        #print("Defined two connection nodes")
        if (a.i1 != -1 and a.rhs != None):
            #Connect bits of single node
            if a.rhs == "constant":
                a.lhs.connection_nodes[a.i1][a.i2].constant = True
            else:
                n1 = a.lhs.connection_nodes[a.i1-a.lhs.widthoffset][a.i2]
                n2 = a.rhs.connection_nodes[a.rhs_i1-a.rhs.widthoffset][a.rhs_i2]
                connect_nodes(n1, n2)
        else:
            #connect whole node if a.rhs exists
            if a.rhs != None and a.rhs != "constant":
                #print("Connect whole signal")
                for i in range(len(a.lhs.connection_nodes)):
                    for j in range(len(a.lhs.connection_nodes[i])):
                        n1 = a.lhs.connection_nodes[i][j]
                        n2 = a.rhs.connection_nodes[i][j]
                        connect_nodes(n1,n2)

#set nodes equal to each other
def connect_nodes(n1, n2):
    if n1 == n2:
        return
    else:
        for i in range(len(n1.connected_inputs)):
            n1_con = n1.connected_inputs[i]
            found = False
            for j in range(len(n2.connected_inputs)):
                n2_con = n2.connected_inputs[j]
                n1.connected_inputs.append(n2_con)
            n2.connected_inputs.append(n1_con)
        if n1.connected_outputs == []:
            n1.connected_outputs = n2.connected_outputs
        elif n2.connected_outputs == []:
            n2.connected_outputs = n1.connected_outputs
        if n1.constant == True: n2.constant = True
        if n2.constant == True: n1.constant = True


#classes 
class register:
    id = 'reg'
    name = ""
    clear = 0
    preset = 0 
    next_state = 0
    clocked_on = 0
    data_in = 0
    enable = 0
    Q = 0
    QN = 0
    synch_clear = 0
    synch_preset = 0
    synch_toggle = 0
    synch_enable = 0
    output_structure_taken = False
    structurecount = 0
    def __str__(self):
        #return "Register: \n clear = " + str(self.clear) + "\n preset = " + str(self.preset) + "\n next_state = " + str(self.next_state) +"\n clocked_on = " + str(self.clocked_on) +"\n data_in = " + str(self.data_in) +"\n enable = " + str(self.enable) +"\n Q = " + str(self.Q)
        return "Register: " + self.name
    def __init__(self):
        #print("made reg!")
        global regs
        regs = np.append(regs, self)
        self.output_nodes_q = [None]*1
        self.output_nodes_qn = [None]*1
        self.has_parent = False
class gtech_or2:
    id = 'gtech_or2'
    name = ""
    A = 0
    B = 0
    Z = 0
    structurecount = 0
    def __str__(self):
        return "OR2: " + self.name
    def __init__(self):
        #print("made or2!")
        global or2s
        or2s = np.append(or2s, self)
        self.output_nodes = [None]*1
class gtech_xor2:
    id = 'gtech_xor2'
    name = ""
    A = 0
    B = 0
    Z = 0
    structurecount = 0
    def __str__(self):
        return "XOR2: " + self.name
    def __init__(self):
        #print("made or2!")
        global xor2s
        xor2s = np.append(xor2s, self)       
        self.output_nodes = [None]*1
class gtech_and2:
    id = 'gtech_and2'
    name = ""
    A = 0
    B = 0
    Z = 0
    structurecount = 0
    def __str__(self):
        return "AND2: " + self.name + " A: "+str(self.A)+" B: "+str(self.B)+" Z: "+str(self.Z)
    def __init__(self):
        global and2s
        and2s = np.append(and2s, self)
        self.output_nodes = [None]*1
class gtech_not:
    id = 'gtech_not'
    name = ""
    A = 0
    Z = 0
    structurecount = 0
    def __str__(self):
        return "NOT: " + self.name
    def __init__(self):
        global nots
        self.output_nodes = [None]*1
        nots = np.append(nots, self)
class gtech_buf:
    id = 'gtech_buf'
    name = ""
    A = 0
    Z = 0
    structurecount = 0
    def __str__(self):
        return "BUF: " + self.name
    def __init__(self):
        self.output_nodes = [None]*1
        global bufs
        bufs = np.append(bufs, self)
class mux_op:
    id = 'mux_op'
    name = ""
    D = np.array([])
    S = np.array([])
    Z = np.array([])
    datawidth = 0
    structurecount = 0
    def __init__(self):
        global muxes
        self.output_nodes = []
        muxes = np.append(muxes, self)
    def __str__(self):
        return "mux: " + self.name + "# inputs: " + str(self.d_size()) + " datawidth: " + str(self.datawidth)
    def d_size(self):
        D = self.D
        print (str(D))
        #print("number of Ds " + str(len(D)))
        return len(D) #D.size()
    def s_size(self):
        S = self.S
        return len(S)
    #def datawidth(self):
    #    D = self.D
    #    return len(D.item(0))
    def print(self):
        print("mux: " + self.name + "# inputs: " + str(self.d_size()) + " datawidth: " + str(self.datawidth))
class select_op: 
    #NB select also has width of select to take into account
    id = 'select_op'
    name = ""
    D        = np.array([])
    CONTROL     = np.array([])
    Z           = np.array([])
    datawidth   = 0
    selectwidth = 0
    structurecount = 0
    def __init__(self):
        global selects
        self.output_nodes = []
        selects = np.append(selects, self)
    def __str__(self):
        return "select: " + self.name + " inputs: \n" + str((self.DATA)) + " \nselect:\n" + str((self.CONTROL)) +"\n datawidth = " +str(self.datawidth)+ " selectwidth = "+ str(self.selectwidth)
class connection:
    id = 'connection'
    name        = ''
    width       = 1
    depth       = 1
    widthoffset = 0
    def __init__(self):
        global connects
        connects = np.append(connects, self)
        self.connection_nodes = []
        self.init_connection_nodes()
    def init_connection_nodes(self):
        self.connection_nodes = [[node(j,i) for i in range(self.depth)] for j in range(self.width)] 
    def add_node_input_connection(self,i1, i2, l, index_type):
        #to increment l[4]
        add = 0
        if index_type == '':
            for i in range(self.width):
                li = l[:]
                li[4] = l[4] + add
                add = add+1
                for j in range(self.depth):
                    self.connection_nodes[i][j].add_input_connection(li)
                
        elif index_type == 'index':
            self.connection_nodes[i1-self.widthoffset][i2].add_input_connection(l)
        elif index_type == 'slice':
            for i in range(i2, i1):
                li = l[:]
                li[4] = l[4] + add
                self.connection_nodes[i-self.widthoffset][0].add_input_connection(li)
                add = add+1
                
    def add_node_output_connection(self,i1, i2, l, index_type,k):
        add = 0
        if index_type == '':
            for i in range(self.width):
                li = l[:]
                li[4] = l[4] + add
                k = li[4]
                for j in range(self.depth):
                    self.connection_nodes[i][j].add_output_connection(li,k)
                add = add+1
        elif index_type == 'bit':
            self.connection_nodes[i1-self.widthoffset][i2].add_output_connection(l,k)
        
        elif index_type == 'index':
            self.connection_nodes[i1-self.widthoffset][i2].add_output_connection(l,k)
        elif index_type == 'slice':
            for i in range(i2, i1):
                li = l[:]
                li[4] = l[4] + add
                k = li[4]
                self.connection_nodes[i][0].add_output_connection(li,k)
                add = add+1
class assign:
    id = 'assign'
    lhs = ''
    rhs = ''
    i1 = 0
    i2 = 0
    lhs = None
    rhs = None
    rhs_i1 = 0
    rhs_i2 = 0
    def __init__(self):   
        global assigns
        assigns = np.append(assigns,self)
    #    self.lhs = lhs
    #    self.rhs = rhs
class node:
    id = 'node'
    def __init__(self,i1, i2):
        self.connected_inputs      = []
        self.connected_outputs     = []
        self.i1 = i1
        self.i2 = i2
        self.constant = False
    def add_input_connection(self,l):
        self.connected_inputs.append(l)
    def add_output_connection(self,l,j):
        self.connected_outputs.append(l)
        connected_object_handle = l[0]
        if l[2] != 'reg':
            #add output node to connected object
            connected_object_handle.output_nodes[j] = self
        else: 
            #add output node to register
            connected_object_handle.output_nodes_q[0] = self

            connected_object_handle.output_nodes_qn[0] = self
    def print(self):
        print("Node:")
        print("\tinputs")
        print(self.connected_inputs)
        print("\toutputs:")
        print(self.connected_outputs)
        print("Endnode")
class input_obj():
    id      = 'input'
    name    = ""
    width   = 1
    depth = 1
    widthoffset = 0
    def __init__(self):
        global inputs
        inputs = np.append(inputs, self)
        self.connection_nodes  = []
    def init_connection_nodes(self):
        #print("\ninitializing connection nodes")
        self.connection_nodes = [[node(j,i) for i in range(self.depth)] for j in range(self.width)] 
        #print(self.connection_nodes)
    def add_node_input_connection(self,i1, i2, l, index_type):
        add = 0
        if index_type == '':
            if (i1 == -1 and i2 == -1):
                for i in range(self.width):
                    li = l[:]
                    li[4] = l[4] + add
                    for j in range(self.depth):
                        #print("added input connection with l[4]: "+str(li[4]))
                        self.connection_nodes[i][j].add_input_connection(li)
                    add = add+1

        elif index_type == 'index':
            self.connection_nodes[i1-self.widthoffset][i2].add_input_connection(l)
        elif index_type == 'slice':
            for i in range(i2, i1):
                li = l[:]
                li[4] = l[4] + add
                self.connection_nodes[i][0].add_input_connection(li)
                add = add+1
class output_obj():
    id      = 'output'
    name    = ""
    width   = 1
    depth = 1
    widthoffset = 0
    def __init__(self):
        global outputs
        outputs = np.append(outputs, self)
        self.connection_nodes = []
    def init_connection_nodes(self):
        #print("\ninitializing connection nodes")
        self.connection_nodes = [[node(j,i) for i in range(self.depth)] for j in range(self.width)] 
        #print(self.connection_nodes)
    def add_node_output_connection(self,i1, i2, l, index_type,k):
        add = 0
        if index_type == '':
            for i in range(self.width):
                li = l[:]
                li[4] = l[4] + add
                k = li[4]
                for j in range(self.depth):
                    self.connection_nodes[i][j].add_output_connection(li,k)
                add = add+1
                #print(add)
        elif index_type == 'bit':
            self.connection_nodes[i1-self.widthoffset][i2].add_output_connection(l,k)
        
        elif index_type == 'index':
            self.connection_nodes[i1-self.widthoffset][i2].add_output_connection(l,k)
        elif index_type == 'slice':
            for i in range(i2, i1):
                li = l[:]
                li[4] = l[4] + add
                k = li[4]
                self.connection_nodes[i][0].add_output_connection(li,k)
                add = add+1
    def add_node_input_connection(self,i1, i2, l, index_type):
        add = 0
        if index_type == '':
            if (i1 == -1 and i2 == -1):
                for i in range(self.width):
                    li = l[:]
                    li[4] = l[4] + add
                    for j in range(self.depth):
                        self.connection_nodes[i][j].add_input_connection(li)
                    add = add+1

        elif index_type == 'index':
            self.connection_nodes[i1-self.widthoffset][i2].add_input_connection(l)
        elif index_type == 'slice':
            for i in range(i2, i1):
                li = l[:]
                li[4] = l[4] + add
                self.connection_nodes[i][0].add_input_connection(li)
                add = add+1
class module:
    name = ""
    connection_point_string = ""
    def __init__(self, name):
        self.regs           = []
        self.nots           = []
        self.bufs           = []
        self.and2s          = []
        self.or2s           = []
        self.muxes          = []
        self.selects        = []
        self.connects       = []
        self.inputs         = []
        self.outputs        = []
        self.dependencies   = []
        self.shifters       = []
        self.comparators    = []
        self.xor2s          = []
        self.multipliers    = []
        self.subtractors    = []
        self.b_shifters     = []
        self.adders         = []
        self.shift_adders   = []
        self.divisors       = []
        self.assigns        = []
        self.name = name
        self.connection_points = []
    def set_lists(self):
        global regs      
        global nots      
        global bufs      
        global and2s     
        global or2s      
        global muxes     
        global selects   
        global connects  
        global inputs    
        global outputs   
        global dependencies
        global shifters
        global comparators
        global xor2s
        global multipliers
        global subtractors
        global b_shifters 
        global adders     
        global shift_adders
        global divisors  
        global assigns

        self.regs           = np.copy(regs        )
        self.nots           = np.copy(nots        )
        self.bufs           = np.copy(bufs        )
        self.and2s          = np.copy(and2s       )
        self.or2s           = np.copy(or2s        )
        self.muxes          = np.copy(muxes       )
        self.selects        = np.copy(selects     )
        self.connects       = np.copy(connects    )
        self.inputs         = np.copy(inputs      )
        self.outputs        = np.copy(outputs     )
        self.dependencies   = np.copy(dependencies)
        self.shifters       = np.copy(shifters    )
        self.comparators    = np.copy(comparators )
        self.xor2s          = np.copy(xor2s       )
        self.multipliers    = np.copy(multipliers )
        self.subtractors    = np.copy(subtractors )
        self.b_shifters     = np.copy(b_shifters  )
        self.adders         = np.copy(adders      )
        self.shift_adders   = np.copy(shift_adders)
        self.divisors       = np.copy(divisors    )
        self.assigns        = np.copy(assigns     )
    def set_connection_points(self):
        self.connection_point_string = self.connection_point_string.translate({ord(i): None for i in '\ \n'}) 
        #print(self.connection_point_string)
        connectionpoints = []
        for key, rx in rx_dict_module_connections.items():
            match = rx.findall(self.connection_point_string) #rx.findall(line)
            #print("found "+str(len(match))+" matches in modulestring")
            if match:
                #print(str(match))
                for m in match:
                    if (m[0] == ''): connectionpoints.append(tuple([m[2]]))
                    else:
                        l =  m[1].translate({ord(i): None for i in '}{'}) 
                        l = l.split(',')
                        connectionpoints.append(tuple([m[0], l]))
                #connectionpoints.append(match)
        #print(connectionpoints)
        self.connection_points = connectionpoints
class dependency: 
    #name of instantiation
    id = 'dep'
    name = ""
    #modulename
    modulename = ""
    module_handle = None
    possible_HINST = False
    def __init__(self):
        global dependencies
        dependencies = np.append(dependencies, self)
        self.connections = []
    def add_connections(self, list):
        self.connections.append(list)
class shift_op:
    id = 'shift_op'
    name = ''
    A = 0
    SH = 0
    Z = 0
    a_width = 0
    sh_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global shifters
        shifters = np.append(shifters,self)
        self.output_nodes = []
class comp_op:
    id = "comp_op"
    name = ""
    A = 0
    B = 0
    Z = 0
    a_width = 0
    b_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global comparators 
        comparators = np.append(comparators, self)
        self.output_nodes = []
        #print("Made comparator")
class sub_op:
    id = "sub_op"
    name = ""
    A = 0
    B = 0
    Z = 0
    structurecount = 0
    def __init__(self):
        global subtractors 
        subtractors = np.append(subtractors, self)
        self.output_nodes = []
        #print("made subtractor")
class add_op:
    id = "add_op"
    name = ""
    A = 0
    B = 0
    Z = 0
    a_width = 0
    b_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global adders
        adders = np.append(adders, self)
        self.output_nodes = []
        #print("made adder")
class mult_op:
    id = "mult_op"
    name = ""
    A = 0
    B = 0 
    Z = 0
    a_width = 0
    b_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global multipliers
        multipliers = np.append(multipliers, self)
        self.output_nodes = []
        #print("made multiplicator")
class div_op:
    id = "div_op"
    name = ""
    A = 0
    B = 0 
    Z = 0
    a_width = 0
    b_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global divisors
        divisors = np.append(divisors, self)
        self.output_nodes = []
        #print("Made divisor")
class b_shift_op:
    id = "b_shift_op"
    name = ""
    A = 0 
    SH = 0
    Z = 0
    a_width = 0
    sh_width = 0
    z_width = 0
    structurecount = 0
    def __init__(self):
        global b_shifters
        b_shifters = np.append(b_shifters, self)
        self.output_nodes = []
        #print("made barrelshift")
class shift_add_op:
    #dont know what content should be here, may need to implement as I go if I encounter it during testing
    id = "shift_add_op"
    name = ""
    structurecount = 0
    def __init__(self):
        global shift_adders
        shift_adders = np.append(shift_adders, self)
        self.output_nodes = []
        #print("Made shift adder")


#dictionaries containing regular expressions to handle different constructs from the elaborated systemverilog
rx_dict_module_start = {
    'begin'     : re.compile(r"module\s+(\S+)")
}
rx_dict_objectconnection = {
    'bit'       : re.compile(r"(1'b\d)"),
    'connect'   : re.compile(r"(\S+)(?:\[(\d{1,4})\])?(?:\[(\d{1,4})\])?")
}
rx_dict_start = { 
    'register'      : re.compile(r"\\\*\*SEQGEN\*\*\s+(\S+)\s" ),
    'GTECH_OR2'     : re.compile(r"GTECH_OR2\s+(\S+)\s"),
    'GTECH_NOT'     : re.compile(r"GTECH_NOT\s+(\S+)\s"),
    'GTECH_BUF'     : re.compile(r"GTECH_BUF\s+(\S+)\s"),
    'GTECH_AND2'    : re.compile(r"GTECH_AND2\s+(\S+)\s"),
    'GTECH_XOR2'    : re.compile(r"GTECH_XOR2\s+(\S+)\s"),
    'MUX_OP'        : re.compile(r"MUX_OP\s+(\S+)\s"),
    'SELECT_OP'     : re.compile(r"SELECT_OP\s+(\S+)\s"),
    #TODO: mux add, sub,mult, shifts and compares remain at least...
    #all of these can be single bit or multibit. if square brackets before name
    #multi, else single (group capture?)
    'input'         : re.compile(r"(input)\s+(?:\[(\d{1,3}):(\d{1,3})\])?"),
    'output'        : re.compile(r"(output)\s+(?:\[(\d{1,3}):(\d{1,3})\])?"),
    'wire'          : re.compile(r"(wire)\s+(?:\[(\d{1,3}):(\d{1,3})\])?"),
    'dep'           : re.compile(r"(\S+)\s+(\S*u_\S+)\s*\("),
    'COMP_OP'       : re.compile(r"^\s*(?:EQ_UNS_OP|NE_UNS_OP|EQ_TC_OP|NE_TC_OP|GEQ_UNS_OP|GEQ_TC_OP|LEQ_UNS_OP|LEQ_TC_OP|GT_UNS_OP|GT_TC_OP|LT_UNS_OP|LT_TC_OP)\s+(\S+)\s"),
    'SUB_OP'        : re.compile(r"SUB_(?:UNS_OP|UNS_CI_OP|TC_OP|TC_CI_OP)\s+(\S+)\s"),
    'ADD_OP'        : re.compile(r"ADD_(?:UNS_OP|UNS_CI_OP|TC_OP|TC_CI_OP)\s+(\S+)\s"),
    'MULT_OP'       : re.compile(r"MULT_(?:UNS_OP|TC_OP)\s+(\S+)\s"),
    'DIV_OP'        : re.compile(r"(?:DIV|MOD|REM|DIVREM|DIVMOD)_(?:UNS|TC)_OP\s+(\S+)\s"), #only div in Yoda
    'SHIFT_OP'      : re.compile(r"(?:ASH|ASHR|SRA)_(?:UNS|TC)_(?:UNS|TC|OP)(?:_OP)?\s+(\S+)\s"), 
    'B_SHIFT_OP'    : re.compile(r"BSH(?:_UNS_OP|_TC_OP|L_TC_OP|R_UNS_OP|R_TC_OP)\s+(\S+)\s"), #not in Yoda
    'SHIFT_ADD_OP'  : re.compile(r"(?:SLA_UNS_OP|SLA_TC_OP)\s+(\S+)\s"), #not in Yoda
    'assign'        : re.compile(r"assign\s([^=]+)")
    #'SRA'           :
}
rx_dict_dep_internals = {
    #'dep'   : re.compile(r"\(\s?(?:\.([^\(\s,]+)\(([^\(\);\s]*)\),?)+\s?\);")
    'dep'   : re.compile(r"\s?(?:\.(?P<connection_point>[^\(\s,]+)\((?P<connected_to>[^\(\);\s]*)\),?)\s?")
}
rx_dict_assign = {
    'rhs' : re.compile(r"=([^=]+);")
}
rx_dict_shift = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'SH'     : re.compile(r"\.SH\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_module_connections = {
    #'reconnect'   : re.compile(r"\s?((?:\.(?P<connection_point>[^\(\s,]+)\((?P<connected_to>[^\(\);\s]*)\)))[,\)]\s?")#|([^,\.\(\)\{\}\[\]]+)[,\)]\s?"),
    #'plain'       : re.compile(r"\s*([^\(\s,]+)\s?[,\)]")
    'connection' : re.compile(r"(?:[,\(]\.([^\(\),]+)\(([^\(\)]+)\))|(?:[,\(]([^\.][^\)\(,;]*))")
}
rx_dict_end = {
    #'end'   : re.compile(r"\);"),
    'semi'  : re.compile(r";") #hopefully this does not ruin anything and all semicolons are ends
}
rx_dict_in_out_wire = {
    'varname' : re.compile(r"[^\s,]+") #one or more char not whitespace comma
}
rx_dict_SELECT = {
    'DATA'      : re.compile(r"\.DATA\d{1,2}\(([^\)]*)\)"),
    'CONTROL'   : re.compile(r"\.CONTROL\d{1,2}\(([^\)]*)\)"),
    'Z'         : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_comp = {
    'A'             : re.compile(r"\.A\(([^\)]*)\)"),
    'B'             : re.compile(r"\.B\(([^\)]*)\)"),
    'QUOTIENT'      : re.compile(r"\.QUOTIENT\(([^\)]*)\)")
}
rx_dict_SUB_ADD_MULT = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'B'     : re.compile(r"\.B\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_MUX = {
    'D'     : re.compile(r"\.D\d{1,2}\(([^\)]*)\)"), # SEEMS TO BE SOME THAT HAS UP TO D31 AS D INPUTS. HOW DO i HANDLE THese VARYING THINgS
                                                    # ALSO SOME ONLY GOING TO D3 BUT ATTACHING 5 BIT TO EACH D data width of d varies, number of D inputs varies
    'S'     : re.compile(r"\.S\d{1,2}\(([^\)]*)\)"), # make arrays for the mux
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_BUF = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_NOT = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_AND2  = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'B'     : re.compile(r"\.B\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_OR2 = {
    'A'     : re.compile(r"\.A\(([^\)]*)\)"),
    'B'     : re.compile(r"\.B\(([^\)]*)\)"),
    'Z'     : re.compile(r"\.Z\(([^\)]*)\)")
}
rx_dict_reg = {
    'clear'           : re.compile(r"\.clear\(([^\)]*)\)"),
    'preset'          : re.compile(r"\.preset\(([^\)]*)\)"),
    'next_state'      : re.compile(r"\.next_state\(([^\)]*)\)"),
    'clocked_on'      : re.compile(r"\.clocked_on\(([^\)]*)\)"),
    'data_in'         : re.compile(r"\.data_in\(([^\)]*)\)"),
    'enable'          : re.compile(r"\.enable\(([^\)]*)\)"),
    'Q'               : re.compile(r"\.Q\(([^\)]*)\)"),
    'QN'              : re.compile(r"\.QN\(([^\)]*)\)"),
    'synch_clear'     : re.compile(r"\.synch_clear\(([^\)]*)\)"),
    'synch_preset'    : re.compile(r"\.synch_preset\(([^\)]*)\)"),
    'synch_toggle'    : re.compile(r"\.synch_toggle\(([^\)]*)\)"),
    'synch_enable'    : re.compile(r"\.synch_enable\(([^\)]*)\)")
}

#process module instantiations
def process_dependencies():
    for top_module in modules:
        set_global_lists(top_module)
        #found_dep = False
        for dep in top_module.dependencies:
            found_dep = False
            #print("Looking for "+dep.modulename+" in dependencies")
            modulename = dep.modulename
            #find modulename in module list
            for dep_module in modules:
                if dep_module.name == modulename:
                    found_dep = True
                    dep.module_handle = dep_module
                    module_connection_list = dep_module.connection_points
                    for dependency_connection_tuple in dep.connections[0]:
                        #print(dependency_connection_tuple)
                        cleaned_dependency_connection_point = dependency_connection_tuple[0].translate({ord(i): None for i in '\ '})
                        found = False
                        for module_connection_tuple in module_connection_list:  
                            if cleaned_dependency_connection_point == module_connection_tuple[0]:
                                #print("Found connection point matching "+cleaned_dependency_connection)
                                found = True
                                cleaned_dep_connectionlist = dependency_connection_tuple[1].translate({ord(i): None for i in '}{\ '}) 
                                cleaned_dep_connectionlist = cleaned_dep_connectionlist.split(',')
                                #connect to module_connection_point[1] if list is that long, or just module_connection_point[0]
                                for i in range(len(cleaned_dep_connectionlist)):
                                    if len(module_connection_tuple) > 1:
                                        i1, i2, module_connection, typeindex = find_indexes(module_connection_tuple[1][i])
                                    else: 
                                        #print(module_connection_tuple)
                                        i1, i2, module_connection, typeindex = find_indexes(module_connection_tuple[0])
                                    
                                    dep_handle, found_dep = search_list(dep_module.inputs, module_connection)
                                    if found_dep: 
                                        #connectiontype = 'input'
                                        #print("adding dep to module connection")
                                        print("sending "+str(cleaned_dep_connectionlist[i])+" into process match")
                                        dataN, datawidth, processed_matchlist = process_match([cleaned_dep_connectionlist[i]], dep_handle, 'input', 'dep' )
                                        
                                        #look for matching input to set as output_node
                                        
                                        #connect dep.module_handle input to correct input 
                                        #if object_handle.module_handle != None:
                                            #dep_module.inputs
                                            
                            
                                    else: 
                                        dep_handle, found_dep = search_list(dep_module.outputs, module_connection)
                                        #print(dep_connection)
                                        if found_dep:
                                            #print("adding dep to module connection")
                                            #connectiontype = 'output'
                                            dataN, datawidth, processed_matchlist = process_match([cleaned_dep_connectionlist[i]], dep_handle, 'input', 'dep')
                                        else: 
                                            
                                           # print("Connection: "+module_connection_tuple[1][i])
                                            #print("could not find connection in inputs or outputs of dep: "+dep_module.name)
                                            print("Did not find dep "+dep_module.name)
                                            #print_list_names(dep_module.outputs)
                                            #print_list_names(dep_module.inputs)
                        
                        #DEP NOT FOUND IN MODULES, MAYBE HINST
                        if found == False:
                            dep.possible_HINST = True
                            #print("Did not find "+cleaned_dependency_connection)
                            #pass
                        #dep_handle, found_bool = search_list(mod.inputs, clean_connection)

                        
                        #if found_bool:
                        #    #it is input to module, add to connection of rhs connection objects
                        #    #print("Found "+connection[0]+" in inputs. Trying to add")
                        #    dataN, datawidth, processed_matchlist = process_match([connection[1]], dep_handle, 'input', 'dep' )
                        #else:
                        #    dep_handle, found_bool = search_list(mod.outputs, clean_connection)
                        #    if found_bool:
                        #        #print("Found "+connection[0]+" in inputs. Trying to add")
                        #        #add connection as outputs¨
                        #        dataN, datawidth, processed_matchlist = process_match([connection[1]], dep_handle, 'output', 'dep' )
                        #    #print("found connection "+connection[0]+" in outputs")
                        #if found_bool == False:
                        #    print("Did not find "+str(clean_connection)+" in in or outputs of module"+ mod.name)
                        #    print_list_names(mod.inputs)
            if found_dep == False:
                print("Did not find dep: "+dep.modulename)                  
        top_module.set_lists()
        empty_global_lists()
                #find dep ports in inputs or outputs

#print name of all objects in a list
def print_list_names(l):
    for e in l:
        print("\t"+e.name) 


#go structure heads and make structure trees
def connect_structure(module):
    global top_level_parents
    #i = 0
    for inp in module.inputs:
        #print(i)
        #i = 0
        #print(inp.name)
        for nl in range(len(inp.connection_nodes)):
            for n in range(len(inp.connection_nodes[nl])):
                #print(str(nl)+" "+str(n))
                structure_handle = structure(None, inp, nl)
                top_level_parents.append(structure_handle)
                connect_children(structure_handle,nl,n)
        #structure_handle.print()
        #print()
    for m in modules: 
        for reg in m.regs:
            #print(reg.name)
            structure_handle = structure(None, reg, 0)
            top_level_parents.append(structure_handle)
            connect_children(structure_handle, 0, 0)

    #for parent in top_level_parents:
    #    #if to manage when file to large
    #    #if parent.represented_object_handle.id == 'reg': 
    #    #    return
    #    print(parent.represented_object_handle.name)
    #    parent.print()
    #    print()
    #    #pass
              
#recursively connects all children to a parent and expand structure tree
def connect_children(parent, i1,i2):
    object_handle = parent.represented_object_handle

    #why this i1?
    i1 = parent.i1
    #if(i2>= 0):
        #print("parent: "+object_handle.id + " "+object_handle.name)
        #print("i1: "+str(i1)+" i2: "+str(i2))
    if object_handle.id != 'input' and object_handle.id != 'output':
        #Attempt to control loops?
        #if object_handle.structurecount > 2:
        #    if object_handle.id == 'gtech_or2' or object_handle.id == 'gtech_and2' or object_handle.id == 'gtech_xor2':
        #        return
        #if object_handle.structurecount > 1:
        #    if object_handle.id == 'gtech_not' or object_handle.id == 'gtech_buf':
        #        return
        #if object_handle.structurecount > 120:
        #    print(object_handle.name+"\tstructure count: "+str(object_handle.structurecount))
        datawidth_set = {'sub_op','select_op', 'mux_op', 'shift_op', 'add_op', 'mult_op', 'comp_op', 'div_op', 'b_shift_op', 'shift_add_op'}

        object_handle.structurecount = object_handle.structurecount+1
        #if object_handle.id in datawidth_set:
        #    if object_handle.id != 'mux_op' and object_handle.id != 'select_op':
        #        if object_handle.structurecount > object_handle.z_width*32:
        #            print(object_handle.name+" structure count "+str(object_handle.structurecount))
        #            return
        #    else:
        #        if object_handle.structurecount > object_handle.datawidth*32:
        #            print(object_handle.name+" structure count "+str(object_handle.structurecount))
        #            return

    global top_level_parents
    #print("Current object: "+object_handle.name)
    output_nodes = []
    output_nodes_q = []
    output_nodes_qn = []
    #print("parent: "+object_handle.name)
    if object_handle.id == 'output':
        output_nodes = []
    elif object_handle.id == 'reg':
        #if parent.parent == None or parent == None:
            #if register is taken here
            #top_level_parents.append(parent)
        #print("found reg")
        if object_handle.output_structure_taken == False:
            output_nodes_q = object_handle.output_nodes_q
            output_nodes_qn = object_handle.output_nodes_qn
            object_handle.output_structure_taken = True
        
        if parent != None:# and parent.connected_inputs[0] != None:
            if parent.parent != None:
                object_handle.has_parent = True
        #else:
        #    
        #    #print(output_nodes_q)
    elif object_handle.id == 'input':
        #print()
        #print(object_handle.name)
        #print("\nConnection_nodes:\t", end = '')
        #print(object_handle.connection_nodes)
        #print(i1)
        #print(i2)
        #print(object_handle.widthoffset)
        output_nodes.append(object_handle.connection_nodes[i1][i2])
        #print("appending input connection ")
        #print("i1: "+str(i1))
        #print("i2: "+str(i2))
    elif object_handle.id == 'comp_op':
        output_nodes = object_handle.output_nodes
    else:
        #print(i1)
        #print(object_handle.id)
        #if(object_handle.id == 'comp_op'):
        #    print(object_handle.z_width)
        #    print(object_handle.output_nodes)
        #print(i1)
        #print(object_handle.name)
        #print(object_handle.output_nodes)
        #print(len(object_handle.output_nodes))
        output_nodes = [object_handle.output_nodes[i1]]

        #ADDED to shorten recursion
        object_handle.output_nodes[i1] = parent
    #print(output_nodes)
    for node in output_nodes:
            #print(object_handle.id+" "+object_handle.name)
        #print(node)
        if node != None:
            if node.id == 'structure':
                #parent.children.append(node)
                #if node.represented_object_handle == parent.represented_object_handle:
                parent = node
                #for c in node.children:
                #    parent.add_child(c)
                #parent.structure_type = node.structure_type
                #parent.structure_connection_characteristic = node.structure_connection_characteristic
                #parent.powerStructure = node.powerStructure
                #set parent to be node:
                #parent = node
                return
            elif(node != None):
                #print(output_nodes)
                #print(object_handle.name)
                #if(object_handle.id == 'mux_op'): 
                #print(object_handle.output_nodes)
                #object_handle.output_nodes[0].print()
                for con in node.connected_inputs:
                    child_handle = con[0]
                    
                    #print("\tParent: "+object_handle.name)
                    #print("\tChild: "+child_handle.name)
                    #print(con)
                    structure_handle = structure(parent, child_handle, con[4])
                    added = parent.add_child(structure_handle)
                    if added:
                        structure_handle.structure_type = child_handle.id
                        structure_handle.structure_connection_characteristic = con[3]
                        #if(child_handle ==object_handle): print("oh no")
                        #if(i2>=0):
                            #print(con)
                            #print(node.i1)
                            #print(node.i2)
                        if con[2] == 'reg' and con[2] != 'control':
                            con[0].has_parent = True
                        if structure_handle.represented_object_handle.id != 'reg' and structure_handle.represented_object_handle.id != 'input':
                            structure_handle.represented_object_handle.output_nodes[0] = structure_handle
                        if(con[3] != 'control' and con[2] != 'reg' and con[2] != 'input'):
                            connect_children(structure_handle, con[4],node.i2)
                        elif(con[2] == 'input'):
                            #if input i2 needs to be set correctly
                            connect_children(structure_handle,con[4],con[5])#node.i2)
        else:
            pass #but probably should do something
            #print("None-connection to output of: "+object_handle.id)
    for node in output_nodes_q:
        #print(object_handle.id)
        #print(node)
        

        if(node != None):

            #if node.id == 'structure':
            #    #parent.children.append(node)
            #    #if node.represented_object_handle == parent.represented_object_handle:
            #    parent = node
            #    return

            for con in node.connected_inputs:
                child_handle = con[0]
                #print(con)
                #print(child_handle.name)
                #remove if if registers are to be part of this
                #if(child_handle.id != 'reg'): 
                structure_handle = structure(parent, child_handle, con[4])
                added = parent.add_child(structure_handle)
                if added:
                    structure_handle.structure_type = child_handle.id
                    structure_handle.structure_connection_characteristic = con[3]
                    if con[2] == 'reg' and con[2] != 'control':
                        con[0].has_parent = True
                    if structure_handle.represented_object_handle.id != 'reg' and structure_handle.represented_object_handle.id != 'input':
                        structure_handle.represented_object_handle.output_nodes[0] = structure_handle
                    if(con[3] != 'control' and con[2] != 'reg' and con[2] != 'input'):
                        connect_children(structure_handle, con[4],node.i2)
                    elif(con[2] == 'input'):
                        connect_children(structure_handle,con[4],con[5])
                #if con[2] == 'reg':
                #    con[0].has_parent = True
    for node in output_nodes_qn:
        #print(object_handle.id)
        #print(node)
        if(node != None):

            if node.id == 'structure':
                #parent.children.append(node)
                #if node.represented_object_handle == parent.represented_object_handle:
                parent = node

                return

            for con in node.connected_inputs:
                child_handle = con[0]
                #print(con)
                structure_handle = structure(parent, child_handle,con[4])
                added = parent.add_child(structure_handle)
                if added:
                    structure_handle.structure_type = child_handle.id
                    structure_handle.structure_connection_characteristic = con[3]
                    if con[2] == 'reg' and con[2] != 'control':
                        con[0].has_parent = True
                    if structure_handle.represented_object_handle.id != 'reg' and structure_handle.represented_object_handle.id != 'input':
                        structure_handle.represented_object_handle.output_nodes[0] = structure_handle
                    if(con[3] != 'control' and con[2] != 'reg' and con[2] != 'input'):
                        connect_children(structure_handle, con[4],node.i2)
                    elif(con[2] == 'input'):
                        connect_children(structure_handle,con[4],con[5])
                    
                #if con[2] == 'reg':
                #    con[0].has_parent = True
    #print("}")

#structure tree class
class structure:
    structure_type = ''
    structure_connection_characteristic = ''
    id = 'structure'
    def __init__(self, parent, represented_object_handle, i1):
        self.parent = parent
        self.children = []
        self.represented_object_handle = represented_object_handle
        self.i1 = i1
        self.powerStructure = None
        #if self.represented_object_handle.id != 'reg' and self.represented_object_handle.id != 'input':
        #    represented_object_handle.output_nodes[0] = self
    def add_child(self, child):
        #foundchild = False
        if child.represented_object_handle == self.represented_object_handle:
                return False
        for c in self.children:
            if c.represented_object_handle == child.represented_object_handle:
                return False
        self.children.append(child)
        return True
    def print(self):
        #print(self.represented_object_handle.id+", ",end = '')
        if self.children != []: print("{", end = '')
        for child in self.children:
            #print(self.represented_object_handle.id+", ",end = '')
            #print( )
            #print(child.represented_object_handle.id+" "+child.represented_object_handle.name+" ,",end = '')
            print(child.represented_object_handle.id+" ,",end = '')
            child.print()
        
        if self.children != []: print("}", end = '')
        #for child in self.children:
        #    child.print()
    def __repr__(self, level=0):
        ret = "\t"*level+repr(self.represented_object_handle.id)+"\n"
        if level < 11:
            for child in self.children:
                ret += child.__repr__(level+1)
        return ret

#calls all the functions in the right order to create the structural representation
def run_parse_elab(filename):
    parse_file(filename)
    for m in modules:
        m.set_connection_points()
    #top_level_parents = []
    process_dependencies()

    connect_structure(modules[0])

    #need to also count module instantiations with no content- assume hinst 
    count_gates(modules[0])
    print_gates()
    return modules, top_level_parents

#count gates in representation
def count_gates(module):
    global reg_n          
    global not_n      
    global buf_n        
    global and2_n        
    global or2_n         
    global mux_n         
    global select_n          
    global shift_n      
    global comp_n     
    global xor2_n         
    global mult_n     
    global sub_n      
    global b_shift_n    
    global add_n        
    global shift_add_n  
    global div_n      
    m = module  
    if m != None:
        for r in m.regs:
            if r.output_nodes_q[0] != None or r.output_nodes_qn[0] != None:
                if r.has_parent:
                #print(r.name) 
                    reg_n       =  reg_n +1
                #else:
                   # reg_n = reg_n+1
        not_n       =  not_n           + len(m.nots        )
        buf_n       =  buf_n           + len(m.bufs        )
        and2_n      =  and2_n          + len(m.and2s       )
        or2_n       =  or2_n           + len(m.or2s        )
        mux_n       =  mux_n           + len(m.muxes       )
        select_n    =  select_n        + len(m.selects     )
        shift_n     =  shift_n         + len(m.shifters    )
        comp_n      =  comp_n          + len(m.comparators )
        xor2_n      =  xor2_n          + len(m.xor2s       )
        mult_n      =  mult_n          + len(m.multipliers )
        sub_n       =  sub_n           + len(m.subtractors )
        b_shift_n   =  b_shift_n       + len(m.b_shifters  )
        add_n       =  add_n           + len(m.adders      )
        shift_add_n =  shift_add_n     + len(m.shift_adders)
        div_n       =  div_n           + len(m.divisors    )
        for d in module.dependencies:
            m = d.module_handle
            count_gates(m)

#print gate counts
def print_gates():
    print("regs\t\t"+ str(reg_n      )) 
    print("muxes\t\t"+ str(mux_n      )) 
    print("nots\t\t"+ str(not_n      )) 
    print("bufs\t\t"+ str(buf_n      ))     
    print("arithmetic:\t"+str(mult_n+sub_n+add_n+shift_add_n+div_n))
    print("logic:\t\t"+str(and2_n+or2_n+shift_n+comp_n+xor2_n+b_shift_n))
    
    print("selects\t\t"+ str(select_n   )) 
    print()
    print("Total:\t\t "+str(reg_n+not_n+buf_n+and2_n+or2_n+mux_n+select_n+shift_n+comp_n+xor2_n+mult_n+sub_n+b_shift_n+add_n+shift_add_n+div_n))


