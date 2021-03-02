import os
from signatures import signatures
from SymbolTable import SymbolTable
from VmWriter import VmWriter
from math_ops import operations, negation
from method_map import method_map

class CompilationEngine:
    def __init__(self, filepath, tokenizer):
        self.from_filepath = filepath
        self.dest_filepath = self.build_dest_filepath()
        self.SymbolTable = SymbolTable()
        self.VmWriter = VmWriter()
        self.tokenizer = tokenizer
        # Current token. Updates with every self.tokenizer.advance() call
        self.token = ''
        # Code tree
        self.tree = ''
        # self.indent is multiplier for '  ' indent.
        self.indent = 0
        # Current class
        self.className = ''
        self.subroutineName = ''
        self.subroutine_id = ''
        self.subroutine_call_comp = ''
        self.arg_number = 0
        # *****
        # *****
        self.ops = []
        self.expression_tree = []

        self.subroutine_names = []
        self.arg_numbers = []

        # condition for VmWriter
        self.crr = []



    def _next(self):
        # Returns _next token
        # It easier to call this methods than everytime write self.tokenizer.advance()
        self.token = self.tokenizer.advance()


    def add_token(self, to_symbol_table=False):
        # This method added only for cosmetic purposes to follow indentation conventions
        # add avoid adding '\n' everytime
        # Calling _next sets token from JackTokenizer to self.token and all the following methods
        # deciding when to get next token with self._next() and when to add token with self.add_token()
        # giving compile_class etc. some level of abstractions
        if (to_symbol_table):
            self.SymbolTable.add_ids(self.token["pure"])
        self.tree += self.indent * '  ' + self.token["wrapped"] + '\n'


    def get_non_terminals(self, k):
        # When closing non terminal element comes into play next tokens should be one indentation backwards
        # Opening element increases indentation for next tokens
        # Such strange placement of if conditions avoids problems with indentation of non terminal tags themselves
        if (k.startswith('e_')):
            self.indent -= 1
        
        non_terminal = self.indent * '  ' + signatures[k] + '\n'

        if (not k.startswith('e_')):
            self.indent += 1

        return non_terminal

        
    def parse_static_tokens(self, steps):
        # There are some tokens placement of which will won't change from user to user such as after class keyword
        # there always must be classname forwarded with '{' symbol. Steps are amount of such 'static' building blocks 
        for i in range(steps):
            self._next()
            self.add_token()


    def is_class_type(self, type_of):
        if type_of not in ['char', 'boolean', 'int']:
            return True
        return False

    def compile_class(self):
        # Compile complete class
        # Add starting class signature 
        self.tree = self.get_non_terminals("class")

        self.parse_static_tokens(1)

        self._next()
        
        # Frist Symbol table needs className. Also VmWriter to name functions. <class_name>.<function_name>
        self.className = self.token["pure"]
        self.VmWriter.set_className(self.className)

        self.add_token()

        self.parse_static_tokens(1)

        self._next()

        cond = True
        while(cond):
            if (self.token["pure"] == 'constructor'):
                self.compile_subroutine('constructor')

            if (self.token["pure"] == 'static' or self.token["pure"] == 'field'):
                # Check for var_declaration
                self.compile_class_var_dec()
            elif (self.token["pure"] == 'function'):
                self.compile_subroutine()
            elif (self.token["pure"] == 'method'):
                self.compile_subroutine('method')
            else:
                cond = False

        # Adds closing curly
        self.add_token()

        

        self.tree += self.get_non_terminals("e_class")
    
        
    def compile_class_var_dec(self):
        # Compiles static and field declarations
        self.tree += self.get_non_terminals("classVarDec")
        self.add_token(True)

        self._next()
        self.add_token(True)


        self._next()
        self.add_token(True)


        self._next()
        while(self.token["pure"] != ';'):

            self.add_token(True)
            self._next()

        # Accepts scope of identifiers <class> | <subroutine>
        self.SymbolTable.define('class')

        self.add_token()

        self.tree += self.get_non_terminals("e_classVarDec")

        self._next()
        if (self.token["pure"] == 'static' or self.token["pure"] == 'field'):
            self.compile_class_var_dec()
        else:
            return


    def compile_subroutine(self, func_type = ''):
        # compiles a complete function, method, or constructor
        self.tree += self.get_non_terminals("subroutineDec")
        
        self.SymbolTable.start_subroutine()
        # Adds <subroutine></subroutine>
        self.add_token()

        if (self.token["pure"] == 'method'):
            self.SymbolTable.set_is_method(True, self.className)
        # Adds (void|type)
        self._next()
        self.add_token()
        # Adds <function_name>
        self._next()
        self.subroutineName = self.token["pure"]
        self.add_token()
        # Adds '('
        self._next()
        self.add_token()


        # Parameter list
        self.compile_parameter_list()

        # self.VmWriter.write_function(func_name, )

        # Adds ')'
        self.add_token()

        self.compile_subroutine_body(func_type)
        # called in the end to reinit another token for future deciding
        self._next()
        self.tree += self.get_non_terminals("e_subroutineDec")
        # print('Subroutine scoped info\n',self.SymbolTable.subroutineScoped)
        return


    def compile_parameter_list(self):
        # compiles a (possibly empty) parameter list, not including the enclosing '()'
        self.tree += self.get_non_terminals("parameterList")
        
        # Adds parameters
        while(True):
            self._next()
            if (self.token["pure"] == ')'):
                break 
            self.add_token(True)
        
        self.SymbolTable.define('subroutine_arg')


        self.tree += self.get_non_terminals("e_parameterList")
        return


    def compile_subroutine_body(self, func_type):
        self.tree += self.get_non_terminals("subroutineBody")
        # Adds '{' to subroutine body
        self.parse_static_tokens(1)
        # Searches for <var> delcaration
        self._next()

        # Searches for var and adds them (if at least one exist) to the tree
        while(self.token["pure"] == 'var'):
            self.compile_var_dec()
        
        # At this point self.subroutineName stores subroutine name to add it
        # to vm command and programm only now knows how many local variables are there
        self.VmWriter.write_function(self.subroutineName,self.SymbolTable.var_count('local'))
        if func_type == 'constructor':
            class_var_count = self.SymbolTable.var_count('field')
            self.VmWriter.write_push('constant', class_var_count)
            self.VmWriter.write_call({"name": "Memory.alloc", "index": 1})
            self.VmWriter.write_pop('pointer', 0)
        
        if func_type == 'method':
            self.VmWriter.write_push('argument', 0)
            self.VmWriter.write_pop('pointer', 0)
        
        if (self.token["pure"] in ["let", "if", "while", "do", "return"]):
            self.compile_statements()

        
        # Adds '}' to subroutine body
        self.add_token()

        self.tree += self.get_non_terminals("e_subroutineBody")
        return


    def compile_var_dec(self):
        # compiles a *var* declaration
        self.tree += self.get_non_terminals('varDec')
        self.add_token()
        while(self.token["pure"] != ';'):
            # self.parse_static_tokens(1)
            self._next()
            self.add_token(True)
        
        self.SymbolTable.define('subroutine_var')

        self._next()
        
        self.tree += self.get_non_terminals('e_varDec')


    def compile_statements(self):
        # compiles a sequence of statements not including the enclosing '{}'
        
        self.tree += self.get_non_terminals("statements")
        self.compile_statement()
        self.tree += self.get_non_terminals("e_statements")


    def compile_statement(self):
        statements = {
            "let": self.compile_let,
            "if": self.compile_if,
            "else": self.compile_else,
            "while": self.compile_while,
            "do": self.compile_do,
            "return": self.compile_return
        }
        # Encloses every single statement under parent <statements></statemens> tag
        
        
        if (self.token["pure"] != '}'):
            statements[self.token["pure"]]()
        

    def compile_do(self):
        # Compiles a do statement
        self.tree += self.get_non_terminals("doStatement")
        # Add <do>
        self.add_token()

        # Add <classname> | <subroutine_name>
        self._next()
        self.add_token()

        # Explanation on top of compile_subroutine_call()
        self.subroutine_id = self.token["pure"]
        self.subroutine_call_comp = self.token["pure"]
        

        self._next()
        self.crr.append('function')
        kind_of = self.SymbolTable.kind_of(self.subroutine_call_comp)
        
        if kind_of != 'NONE':
            
            type_of = self.SymbolTable.type_of(self.subroutine_call_comp)
            if (kind_of == 'field' and self.is_class_type(type_of)):
                kind_of = 'this'
            
            self.VmWriter.write_push(kind_of, self.SymbolTable.index_of(self.subroutine_call_comp))
        self.compile_subroutine_call()


        # &&&&&&&&&&&& TEMP
        self.VmWriter.write_expression()
        # &&&&&&&&&&&& TEMP


        self.add_token()

        self.VmWriter.write_pop('temp', 0)

        self.tree += self.get_non_terminals("e_doStatement")
        self._next()
        self.compile_statement()
    

    def compile_subroutine_call(self):
        """
            Every call of current function sets arg_number on top of the list(which mimics stack data structure)
            <def compile_expression()> increments top stack value every time it sees ','
            (which means there is one more argument).
            When list of arguments is exausted for the current call - it pops value from top
            and writes it into VmWriter.
            The same is done with <self.subroutine_names>. It's a stack of subroutines names
        """
        self.arg_number = 0
        self.arg_numbers.append(self.arg_number)
        sub = ''
        # Adds '(' or '.'
        # self._next()
        
        self.add_token()
        if (self.token["pure"] == '('):
            self._next()
            self.compile_expression_list()
            self.add_token()
            idx = 0
            for meth in method_map:
                if meth.startswith(self.subroutine_id):
                    self.VmWriter.write_push('pointer', 0)
                    idx += 1
            self.subroutine_names.append({"name": f"{self.className}.{self.subroutine_id}", "index": self.arg_numbers.pop() + idx})
            # self.VmWriter.write_call(self.subroutine_names.pop())
            sub = self.subroutine_names.pop()
            self._next()
        else:
            self._next()
            self.add_token()
            compound_subroutine_n = self.subroutine_call_comp + f".{self.token['pure']}"
            self.parse_static_tokens(1)
            self._next()
            self.compile_expression_list()
            self.add_token()
            self._next()
            self.subroutine_names.append({"name": f"{compound_subroutine_n}", "index": self.arg_numbers.pop()})
            sub = self.subroutine_names.pop()
            # self.VmWriter.write_call(self.subroutine_names.pop())

        v = self.subroutine_call_comp 
        type_of = self.SymbolTable.type_of(v)
        temp = ''
        if type_of != 'NONE':
            idx = 0
            if type_of not in ["char", "boolean", "int"]:
                idx += 1
            sub_call = sub['name'].split('.')
            sub_call[0] = self.SymbolTable.type_of(v)
            # self.VmWriter.add_operand(f"call {'.'.join(sub_call)} {sub['index'] + idx}")
            temp = f"call {'.'.join(sub_call)} {sub['index'] + idx}"
            self.VmWriter.add_operand(temp)
        else:
            
            # self.VmWriter.add_operand(f"call {sub['name']} {sub['index']}")
            temp = f"call {sub['name']} {sub['index']}"
            self.VmWriter.add_operand(temp)

        # if (self.token["pure"] == ';'):
        #     self.add_token()
        

    def compile_let(self):
        self.tree += self.get_non_terminals("letStatement")
        # Property showing does it save in Variable or in Array
        is_array = False
        # Adds <keyword> let </keywrod>
        self.add_token()
        # Adds variable name etc.
        self.parse_static_tokens(1)

        var_name = self.token["pure"]

        self._next()
        if (self.token["pure"] == '['):
            is_array = True
            self._next()
            self.compile_array_subterm()
            comm = f"push {self.SymbolTable.kind_of(var_name)} {self.SymbolTable.index_of(var_name)}"
            self.VmWriter.add_operand(comm)
            self.VmWriter.add_operand('add')
            self.VmWriter.write_expression()

        self.add_token()
        self._next()
        self.compile_expression()
        self.add_token()
        self._next()

        # From here
        self.VmWriter.write_expression()
        

        # Till here
        if not is_array:
            v = 'this' if self.SymbolTable.kind_of(var_name) == 'field' else self.SymbolTable.kind_of(var_name)
            self.VmWriter.write_pop(v, self.SymbolTable.index_of(var_name))
        else:
            self.VmWriter.write_pop('temp', 0)
            self.VmWriter.write_pop('pointer', 1)
            self.VmWriter.write_push('temp', 0)
            self.VmWriter.write_pop('that', 0)
        self.tree += self.get_non_terminals("e_letStatement")
        # Recursive call to check for next statements
        self.compile_statement()

    def compile_while(self):
        # Compiles a while statement
        self.tree += self.get_non_terminals("whileStatement")
        # Adds <while> keyword
        self.VmWriter.write_label('WHILE_EXP')
        self.add_token()
        # Adds '('
        self.parse_static_tokens(1)
        # Seeks for expression
        self._next()
        self.compile_expression()
        self.VmWriter.write_expression()

        self.VmWriter.add_negation()
        self.VmWriter.if_goto('WHILE_END')
        # Compile expression at the end of its own functions calls self._next()
        # So the next token already been parsed. Its time to add one
        # Feels like a crap. Next token is ')'
        self.add_token()
        # Adds '{'
        self.parse_static_tokens(1)
        self._next()
        self.compile_statements()
        # Adds '}'
        self.add_token()
        self.VmWriter.goto('WHILE_EXP')
        self.VmWriter.write_label('WHILE_END')
        self.tree += self.get_non_terminals("e_whileStatement")
        self._next()
        self.compile_statement()


    def compile_return(self):
        # Compiles a return statement
        self.tree += self.get_non_terminals("returnStatement")
        # Adds returns keyword
        self.add_token()
        
        self._next()
        # Checks if next token not ';' than it should be watched as expression
        if (self.token["pure"] != ';'):
            self.compile_expression()
            self.VmWriter.write_expression()
            
        else:
            self.VmWriter.write_push("constant", 0)
        # Adds token not depending on expression nor ';'
        self.VmWriter.write_return()
        self.add_token()


        self.tree += self.get_non_terminals("e_returnStatement")
        self._next()


    def compile_if(self):
        self.tree += self.get_non_terminals("ifStatement")
        # Adds <keyword>if<>
        self.add_token()

        self.parse_static_tokens(1)
        self._next()
        self.compile_expression()

        self.VmWriter.write_expression()

        self.VmWriter.if_goto('IF_TRUE')
        self.VmWriter.goto('IF_FALSE')
        self.VmWriter.write_label('IF_TRUE')

        # Adds ) then {
        self.add_token()
        self.parse_static_tokens(1)
        self._next()
        self.compile_statements()
        
        self.add_token()
        self._next()

        if (self.token["pure"] == 'else'):
            self.VmWriter.goto('IF_END')
            self.VmWriter.write_label('IF_FALSE', 'HELLO')
            self.add_token()
            self.parse_static_tokens(1)
            self._next()

            self.compile_statements()
            self.add_token()
            self._next()
            self.VmWriter.write_label('IF_END')
        else:
            self.VmWriter.write_label('IF_FALSE', 'BYE')
        
        self.tree += self.get_non_terminals("e_ifStatement")

        
        self.compile_statement()
        

    def compile_else(self):
        self.add_token()
        self.parse_static_tokens(1)


    def compile_expression(self):
        self.tree += self.get_non_terminals('expression')
        
        self.compile_term()
        # print(self.some_values)
        # if (self.VmWriter.op):
        #     self.VmWriter.vmCode.append(self.VmWriter.op.pop())

        
        self.tree += self.get_non_terminals('e_expression')


        if (self.token["pure"] == ','):
            self.arg_numbers[len(self.arg_numbers) - 1] += 1

            self.add_token()
            self._next()
            self.compile_expression()

        # self._next()


    def compile_term(self):
        if (self.token["pure"] == 'this'):
            self.VmWriter.write_push('pointer', 0)

        if (self.token["pure"] in ["false", "null"]):
            self.VmWriter.write_push('constant', '0')
        elif (self.token["pure"] == 'true'):
            self.VmWriter.write_push('constant', '0')
            self.VmWriter.add_negation()

        if (self.token["pure"] == ")" or self.token["pure"] == ';'):
            if (self.token["pure"] == ')'):
                temp = ''
                if self.crr:
                    temp = self.crr.pop()

                if temp == 'expression':
                    self.VmWriter.operands.append(')')
            return

            

        if (self.token["pure"] == ','):
            return
            

        if (self.token["pure"] == ']'):
            self._next()
            return
        
        self.tree += self.get_non_terminals("term")

        if (self.token["pure"] == '('):
            self.add_token()
            self.VmWriter.operands.append('(')
            # self.VmWriter.arithm_ops.append('(')
            self.crr.append('expression')
            self._next()
            self.compile_expression()
        
        if (self.token["pure"] == '~' or self.token["pure"] == '-'):
            self.add_token()
            self.VmWriter.operands.append(negation[self.token["pure"]])
            # self.VmWriter.arithm_ops.append(negation[self.token["pure"]])
            self._next()
            self.compile_term()
            self.tree += self.get_non_terminals('e_term')
            return
        self.add_token()


        # At this point it's not clear if identifier is a function or a variable
        token_type = self.token["type"]
        token_pure = self.token["pure"]

        if (token_type == 'integerConstant'):
            self.VmWriter.add_operand(f'push constant {token_pure}')
        elif (token_type == 'identifier'):
            # Saves state of VmWriter to implement awful array proccessing
            saved_vm_writer = self.VmWriter
            self._next()

            if self.token["pure"] == '[':
                print(token_pure)
                print(saved_vm_writer)

                self.VmWriter = VmWriter()
                

            if (token_pure in self.SymbolTable.subroutineScoped):
                kind_of = self.SymbolTable.kind_of(token_pure)
                index_of = self.SymbolTable.index_of(token_pure)
                self.VmWriter.add_operand(f"push {kind_of} {index_of}") 
            elif (token_pure in self.SymbolTable.classScoped):
                kind_of = self.SymbolTable.kind_of(token_pure)
                index_of = self.SymbolTable.index_of(token_pure)
                kind_of = 'this' if kind_of == 'field' else kind_of
                self.VmWriter.add_operand(f"push {kind_of} {index_of}")

            if (self.SymbolTable.type_of(token_pure) not in ["char", "int", "boolean"]):
                self.subroutine_call_comp = token_pure
                

            if self.token["pure"] == '[':
                self.VmWriter.add_operand('+')
                # self.VmWriter.add_operand('(')
                self.compile_expression()
                # self.VmWriter.add_operand(')')
                array_exp = self.VmWriter.write_expression(True)
                array_exp += 'pop pointer 1' + '\n' + 'push that 0'
                self.VmWriter = saved_vm_writer
                self.VmWriter.add_operand(array_exp)
                # self.VmWriter.add_operand(')')/   
                print("Bottom",self.VmWriter.operands)
                self.VmWriter.write_expression()

        elif (token_type == 'stringConstant'):
            # String constant without quotes
            string = token_pure.split('"')[1]
            self.VmWriter.write_push('constant', len(string))
            self.VmWriter.write_call({"name": "String.new", "index": 1})
            for char in string:
                self.VmWriter.write_push('constant', ord(char))
                self.VmWriter.write_call({"name": "String.appendChar", "index": 2})
            # kind_of = self.SymbolTable.kind_of(token_pure)
            # index_of = self.SymbolTable.index_of(token_pure)
            # self.VmWriter.add_operand(f"push {kind_of} {index_of}")  

        if token_type != 'identifier':
            self._next()

        if (self.token["pure"] == '('):
            self.subroutine_id = token_pure
            self.crr.append('function')
            self.compile_subroutine_call()
            

        if (self.token["pure"] in ["+", "-", "<", '&', '=', '|', '>', '/', '*']):
            self.tree += self.get_non_terminals("e_term")
            self.add_token()
            self.VmWriter.operands.append(self.token["pure"])
            
            self._next()
        elif (self.token["pure"] == '.'):
            self.crr.append('function')

            self.compile_subroutine_call()

            self.tree += self.get_non_terminals("e_term")

            
        else:
            self.tree += self.get_non_terminals("e_term")
            
        
        self.compile_term()


    def compile_array_subterm(self):
        # self.add_token()
        # self._next()

        self.compile_expression()


        # self.add_token()
        # self._next()


    def compile_expression_list(self):
        # compiles a possibly empty comma-separeted list of expressions
        self.tree += self.get_non_terminals('expressionList')
        if (self.token["pure"] != ')'):
            self.arg_numbers[len(self.arg_numbers) - 1] = 1
            self.compile_expression()


        self.tree += self.get_non_terminals('e_expressionList')


    def build_dest_filepath(self):
        temp = self.from_filepath.split('\\')[-1].split('.')[0] + '.xml'
        filename = self.from_filepath.split('\\')
        filename[-1] = temp
        filename = '\\'.join(filename)

        self.rewrite_file(filename)

        return filename
    

    def create_file(self):
        self.compile_class()
        with open(self.dest_filepath, 'a+') as f:
            # f.write(self.tree)
            # print(self.tree)
            pass
        with open(self.dest_filepath[:-3]+'vm', 'a+') as f:
            
            for s in self.VmWriter.vmCode:
                f.write(s+'\n')
            # print(self.tree)


    def rewrite_file(self, filename):
        # Deleting old copy of file to replace it with new one
        if (os.path.exists(filename)):
            os.remove(filename)

    

        
