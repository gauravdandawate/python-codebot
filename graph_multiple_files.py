import ast
from typing import List, Tuple
from matplotlib import interactive, pyplot as plt
import networkx as nx
from pyvis.network import Network

from networkx.algorithms.community import greedy_modularity_communities

import os


def find_entities(code: str, file_name: str) -> List[Tuple[str, str, str]]:
    entities = []

    class EntityVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            entities.append((node.name, "function", file_name))
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            entities.append((node.name, "class", file_name))
            self.generic_visit(node)

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    entities.append((target.id, "variable", file_name))
            self.generic_visit(node)

    tree = ast.parse(code)
    EntityVisitor().visit(tree)
    return entities



def find_relationships(code: str, file_name: str, all_entities: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    relationships = []
    current_class = None
    current_function = None

    class RelationVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            nonlocal current_class
            current_class = node.name
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    relationships.append((current_class, item.name, "has_method"))
            self.generic_visit(node)
            current_class = None

        def visit_FunctionDef(self, node):
            nonlocal current_function
            current_function = node.name
            self.generic_visit(node)
            current_function = None

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                if current_function:
                    relationships.append((current_function, node.func.id, "calls"))
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            # Handle imports from other files
            for alias in node.names:
                relationships.append((file_name, alias.name, "imports"))
            self.generic_visit(node)

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if current_function:
                        relationships.append((current_function, target.id, "defines_var"))
                    elif current_class:
                        relationships.append((current_class, target.id, "defines_var"))
            self.generic_visit(node)

    tree = ast.parse(code)
    RelationVisitor().visit(tree)

    # Check for cross-file function calls by matching function names and imported names
    for src_func, src_type, src_file in all_entities:
        if src_file != file_name:  # Skip self-references
            relationships.append((file_name, src_func, "calls_across_files"))

    return relationships


def build_graph(entities, relationships):
    G = nx.DiGraph()

    for name, node_type, file_name in entities:
        G.add_node(f"{file_name}_{name}", type=node_type)

    for src, tgt, rel in relationships:
        G.add_edge(src, tgt, relation=rel)

    return G


def read_python_files(folder_path):
    file_data = {}
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    file_data[path] = f.read()
    return file_data


def main(folder_path):
    # Step 1: Read all Python files
    file_data = read_python_files(folder_path)

    all_entities = []
    all_relationships = []

    # Step 2: Extract entities first
    for file_path, code in file_data.items():
        entities = find_entities(code, file_path)
        all_entities.extend(entities)

    # After collecting all_entities
    all_entities = list(set(all_entities))

    

    # Step 3: Extract relationships
    for file_path, code in file_data.items():
        relationships = find_relationships(code, file_path, all_entities)
        all_relationships.extend(relationships)
    
    all_relationships = list(set(all_relationships))

    # # Remove self-references (e.g., a function calling itself)
    # all_relationships = [rel for rel in all_relationships if rel[0] != rel[1]]

    # Step 4: Build the graph
    graph: nx.DiGraph = build_graph(all_entities, all_relationships)

    node_community_map=build_community_graph(graph)
 
    # Draw the graph
    # draw_graph(graph=graph, node_community_map=node_community_map)

    # Draw the interactive graph
    draw_interactive_graph(graph, node_community_map)

def draw_graph(graph, node_community_map):
        # Create a color map
    colors = [node_community_map[node] for node in graph.nodes]

    # Step 5: Visualize the graph
    pos = nx.spring_layout(graph,seed=32)
    # pos = nx.planar_layout(graph)


    nx.draw(graph, pos, with_labels=True, node_color=colors, edge_color='gray')
    edge_labels = nx.get_edge_attributes(graph, 'relation')
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    plt.show()


def build_community_graph(graph):
    #build communities
    communities = list(greedy_modularity_communities(G=graph.to_undirected()))

    # Build a community mapping {node: community_id}
    node_community_map = {}
    for community_id, community_nodes in enumerate(communities):
        for node in community_nodes:
            node_community_map[node] = community_id

    # Print the communities
    for node, community_id in node_community_map.items():
        print(f"Node {node} belongs to community {community_id}")
    
    return node_community_map



def draw_interactive_graph(G, communities):
    interactive_graph = Network(notebook=False, height="750px", width="100%", bgcolor="#ffffff", font_color="black")

    # Add nodes
    for node in G.nodes():
        interactive_graph.add_node(node, label=node, color=f"#{hash(str(communities.get(node, 0)))%0xFFFFFF:06x}")

    # Add edges
    for source, target in G.edges():
        interactive_graph.add_edge(source, target)

    # Save and open in browser
    interactive_graph.show("graph.html",notebook=False)

# ---- Run the graph generator ----
if __name__ == "__main__":
    folder = "codebase/fastapi-master/app"  # 🔥 replace with your folder path
    main(folder)