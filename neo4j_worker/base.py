import os
from langchain_community.graphs import Neo4jGraph
from typing import List
from langchain_community.graphs.graph_document import GraphDocument
from config import *

class Neo4jWorker:
    def __init__(self):
        self.graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)

    def run(self, query, param=None):
        return self.graph.query(query, param)

    def save_graph_documents_in_neo4j(self, graph_document_list: List[GraphDocument]):
        """将图文档存入数据库neo4j
        Args:
            graph_document_list (List[GraphDocument]): 图文档列表
        """
        # 将图文档存入数据库
        # graph.add_graph_documents(graph_document_list, baseEntityLabel=True)

        ###
        print(graph_document_list)

        self.graph.add_graph_documents(graph_document_list, True)




if __name__ == '__main__':
    worker = Neo4jWorker()


    query = """
    MATCH (d:Document)-[r]->(n)
    RETURN d.source_id, n.id, type(r)
    """

    #先删关系，再删节点
    clean_all_query = """
    // 删除所有关系
    MATCH ()-[r]->()
    DELETE r
    
    // 删除所有节点
    MATCH (n)
    DETACH DELETE n
    """

    result = worker.run(query)

    print(result)



