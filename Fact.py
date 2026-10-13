import re

Implies = '->'
Or = '|'
And = '&'
Not = '~'

class Fact:

    """
    • TELL <S> <W>
    • RETRACT <S>
    • ASK <S>
    """
    def __init__(self, statement, kbase, already_cnf=False, derived=False):
        # First position action, last is weight if it has weight
        parts = [part.strip() for part in statement.split()]
        self.Action = parts[0]
        self.Knowledge = " ".join(parts[1:-1] if self.Action == 'TELL' else parts[1:])
        self.Weight = float(parts[-1]) if self.Action == 'TELL' else 0.0
        if self.Action != 'RETRACT' and not already_cnf:
            self.Knowledge = self.convert_to_cnf(kbase)  # TODO need to keep ground truth? and in other facts spawned
        """Could be csv per entry"""
        self.Justifications = []  # parent keys that imply this truth
        self.Assumptions = []  # child keys implied by this
        self.Derived = derived

    def ground_truth(self):
        # am I a truth value? ONLY 1 capitol letter means I am a truth so return my weight or 0 if I dont exist
        return self.Weight if re.fullmatch(r"[A-Z]", self.Knowledge) else 0.0

    def is_implication(self):
        return Implies in self.Knowledge

    def deconstructed_variables(self, kb):
        # tear apart the non ground truth values into pieces
        if self.ground_truth():
            return {self.Knowledge: self.Weight}
        else:
            if self.is_implication():
                # we have two () sets of truths or con/dis junctions
                operands = [part.strip() for part in self.Knowledge.split(sep=Implies)]
                return_set = {}
                for v in operands:
                    # return what we know from the KB, which could be a false, it could recursively seek to discover
                    return_set[v] = max(kb.ask_string(v),self.Weight)# todo fix later to update truth
                return return_set
            else:  # must be a truth constant, con/dis junction of some sort
                return {self.Knowledge: kb.ask_string(self.Knowledge)}

    def convert_to_cnf(self, kbase):
        # eliminate implications
        # move nots in
        # standardize/skolemize
        # distribute or over and
        cnf_knowledge = self.Knowledge
        newer_facts = []
        if Implies in cnf_knowledge:
            cnf_knowledge = self.elim_implications(cnf_knowledge)
        if Not in cnf_knowledge:
            # if we had an implication then we will have 1 not we have to move in
            cnf_knowledge = self.move_not_in(cnf_knowledge)
        if And in cnf_knowledge and Or in cnf_knowledge:
            # special case, or over and, and over or
            # print(f'SPECIAL case :{cnf_knowledge}')
            expr = self.clean_expression(cnf_knowledge)

            # top or depth
            depth = 0
            or_index = -1

            for i, char in enumerate(expr):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                elif char == Or and depth == 0:
                    or_index = i
                    break

            if or_index != -1:
                left = expr[:or_index].strip()
                right = expr[or_index + 1:].strip()

                # A | (B & C)
                if right.startswith("(") and self.matching_parens(right, 0) == len(right) - 1:
                    inside = right[1:-1]

                    if And in inside:
                        b, c = inside.split(And, 1)
                        cnf_knowledge = (
                            f"({left}{Or}{b.strip()})"
                            f"{And}"
                            f"({left}{Or}{c.strip()})"
                        )

                # (A & B) | C
                elif left.startswith("(") and self.matching_parens(left, 0) == len(left) - 1:
                    inside = left[1:-1]

                    if And in inside:
                        a, b = inside.split(And, 1)
                        cnf_knowledge = (
                            f"({a.strip()}{Or}{right})"
                            f"{And}"
                            f"({b.strip()}{Or}{right})"
                        )

            # will return one and add the other directly to the kb via tell clean outer ( ) first here
            parts = self.clean_expression(cnf_knowledge).split(And)

            # only want the variable
            parts = [self.clean_expression(p) for p in parts]

            fact = Fact(f"TELL {parts[0]} {self.Weight}", kbase, True)
            resolved, n_facts = kbase.perform_resolution(fact, [parts[1]])

            if resolved:
                newer_facts.extend(n_facts)
            # need to sneak add the extra literal here
            kbase.tell(fact)

            # Return the second part
            cnf_knowledge = parts[1]


        elif And in cnf_knowledge and not self.operators_at_different_levels(cnf_knowledge):
            # a & b or a & b & c & d..
            # a
            # b
            # will return one and add the other directly to the kb via tell clean outer ( ) first here
            parts = self.clean_expression(cnf_knowledge).split(And)

            # only want the variable
            parts = [self.clean_expression(p) for p in parts]

            fact = Fact(f"TELL {parts[0]} {self.Weight}", kbase, True)
            resolved, n_facts = kbase.perform_resolution(fact, [parts[1]])

            if resolved:
                newer_facts.extend(n_facts)
            # need to sneak add the extra literal here
            kbase.tell(fact)

            # Return the second part
            cnf_knowledge = parts[1]

        if len(newer_facts) > 0:
            kbase.insert_and_resolve_new_facts(newer_facts)

        cnf_knowledge = self.clean_expression(cnf_knowledge)
        # print(f'Cleaned: {cnf_knowledge}')
        return cnf_knowledge

    @staticmethod
    def raw_cnf(cnf_knowledge):
        # eliminate implications
        # move nots in
        # standardize/skolemize
        # distribute or over and
        return_knowledge = [cnf_knowledge] # start out like this because 1 literal
        if Implies in cnf_knowledge:
            cnf_knowledge = Fact.elim_implications(cnf_knowledge)
            return_knowledge = [cnf_knowledge]
        if Not in cnf_knowledge:
            # if we had an implication then we will have 1 not we have to move in
            cnf_knowledge = Fact.move_not_in(cnf_knowledge)
            return_knowledge = [cnf_knowledge]
        if And in cnf_knowledge and Or in cnf_knowledge:
            # special case, or over and, and over or
            expr = Fact.clean_expression(cnf_knowledge)
            # top or depth
            depth = 0
            or_index = -1
            for i, char in enumerate(expr):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                elif char == Or and depth == 0:
                    or_index = i
                    break
            if or_index != -1:
                left = expr[:or_index].strip()
                right = expr[or_index + 1:].strip()
                # A | (B & C)
                if right.startswith("(") and Fact.matching_parens(right, 0) == len(right) - 1:
                    inside = right[1:-1]
                    if And in inside:
                        b, c = inside.split(And, 1)
                        cnf_knowledge = (
                            f"({left}{Or}{b.strip()})"
                            f"{And}"
                            f"({left}{Or}{c.strip()})"
                        )
                # (A & B) | C
                elif left.startswith("(") and Fact.matching_parens(left, 0) == len(left) - 1:
                    inside = left[1:-1]

                    if And in inside:
                        a, b = inside.split(And, 1)
                        cnf_knowledge = (
                            f"({a.strip()}{Or}{right})"
                            f"{And}"
                            f"({b.strip()}{Or}{right})"
                        )
            # will return one and add the other directly to the kb via tell clean outer ( ) first here
            parts = Fact.clean_expression(cnf_knowledge).split(And)
            # only want the variable
            parts = [Fact.clean_expression(p) for p in parts]
            # Return the second part
            return_knowledge = parts
        elif And in cnf_knowledge and not Fact.operators_at_different_levels(cnf_knowledge):
            parts = Fact.clean_expression(cnf_knowledge).split(And)
            # only want the variable
            parts = [Fact.clean_expression(p) for p in parts]
            return_knowledge = parts

        cnf_knowledge = [
            Fact.clean_expression(part)
            for part in return_knowledge
        ]
        return cnf_knowledge

    @staticmethod
    def elim_implications(knowledge):
        left, right = knowledge.split(Implies)
        # not a V b in the form (V) -> (Z) where V could be (Y & A) or Z could be (O | L)
        # do step 1 and eliminate implications
        return f"({Not}{left.strip()} {Or} {right.strip()})"  # add parens we will strip later

    @staticmethod
    def move_not_in(knowledge):
        # print("START: Move NOT in:", knowledge)
        output = ''
        found_not = False
        for i, char in enumerate(knowledge):
            if char == Not:
                if i + 1 < len(knowledge) and knowledge[i + 1] == "(":
                    end = Fact.matching_parens(knowledge, i + 1)
                    inside = knowledge[i + 2:end]

                    # we could have single literal, or conjunctions or disjunctions
                    if And in inside or Or in inside:
                        # ands become ors ors become ands
                        new_inside = ''
                        new_operator = Or if And in inside else And
                        for c in inside:
                            if c.isalpha():
                                new_inside += Not + c
                            elif c == And or c == Or:
                                new_inside += new_operator
                            else:
                                new_inside += c

                        # replace only the ~(...) portion then end we are done
                        output += (f'({new_inside})' + knowledge[end + 1:])
                        break
                    else:
                        # just add the not
                        output += Not
            else:
                output += char  # rebuild string as we go
        return output


    @staticmethod
    def clean_expression(knowledge):
        knowledge = knowledge.replace(" ", "")
        # do this first ~(G) -> ~G
        knowledge = re.sub(r'~\(([A-Z])\)', r'~\1', knowledge)
        # now this, its extra work but clean (G) -> G
        knowledge = re.sub(r'(?<!~)\(([A-Z])\)', r'\1', knowledge)
        # remove ( ..... ) from outside
        if knowledge.startswith("(") and knowledge.endswith(")"):
            if Fact.matching_parens(knowledge, 0) == len(knowledge) - 1:
                knowledge = knowledge[1:-1]

        return knowledge

    def get_literals(self):
        return re.findall(r'~?[A-Z]', self.Knowledge)

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
        return f"Action: {self.Action}, Knowledge: {self.Knowledge}{f", Weight: {self.Weight}" if self.Action == 'TELL' else ""}, Assumptions: {self.Assumptions}, Justifications: {self.Justifications}"


