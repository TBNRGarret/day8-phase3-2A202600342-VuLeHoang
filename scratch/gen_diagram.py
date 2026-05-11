import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from langgraph_agent_lab.graph import build_graph

def generate_diagram():
    graph = build_graph()
    mermaid = graph.get_graph().draw_mermaid()
    print(mermaid)
    with open("outputs/graph_diagram.mmd", "w") as f:
        f.write(mermaid)

if __name__ == "__main__":
    generate_diagram()
