import decimal
import re

class Fact:
    Implies = '->'
    Or = '|'
    And = '&'
    """
    • TELL <S> <W>
    • RETRACT <S>
    • ASK <S>
    """
    def __init__(self, statement):
        # First position action, last is weight if it has weight
        parts = [part.strip() for part in statement.split()]
        self.Action = parts[0]
        self.Knowledge = " ".join(parts[1:-1] if self.Action == 'TELL' else parts[1:])
        self.Weight = decimal.Decimal(parts[-1]) if self.Action == 'TELL' else 0.0
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



    # def operators_ordered:
    #     return re.

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
        if fact.Action == 'NOOP':
            return
        # Do stuff with it here
        print(f'TELL - {fact}')
        # some debug stuff remove
        if self.Facts.get(fact.Knowledge):
            print(f'==== Existing fact for {fact.Knowledge} is {self.Facts[fact.Knowledge]} and will be replaced with {fact} ====')

        self.Facts[fact.Knowledge] = fact
        # we need to infer and tell anything we can from this fact
        if not fact.ground_truth():
            # we do have parts to work with
            # they will have their current known weights that have been deduced as needed and can be used to update
            # any other changing values
            variables_from_knowledge = fact.deconstructed_variables(self)
            for v in variables_from_knowledge:
                self.tell(Fact(f'NOOP {v}'))  #dummy action that will never be called but for the unelegant split I am using

    def ask(self, fact):
        print(f'ASK - {fact}')
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
        if self.Facts[fact.Knowledge]:
            print(
                f'Retracting fact for {fact.Knowledge} is {self.Facts[fact.Knowledge]}')

        del self.Facts[fact.Knowledge]

    def re_evaluate(self, fact):
        #
        l = 6

    def anded(self, p, q):
        return min(p, q)

    def ored(self, p, q):
        return max(p, q)