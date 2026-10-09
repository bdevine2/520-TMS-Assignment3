import decimal
import re


class Fact:
    Implies = '->'
    Or = '|'
    And = '&'
    Not = '~'
    """
    • TELL <S> <W>
    • RETRACT <S>
    • ASK <S>
    """
    def __init__(self, statement, kbase):
        # First position action, last is weight if it has weight
        parts = [part.strip() for part in statement.split()]
        self.Action = parts[0]
        self.Knowledge = " ".join(parts[1:-1] if self.Action == 'TELL' else parts[1:])
        self.Weight = decimal.Decimal(parts[-1]) if self.Action == 'TELL' else 0.0
        self.Knowledge = self.convert_to_cnf(self.Knowledge, kbase, self.Weight) # TODO need to keep ground truth? and in other facts spawned
        self.Justifications = []  # parent keys that imply this truth
        self.Assumptions = []  # child keys implied by this

    def ground_truth(self):
        # am I a truth value? ONLY 1 capitol letter means I am a truth so return my weight or 0 if I dont exist
        return self.Weight if re.fullmatch(r"[A-Z]", self.Knowledge) else 0.0

    def is_implication(self):
        return self.Implies in self.Knowledge

    def deconstructed_variables(self, kb):
        # tear apart the non ground truth values into pieces
        if self.ground_truth():
            return {self.Knowledge: self.Weight}
        else:
            if self.is_implication():
                # we have two () sets of truths or con/dis junctions
                operands = [part.strip() for part in self.Knowledge.split(sep=self.Implies)]
                return_set = {}
                for v in operands:
                    # return what we know from the KB, which could be a false, it could recursively seek to discover
                    return_set[v] = max(kb.ask_string(v),self.Weight)# todo fix later to update truth
                return return_set
            else:  # must be a truth constant, con/dis junction of some sort
                return {self.Knowledge: kb.ask_string(self.Knowledge)}

    def convert_to_cnf(self, knowledge, kbase, weight):
        # eliminate implications
        # move nots in
        # standardize/skolemize
        # distribute or over and
        cnf_knowledge = knowledge

        if self.Implies in cnf_knowledge:
            cnf_knowledge = self.elim_implications(cnf_knowledge)
        if self.Not in cnf_knowledge:
            # if we had an implication then we will have 1 not we have to move in
            cnf_knowledge = self.move_not_in(cnf_knowledge)
        if self.And in cnf_knowledge and self.Or in cnf_knowledge:
            # special case, or over and, and over or
            print(f'SPECIAL case :{cnf_knowledge}')
            andParts = cnf_knowledge.split(self.And, 1)
            orParts = cnf_knowledge.split(self.Or, 1)
            if any(self.Or in part for part in andParts):
                for part in andParts:
                    if self.Or not in part or not self.operators_at_different_levels(part): # TODO need to solve for ~A | ~B & C should not run but ~A | (B & C) should
                        continue
                    # (A & (b | C)) something like this = (a & b) | (a & c)

                    left, right = part.split(self.Or, 1)
                    left = left.strip()
                    right = right.strip()
                    if right.startswith("(") and self.matching_parens(right, 0) == len(right) - 1:
                        inside = right[1:-1]
                        if self.And in inside:
                            left = left
                            b, c = inside.split(self.And, 1)
                            cnf_knowledge = f"({left}{self.Or}{b.strip()}){self.And}({left}{self.Or}{c.strip()})"
            elif any(self.And in part for part in orParts):
                # (A | (b & c)) = (a | b) & (a | c) splits into two facts
                for part in orParts:
                    if self.And not in part or not self.operators_at_different_levels(part): # TODO need to solve for ~A | ~B & C should not run but ~A | (B & C) should
                        continue
                    # (A & (b | C)) something like this = (a & b) | (a & c)

                    left, right = part.split(self.And, 1)
                    left = left.strip()
                    right = right.strip()
                    if right.startswith("(") and self.matching_parens(right, 0) == len(right) - 1:
                        inside = right[1:-1]
                        if self.Or in inside:
                            left = left
                            b, c = inside.split(self.And, 1)
                            cnf_knowledge = f"({left}{self.And}{b.strip()}){self.Or}({left}{self.And}{c.strip()})"
            else:
                #failure
                self.print_error('BROKEN Special case')

        elif self.And in cnf_knowledge and not self.operators_at_different_levels(cnf_knowledge):
            # a & b or a & b & c & d..
            # a
            # b
            # will return one and add the other directly to the kb via tell clean outer ( ) first here
            parts = self.clean_expression(cnf_knowledge).split(self.And)

            # only want the variable
            parts = [self.clean_expression(p) for p in parts]

            # need to sneak add the extra literal here
            for part in parts[1:]:
                kbase.tell(Fact(f"TELL {part} {weight}", kbase))

            # Return the first part
            cnf_knowledge = parts[0]
        cnf_knowledge = self.clean_expression(cnf_knowledge)
        # print(f'Cleaned: {cnf_knowledge}')
        return cnf_knowledge

    def elim_implications(self, knowledge):
        left, right = knowledge.split(self.Implies)
        # not a V b in the form (V) -> (Z) where V could be (Y & A) or Z could be (O | L)
        # do step 1 and eliminate implications
        return f"({self.Not}{left.strip()} {self.Or} {right.strip()})"  # add parens we will strip later

    def move_not_in(self, knowledge):
        # print("START: Move NOT in:", knowledge)
        output = ''
        found_not = False
        for i, char in enumerate(knowledge):
            if char == self.Not:
                if i + 1 < len(knowledge) and knowledge[i + 1] == "(":
                    end = self.matching_parens(knowledge, i + 1)
                    inside = knowledge[i + 2:end]

                    # we could have single literal, or conjunctions or disjunctions
                    if self.And in inside or self.Or in inside:
                        # ands become ors ors become ands
                        new_inside = ''
                        new_operator = self.Or if self.And in inside else self.And
                        for c in inside:
                            if c.isalpha():
                                new_inside += self.Not + c
                            elif c == self.And or c == self.Or:
                                new_inside += new_operator
                            else:
                                new_inside += c

                        # replace only the ~(...) portion then end we are done
                        output += (f'({new_inside})' + knowledge[end + 1:])
                        break
                    else:
                        # just add the not
                        output += self.Not


            else:
                output += char  #rebuild string as we go
       # print("END: Move NOT in:", output)
        return output

    def clean_expression(self, knowledge):
        knowledge = knowledge.replace(" ", "")

        # remove (V) >> V
        knowledge = re.sub(r'\(([A-Z])\)', r'\1', knowledge)

        # remove ( ..... ) from outside
        if knowledge.startswith("(") and knowledge.endswith(")"):
            if self.matching_parens(knowledge, 0) == len(knowledge) - 1:
                knowledge = knowledge[1:-1]

        return knowledge

    @staticmethod
    def matching_parens(expression, start):
        depth = 0
        for i in range(start, len(expression)):
            if expression[i] == "(":
                depth += 1
            elif expression[i] == ")":
                depth -= 1
                if depth == 0:
                    return i
        raise ValueError("Unmatched parenthesis")

    @staticmethod
    def operators_at_different_levels(expression):
        depth = 0
        operator_depths = {}

        for char in expression:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char in ("&", "|"):
                operator_depths.setdefault(char, set()).add(depth)

        return any(a_depth != o_depth for a_depth in operator_depths.get("&", set()) for o_depth in operator_depths.get("|", set()))

    @staticmethod
    def print_error(error):
        print(f'\033[91m{error}\033[0m')

    def __str__(self):
        return f"Action: {self.Action}, Knowledge: {self.Knowledge}{f", Weight: {self.Weight}" if self.Action == 'TELL' else ""}"


