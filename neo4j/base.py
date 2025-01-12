#https://blog.csdn.net/sinat_20471177/article/details/134056788

from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jController:
    def __init__(self):
        """
        初始化 Neo4j 连接
        :param uri: 数据库 URI
        :param auth: 认证信息 (用户名, 密码)
        """
        self.graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    def create_node(self, labels, **properties):
        """
        创建节点
        :param labels: 节点标签
        :param properties: 节点属性
        :return: 创建的节点
        """
        node = Node(labels, **properties)
        self.graph.create(node)
        return node

    def create_relationship(self, start_node, end_node, rel_type, **properties):
        """
        创建关系
        :param start_node: 起始节点
        :param end_node: 结束节点
        :param rel_type: 关系类型
        :param properties: 关系属性
        :return: 创建的关系
        """
        rel = Relationship(start_node, rel_type, end_node, **properties)
        self.graph.create(rel)
        return rel

    def create_path(self, *entities):
        """
        创建路径
        :param entities: 路径中的实体（节点或关系）
        :return: 创建的路径
        """
        from py2neo import Path
        path = Path(*entities)
        self.graph.create(path)
        return path

    def create_subgraph(self, nodes, relationships):
        """
        创建子图
        :param nodes: 节点列表
        :param relationships: 关系列表
        :return: 创建的子图
        """
        from py2neo import Subgraph
        subgraph = Subgraph(nodes, relationships)
        self.graph.create(subgraph)
        return subgraph

    def delete_all(self):
        """
        删除数据库中的所有节点和关系
        """
        self.graph.delete_all()

    def delete_node(self, node):
        """
        删除单个节点
        :param node: 要删除的节点
        """
        self.graph.delete(node)

    def delete_relationship(self, rel):
        """
        删除单个关系
        :param rel: 要删除的关系
        """
        self.graph.delete(rel)

    def delete_by_cypher(self, cypher):
        """
        使用 Cypher 语句删除节点或关系
        :param cypher: Cypher 语句
        """
        self.graph.run(cypher)

    def update_node(self, node, **properties):
        """
        更新节点属性
        :param node: 要更新的节点
        :param properties: 新的属性
        """
        for key, value in properties.items():
            node[key] = value
        self.graph.push(node)

    def query_nodes(self, *labels, **properties):
        """
        查询节点
        :param labels: 节点标签
        :param properties: 节点属性
        :return: 查询结果
        """
        matcher = NodeMatcher(self.graph)
        return matcher.match(*labels, **properties)

    def query_relationships(self, nodes=None, r_type=None, **properties):
        """
        查询关系
        :param nodes: 节点范围
        :param r_type: 关系类型
        :param properties: 关系属性
        :return: 查询结果
        """
        matcher = RelationshipMatcher(self.graph)
        return matcher.match(nodes, r_type, **properties)



if __name__ == '__main__':
    neo4j = Neo4jController()



