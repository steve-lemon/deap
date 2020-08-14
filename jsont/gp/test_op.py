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
    "c":"C"
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
