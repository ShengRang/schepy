# coding: utf-8

from collections import defaultdict
from Queue import Queue

from util import unions


class BaseNode(object):
    """
    FA节点
    self.next {alpha: list(NFANode)} "ep"表示空弧转换
    self.meta {info: val}   例如该节点代表终结符时为哪种token(id, comment, num)
    self.end  是否终结符
    """
    def __init__(self, next_type, **kwargs):
        #self.next = defaultdict(next_type)
        self.next = dict()
        self.meta = dict(kwargs)
        self.end = False

    def __getattr__(self, item):
        if item in self.meta:
            return self.meta[item]
        print 'meta has not this key: ', item
        raise AttributeError


class NFANode(BaseNode):
    """
    NFA节点
    self.next {alpha: list(NFANode)} "ep"表示空弧转换
    self.meta {info: val}   例如该节点代表终结符时为哪种token(id, comment, num)
    self.end  是否终结符
    """
    def __init__(self, **kwargs):
        super(NFANode, self).__init__(next_type=set, **kwargs)


class DFANode(BaseNode):

    def __init__(self, **kwargs):
        super(DFANode, self).__init__(next_type=DFANode, **kwargs)


class FA(object):
    """
    start 起始状态
    alpha 字母表
    end 终结状态
    转换函数在node中体现
    """
    def __init__(self, node_type, alpha=None):
        self.start = node_type()
        self.alpha = alpha or []
        self.end = set()


def closure(nodes):
    if not isinstance(nodes, set):
        return closure({nodes})
    s1 = unions([node.next.get("ep", set()) for node in nodes])
    #print [s.meta["id"] for s in s1]
    new_nodes = nodes.union(s1)
    #print [s.meta["id"] for s in new_nodes]
    s2 = new_nodes.difference(nodes)
    #print [s.meta["id"] for s in s2]
    if len(s2):
        # nodes集合通过空弧转换得到新的状态.
        return closure(new_nodes)
    else:
        return new_nodes


def move(t_nodes, a):
    """
    :param t_nodes: T
    :param a: a
    :return: move(T, a)
    """
    return unions([node.next.get(a, set()) for node in t_nodes])


class NFA(FA):

    def __init__(self):
        super(NFA, self).__init__(node_type=NFANode)

    # def __getitem__(self, item):
    #     return self.node_list[item]
    #
    # def __setitem__(self, key, value):
    #     self.node_list[key] = value
    #
    # def __len__(self):
    #     #return len(self.node_list)
    #     return self.cnt

    def convert_dfa(self):
        """
        :return: 与本nfa等价的dfa
        """
        nfa, dfa = self, DFA()
        vis = dict()
        cur_set = closure(nfa.start)
        que = Queue()
        que.put(cur_set)
        dfa.start = None
        while not que.empty():
            tmp = que.get()
            if frozenset(tmp) in vis:
                continue
            dfa_node = DFANode(id=[node.meta["id"] for node in tmp], nfa_set=tmp)
            vis[frozenset(tmp)] = dfa_node
            print "vis add node:", [node.meta["id"] for node in tmp]
            if dfa.start is None:
                dfa.start = dfa_node
            #print tmp
            print [node.meta["id"] for node in tmp]
            #print [(node.next.keys(), node.meta["id"], [t.meta["id"] for t in node.next.get("ep", set())]) for node in tmp]
            next_set = unions([set(node.next.keys()) for node in tmp]).difference({"ep"})
            print next_set
            for a in next_set:
                u = closure(move(tmp, a))
                if frozenset(u) not in vis:
                    que.put(u)
                    print "push: ", [node.meta["id"] for node in u]
                    dfa_node.next[a] = DFANode(id=[node.meta["id"] for node in u])
                    # 这里直接进行转移会导致重复节点(虽然在最小化的时候可以消除)
        que.put(dfa.start)
        while not que.empty():
            tmp = que.get()
            print tmp.meta["nfa_set"], "nfa_end: ", nfa.end
            print tmp.meta["nfa_set"] & nfa.end
            if tmp.meta["nfa_set"] & nfa.end:
                tmp.end = True
                dfa.end.add(tmp)
            next_set = unions([set(node.next.keys()) for node in tmp.meta["nfa_set"]]).difference({"ep"})
            for a in next_set:
                u = move(tmp.meta["nfa_set"], a)
                tmp.next[a] = vis[frozenset(u)]
                print "add ", tmp.meta["id"], "-", a, "-", tmp.next[a].meta["id"]
                que.put(tmp.next[a])
        return dfa


class DFA(FA):

    def __init__(self):
        super(DFA, self).__init__(node_type=DFANode)

    def debug(self):
        que = Queue()
        que.put(self.start)
        vis = dict()
        while not que.empty():
            tmp = que.get()
            if tmp in vis:
                continue
            vis[tmp] = 1
            print tmp.meta["id"], [("- " + key + " ->"+tmp.next[key].meta["id"].__str__(), id(tmp.next[key])) for key in tmp.next.keys()]
            for x in [tmp.next[key] for key in tmp.next.keys()]:
                que.put(x)
        print 'end: ', self.end

if __name__ == '__main__':
    nfa = NFA()
    nfa.start = NFANode(id=1)
    t1, t2 = NFANode(id=2), NFANode(id=3)
    t3 = NFANode(id=4)
    nfa.start.next["ep"] = {t1, t2}
    t1.next["a"] = t2.next["b"] = {t3}
    t3.end = True
    nfa.end.add(t3)
    print "nfa end:", nfa.end
    #print nfa.start.next.keys()
    #print t1.next.keys(), t2.next.keys(), t3.next.keys()
    s0 = closure(nfa.start)
    #print t1.next.keys(), t2.next.keys(), t3.next.keys()
    #print [(node.next.keys(), node.meta["id"], [t.meta["id"] for t in node.next.get("ep", set())]) for node in s0]
    dfa = nfa.convert_dfa()
    print dfa.start, dfa.start.next.keys()
    dfa.debug()
