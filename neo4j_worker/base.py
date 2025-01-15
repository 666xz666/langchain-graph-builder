import os
from langchain_community.graphs import Neo4jGraph
from typing import List
from langchain_community.graphs.graph_document import GraphDocument
from config import *
import logging
import json


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
        for graph_document in graph_document_list:
            logging.info(graph_document)
        self.graph.add_graph_documents(graph_document_list, True)

    def delete_by_uuid(self, kb_uuid: str):
        query = f"""
           MATCH (d:Document)-[r0]->(m) WHERE d.kb_uuid = '{kb_uuid}'
           WITH d, r0
           MATCH (d)-[]->(n)
           WITH n, d, r0
           OPTIONAL MATCH (other_d:Document)-[]->(n) WHERE other_d.kb_uuid <> d.kb_uuid
           WITH n, d, COUNT(other_d) AS other_count, r0
           WHERE other_count = 0
           MATCH (n)-[r]-()
           DELETE r0, r, n, d
           """
        query1 = f"""
           MATCH (d:Document)-[r]->()
           WHERE d.kb_uuid = '{kb_uuid}'
           DELETE r, d
           """
        self.run(query)
        self.run(query1)

    def get_graph_info(self, vec_list):
        """
        :param vec_list:
        :return:
            [
                {
                    "target_labels": [
                        "function"
                    ],
                    "source": "langchain-graph-builder",
                    "rel_type": "HAS",
                    "source_labels": [
                        "tool"
                    ],
                    "target": "knowledge base information retrieval"
                },
                {
                    "target_labels": [
                        "function"
                    ],
                    "source": "langchain-graph-builder",
                    "rel_type": "HAS",
                    "source_labels": [
                        "tool"
                    ],
                "target": "RAG dialogue"
                }
            ]
        """
        id_list = [vec[0] for vec in vec_list]
        query = """
        MATCH (d:Document)-[]->(n) 
        WHERE d.id IN $id_list 
        WITH n 
        MATCH (n)-[r]->(m) 
        RETURN collect(distinct {
            source: n.id, 
            source_labels: labels(n), 
            target: m.id, 
            target_labels: labels(m), 
            rel_type: type(r)
        }) as relations
        """
        result = self.run(query, {"id_list": id_list})
        return result[0]['relations']


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

    # result = worker.run(query)
    #
    # print(result)

    # worker.delete_by_uuid("276e4a6f-8c00-45cf-b6d3-59304698e320")

    vec_list = [
        (
            "733150d93c1b40718a2425dfdf76f2fdbb73bedc803919141cc03fc4350b243f",
            "123"
        )]

    print(json.dumps(worker.get_graph_info(vec_list), indent=4, ensure_ascii=False))
