import client
from Fact import KnowledgeBase, Fact
LOCAL_TESTING = True
UnityId = 'bdevine2'
Seed = 'ThETruTHISouTtHERe'
# MEMORY is other and it is declaring what you want to SAVE. there is a small example of differing approaches I thought of
Mode = 'TIME'
'''
    Maybe we need to hand groups recursively?
    justification should contain the set of sentences that can infer this pg 354 book
'''


def handle_statement(kbase, statement):
    print(f'Incoming statement: {statement}')
    fact = Fact(statement, kbase)
    do_resolution = act(kbase, fact)
    if do_resolution:
        # now we need to derive anything new starting at the beginning.
        resolved = kbase.perform_resolution(fact.Knowledge, fact.get_literals(), fact.Weight)
        if resolved:
            print(f'Performed resolution - new clauses found: {resolved}')


def act(kbase, fact):
    perform_resolution = False
    match fact.Action:
        case 'TELL':
            perform_resolution = True
            kbase.tell(fact)
        case 'ASK':
            print(f'Response: {kbase.ask(fact)}')
        case 'RETRACT':
            kbase.retract(fact)
        case 'DONE':
            # noop
            _ = 1
        case _:
            print(f'Invalid action: {fact.Action}')
    return perform_resolution


stuff = ''
kb = KnowledgeBase(Mode)
reset = True
test_file = open("samplefile.txt", "r")
while stuff != 'DONE':
    if LOCAL_TESTING:
        stuff = test_file.readline().strip()
    else:
        stuff = client.next_statement(UnityId, Seed, reset=reset)
    # print(f'Raw: {stuff}')
    reset = False
    handle_statement(kb, stuff)
print(kb)
