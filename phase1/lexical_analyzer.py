import re

class Token:
    def __init__(self, type, value, line, position):
        self.type = type
        self.value = value
        self.line = line
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, '{self.value}', line={self.line}, pos={self.position})"

class LexicalAnalyzer:
    def __init__(self):
        self.tokens = []
        
        # Token patterns
        self.patterns = [
            ('KEYWORD', r'\b(def|if|else|elif|for|while|return|import|from|as|class|try|except|finally|with|in|is|not|and|or|True|False|None)\b'),
            ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
            ('NUMBER', r'\d+(\.\d+)?'),
            ('STRING', r'\".*?\"|\'.*?\''),
            ('OPERATOR', r'[\+\-\*/=<>!%&\|^~]+'),
            ('DELIMITER', r'[\(\)\[\]\{\},;:.]'),
            ('NEWLINE', r'\n'),
            ('WHITESPACE', r'[ \t]+'),
            ('COMMENT', r'#.*')
        ]
        
        # Compile patterns
        self.regex_patterns = [(token_type, re.compile(pattern)) for token_type, pattern in self.patterns]
    
    def tokenize(self, code):
        """source code to tokens"""
        self.tokens = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            position = 0
            while position < len(line):
                match = None
                for token_type, pattern in self.regex_patterns:
                    regex_match = pattern.match(line[position:])
                    if regex_match:
                        value = regex_match.group(0)
                        if token_type not in ['WHITESPACE', 'COMMENT']:  # Skip whitespace and comments
                            self.tokens.append(Token(token_type, value, line_num, position))
                        position += len(value)
                        match = True
                        break
                
                if not match:
                    # Handle unrecognized character
                    self.tokens.append(Token('ERROR', line[position], line_num, position))
                    position += 1
        
        return self.tokens

def analyze_code(code):
    """lexical analysis"""
    lexer = LexicalAnalyzer()
    tokens = lexer.tokenize(code)
    
    # tokens to a serializable format
    token_list = [
        {
            'type': token.type,
            'value': token.value,
            'line': token.line,
            'position': token.position
        }
        for token in tokens
    ]
    
    return token_list