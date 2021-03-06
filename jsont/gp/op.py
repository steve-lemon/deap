#   `op.py`
#   - operators
#   
#   ```sh
#   cd jsont
#   python -m unittest tests.test_str
import os, json

def load_json(txt):
    if not isinstance(txt, str): raise TypeError('txt should be str')
    if txt.startswith('./'):        # as file-name
        with open(txt, 'r') as f:
            return json.load(f)
    return json.loads(txt.strip())  # as json-text

def copy_json(data):
    import copy
    return copy.deepcopy(data)

def dump_json(data,indent=2):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=indent)

def spec_json(data, forward=True):
    ''' convert json to spec format '''
    def walker(N):
        if isinstance(N, dict):
            for i,k in enumerate(N):
                N[k] = walker(N[k])
        elif isinstance(N, list):
            return { '*': walker(N[0]) if len(N) > 0 else None }    # transform `[A,B,...]`` to `{ '*': A }``
        return N
    return walker(data)

def build_tables(jsn):
    '''
    build `node` and `branch` lookup table.
    @param M - map of node by id
    @param B - branch count by name
    @param H - head of node by id
    @param N - current node.
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
    return reduce_node({}, {}, {}, spec_json(jsn), '$')  # `$` means the root node.

def score(left, right, branch='', depth=0):
    ''' calculate element's score '''
    isdict = right and isinstance(right, dict)
    if not isdict:
        # check if same value at leaf.
        if not left is None and left == right and type(left) == type(right):
            # print('>> @{}[{}] {}=={}'.format(branch, depth, left, right))
            return { 'n': 0, 'l': 1, 't': 1, 'd': depth }
        return { 'n': 0, 'l': 0, 't': 1, 'd': depth }        
    # search in deep
    Rs = list(right.keys())
    Ls = list(left.keys()) if left and isinstance(left, dict) else []
    # print('> @{}[{}].Rs={}'.format(branch, depth, Rs))
    # print('> @{}[{}].Ls={}'.format(branch, depth, Ls))
    Out = [x for x in Ls if not x in Rs]
    R = { 'n': 1 if len(Ls) > 0 else 0 , 'l': 0, 't': 1 + len(Out), 'd': depth }
    for i,k in enumerate(Rs):
        # print('>> [{}]={}'.format(i, k))
        S = score(left[k] if k in Ls else None, right[k] if k in Ls else None, k, depth+1)
        R['n'] += S['n'] if 'n' in S else 0                     # node count
        R['l'] += S['l'] if 'l' in S else 0                     # leaf count
        R['t'] += S['t'] if 't' in S else 0                     # total count
        R['d'] = max(R['d'], S['d'] if 'd' in S else 0)         # max depth.
    # `Expense` summary.
    return R

def fitness(left, right):
    ''' calculate tree fitness '''
    S = score(left, right)
    return S['n'] + (1.0 * (S['n'] + S['l'])) / max(S['t'], 1)

class AbstractGP(object):
    '''
    class: `AbstractGP`
    - abstract common class.
    '''
    def __init__(self):
        pass

