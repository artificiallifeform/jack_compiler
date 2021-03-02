class SymbolTable:
    def __init__(self):
        # Signature:
        # "[name]": {"type": ..., "kind": ..., "#": ...}
        self.classScoped = {}

        self.subroutineScoped = {}

        # If subroutine is method then *this* argument should registered in subroutine scope in the background
        self.isMethod = False
        self.className = ''

        self.identifier_counter = {
            "field": 0,
            "static": 0,
            "argument": 0,
            "local": 0
        }

        self.ids = []
    
    def add_ids(self, token):
        self.ids.append(token)

    def set_is_method(self, is_method, classname = ''):
        # Sets is_method to True and gives className because *this* property should be of Class Type
        self.isMethod = is_method
        self.className = classname
        

    def start_subroutine(self):
        # Starts a new subroutine scope (restes the subroutines symbol table)
        self.subroutineScoped = {}
        self.set_is_method(False, '')
        self.identifier_counter["argument"] = 0
        self.identifier_counter["local"] = 0

    def define(self, scope):
        # arg : [scope] = <class>|<subroutine_arg>|<subroutine_var>
        # Defines a new identifier of a given name, type, and kind and assings it a running index
        # Inner get_obj() function for dynamic generation to call self.var_count function
        def get_obj(tp, kind):
            obj = {
                "type": tp,
                "kind": kind,
                "count": self.var_inc(kind)
            }
            return obj
        if (scope == 'subroutine_arg'):
            if (self.isMethod):
                self.subroutineScoped['this'] = get_obj(self.className, 'argument')


        if (scope == 'class'):
            self.classScoped[self.ids[2]] = get_obj(self.ids[1], self.ids[0])

            if (len(self.ids) > 3):
                # E.G ['static', 'int', 'hello', ',', 'bye'] becomes [',', 'bye', {any number of identifiers}]
                for identifier in self.ids[3:]:
                    if (identifier == ','):
                        continue
                    self.classScoped[identifier] = get_obj(self.ids[1], self.ids[0])

        elif (scope == 'subroutine_arg' and len(self.ids)):
            # if (self.isMethod):
            #     print("IT MUST EXECUTE")
            #     self.subroutineScoped['this'] = get_obj(self.className, 'argument')

            self.subroutineScoped[self.ids[1]] = get_obj(self.ids[0], 'argument')
                # Cuts an array ["int", "x", ",", "char", "z"] becomes ["char", "z"]
            self.ids = self.ids[3:]
            
            while(len(self.ids)):
                self.subroutineScoped[self.ids[1]] = get_obj(self.ids[0],'argument')
                self.ids = self.ids[3:]
                

        elif (scope == 'subroutine_var' and len(self.ids)):            
            self.subroutineScoped[self.ids[1]] = get_obj(self.ids[0], 'local')
            tp = self.ids[0]    
            self.ids = self.ids[3:]
            while (len(self.ids)):
                self.subroutineScoped[self.ids[0]] = get_obj(tp, 'local')
                self.ids = self.ids[2:]



        
        self.ids = []

        
    
    def var_inc(self, kind):
        temp = self.identifier_counter[kind] 
        self.identifier_counter[kind] += 1
        return temp

    def var_count(self, kind):
        # Args kind (STATIC, FIELD, ARG or VAR)
        # Returns the number of variables of the given kind already defined in the current scope
        # Returns int
        return self.identifier_counter[kind]
                
            
    def kind_of(self, name):
        # Returns the kind of the given variable
        return self.property_searcher(name, 'kind')
    

    def type_of(self, name):
        # Args name(String)
        # Returns String
        # Return the type of the named identifier in the current scope
        return self.property_searcher(name, 'type')


    def index_of(self, name):
        # Args name(String)
        # Return int
        #  Returns the index assigned to the named identifier
        return self.property_searcher(name, 'count')


    def property_searcher(self, name, prp):
        try:
            return self.subroutineScoped[name][prp]
        except KeyError:
            try:
                return self.classScoped[name][prp]
            except KeyError:
                return 'NONE'