# TODO explain yourself in the __str__ How you were derived or why you exist


class KnowledgeBase:
    def __init__(self):
        self.Facts = {}  # dictionary of facts known and derived, keyed on all known truths

    def tell(self, fact):
        if fact.Knowledge in self.Facts:
            return

        self.Facts[fact.Knowledge] = fact
        print(f'ADDED: {fact}')
        # we need to infer and tell anything we can from this fact
        # if not fact.ground_truth():
        #     # we do have parts to work with
        #     # they will have their current known weights that have been deduced as needed and can be used to update
        #     # any other changing values
        #     variables_from_knowledge = fact.deconstructed_variables(self)
        #     for v in variables_from_knowledge:
        #         newfact = Fact(f'TELL {v} {variables_from_knowledge[v]}', self)
        #         newfact.Justifications.append(fact.Knowledge)
        #         if fact.is_implication():
        #             fact.Assumptions.append(newfact.Knowledge)
        #         self.tell(newfact)  #dummy action that will never be called but for the unelegant split I am using

    def ask(self, fact):
        # print(f'ASK - {fact}')
        return self.ask_string(fact.Knowledge)

    def ask_string(self, knowledge):

        #todo Ask could be complicated like ASK (A) -> (Q)
        #todo Need a because method that trails back and says where I came from, which could loop on collections of inferences
        return self.Facts[knowledge].Weight if self.Facts.get(knowledge) else 0.0

    def retract(self, fact):
        # recursive? retracting can crawl around children to see if any retract, if none then return
        # can check parents to see if that was the only parent, if so you will be set retracted
        # then keep recursively diving into affected children
        print(f'RETRACT - {fact.Knowledge}')
        # todo check if any OTHER parents exist that prevent this specific retraction from deleting
        # todo this will split into sub retracts when cnf  is A & B and retract A and retract B
        existing_fact = self.Facts[fact.Knowledge]
        # only delete if there are NOT any other justifications
        if not any(k != fact.Knowledge for k in existing_fact.Justifications):
            if existing_fact:
                print(f'Retracting fact for {fact.Knowledge} is {existing_fact}')

            del self.Facts[fact.Knowledge]
            # cascade retractions
            for a in existing_fact.Assumptions:
                self.retract(self.Facts[a])
        else:
            print(f'{existing_fact} was not retracted because it was justified by {existing_fact.Justifications}')


    def re_evaluate(self, fact):
        #
        l = 6

    def anded(self, p, q):
        return min(p, q)

    def ored(self, p, q):
        return max(p, q)

    def __str__(self):
        output = '======= KB Fact Dump =======\n\r'
        for f in self.Facts:
            output += f'{f}\n\r'
        return output
