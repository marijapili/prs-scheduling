import networkx as nx
from numpy import inf

def get_key_by_value(dict, val):
    for key, value in dict.items():
        if value == val:
            return key

class JobShop(nx.DiGraph):
    def __init__(self, jobs):
        super().__init__()
        self.machines = []
        self.machines_out = dict()

        self.start_node = Operation(None, 0, None, None, start=0, id='START')
        self.end_node = Operation(None, 0, None, None, id = 'END')
        self.add_node(self.start_node)
        self.add_node(self.end_node)
        self.add_jobs(jobs)
    
    def add_jobs(self, jobs):
        for job_id, job in enumerate(jobs):
            self.add_job(job, job_id)
        self.update_graph()
    
    def add_job(self, job, job_id):
        previous_op = self.start_node
        for op_id, op in enumerate(job):
            m,t = op
            if m not in self.machines:
                self.machines.append(m)
            current_op = Operation(m,t, job_id+1, op_id+1, start=previous_op.end)
            self.add_node(current_op)
            self.add_edge(previous_op, current_op, weight=previous_op.duration)
            previous_op = current_op
        current_op = self.end_node
        self.add_edge(previous_op, current_op, weight=previous_op.duration)
    
    def single_source_longest_dag_path_length(self, s):
        dist = dict.fromkeys(self.nodes, -float('inf'))
        dist[s] = 0
        topo_order = nx.topological_sort(self)
        for n in topo_order:
            for s in self.successors(n):
                if dist[s] < dist[n] + self.edges[n,s]['weight']:
                    dist[s] = dist[n] + self.edges[n,s]['weight']
        return dist
    
    def calculate_rs(self):
        rs = self.single_source_longest_dag_path_length(self.get_node_by_id('START'))
        for node in self.nodes:
            node.set_r(rs[node])
    
    def calculate_qs(self):
        for node in self.nodes:
            dist = self.single_source_longest_dag_path_length(node)
            node.set_q(dist[self.get_node_by_id('END')]-node.duration)

    def HBT(self, m):
        t = 0
        order = list()
        makespans = list()
        ops = self.get_operations_for_machine(m)
        while ops:
            available = list(filter(lambda op: op.r <= t, ops))
            while not available:
                t += 1
                available = list(filter(lambda op: op.r <= t, ops))
            lt = self.get_node_with_longest_tail(available)
            ops.remove(lt)
            order.append(lt)
            lt.update_start(t)
            t += lt.duration
            makespans.append(t+lt.q)
        M = max(makespans)
        return M, order
    
    def shifting_bottleneck(self):
        machines = self.machines
        while machines:
            order_dict = dict()
            M = dict()
            for m in machines:
                M[m], order_dict[m] = self.HBT(m)
            m = get_key_by_value(M, max(M.values()))
            machines.remove(m)
            intervals = []
            order = []
            for op in order_dict[m]:
                order.append(op.id)
                intervals.append(op.get_interval())
            self.machines_out[m] = (order, intervals)
            for op1, op2 in zip(order_dict[m][:-1], order_dict[m][1:]):
                self.add_edge(op1, op2, weight=op1.duration)
            self.update_graph()
        return self.machines_out
        
    def get_node_by_id(self, id):
        for node in self.nodes:
            if node.id == id:
                return node
    
    def get_operations_for_machine(self, m):
        return [node for node in self.nodes if node.machine == m]
    
    def get_node_with_longest_tail(self, nodes):
        return max(nodes, key=lambda x: x.q)
    
    def update_graph(self):
        self.calculate_rs()
        self.calculate_qs()
    
        
class Operation(object):
    def __init__(self, machine, duration, job, operation_number, start = -inf, id=None):
        self.machine = machine
        self.duration = duration
        self.job = job
        self.operation_number = operation_number
        self.start = start
        self.calculate_end()
        self.id = id if id else (self.job, self.operation_number)
        self.r = None
        self.q = None

    def update_start(self, start):
        self.start = start
        self.calculate_end()

    def calculate_end(self):
        self.end = self.start + self.duration
    
    def get_interval(self):
        return (self.start, self.end)

    def get_id(self):
        return self.id
    
    def set_q(self, q):
        self.q = q
    
    def set_r(self, r):
        self.r = r
    
    def hbt(self):
        return (self.r, self.duration, self.q)
    