# TODO explain yourself in the __str__ How you were derived or why you exist


class KnowledgeBase:
    def __init__(self, mode: str):
        self.Facts = {}  # dictionary of facts known and derived, keyed on all known truths
        self.Literals = {}  # potential dict used if in TIME mode to save lookup time
        self.Mode = mode

    def insert_and_resolve_new_facts(self, new_facts):
        newer_facts = []
        for fact in new_facts:
            resolved, n_facts = self.perform_resolution(fact, [f.Knowledge for f in new_facts if f.Knowledge != fact.Knowledge])
            #print(f'resolved {resolved} - new facts {n_facts}')
            if resolved:
                newer_facts = n_facts

            self.tell(fact)
            if len(newer_facts) > 0:
                self.insert_and_resolve_new_facts(newer_facts)



    def perform_resolution(self, fact: Fact, incoming_fact_strings: list):
        #print(f'starting resolution {fact} - {incoming_fact_strings}')
        clause = fact.Knowledge
        literals_to_resolve = fact.get_literals()
        weight = fact.Weight
        resolutions_found = False
        new_facts = {}
        if len(self.Facts) < 1:
            return resolutions_found, []  # one fact nothing to resolve
        # start with fact 1 and forward chain
        # grab a literal and select all inverse facts

        for literal in literals_to_resolve:
            resolutions_found = True
            # find opposites
            negative_literal = self.negate(literal)
            # print(f'Token to resolve: {token} for literal: {literal}')
            # get the list of linked truths
            # create a list we can use as we resolve this literal
            facts_with_literal_opposite = self.Literals.get(negative_literal, []) if self.Mode == "TIME" else []  # TODO if doing MEM ever
            #    print(f'Facts that have token: {facts_with_literal_opposite}')
            for fact_literals in facts_with_literal_opposite:
                # weight for the newest object we are calling resolve with
                # also passing its clause and literals in the clause to resolve against

                fact_object = self.Facts.get(fact_literals)
                if fact_object is None:
                    z = 1
                # fact_obj is the other fact we can resolve with since we have opposing literals
                # 3 algorithms should be considered
                # book: min/max
                # just because: avg
                # complex based on fuzzy logic which will probably be just min for | TODO or is this the same as #1?
                #  If complex is the same as 1 do something where you weight how many records they are a part of


                new_fact = self.merge_expressions(re.findall(r'~?[A-Z]', clause), literal, re.findall(r'~?[A-Z]', fact_literals))
                # print(f'Incoming facts: {incoming_fact_strings} - New Fact: {new_fact}')
                if new_fact and (incoming_fact_strings is None or all(set(self.get_literals(new_fact)) != set(self.get_literals(clause)) for clause in incoming_fact_strings)):
                    add = True
                    for f in new_facts.values():
                        existing_literals = self.get_literals(f.Knowledge)
                        literals = self.get_literals(new_fact)
                        if set(literals) == set(existing_literals):
                            add = False
                            print(f'Skipping - {literals} : {existing_literals}')
                            break
                    if add and self.ensure_new(new_fact):
                        # ensure no existing combination of these variables exists
                        new_fact_obj = Fact(f"TELL {new_fact} {weight}", self, True, derived=True)  # derived via resolution
                        fact.Assumptions.append(new_fact)
                        # justification for this are the two that were merged. If one is removed then this must also be retracted
                        new_fact_obj.Justifications.append(f'{clause},{fact_literals}')
                        new_facts[new_fact] = new_fact_obj
                        # print(f'New fact added during resolution: {new_fact} weight: {weight}')
        return resolutions_found, list(new_facts.values())