class JsonNode(AbstractGP):
    '''
    class: `JsonNode`
    - represent single node instance in GP process.
    '''
    _next = 100000
    def __init__(self, id='', head='', node=None, src=''):
        super().__init__()
        if not node is None and not isinstance(node, dict): raise TypeError('node({}/{}) should be dict'.format(head, id))
        self.id = id                    # the id of this
        self.head = head                # the up-branch name
        self.node = node                # the json data
        self._src = src                 # the origin-id of source

    def __repr__(self):
        return {'id':self.id,'head':self.head,'node':self.node}

    def hello(self):
        return 'json-node'

    def has_brach(self, branch):
        if branch == '': return False
        return self.node and isinstance(self.node, dict) and branch in self.node

    def branch(self, branch=''):
        ''' move self to branch node '''
        if not branch: return self
        if self.has_brach(branch):
            self.head = branch
            self.node = self.node[branch]
        else:
            self.node = None            # clear self' node
        return self
    
    def child(self, branch=''):
        ''' move self to child node by branch '''
        if not branch: return self
        if self.has_brach(branch):
            self.node = self.node[branch]
        else:
            self.node = None            # clear self' node
        return self
    
    def child2(self, branch='', branch2=''):
        ''' move self to child node by branch '''
        if not branch: return self
        if self.has_brach(branch):
            node = self.node[branch]
            if branch2 and node and isinstance(node, dict) and branch2 in node:
                self.node[branch] = node[branch2]   # replace branch.
            else:
                self.node = None
        else:
            self.node = None            # clear self' node
        return self
    
    def last(self):
        ''' get the last branch name '''
        if self.node and isinstance(self.node, dict):
            keys = list(self.node.keys())
            return keys[-1]
        return ''

    def first(self):
        ''' get the fist branch name '''
        if self.node and isinstance(self.node, dict):
            keys = list(self.node.keys())
            return keys[0]
        return ''

    def append(self, right):
        if self.node and isinstance(self.node, dict):
            if right and right.head:
                self.node[right.head] = copy_json(right.node) if right.node else None
        return self


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
        self._input  = load_json(input) if isinstance(input, str) else input
        self._output = load_json(output) if isinstance(output, str) else output
        self._tables = build_tables(self._input)
        self._nodes  = {}            # map of JsonNode by id.

    def hello(self):
        return 'json-transformer'

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
            jn = JsonNode(I, N['head'], copy_json(N['node']), id)
            self._nodes[I] = jn
        return jn

    def select(self, id, idx=0):
        ''' select the node by (id, idx?) '''
        branch = '' if not idx else self.branches(idx)
        return self.get(id).branch(branch)

    def child(self, id, idx=0):
        ''' go donwn to child by (idx) '''
        branch1 = '' if not idx else self.branches(idx)
        return self.get(id).child(branch1)

    def child2(self, id, idx1=0, idx2=0):
        ''' go donwn to child by (idx) '''
        branch1 = '' if not idx1 else self.branches(idx1)
        branch2 = '' if not idx2 else self.branches(idx2)
        return self.get(id).child2(branch1, branch2)

    def append(self, left, right):
        ''' append right-node to left-node '''
        if not left: raise IndexError('@left (id) is required at append!')
        if not right: raise IndexError('@right (id) is required at append!')
        left = self.get(left)
        right = self.get(right)
        return left.append(right)

    def fitness(self, id):
        ''' calculate the fitness of node[id] '''
        left = self.get(id).node
        right = self._output
        return fitness(left, right)

    def run(self, population=40, max_=4):
        import numpy, random, operator
        from deap import algorithms, base, creator, tools, gp

        node_id_list = self.nodes()         # like ['$.0']
        node_branches = self.branches()     # like ['a','b']
        print('! node_id_list = {}'.format(node_id_list))

        #! operators
        _branch = lambda b: node_branches.index(b) if b in node_branches else 0
        select  = lambda id, idx: self.select(id, idx).id           # (str, int) -> str
        child   = lambda id, idx: self.child(id, idx).id            # (str, int) -> str
        child2  = lambda id, i1, i2: self.child2(id, i1, i2).id     # (str, int, int) -> str
        append  = lambda id1, id2: self.append(id1, id2).id         # (str, str) -> str
        head    = lambda id: 0                                      # (str) -> int
        first   = lambda id: _branch(self.get(id).first())          # (str) -> int
        last    = lambda id: _branch(self.get(id).last())           # (str) -> int

        #! prepare GP
        pset = gp.PrimitiveSetTyped("main", [], str)
        pset.addPrimitive(select, [str, int]        , str, name='select')
        # pset.addPrimitive(child , [str, int]      , str, name='child')
        pset.addPrimitive(child2, [str, int, int]   , str, name='child2')
        pset.addPrimitive(append, [str, str]        , str, name='append')
        pset.addPrimitive(first , [str]             , int, name='first')
        # pset.addPrimitive(last  , [str]           , int, name='last')
        pset.addTerminal(0, int)
    
        #! ephemeral-constrant
        pset.addEphemeralConstant('id', lambda: random.choice(node_id_list), str)
        pset.addEphemeralConstant('idx', lambda: random.randint(0, len(node_branches)), int)

        #! fitness
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("expr", gp.genFull, pset=pset, min_=2, max_=max_)
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("compile", gp.compile, pset=pset)

        def evaluate(individual):
            id = toolbox.compile(expr=individual)
            fit = self.fitness(id)
            # print('> node[{}] = {:1f} - {}'.format(id, fit, dump_json(self.get(id).node)))
            return fit,

        toolbox.register("evaluate", evaluate)
        toolbox.register("select", tools.selTournament, tournsize=7)
        toolbox.register("mate", gp.cxOnePoint)
        toolbox.register("expr_mut", gp.genGrow, min_=0, max_=2)
        toolbox.register("mutate", gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

        #! gen statistics
        pop = toolbox.population(n=population)
        hof = tools.HallOfFame(1)
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", numpy.mean)
        stats.register("std", numpy.std)
        stats.register("min", numpy.min)
        stats.register("max", numpy.max)
        
        algorithms.eaSimple(pop, toolbox, 0.8, 0.1, 40, stats, halloffame=hof)
        
        best_solution = tools.selBest(pop, 1)[0]
        best_id = toolbox.compile(expr=best_solution)

        print("-"*64)
        print("Branches      = %s "   % ( node_branches ))
        print("Best Score    = %s "   % ( best_solution.fitness.values ))
        print("Best Solution = %s "   % ( best_solution ))
        print("Best Node[%s] = %s "   % ( best_id, dump_json(self.get(best_id).node) ))
        # print("Expected      = %s "   % ( dump_json(self.get(toolbox.compile(expr="select(select('$.0', 0), first(select('$', 0)))")).node, indent=None) ) )
        print("Expected      = %s "   % ( dump_json(self.get(toolbox.compile(expr="child2(select('$.0', 0),0,2)")).node, indent=None) ) )
        print("-"*64)

        return pop, stats, hof,  best_solution

##################################################
# MAIN FOR GP TREE
##################################################
def main():
    import random
    random.seed(10)

    (A, B, C, D, E, F, G, H, I, J, X, Y, Z) = list('A,B,C,D,E,F,G,H,I,J,X,Y,Z'.split(','))
    (a, b, c, d, e, f, g, h, i, j, x, y, z) = list('a,b,c,d,e,f,g,h,i,j,x,y,z'.split(','))

    jt = JsonTransformer({ A:{ B:1 } }, { A:1 })        #TODO - improve! `child('$', last('$'))`
    # jt = JsonTransformer({ A:{ B:1 }, C:{ D: 2 } }, { A:1 })
    # jt = JsonTransformer({ A:{ B:1 } }, { B:1 })
    # jt = JsonTransformer({ A:{ B:1 }, C:{ D: 2 } }, { B:1 })
    # jt = JsonTransformer({ A:{ B:{ X:2 }} }, { X:2 })
    # jt = JsonTransformer({ A:{ B:{ X:2 }} }, { B:2 })
    # jt = JsonTransformer({ A:{ X:2, Y:3 } }, { A:3 })
    # jt = JsonTransformer({ A:{ X:2, Y:3 }, B:{ X:3, Y:4 } }, { A:3 })
    # jt = JsonTransformer({ A:{ X:2, Y:3 }, B:{ X:2, Y:3 } }, { X:2, A:3 })
    # jt = JsonTransformer({ A:{ X:2, Y:3 }, B:{} }, { X:2 })
    # jt = JsonTransformer({ A:{ X:[2] } }', '{ X:[2] }')
    # jt = JsonTransformer({ A:{ X:{ Y:Y, G:G }, Z:Z }, B:{ C:c }, D:d }, { A:'G' })
    (pop, stats, hof, best) = jt.run(50)

#! run main()
# $ python -m gp.op
if __name__ == "__main__":
    main()

