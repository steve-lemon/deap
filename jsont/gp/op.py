#   `op.py`
#   - operators
#   
#   ```sh
#   cd jsont
#   python -m unittest tests.test_str
import os, json

def load_json(txt):
    if not isinstance(txt, str): raise TypeError('txt should be str')
    return json.loads(txt.strip())

def copy_json(data):
    import copy
    return copy.deepcopy(data)

def dump_json(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2)

class AbstractGP(object):
    '''
    class: `AbstractGP`
    - abstract common class.
    '''
    pass

class JsonNode(AbstractGP):
    '''
    class: `JsonNode`
    - represent single node instance in GP process.
    '''
    _next = 100000
    def __init__(self, id='', head='', node=None):
        super().__init__()
        if not node is None and not isinstance(node, dict): raise TypeError('node should be dict')
        self.id = id                    # the id of this
        self.head = head                # the up-branch name
        self.node = node                # the json data

    def __repr__(self):
        return {'id':self.id,'head':self.head,'node':self.node}

    def hello(self):
        return 'json-node'

    @staticmethod
    def uuid():
        JsonNode._next += 1
        return '{}'.format(JsonNode._next)


class JsonTransformer(AbstractGP):
    '''
    class: `JsonTransformer`
    - transform input-json to output-json by searching branch-op.
    '''
    def __init__(self, input, output):
        super().__init__()
        self._input = load_json(input) if isinstance(input, str) else input
        self._output = load_json(output) if isinstance(output, str) else output
        self._tables = self.build_tables(self._input)
        self._nodes = {}            # map of JsonNode by id.

    def hello(self):
        return 'json-transformer'

    def build_tables(self, j):
        '''
        build `node` and `branch` lookup table.
        '''
        def reduce_node(M, B, H, N, id = '', attr = ''):
            ''' reduce `N` to M{id:node}, B[branch-name], H[head-branch] '''
            if (isinstance(N, list)):
                M[id] = N
                H[id] = attr
                for i,k in enumerate(N):
                    # print('{} : {}'.format(i, k))
                    reduce_node(M, B, H, N[i], '{}.{}'.format(id, i), '[{}]'.format(i))
            elif isinstance(N, dict):
                M[id] = N
                H[id] = attr
                for i,k in enumerate(N.keys()):
                    # print('{} - {}'.format(i, k))
                    B[k] = B[k] + 1 if k in B else 1       # increment count#
                    reduce_node(M, B, H, N[k], '{}.{}'.format(id, i), k)
            return (M, B, H)
        # build node-table by id to node.
        return reduce_node({}, {}, {}, j, '$')  # `$` means the root node.

    def nodes(self, id=None):
        ''' select node by id '''
        (NT, BT, UP) = self._tables
        if id is None: return list(NT.keys())
        if not id in NT: raise IndexError('node({}) is not found!'.format(id))
        return {'id':id, 'node':NT[id], 'head':UP[id]}

    def branches(self, i=None):
        ''' select branch by index(1...N) '''
        (NT, BT, UP) = self._tables
        keys = list(BT.keys())
        size = len(keys)
        i = int('{}'.format(i)) if i else 0
        if i == 0: return keys
        if i<0 or i > size: raise IndexError('branch[{}] is not found!'.format(i))
        return keys[i-1]

    def get(self, id):
        ''' get the node by id (or clone via origin) '''
        jn = self._nodes[id] if id in self._nodes else None
        if jn and jn.id != id: raise TypeError('get({}) is not json-node'.format(id)) 
        if jn is None:
            N = self.nodes(id)
            I = JsonNode.uuid()
            jn = JsonNode(I, N['head'], copy_json(N['node']))
            self._nodes[I] = jn
        return jn


##################################################
# MAIN FOR GP TREE
##################################################
import numpy, random, operator
from deap import algorithms, base, creator, tools, gp

def if_then_else(input, output1, output2):
    return output1 if input else output2
def my_sel(i):
    return ''

pset = gp.PrimitiveSetTyped("main", [], int)
pset.addPrimitive(my_sel, [int], str)
pset.addPrimitive(if_then_else, [str, int, int], int)
pset.addTerminal('x', str)
pset.addTerminal(3, int)

# pset.renameArguments(ARG0="x")
pset.addEphemeralConstant('x', lambda: '', str)
pset.addEphemeralConstant('y', lambda: random.randint(-10, 10), int)

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("expr", gp.genFull, pset=pset, min_=2, max_=4)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

def evalMultiplexer(individual):
    func = toolbox.compile(expr=individual)
    return 1,

toolbox.register("evaluate", evalMultiplexer)
toolbox.register("select", tools.selTournament, tournsize=7)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genGrow, min_=0, max_=2)
toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

def main():
    random.seed(10)
    pop = toolbox.population(n=40)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)
    
    algorithms.eaSimple(pop, toolbox, 0.8, 0.1, 40, stats, halloffame=hof)
    
    return pop, stats, hof

#! run main()
# $ python -m gp.op
if __name__ == "__main__":
    main()

