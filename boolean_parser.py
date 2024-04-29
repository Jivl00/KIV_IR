import re

def infix_to_postfix(query):
    # Check if the boolean query is valid (e.g. no two operators next to each other)
    try:
        while re.search(r"AND AND|AND OR|OR AND|OR OR|NOT NOT| {2}", query):
            query = re.sub(r"AND AND", "AND", query)
            query = re.sub(r"AND OR", "OR", query)
            query = re.sub(r"OR AND", "OR", query)
            query = re.sub(r"OR OR", "OR", query)
            query = re.sub(r"NOT NOT", "", query)
            query = re.sub(r" {2}", " ", query)

        precedence = {"NOT": 3, "AND": 2, "OR": 1}  # Define precedence
        stack = []  # Initialize stack
        postfix = []  # Initialize postfix list
        # Add space around brackets if they are not already there
        query = re.sub(r"(\w)(\()", r"\1 (", query)
        query = re.sub(r"(\()(\w)", r"( \2", query)
        query = re.sub(r"(\))(\w)", r") \2", query)
        query = re.sub(r"(\w)(\))", r"\1 )", query)

        tokens = query.strip().split(" ")  # Split query into tokens
        for i in range(len(tokens)):
            token = tokens[i]
            if token == "":
                continue
            if token in ["AND", "OR", "NOT"]:  # If token is an operator
                while stack and stack[-1] != "(" and precedence[token] <= precedence.get(stack[-1], 0):
                    postfix.append(stack.pop())  # Pop operators from stack to output
                stack.append(token)  # Push current operator to stack
            elif token == "(":  # If token is an open bracket
                stack.append(token)
            elif token == ")":  # If token is a close bracket
                while stack and stack[-1] != "(":
                    postfix.append(stack.pop())  # Pop operators from stack to output
                stack.pop()  # Pop the open bracket from stack
            else:  # If token is a variable
                postfix.append(token)
                # If the previous token is also a variable, insert an "OR"
                if i > 0 and tokens[i - 1] not in ["AND", "OR", "NOT", "(", ")"]:
                    postfix.append("OR")

        while stack:
            if stack[-1] == "(":
                raise ValueError("Mismatched parentheses")
            postfix.append(stack.pop())  # Pop any remaining operators from stack to output

        return postfix
    except Exception as e:
        return ['']