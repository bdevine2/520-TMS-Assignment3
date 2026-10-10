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
            resolved, new_facts = kbase.perform_resolution(fact.Knowledge, fact.get_literals(), fact.Weight)
            if resolved:
                # print(f'Performed resolution - new clauses found:')
                # for f in new_facts:
                #     print(f'  {f}')
                # new_facts dont exist in kb yet  and need to be resolved as well
                kbase.insert_and_resolve_new_facts(new_facts)

            kbase.tell(fact)
        case 'ASK':
            # print(kbase)
            print(f'Response: {kbase.ask(fact)}')
        case 'RETRACT':
            kbase.retract(fact)
        case 'DONE':
            # noop
            _ = 1
        case _:
            print(f'Invalid action: {fact.Action}')


stuff = ''
kb = KnowledgeBase(Mode)
reset = True
statements = []
test_file = open("samplefile.txt", "r")
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
