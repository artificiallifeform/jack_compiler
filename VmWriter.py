from math_ops import operations, negation

class VmWriter:
    def __init__(self):
        self.className = ''
        self.segments = []
        self.operands = []      
        # Array of all commands
        self.vmCode = []

        self.whileInc = 0
        self.ifInc = 0
        self.whileStack = []
        self.ifStack = []

        self.index = 0


        self.compound_arr = []

    def set_className(self, name):
        self.className = name

    def write_expression(self, array=False):
        self.cond = True
        
        while (self.cond):
            self.__exp()
        
        if array:
            array_exp = ''
            for op in self.compound_arr:
                array_exp += op + '\n'
            return array_exp
            
        self.vmCode.extend(self.compound_arr)
        self.compound_arr = []
        # Added on top. If program break, maybe because of this line
        self.operands = []
        self.index = 0

    def __exp(self):
        if (self.index == len(self.operands)):
            self.cond = False
            return

        temp = self.operands[self.index]

        if temp == 'neg' or temp == 'not':
            self.index += 1
            self.__exp()
            self.compound_arr.append(temp)
        elif temp == '(':
            self.index += 1
            while self.operands[self.index] != ')':
                self.__exp()
            self.index += 1
            return
        elif temp in operations:
            self.index += 1
            self.__exp()
            self.compound_arr.append(operations[temp])
        else:
            self.compound_arr.append(temp)
            self.index += 1
            return

    
    def add_operand(self, operand):
        self.operands.append(operand)
    

    # def get_array_exp(self):
    #     print("From newly created ob", self.operands)
    #     for op in self.operands:
    #         array_exp += op + '\n'
    #     return array_exp
            
    def increment_while(self):
        self.whileStack.append(self.whileInc)
        self.whileInc += 1
        return self.whileStack[-1]

    def increment_if(self):
        self.ifStack.append(self.ifInc)
        self.ifInc += 1
        return self.ifStack[-1]


    def write_function(self, name, nLocal):
        # Writes a VM function command
        self.ifInc = 0
        self.whileInc = 0
        vmComm = f"function {self.className}.{name} {nLocal}"
        self.vmCode.append(vmComm)

    
    def write_call(self, obj):
        # Recieves dictionary - {"name", "index"}
        # Writes Vm call command
        # print("This is from write call: ", name, nArgs)
        self.vmCode.append(f"call {obj['name']} {obj['index']}")

    def write_pop(self, segment, index):
        self.vmCode.append(f"pop {segment} {index}")

    def write_push(self, segment, index):
        # self.vmCode.append(f"push {segment} {index}")
        self.vmCode.append(f"push {segment} {index}")
        
    def write_arithmetic(self, op, op_type='stdr'):
        pass
    
    def write_label(self, label, ext_cond=None):
        if (label == 'WHILE_EXP'):
            self.vmCode.append(f'label {label}{self.increment_while()}')
        elif (label == 'WHILE_END'):
            self.vmCode.append(f'label {label}{self.whileStack.pop()}')
        elif (label == 'IF_TRUE'):
            self.vmCode.append(f'label {label}{self.ifStack[-1]}')
        elif (label == 'IF_FALSE'):
            if (ext_cond == 'BYE'):
                self.vmCode.append(f'label {label}{self.ifStack.pop()}')
            else:
                self.vmCode.append(f'label {label}{self.ifStack[-1]}')
        elif (label == 'IF_END'):
            self.vmCode.append(f'label {label}{self.ifStack.pop()}')
        


    def add_negation(self):
        self.vmCode.append('not')

    def if_goto(self, label):
        # In case if while statement, first appears <label WHILE_EXP> so
        # it initializes in write_label
        # In <if-true> first appearse if-goto statement
        if (label == 'WHILE_END'):
            self.vmCode.append(f"if-goto {label}{self.whileStack[-1]}")
        elif (label == 'IF_TRUE'):
            self.vmCode.append(f"if-goto {label}{self.increment_if()}")


    def goto(self, label):
        if (label == 'WHILE_EXP'):
            self.vmCode.append(f"goto {label}{self.whileStack[-1]}")
        if (label == 'IF_FALSE'):
            self.vmCode.append(f"goto {label}{self.ifStack[-1]}")
        if (label == 'IF_END'):
            self.vmCode.append(f"goto {label}{self.ifStack[-1]}")


    def write_return(self):
        self.vmCode.append('return')
    