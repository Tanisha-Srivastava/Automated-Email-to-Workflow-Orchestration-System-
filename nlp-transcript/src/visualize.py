import json
import networkx as nx
import matplotlib.pyplot as plt
import textwrap

# ----------------------------
# Load workflow
# ----------------------------
with open("output/workflow.json") as f:
    data = json.load(f)

tasks = data["tasks"]
edges = data["edges"]

# ----------------------------
# Helpers
# ----------------------------
def extract_name(text):
    return text.split()[0]

def wrap(text, width=40):
    return "\n".join(textwrap.wrap(text, width))

def node_color(role):
    return {
        "UX Designer": "#CFE2F3",
        "Frontend Engineer": "#D9EAD3",
        "Backend Engineer": "#FFF2CC",
        "QA Lead": "#FCE5CD",
        "Project Manager": "#EAD1DC"
    }.get(role, "#EEEEEE")

# ----------------------------
# Build graph
# ----------------------------
G = nx.DiGraph()

for task in tasks:
    owner = extract_name(task["text"])
    role = task.get("role", "Unknown")

    label = (
        f"{task['id']}\n"
        f"{owner} ({role})\n"
        f"{wrap(task['text'])}"
    )

    G.add_node(
        task["id"],
        label=label,
        color=node_color(role)
    )

for e in edges:
    G.add_edge(e["from"], e["to"])

# ----------------------------
# Layout (KEY CHANGE)
# ----------------------------
pos = nx.kamada_kawai_layout(G)  # much better spacing than spring_layout

# ----------------------------
# Draw
# ----------------------------
plt.figure(figsize=(14, 10))

node_colors = [G.nodes[n]["color"] for n in G.nodes]

nx.draw(
    G,
    pos,
    with_labels=False,
    node_size=5200,
    node_color=node_colors,
    edgecolors="black",
    linewidths=1.2,
    arrows=True
)

labels = nx.get_node_attributes(G, "label")
nx.draw_networkx_labels(
    G,
    pos,
    labels,
    font_size=9,
    verticalalignment="center"
)

plt.title("Meeting → Executable Workflow DAG (NLP-Inferred)", fontsize=14)
plt.axis("off")

# Save first
plt.savefig(
    "output/workflow_dag.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()
