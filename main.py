import client
from Fact import KnowledgeBase, Fact
LOCAL_TESTING = True
UnityId = 'bdevine2'
Seed = 'ThETruTHISouTtHERe'

'''
    Maybe we need to hand groups recursively?
    justification should contain the set of sentences that can infer this pg 354 book
'''


def handle_statement(kbase, statement):
    print(f'Incoming statement: {statement}')
    fact = Fact(statement, kbase)
    act(kbase, fact)


def act(kbase, fact):
    match fact.Action:
        case 'TELL':
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


stuff = ''
kb = KnowledgeBase()
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
