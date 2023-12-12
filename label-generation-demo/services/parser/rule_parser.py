#  Copyright (c) 2023. Dynatrace LCC. All Rights Reserved.

#  Licensed under the Apache License, Version 2.0 (the "License").
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
#  implied. See the License for the specific language governing
#  permissions and limitations under the License.

import ast
import textwrap


class RuleParser:
    def __init__(self, feature_matrix_name='', level=0):
        self.feature_matrix_name = feature_matrix_name
        self.result = ''
        self.features = set()
        self.level = level

    def parse(self, r):
        self.result = ''

        try:
            ast_rule = ast.parse(textwrap.dedent(r))
            self.parse_sub_rule(ast_rule.body[0])
        except SyntaxError:
            print('Syntax Error')
            return None

        return self.result

    def parse_sub_rule(self, r):
        if isinstance(r, ast.Compare):
            self.parse_compare(r)
        elif isinstance(r, ast.BinOp):
            self.parse_binop(r)
        elif isinstance(r, ast.BoolOp):
            self.parse_boolop(r)
        elif isinstance(r, ast.Constant):
            self.parse_constant(r)
        elif isinstance(r, ast.Name):
            self.parse_name(r)
        elif isinstance(r, ast.operator) or isinstance(r, ast.boolop):
            self.parse_op(r)
        elif isinstance(r, ast.cmpop):
            self.parse_cmpop(r)
        elif isinstance(r, ast.Expr):
            self.parse_sub_rule(r.value)
        elif isinstance(r, ast.If):
            # st.write('IfExp found')
            self.parse_if(r)
        elif isinstance(r, ast.Return):
            # st.write('Return found')
            self.parse_return(r)
        elif isinstance(r, ast.UnaryOp):
            self.parse_unaryop(r)

    def parse_unaryop(self, r):
        if isinstance(r.op, ast.USub):
            print('-', end='')
            self.result += '-'
            self.parse_sub_rule(r.operand)

    def parse_return(self, r):
        print('return ', end='')
        # self.result += '\t'*self.level + 'return '
        # self.parse_sub_rule(r.value)
        # self.result += '\n'
        self.result += '\t' * self.level + 'return '
        if hasattr(r.value, 'id'):
            self.result += r.value.id
        else:
            self.parse_sub_rule(r.value)
        self.result += '\n'

    def parse_if(self, r):
        print('if ', end='')
        self.result += '\t' * self.level + 'if '
        self.parse_sub_rule(r.test)
        self.level += 1
        print(':')
        self.result += ':\n'
        for i in r.body:
            self.parse_sub_rule(i)
        for i in r.orelse:
            print('else:')
            self.result += '\t' * (self.level - 1) + 'else:\n'
            self.parse_sub_rule(i)
        self.level -= 1

    def parse_compare(self, r):
        print('(', end='')
        self.result += '('
        self.parse_sub_rule(r.left)
        # this is not right for now. need to fix the order of operations to be able to eval
        for i in range(len(r.ops)):
            self.parse_sub_rule(r.ops[i])
            self.parse_sub_rule(r.comparators[i])
        print(')', end='')
        self.result += ')'

    def parse_binop(self, r):
        # print('(', end='')
        self.parse_sub_rule(r.left)
        self.parse_sub_rule(r.op)
        self.parse_sub_rule(r.right)
        # print(')', end='')

    def parse_boolop(self, r):
        print('(', end='')
        self.result += '('

        self.parse_sub_rule(r.values[0])
        for v in r.values[1:]:
            self.parse_sub_rule(r.op)
            self.parse_sub_rule(v)

        print(')', end='')
        self.result += ')'

    def parse_constant(self, r):
        print(r.value, end='')
        self.result += str(r.value)

    def parse_name(self, r):
        if not self.feature_matrix_name == '':
            print(self.feature_matrix_name + '["' + r.id + '"]', end='')
            self.result += self.feature_matrix_name + '["' + r.id + '"]'
        else:
            print(r.id, end='')
            self.result += r.id
        self.features.add(r.id)

    def parse_op(self, r):
        if isinstance(r, ast.BitOr):
            print(' | ', end='')
            self.result += ' | '
        elif isinstance(r, ast.Or):
            print(' or ', end='')
            self.result += ' or '
        elif isinstance(r, ast.BitAnd):
            print(' & ', end='')
            self.result += ' & '
        elif isinstance(r, ast.And):
            print(' and ', end='')
            self.result += ' and '

    def parse_cmpop(self, r):
        if isinstance(r, ast.Eq):
            print(' == ', end='')
            self.result += ' == '
        elif isinstance(r, ast.NotEq):
            print(' != ', end='')
            self.result += ' != '
        elif isinstance(r, ast.Lt):
            print(' < ', end='')
            self.result += ' < '
        elif isinstance(r, ast.LtE):
            print(' <= ', end='')
            self.result += ' <= '
        elif isinstance(r, ast.Gt):
            print(' > ', end='')
            self.result += ' > '
        elif isinstance(r, ast.GtE):
            print(' >= ', end='')
            self.result += ' >= '


# main for testing
#
if __name__ == '__main__':
    res = ast.parse(
        '(robust_dispersion_ > 0.5 or robust_dispersion_ < 0.2) | var == 0.2 | (perc_avail_ > 1 & median <= 7)',
        mode='eval')

    parser = RuleParser()
    print('\n')
    parser.parse_sub_rule(res.body)
    print('\n')

    res1 = ast.parse(
        '(robust_dispersion_ > 0.5 | robust_dispersion_ < 0.2) | estimated_noise != 0.2 | (perc_avail_ > 0 & median != 7)',
        mode='eval')
    parser1 = RuleParser(feature_matrix_name='fm')
    print('\n')
    parser1.parse_sub_rule(res1.body)
    print('\n')

    test = ast.parse("""
if perc_avail_ < 0.3:
    if robust_dispersion_ > 0.2:
        return 1
    else:
        if mean > 0 and median > 0:
            return 0
        elif perc_avail_ > 0.99:
            return 1
else:
    return 0""")

    # print(ast.dump(test, indent=2))

    parser2 = RuleParser()
    print('\n')
    parser2.parse_sub_rule(test.body)
