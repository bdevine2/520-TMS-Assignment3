import client
from Fact import KnowledgeBase, Fact
LOCAL_TESTING = True
UnityId = 'bdevine2'
Seed = 'ThETruTHISouTtHERe'
# MEMORY is other and it is declaring what you want to SAVE.
#    there is a small example of differing approaches I thought of
Mode = 'TIME'
'''
    Maybe we need to hand groups recursively?
    justification should contain the set of sentences that can infer this pg 354 book
'''


def handle_statement(kbase, new_statement):
    print(f'{new_statement}')
    fact = Fact(new_statement, kbase)
    act(kbase, fact)


def act(kbase, fact):
    match fact.Action:
        case 'TELL':
            resolved, new_facts = kbase.perform_resolution(fact, None)
            if resolved:
                # print(f'Performed resolution - new clauses found:')
                # for f in new_facts:
                #     print(f'  {f}')
                # new_facts dont exist in kb yet  and need to be resolved as well
                kbase.insert_and_resolve_new_facts(new_facts)

            kbase.tell(fact)
            #print(kbase)
            x = 1  # stop
        case 'ASK':
            # print(kbase)
            results, weight = kbase.ask(fact)
            print(f'{fact.Knowledge} is {results} with a weight of {weight}')
        case 'RETRACT':
            #print(kbase)
            cnf_parts = Fact.raw_cnf(fact.Knowledge)  # need cnf to work with but dont build in constructor
            kbase.retract(cnf_parts)
        case 'DONE':
            # noop
            _ = 1
        case _:
            print(f'Invalid action: {fact.Action}')


stuff = ''
kb = KnowledgeBase(Mode)
reset = True
statements = []
test_file = open("go_out_tms.txt", "r")   # open("samplefile.txt", "r")
while stuff != 'DONE':
    if LOCAL_TESTING:
        stuff = test_file.readline().strip()
    else:
        stuff = client.next_statement(UnityId, Seed, reset=reset)
    statements.append(stuff)
    reset = False
    handle_statement(kb, stuff)

print('++++++ INCOMING STATEMENTS ++++++')
for statement in statements:
    print(statement)

print('====== KNOWLEDGE BASE FACTS ======')
print(kb)
