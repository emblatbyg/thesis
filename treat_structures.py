import parse_elab
#import count_gates
import liberty_data
import sys 

filename = sys.argv[1]



#print(modules[0].name)
#liberty_data.set_cells_and_environment()
#list of all cells from the cell library
cellLib = liberty_data.sort_cells(liberty_data.processed_library_path)

#print(cells[0])
powerStructures = []

#iterate through structures
def go_through_structures():
    modules, top_structures = parse_elab.run_parse_elab(filename)
    for s in top_structures:
        #iterate through structure
        #s.print()
        #print()
        #when sequence of structure elements without fanout, save in variable until fanout
        #l = [s.structure_type]
        #print("calling from top")
        #l = [s.represented_object_handle.id]
        #st = liberty_data.transform_list(cellLib,l)
        #if s.represented_object_handle == 'reg' and s.represented_object_handle.has_parent == False:
        #    pass
        #else:
        p = power_structure(s)
        p.parent = None
        p.name = s.represented_object_handle.name
        powerStructures.append(p)
        #print()
        elementlist = liberty_data.transform_list(cellLib,[s.represented_object_handle.id])
        p.cell_lib_list = elementlist
        p.structural_rep_list = [s]
        #print(s.represented_object_handle.name)
        #print(s.represented_object_handle.id+" ",end='')
        #s.print()
        #print()
        #p.print()
        #print()
        #pass
        srepr = repr(s)
        print(s.represented_object_handle.name)
        print(srepr)
        count_powerStructure(p)
        lists_from_top(s,p)
    for p in powerStructures:
        
        print(p.name)
        #v = value()
        #p.print(v, 0)
        #print()

        r = repr(p)
        print(r)
    print_powercount()
    #print_stuff(top_structures)
#compare with lists in cellib starting with the longest sequences and then shortening down

#replace gates with match if found

#recursive function: append to list as long as # children = 1
#return handle to structure object that has next fanout
# go recursively while there is children.
# every time there is fanout, need to return and handle list
# replace lists in structure?
# 

# While children:
# for each child:
# go through structure and append structure type to list until fanout 
# return list and handle to structure with more children
def print_stuff(top_structures):
    for s in top_structures:
        print("Top structure: ")
        print(s.represented_object_handle.name)
        print("Children:")
        for c in s.children:
            print("\t"+c.represented_object_handle.name)
            #print("\tlvl3: ")
            for gc in c.children:
                print("\t\t"+gc.represented_object_handle.name)
                for ggc in gc.children:
                    print("\t\t\t"+ggc.represented_object_handle.name)


def lists_from_top(s, power_s):
    #print(s.represented_object_handle.name)

    l = []
    #while s != None:   
    st = None
    for c in s.children:
        #s = c
        #l = []
        #structure_list = []
        #add_s_list = []
        ##goes through structure elements until fanout
        #st = add_structure(l, structure_list, c, add_s_list)
        ##print("\t",end='')
        ##print(l)
        ##go through cell lists compare to l
        #elementlist = liberty_data.transform_list(cellLib,l)
        #make power structure object with s as parent
        #p = power_structure(s, structure_list, elementlist)
        #power_s.children.append(p)
        if c.powerStructure == None:
            l = []
            structure_list = []
            add_s_list = []
            #goes through structure elements until fanout
            st = add_structure(l, structure_list, c, add_s_list)
            #print("\t",end='')
            #print(l)
            #go through cell lists compare to l
            elementlist = liberty_data.transform_list(cellLib,l)

            p = power_structure(power_s)
            for s in structure_list:
                s.powerStructure = p
            power_s.children.append(p)
            p.structural_rep_list = structure_list
            p.cell_lib_list = elementlist
            #count_powerStructure(p)
            #if output_nodes[0] == None or is reg
            if c.structure_connection_characteristic != 'control':
                #if c.represented_object_handle.output_nodes[0] != None:
                count_powerStructure(p)
            for add_l in add_s_list:
                #after fanout, go through children until fanout...
                #for c in st.children:
                lists_from_top(add_l, p)
        else: 
            p = c.powerStructure
            power_s.children.append(p)
        
        #for e in elementlist:
        #    print(e.matching_key)
        #if st != None:
        #for add_l in add_s_list:
        #    #after fanout, go through children until fanout...
        #    #for c in st.children:
        #    lists_from_top(add_l, p)

def add_structure(l, structure_list, s, s_list):
    
    #look at what rep obj handle is and change it if select, add etc
    l.append(s.represented_object_handle.id)
    structure_list.append(s)
    #print("\t"+s.represented_object_handle.name)
    if len(s.children) == 1 and s.children[0] != None:
        #print(s.represented_object_handle.name)
        add_structure(l, structure_list, s.children[0], s_list)
    elif len(s.children) == 0:
        #no child 
        return None
    else:
        #append to structure children?
        #return handle to structure with fanout and list appended to recursively
        #only returning most recent s.... not all structure paths will be included.
        #recursive call to add structure do not save s.
        #s_list has all info, not s.
        s_list.append(s)
        return s

