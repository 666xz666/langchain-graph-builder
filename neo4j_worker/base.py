import os
from langchain_community.graphs import Neo4jGraph
from typing import List
from langchain_community.graphs.graph_document import GraphDocument
from config import *

class Neo4jWorker:
    def __init__(self):
        self.graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)

    # 需要添加一些图谱修改的函数
    # 1.合并指定结点

    def close_db_connection(self):
        if not self.graph._driver._closed:
            self.graph._driver.close()

    def run(self, query, param=None):
        return self.graph.query(query, param)

    def get_graphinfo_by_source_id(self, source_id_list: List[str]):
        query = """
        MATCH (d:Document)-[r]->(n)
        where d.source_id in $source_id_list
        RETURN collect(distinct {id:id(d), title:d.source_id, label:labels(d)[0],text:d.text,source:d.source}) as documents, collect(distinct {id:id(n), title:n.id, label:labels(n)[0]}) as nodes, collect(distinct {source:id(d), target:id(n), label:type(r)}) as relations
        """
        query2 = """
        MATCH (d:Document)-[r]->(n)
        where d.source_id in $source_id_list
        WITH n
        MATCH (n)-[r2]->(m)
        RETURN collect(distinct {source:id(n), target:id(m), label:type(r2)}) as relations
        """
        result = self.run(query, {'source_id_list': source_id_list})
        result2 = self.run(query2, {'source_id_list': source_id_list})
        self.close_db_connection()

        document_list = result[0]['documents']
        node_list = result[0]['nodes']
        relation_list = result[0]['relations'] + result2[0]['relations']

        result_dict = {"document_list": document_list, "node_list": node_list, "relation_list": relation_list}
        return result_dict

    def save_graphDocuments_in_neo4j(self, graph_document_list: List[GraphDocument]):
        """将图文档存入数据库neo4j
        Args:
            graph_document_list (List[GraphDocument]): 图文档列表
        """
        # 将图文档存入数据库
        # graph.add_graph_documents(graph_document_list, baseEntityLabel=True)

        ###
        print(graph_document_list)

        self.graph.add_graph_documents(graph_document_list, True)

    def check_documents_exist(self, source_ids: list) -> List[bool]:
        # 检查给定的source_ids列表中的每个Document是否存在
        exist_query = """
        MATCH (d:Document)
        WHERE d.source_id IN $source_ids
        RETURN d.source_id
        """

        result = self.run(exist_query, {'source_ids': source_ids})

        # 创建一个集合，包含所有存在的source_id
        existing_ids = {item['d.source_id'] for item in result}

        # 创建一个列表，按照输入的source_ids顺序返回存在性结果
        existence_list = [source_id in existing_ids for source_id in source_ids]

        return existence_list

    def check_files_exist(self, filenames: List[str]) -> List[bool]:
        # 检查给定的filenames列表中的每个文件是否存在
        exist_query = """
        MATCH (d:Document)
        WHERE d.source IN $filenames
        RETURN d.source
        """

        result = self.run(exist_query, {'filenames': filenames})

        # 创建一个集合，包含所有存在的文件名
        existing_filenames = {item['d.source'] for item in result}

        # 创建一个列表，按照输入的filenames顺序返回存在性结果
        existence_list = [filename in existing_filenames for filename in filenames]

        return existence_list

    def delete_nodes_and_relationships_by_source_id_list(self, source_id_list: List[str]):
        """删除单个embedding向量对应的节点和关系

        Args:
            source_id_list (List[str]): 要删除的source_id列表，每个source_id对应一个embedding向量
        """

        query_to_delete_nodes_and_relationships_by_source_id_list = """
        MATCH (d:Document) where d.source_id in $source_id_list
        with collect(d) as documents 
        unwind documents as d
        optional match (d)-[:MENTIONS]->(n)
        where not exists {(d1)-[:MENTIONS]->(n) WHERE NOT d1 IN documents}
        detach delete n, d
        """

        self.run(query_to_delete_nodes_and_relationships_by_source_id_list, {'source_id_list': source_id_list})

    def delete_nodes_and_relationships_by_filename_list(self, filename_list: List[str]):
        """删除指定文件的节点和关系

        Args:
            filename_list (List[str]): 要删除的文档的文件名列表
        """

        query_to_delete_nodes_and_relationships_by_filename_list = """
        MATCH (d:Document) where d.source in $filename_list
        with collect(d) as documents 
        unwind documents as d
        optional match (d)-[:MENTIONS]->(n)
        where not exists {(d1)-[:MENTIONS]->(n) WHERE NOT d1 IN documents}
        detach delete n, d
        """

        self.run(query_to_delete_nodes_and_relationships_by_filename_list, {'filename_list': filename_list})




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



