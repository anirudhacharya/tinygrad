import unittest
from tinygrad import Tensor
from tinygrad.ops import PatternMatcher, Ops, UPat, graph_rewrite, RewriteContext, UOp

class TestRewriteTrackedChildren(unittest.TestCase):
  def test_children_in_context(self):
    def print_children(ctx:RewriteContext, sink:UOp):
      view_w_child = sink.src[0].src[0].src[0]
      assert view_w_child.op is Ops.VIEW
      assert set([x.arg for x in ctx.children[view_w_child]]) == set((2,3))
      ctx.update_children()
      assert set([x.arg for x in ctx.children[view_w_child]]) == set((3,4))
      # this is the 3
      assert len(ctx.children[sink.src[0].src[1]]) == 1
      assert next(iter(ctx.children[sink.src[0].src[1]])).op is Ops.ADD
      # this is the 4
      assert len(ctx.children[sink.src[0].src[0]]) == 1
      assert next(iter(ctx.children[sink.src[0].src[0]])).op is Ops.ADD
    rewrite = PatternMatcher([
      (UPat(Ops.CONST, arg=2, name="x"), lambda x: x.replace(arg=4)),
      (UPat(Ops.SINK, name="sink"), print_children)
    ])
    a = Tensor(2)
    b = Tensor(3)
    c = a + b
    sink = c.lazydata.sink()
    sink = graph_rewrite(sink, rewrite, track_children=True)

  def test_simple_child(self):
    rewrite = PatternMatcher([
      (UPat(Ops.CONST, arg=2, name="x"), lambda x: x.replace(arg=4)),
    ])
    a = Tensor(2)
    b = Tensor(3)
    c = a + b
    sink = c.lazydata
    view_w_child = a.lazydata.src[0]
    print([x().arg for x in view_w_child.children])
    print([x.arg for x in sink.get_children_map()[view_w_child]])
    self.assertSetEqual(set([x.arg for x in sink.get_children_map()[view_w_child]]), set((2,3)))
    # children can either be added to or removed from the map with graph_rewrite
    # added to is easy to detect, just hook the UOp constructor
    # when are children removed?
    #  * if a rewrite rule returns a UOp, the matched node is removed from the graph
    sink = graph_rewrite(sink, rewrite)
    print([x().arg for x in view_w_child.children])
    print([x.arg for x in sink.get_children_map()[view_w_child]])
    self.assertSetEqual(set([x.arg for x in sink.get_children_map()[view_w_child]]), set((3,4)))

if __name__ == '__main__':
  unittest.main()
