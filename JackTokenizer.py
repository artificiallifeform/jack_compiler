from hash_map import patterns, symbols
import re
# Flow of a program
# 1.Constructor executes read_jack()
# 2. read_jack() loads code into memory and saves under self.code property
# 3. When outside citizen executes advance() self.currentToken updates. 
# and self.tokenType updates also
# 4. Then anyone can access currentToken and tokenType via corresponding methods
# get_current_token_wrapped, get_token_type
# 5. To read next token executor must call advance() every time before all code
# woudn't be read.
from method_map import fill_method_map, code_list, clear_method_map



class JackTokenizer:
    def __init__(self, jackfile):
        self.jackfile = jackfile
        self.code_length = 0
        self.code = ''
        self.currentToken = None
        self.tokenType = None
        self.code_index = 0
        self.read_jack()

    def read_jack(self):
        with open(self.jackfile, 'r') as f:
            code_line = f.readline()
            while(code_line):
                code_list.append(code_line.strip())
                # Strips code line two solve issue with multi line comments with * where * 
                # comes after <space>
                temp = code_line.strip() + '\n'
                result = re.sub('/\*\*.*\*/|//.*?(?=\n)|(/\*\*.*|^\*.*)', '', temp)
                if (result != '\n'):
                    self.code += result
                code_line = f.readline()

            clear_method_map()
            fill_method_map()
            self.code_length = len(self.code)


    def has_more_tokens(self):
        # returns boolean
        # do we have more tokens in the input
        return self.code_index < self.code_length

    def advance(self):
        #         Gets the next token from the input
        # and makes it the current token. This
        # method should only be called if
        # hasMoreTokens() is true. Initially
        # there is no current token
        if (self.has_more_tokens()):
            self.currentToken = self.parse_code(self.code)
            if (self.currentToken == None):
                return ''
            self._define_type(self.currentToken)

            pure = self.currentToken
            wrapped = self.get_current_token_wrapped()
            token_type = self.get_token_type()

            return {
                "wrapped": wrapped,
                "pure": pure,
                "type": token_type
            }


    def get_current_token_wrapped(self):
        token_t = self.get_token_type()
        if (token_t == 'stringConstant'):
            self.currentToken = self.currentToken.split('"')[1] 
        builded_token = "<" + token_t +"> " + self.currentToken + " </" + token_t + ">"
        return builded_token

    def get_token_type(self):
        # Returns KEYWORD, SYMBOL, IDENTIFIER, INT_CONST,
        # STRING_CONST
        # Returns the type of the current token
        return self.tokenType

    def keyWord(self):
        # Returns the keyword which is the current tokne. Should
        # be called only when tokenType() is KEYWORD
        self.tokenType = "keyword"

    def symbol(self):
        # Returns Char
        # Returns the chracter which is the current tokne. Should be called only
        # when tokenType() is SYMBOL
        self.tokenType = "symbol"

    def identifier(self):
        # Return String
        # Return the identifier which is the current token. Should be
        # be called only when tokenType() is IDENTIFIER
        self.tokenType = "identifier"

    def intVal(self):
        # Returns Int
        self.tokenType = "integerConstant"

    def stringVal(self):
        # Returns string
        self.tokenType = "stringConstant"

    def parse_code(self, code):
        # Parse each letter in a code. Defines 
        # if token is a symbol => writes it to file
        # else => calls define function that assigns right type (1 of 4 last)
        token = ''
        cond = True
        while (cond):

            try:
                letter = code[self.code_index]
            except IndexError:
                return None
            

            if (letter == "\n"):
                self.code_index += 1
                continue
            
            if (token.startswith('"')):
                if (letter == '"'):
                    token += letter
                    self.code_index += 1
                    return token

                token += letter
                self.code_index += 1
                continue
    
            if (letter in symbols):
                if (len(token) > 0):
                    return token

                if (letter == ' '):
                    self.code_index += 1
                    continue
                else:
                    self.code_index += 1
                    return letter
                
            token += letter
            self.code_index += 1
    
    def _define_type(self, token):
        # If token isn't a SYMBOL then define its type
        if (token in patterns):
            self.keyWord()
        elif (token in symbols):
            self.symbol()
        elif (self._represents_int(token)):
            self.intVal()
        elif (token.startswith('"')):
            self.stringVal()
        else:
            self.identifier()

    def _represents_int(self,val):
        # Checks if token is an integer value
        try:
            int(val)
            return True
        except ValueError:
            return False