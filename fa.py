# coding: utf-8

from Queue import Queue
import pdb

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

    @property
    def nexts(self):
        return unions([self.next[key] for key in self.next.keys()])


class DFANode(BaseNode):

    def __init__(self, **kwargs):
        super(DFANode, self).__init__(next_type=DFANode, **kwargs)

    @property
    def nexts(self):
        """
        返回可以转移到的下一阶段所有节点组成的list
        """
        return [self.next[key] for key in self.next.keys()]


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


# @profile
def closure(nodes):
    if not isinstance(nodes, set):
        return closure({nodes})
    que = Queue()
    for node in nodes:
        que.put(node)
    res = set(nodes)
    while not que.empty():
        t = que.get()
        for x in t.next.get("ep", set()):
            if x not in res:
                res.add(x)
                que.put(x)
    return res


#@profile
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

    # @profile
    def convert_dfa(self, copy_meta=None):
        """
        :return: 与本nfa等价的dfa
        """
        if copy_meta is None:
            copy_meta = []
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
            dfa_node = DFANode(nfa_set=tmp)
            vis[frozenset(tmp)] = dfa_node
            if dfa.start is None:
                dfa.start = dfa_node
            next_set = unions([set(node.next.keys()) for node in tmp]).difference({"ep"})
            for a in next_set:
                u = closure(move(tmp, a))
                if frozenset(u) not in vis:
                    que.put(u)
        que.put(dfa.start)
        vis2 = dict()   # 例如a*产生的nfa, 可能会有a弧转换指向自身. 因此需要去重防止无限循环
        while not que.empty():
            tmp = que.get()
            if tmp in vis2:
                continue
            vis2[tmp] = 1
            intersection = tmp.nfa_set & nfa.end
            if intersection:
                for key in copy_meta:
                    tmp.meta.setdefault(key, [])
                    tmp.meta[key].extend([node.meta.get(key) for node in intersection])
                tmp.end = True
                dfa.end.add(tmp)
            next_set = unions([set(node.next.keys()) for node in tmp.meta["nfa_set"]]).difference({"ep"})
            for a in next_set:
                u = closure(move(tmp.meta["nfa_set"], a))
                tmp.next[a] = vis[frozenset(u)]
                que.put(tmp.next[a])
        return dfa

    @classmethod
    def combine(cls, *args):
        res = NFA()
        res.start.next["ep"] = set()
        res.end = set()
        for nfa in args:
            res.start.next["ep"].add(nfa.start)
            res.end.update(nfa.end)
        return res

    def draw(self, filename="nfa", show_meta=False):
        que = Queue()
        que.put(self.start)
        vis = dict()
        cnt = 0
        while not que.empty():
            tmp = que.get()
            if tmp in vis:
                continue
            vis[tmp] = 1
            tmp.meta["id"] = cnt
            cnt += 1
            for x in tmp.nexts:
                que.put(x)
        que = Queue()
        que.put(self.start)
        vis = dict()
        with open(filename+'.dot', 'wt') as f:
            f.write('digraph regex_dfa{\nrankdir=LR;\n')
            while not que.empty():
                tmp = que.get()
                if tmp in vis:
                    continue
                vis[tmp] = 1
                if tmp.end:
                    if show_meta:
                        f.write('\t %d [label="%d %s", shape=doublecircle]\n' % (tmp.id, tmp.id, repr(tmp.meta)))
                    else:
                        f.write('\t %d [label="%d", shape=doublecircle]\n' % (tmp.id, tmp.id))
                else:
                    f.write('\t%d [label=%d]\n' % (tmp.id, tmp.id))
                for key in tmp.next.keys():
                    nexts = tmp.next[key]
                    for u in nexts:
                        f.write('\t%d-> %d [label="%s"]\n' % (tmp.id, u.id, key))
                        que.put(u)
            f.write('}\n')


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

    def generate_id(self):
        que = Queue()
        que.put(self.start)
        cnt = 0
        vis = dict()
        while not que.empty():
            tmp = que.get()
            if tmp in vis:
                continue
            vis[tmp] = 1
            tmp.meta["id"] = cnt
            cnt += 1
            for x in tmp.nexts:
                que.put(x)

    def draw(self, filename="dfa", show_meta=None, generate_id=True):
        if not show_meta:
            show_meta = []
        if generate_id:
            self.generate_id()
        que = Queue()
        que.put(self.start)
        vis = dict()
        with open(filename+'.dot', 'wt') as f:
            f.write('digraph regex_dfa{\nrankdir=LR;\n')
            while not que.empty():
                tmp = que.get()
                if tmp in vis:
                    continue
                vis[tmp] = 1
                if tmp.end:
                    if show_meta:
                        f.write('\t %d [label="%d [%s]", shape=doublecircle]\n' % (tmp.id, tmp.id, repr({key: tmp.meta[key] for key in show_meta if key != 'nfa_set'})))
                    else:
                        f.write('\t %d [label="%d", shape=doublecircle]\n' % (tmp.id, tmp.id))
                else:
                    if show_meta:
                        f.write('\t%d [label="%d %s"]\n' % (tmp.id, tmp.id, repr({key: tmp.meta[key] for key in show_meta if key != 'nfa_set'})))
                    else:
                        f.write('\t%d [label=%d]\n' % (tmp.id, tmp.id))
                for key in tmp.next.keys():
                    x = tmp.next[key]
                    f.write('\t%d-> %d [label="%s"]\n' % (tmp.id, x.id, key))
                    que.put(x)
            f.write('}\n')


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
    dfa.draw()
