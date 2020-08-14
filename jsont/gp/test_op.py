#   
#   
#   
#   ```sh
#   cd jsont
#   python -m unittest tests.test_op
import unittest

#! input spec.
input = """
{
    "b":{
        "e":"E",
        "f":"F"
    },
    "c":"C",
    "d":{
        "g":"G",
        "h":[1]
    }
}
"""

#! output spec.
output = """
{
    "e":"E"
}
"""

class TestBranchOperation(unittest.TestCase):
    def test_hello(self):
        print('hello test-branch')

    def test_load_json(self):
        from . import op
        j = op.load_json(input)
        self.assertEqual(j['b']['e'], "E")
        self.assertEqual(j['b']['f'], "F")
        self.assertEqual(j['c'], "C")
        self.assertEqual(j['d']['g'], "G")
        self.assertIsNot(j, op.copy_json(j))
        self.assertEqual(op.dump_json(j), op.dump_json(j))
        self.assertEqual(op.dump_json(j), op.dump_json(op.copy_json(j)))

    def test_json_node(self):
        from . import op
        jn = op.JsonNode()
        self.assertEqual(jn.hello(), 'json-node')
        self.assertEqual(op.JsonNode._next, int('100000'))
        self.assertEqual(op.JsonNode.uuid(), '100001')
        self.assertEqual(op.JsonNode.uuid(), '100002')
        self.assertRaises(TypeError, lambda: op.JsonNode(node=''))

    def test_score(self):
        from . import op
        (A, B, C, D, E, F) = ('A', 'B', 'C', 'D', 'E', 'F')
        (n, l, t, d) = ('n', 'l', 't', 'd')
        check = lambda x,y,z: self.assertEqual(op.score(x, y), z)
        fit = lambda x,y,z: self.assertEqual(op.fitness(x, y), z)

        check(1, 1          ,{ n: 0, l: 1, t: 1, d: 0 })
        check(1, 0          ,{ n: 0, l: 0, t: 1, d: 0 })
        check(0, 1          ,{ n: 0, l: 0, t: 1, d: 0 })

        check({ A: 1 }, { A: 1 }                ,{ n: 1, l: 1, t: 2, d: 1 })    #! fitness = 1 + (1+1)/2
        check({ A: 0 }, { A: 1 }                ,{ n: 1, l: 0, t: 2, d: 1 })    #! fitness = 1 + (1+0)/2
        check({ A: 1 }, { A: { B: 1 } }         ,{ n: 1, l: 0, t: 3, d: 2 })    #! fitness = 1 + (1+1)/3

        check({ A: { B: 1 } }, { A: 1 }         ,{ n: 1, l: 0, t: 2, d: 1 })    #! fitness = 1 + (1+0)/2
        check({ B: { A: 1 } }, { A: 1 }         ,{ n: 1, l: 0, t: 3, d: 1 })    #! fitness = 1 + (1+1)/3
        check({ A: { B: 1 } }, { A: { B: 1 } }  ,{ n: 2, l: 1, t: 3, d: 2 })    #! fitness = 2 + (2+1)/3
        check({ A: { B: 1 } }, { A: { B: 2 } }  ,{ n: 2, l: 0, t: 3, d: 2 })    #! fitness = 2 + (2+0)/3
        check({ A: { C: 1 } }, { A: { B: 1 } }  ,{ n: 2, l: 0, t: 4, d: 2 })    #! fitness = 2 + (2+0)/4

        fit({ A: { B: 1 } }, { A: { B: 1 } }    ,2 + (2+1)/3.0 )    #! fitness = 2 + (2+1)/3
        fit({ A: { C: 1 } }, { A: { B: 1 } }    ,2 + (2+0)/4.0 )    #! fitness = 2 + (2+1)/4


    def test_json_transformer(self):
        from . import op
        jp = op.JsonTransformer(input, output)
        self.assertEqual(jp.hello(), 'json-transformer')

        # test build_tables() - node_table
        self.assertEqual(jp.build_tables({})[0], {'$':{}})
        self.assertEqual(jp.build_tables([])[0], {'$':[]})
        self.assertEqual(jp.build_tables({'a':1})[0], {'$':{'a':1}})
        self.assertEqual(jp.build_tables({'a':{'b':1}})[0], {'$':{'a':{'b':1}},'$.0':{'b':1}})
        self.assertEqual(list(jp.build_tables({'a':{'b':1}})[0].keys()), ['$','$.0'])

        # test build_tables() - branch_table
        self.assertEqual(jp.build_tables({})[1], {})
        self.assertEqual(jp.build_tables([])[1], {})
        self.assertEqual(jp.build_tables({'a':1})[1], {'a':1})
        self.assertEqual(jp.build_tables({'a':{'b':1}})[1], {'a':1,'b':1})

        # test build_tables() - up-branch of node
        self.assertEqual(jp.build_tables({})[2], {'$':''})
        self.assertEqual(jp.build_tables([])[2], {'$':''})
        self.assertEqual(jp.build_tables({'a':1})[2], {'$':''})
        self.assertEqual(jp.build_tables({'a':{'b':1}})[2], {'$':'','$.0':'a'}) # 'a' is branch name

        # test nodes() to select node
        self.assertRaises(IndexError, lambda: jp.nodes(''))
        self.assertEqual(jp.nodes('$')['node'], op.load_json(input))
        self.assertEqual(jp.nodes(), ['$','$.0','$.2','$.2.1'])
        self.assertEqual(jp.nodes('$.0')['node'], {'e':'E','f':'F'})
        self.assertEqual(jp.nodes('$.0')['head'], 'b')
        self.assertEqual(jp.nodes('$.2')['node'], {'g':'G','h':[1]})
        self.assertEqual(jp.nodes('$.2')['head'], 'd')

        # test branchs() to select branch.
        self.assertRaises(IndexError, lambda: jp.branches(-1))
        self.assertEqual(jp.branches(), 'b,e,f,c,d,g,h'.split(','))
        self.assertEqual(jp.branches(0), 'b,e,f,c,d,g,h'.split(','))
        self.assertEqual(jp.branches(1), 'b')
        self.assertEqual(jp.branches(2), 'e')

        # test get() to select JsonNode.
        self.assertRaises(IndexError, lambda: jp.get('HAHA'))
        self.assertNotEqual(jp.get('$.0').id, '$.0')
        #- reset uuid index.
        op.JsonNode._next = 200000
        self.assertEqual(jp.get('$.0').id, '200001')                    # clone node
        self.assertEqual(jp.get('200001').node, {'e':'E','f':'F'})
        #- try to change origin input.
        jp._input['b']['e'] = 'EE'
        self.assertEqual(jp.get('200001').node, {'e':'E','f':'F'})      # keep the origin
        self.assertEqual(jp.get('$.0').node, {'e':'EE','f':'F'})        # clone new node
        self.assertEqual(jp.get('200002').node, {'e':'EE','f':'F'})     # keep the changed

        # test members
        self.assertEqual(jp.get('200002').head, 'b')
        self.assertEqual(jp.get('200002').node, {'e':'EE','f':'F'})
        j002 = jp.get('200002')
        self.assertEqual(j002.node,             {'e':'EE','f':'F'})
        self.assertEqual(j002.branch('').node,  {'e':'EE','f':'F'})
        self.assertEqual(j002.branch('e').node, 'EE')
        #- post condition.
        self.assertEqual(jp.get('200002').head, 'e')                   # should be changed
        self.assertEqual(jp.get('200002').node, 'EE')                   # should be changed

        self.assertEqual(jp.append('200002', '200001').node, 'EE')
        self.assertEqual(jp.append('200001', '200002').node, {'e':'EE','f':'F'})

        #- revert to origin
        jp._input['b']['e'] = 'E'

        # test select_id
        self.assertEqual(jp.select('$',4).head, 'c')
        self.assertEqual(jp.select('$',4).node, 'C')
        self.assertEqual(jp.get('$.0').node,    {'e':'E','f':'F'})
        self.assertEqual(jp.fitness('$.0'), 1 + 2.0/3)
        # self.assertEqual(jp.fitness(), '')