# two modes mem, time second dict by literal
# add second on tell for all the literals

    @staticmethod
    def negate(literal):
        return f'~{literal}' if Not not in literal else literal.replace('~', '')

    @staticmethod
    def merge_expressions(expression1_literals: list, literal, expression2_literals: list):
        # print(f'Expression 1 {expression1_literals} Expression 2 {expression2_literals} - Joining literal negation: {literal} ')
        neg_literal = KnowledgeBase.negate(literal)
        # print(f'Negative literal: {neg_literal}')
        if literal not in expression1_literals or neg_literal not in expression2_literals:
            return None

        # get literals that are not the ones we are removing
        # this may produce an empty list in one which is fine
        remaining = [
            item for item in expression1_literals if item != literal
        ]
        remaining += [
            item for item in expression2_literals if item != neg_literal
        ]
    #    print(f'Remaining literals: {remaining}')
        # Remove duplicate literals while preserving order.
        remaining = list(dict.fromkeys(remaining))

        # throw away any A | ~A
        if any(KnowledgeBase.negate(item) in remaining for item in remaining):
            return None

        #TODO is this ok to be empty here?
        if len(remaining) == 0:
            Fact.print_error('Empty')
        return "|".join(remaining)

    def tell(self, fact: Fact):
        self.Facts[fact.Knowledge] = fact

        if self.Mode == 'TIME':
            # build usable cross ref dictionary that links literals to facts that contain them
            literals = fact.get_literals()
            for literal in [literal for literal in literals if literal != fact.Knowledge]:
                items = self.Literals.setdefault(literal, [])  # get existing list if exists or a blank one
                if fact.Knowledge not in items:
                    items.append(fact.Knowledge)  # not already in so add it to the list

    def ask(self, fact: Fact):
        # print(f'ASK - {fact}')
        return self.ask_string(fact.Knowledge)

    @staticmethod
    def is_literal_only(check_string):
        return re.fullmatch(r"[A-Z]", check_string)

    @staticmethod
    def get_literals(clause):
        return re.findall(r'~?[A-Z]', clause)

    def clean_literals(self, deleting_cnf):
        for literal_list in self.Literals.values():
            if deleting_cnf in literal_list:
                literal_list.remove(deleting_cnf)

    def ask_string(self, knowledge: str):
        #### if not directly found do a MAX for all that contain it because we are a conjunction of truths
        cnf_s = Fact.raw_cnf(knowledge)
        #todo Ask could be complicated like ASK (A) -> (Q)
        #todo Need a because method that trails back and says where I came from, which could loop on collections of inferences

        # need to evaluate if I am in some OR I can deduce something if I do not have a direct weight!
        # if there are more than one clause then self.anded
        for know in cnf_s:
            not_know = None
            if self.is_literal_only(know):
                # this is a single literal checking inverse is simple
                not_know = KnowledgeBase.negate(know)
            if self.Facts.get(know):
                return self.Facts[know].Weight  # DIRECTLY known
            elif not_know and self.Facts.get(not_know):
                return 1 - self.Facts[not_know].Weight  # INDIRECTLY known
            else:
                if not_know:
                    # we are a literal so get everything that references us
                    lits = self.Literals.get(know)
                    if lits:
                        values = []
                        for literal in lits:
                            if self.Facts.get(literal):
                                values.append(self.Facts[literal].Weight)
                        #TODO define functions here
                        return min(values)  # because its anded clauses so return min as value since we did not find ground truth
                    elif not_know:
                        # try the NOT 1 - weight value for single literal
                        un_lits = self.Literals.get(know)
                        if un_lits:
                            values = []
                            for literal in un_lits:
                                if self.Facts.get(literal):
                                    values.append(self.Facts[literal].Weight)
                            # TODO define functions here
                            return 1 - min(values)  # because its anded clauses so return min as value since we did not find ground truth
                else:
                    know_literals = self.get_literals(know)
                    # maybe we can find some value for the pieces and max them because this should be a disjunction
                    values = []
                    for literal in know_literals:
                        values.append(self.ask_string(literal))

                    if len(values) > 0:
                        # TODO define functions here
                        return min(values)
                    return 0.0  # for now cannot determine!

    def retract(self, clauses):
        # recursive? retracting can crawl around children to see if any retract, if none then return
        # can check parents to see if that was the only parent, if so you will be set retracted
        # then keep recursively diving into affected children

        for cnf in clauses:
            print(f'RETRACT - {cnf}')
            # todo check if any OTHER parents exist that prevent this specific retraction from deleting
            # todo this will split into sub retracts when cnf  is A & B and retract A and retract B
            # TODO need to update weights after retract
            existing_fact = self.Facts[cnf]
            # only delete if there are NOT any other justifications
            print(f'Existing justifications for this item: {existing_fact.Justifications}')
            if not any(cnf in k.split(',') for k in existing_fact.Justifications):  # do we have any other justifications?
                if existing_fact:
                    print(f'Retracting fact for {cnf} is {existing_fact}')

                del self.Facts[cnf]

                if KnowledgeBase.is_literal_only(cnf):
                    # need to recalc w and ~w
                    not_literal = self.negate(cnf)
                    neg_clauses_to_evaluate = self.Literals.get(cnf, [])
                    for neg_clause in neg_clauses_to_evaluate:
                        # need to recalc w and ~w
                        not_literal = self.negate(neg_clause)
                else:
                    self.clean_literals(cnf)  # removes it from lists
                # cascade retractions
                for f in self.Facts.values():
                    for j in f.Justifications:
                        print(j)
                        # self.retract([self.Facts[a].Knowledge])
            else:
                print(f'{existing_fact} was not retracted because it was justified by {existing_fact.Justifications}')

            #now find and update any weights to 0

    def set_new_weight(self, new_weight, clause):
        # need to determine how to update the weight based on the clause and what we know
        if Or in clause:
            # will be max of values
            literals = self.get_literals(clause)
        else:
            #
            x=2

    '''This either gets ground truth or min of all clauses'''
    def get_weight(self, literal):
        # find exact if exists
        if self.Facts.get(literal):
            return self.Facts[literal].Weight  # DIRECTLY known
        else:
            # and everything and do min
            if self.Literals.get(literal):
                clauses = self.get_literals(literal)
                w = float('inf')
                for c in clauses:
                    if self.Facts.get(c):
                        w - min(c.Weight, w)

                return w if w != float('inf') else 0.0
            else:
                return 0.0  # no knowledge of that fact, nor supporting facts

    def ensure_new(self, clause):
        # we are a conjunction of disjunctions so any order is fine
        literals = self.get_literals(clause)
        for f in self.Facts:
            existing_literals = self.get_literals(f)
            if set(literals) == set(existing_literals):
                return False
        return True

    def anded(self, p, q):
        return min(p, q)

    def ored(self, p, q):
        return max(p, q)

    def __str__(self):
        output = '======= KB Fact Dump =======\n\r'
        for f in self.Facts.values():
            output += f'{f}\n\r'
        return output