#save first elements parent, and last elements children,
#envelop with structure having old objects in list and new objects in list
class power_structure:
    name = ''
    countedBool = False
    def __init__(self, parent):#, structural_rep_list, cell_lib_list):
        self.structural_rep_list    = []#structural_rep_list
        self.cell_lib_list          = []#cell_lib_list
        self.children               = []
        self.parent                 = parent
    #def printstart(self):
    #    for c in self.cell
    def print(self, depth, startlvl):
        
        #print(self.represented_object_handle.id+", ",end = '')
        #if self.children != []: print("{", end = '')
        #print("{ ", end = '')
        if self.cell_lib_list != []: 
            print("{", end = '')
            depth.i = depth.i+1
        #if self.children != []: print("{", end='')
        for c in range(len(self.cell_lib_list)):
            if c+1 == len(self.cell_lib_list):
                print(self.cell_lib_list[c].matching_key+" ",end = '')
                if self.children != []: 
                    depth.i = depth.i+1
                    print("{", end = '')
                #else:
                #    if lastchild: print("}", end = '')
            else:    
                print(self.cell_lib_list[c].matching_key+" {",end = '')
                depth.i = depth.i +1
        #if self.cell_lib_list != []:
        #    print("}", end = '')
        
        #elif (len(self.children))
        #if self.children != []: 
        #    print("{", end='')
        #childbracketcount = len()
        
        for child in range(len(self.children)):
            #print(self.represented_object_handle.id+", ",end = '')
            if child+1 == len(self.children):
                self.children[child].print(depth, depth.i)
            else:
                self.children[child].print(depth, depth.i)
            #if self.children[child].children == []:
            #    print("}",end='')
                #childbracketcount = childbracketcount-1
            #else:
            #    print(", ", end= '')
        
        #if lastchild: print("}",end='')
        #if self.children == []: print("}",end='')
        #if self.children != []: print("}", end='')
        #if self.cell_lib_list != [] and self.children == []: 
        #    print("}", end = '')
        #    depth.i = depth.i -1
        
        while depth.i != startlvl:
            print("}", end = '')
            depth.i = depth.i-1
        #if self.children != []: print("}", end='')
        #if self.cell_lib_list == []:
        #    print("}", end = '')
        #print( )
        #print("}", end = '')
            #for c in child.cell_lib_list:
            #    print(c.matching_key+" ,",end = '')

    def __repr__(self, level=0):
        value = ''
        for v in self.cell_lib_list:
            value = value+v.matching_key+" "
        ret = "\t"*level+repr(value)+"\n"
        if level < 11:    
            for child in self.children:
                ret += child.__repr__(level+1)
        return ret
class value:
    i = 0
        #if self.children == []: print("}", end = '')

nots    = 0
logic   = 0
mux     = 0
arithm  = 0
comp    = 0
regs     = 0
def count_powerStructure(s):
    notstruct = {'not'}
    logicstruct = {'and5', 'nor5', 'or5', 'xor5', 'xnor5', 'nand5', 'oa221', 'ao221', 'andor22' ,'andori31' ,'andor31' ,'ind4', 'and4','nor4','nand4','xnor4','xor4','orand211','or4','iinor4','andor211', 'and3','nand3','inand3','nor3','inor3','iao21','or3','xor3','andori21' ,'orand21','xnor3','iorand21' ,'andori222','and2' ,'ind2' ,'nand2','nor2' ,'xnor2','or2'  ,'xor2' ,'inor2'  }
    regstruct = {'reg'}
    muxstruct = {'mux', 'mux2n'}
    arithmstruct = {'adder', 'mult'}
    compstruct = {'comp'}
    global nots   
    global logic  
    global mux    
    global arithm 
    global comp   
    global regs   
    #print(s.cell_lib_list)
    str_rep_offset = 0
    strlist2 = []
    removestruct = {'input', 'output', 'gtech_buf'}
    if s.countedBool == False:
        for obj in s.structural_rep_list:
            h = obj.represented_object_handle
            if h.id in removestruct:
                pass
            else:
                strlist2.append(obj)
        s.countedBool = True
        for cellindex in range(0,len(s.cell_lib_list)):
            #print(s.cell_lib_list)
            #for c in s.cell_lib_list:
            #    print(c.matching_key)
            cell = s.cell_lib_list[cellindex]
            #print("new cellindex:")
            #print(cell.matching_key)
            #print(len(s.cell_lib_list))
            #print(str_rep_offset)
            #print(cellindex)
            structure = strlist2[cellindex+str_rep_offset]
            handle = structure.represented_object_handle
            #print(structure)
            #print(handle.id)

            handle = structure.represented_object_handle

            str_rep_offset = str_rep_offset + len(cell.synthetic_gate_list)-1

            if handle.id == 'reg' :#and structure.structure_connection_characteristic != 'control':
                #if handle.output_nodes_q[0] != None or handle.output_nodes_qn[0] != None:
                if handle.has_parent:
                    if cell.matching_key in regstruct and cellindex < 1:
                            regs = regs +1
                            print("added reg")
            elif handle.id != 'input' and handle.id != 'output' and structure.structure_connection_characteristic != 'control':
                if handle.output_nodes[0] != None:
                    if cell.matching_key in notstruct:
                        nots = nots+1
                        print("added not")
                    elif cell.matching_key in logicstruct:
                        logic = logic+1
                        print("added logic")
                    elif cell.matching_key in muxstruct:
                        mux = mux+1
                        print("added mux")
                    elif cell in arithmstruct:
                        arithm = arithm +1
                        print("added arithm")
                    elif cell.matching_key in compstruct:
                        comp = comp+1
                        print("added comp")

#need to find a good way to count so not multiplied.... structure... make objects?
def print_powercount():
    print("nots:\t"+str(nots))
    print("regs:\t"+str(regs))
    print("logic:\t"+str(logic))
    print("mux:\t"+str(mux))    
    print("arithm:\t"+str(arithm))
    print("comp:\t"+str(comp))
    print("total:\t"+str(nots+logic+mux+arithm+comp+regs))
go_through_structures()

