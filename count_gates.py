#assume cell name does not contain underscores, and that module names do? 

import re
import sys

filename = sys.argv[1]

cell = re.compile(r"([^\s\)\(_])+\s(\S+)\s*\(")
reg = re.compile(r"DF[C|S|Q|N][N|D|C]")

retention = re.compile(r"RSDFCR")
beginModule = re.compile(r"module\s(\S+)")
endmodule = re.compile(r"endmodule")
dependency = re.compile(r"^\s*(\S+)\s+(\S*u_\S+)\s*")
mux = re.compile(r"^\s*(MUX.*)\s+\S+")
#and_g = re.compile(r"")
inverter = re.compile(r"INV")
buffer = re.compile(r"(BUF|CKBD)")
arithm = re.compile(r"[H|F]A1D")
filler = re.compile(r"FILL")
tie = re.compile(r"TIE[H|L]")
latch = re.compile(r"(L[H|N]Q)")
delc = re.compile(r"^\s*DEL")
decap = re.compile(r"CAP")

#reg2 = re.compile(r"DFSN")
modules = []
instantiations = []
class module:
    name = ''
    cellcount = 0 
    registercount = 0
    logiccount = 0
    muxcount = 0
    retention_reg_count = 0
    buffcount = 0
    invcount = 0
    arithm = 0
    otherscount = 0
    def __init__(self, name):
        self.dependency_strings = []
        self.dependency_list = []
        global modules
        self.name = name
        modules.append(self)
#open file
with open(filename, 'r') as svfile:
        line = svfile.readline()
        linenum = 1
        in_module = False
        module_handle = None
        #go through file line for line and add 1 to count if match to cell regex
        while line:
            if in_module:
                if endmodule.search(line):
                    in_module = False
                else:
                    #look for cells and deps
                    match = dependency.search(line)
                    if match:
                        #is dep add group to list
                        module_handle.dependency_strings.append(match.group(1))
                        #print("Added dependency: "+match.group(1))
                    elif retention.search(line):
                        module_handle.retention_reg_count = module_handle.retention_reg_count +1
                    elif (reg.search(line) or latch.search(line)): 
                            module_handle.registercount = module_handle.registercount +1
                    elif mux.search(line):
                        module_handle.muxcount = module_handle.muxcount +1
                    elif buffer.search(line):
                        module_handle.buffcount = module_handle.buffcount +1
                    elif inverter.search(line):
                        module_handle.invcount = module_handle.invcount +1
                    elif arithm.search(line):
                        module_handle.arithm = module_handle.arithm +1
                    elif (cell.search(line)):
                        #add capture group to list of all captured groups
                        #add count to specific cell group
                        if filler.search(line) or tie.search(line) or delc.search(line) or decap.search(line):
                            module_handle.otherscount = module_handle.otherscount +1 #pass
                        else:
                            module_handle.cellcount = module_handle.cellcount +1
                        
            else:
                match = beginModule.search(line)
                if match:
                    in_module = True
                    module_handle = module(match.group(1))
                    #print("In module: "+match.group(1))
            line = svfile.readline()


#for m in modules look for dependency string and replace it with module handle
def find_depstrings(module):
    #print("looking for deps of module: "+module.name)
    global instantiations
    instantiations.append(module)
    for d in module.dependency_strings:
        #print("looking for dep "+d)
        item = search_list(d, modules)
        if item != None:
            #print("Found dep "+ d)
            module.dependency_list.append(item)
            find_depstrings(item)
        else:
            print("did not find dep: "+d)
            

#go through module dependencies recursively and sum together all counts
def count_cells():
    print(instantiations)
    cellcount               = 0
    registercount           = 0
    retention_reg_count     = 0
    muxcount                = 0
    invcount                = 0
    buffcount               = 0
    arithmcount             = 0
    otherscount = 0
    for inst in instantiations:
        #print(inst.name)
        cellcount           = cellcount + inst.cellcount
        registercount       = registercount + inst.registercount
        retention_reg_count = retention_reg_count + inst.retention_reg_count
        muxcount            = muxcount + inst.muxcount
        buffcount           = buffcount + inst.buffcount
        invcount            = invcount + inst.invcount
        arithmcount         = arithmcount + inst.arithm
        otherscount         = otherscount + inst.otherscount
    
    print("regcount:\t"+str(registercount))
    print("ret reg count:\t"+str(retention_reg_count))
    
    print("muxes:\t\t"+str(muxcount))
    
    print("inverters:\t"+str(invcount))
    print("buffcount:\t"+str(buffcount))
    print("arithmetic:\t"+str(arithmcount))
    print("logic:\t\t"+str(cellcount))
    print("others:\t\t"+str(otherscount))
    print()
    print("total:\t\t"+str(registercount+retention_reg_count+muxcount+invcount+buffcount+arithmcount+cellcount+otherscount))


def search_list(string, modulelist):
    for item in modulelist:
        if item.name == string:
            return item
    return None

find_depstrings(modules[0])
count_cells()