import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from plotly.graph_objs import *
import igraph as ig
import io

# xlsNodes_path = r'C:/Python code/data mining/3D-viz/Data/Nodes.xlsx'
# xlsvertices_path = r'C:/Python code/data mining/3D-viz/Data/Vertices.xlsx'

xlsNodes_path = r'Data/Nodes.xlsx'
xlsvertices_path = r'Data/Vertices.xlsx'

df_nodes_initial = pd.read_excel(xlsNodes_path)
df_vertices_initial = pd.read_excel(xlsvertices_path)

df_nodes_initial.drop_duplicates(inplace=True)
df_vertices_initial.drop_duplicates(inplace=True)

df_nodes_initial["node_lower"] = df_nodes_initial["name"].str.lower()
df_nodes_initial.drop_duplicates(subset='node_lower',inplace=True)
df_nodes_initial.drop(columns='node_lower',inplace=True)
df_nodes_initial.reset_index(inplace=True, drop=True)

df_vertices_initial["source_lower"] = df_vertices_initial["source"].str.lower()
df_vertices_initial["target_lower"] = df_vertices_initial["target"].str.lower()
df_vertices_initial.drop_duplicates(["source_lower","target_lower"],inplace=True,keep="last")
df_vertices_initial.drop(columns=["source_lower","target_lower"],inplace=True)
df_vertices_initial.reset_index(inplace=True,drop=True)

df_nodes_initial = df_nodes_initial.replace("/s+"," ",regex=True).apply(lambda x: x.str.strip())
df_vertices_initial = df_vertices_initial.replace("\s+"," ",regex=True).apply(lambda x: x.str.strip())

def get_nlevel_siblings(df_vertices,n,current_nodes) :
    if n == 1 :
        return current_nodes
    for _ in range(n-1) :
        augmented_nodes = list(
            set(
                df_vertices[
                    df_vertices["source"].str.lower().isin([x.lower() for x in current_nodes]) | 
                    df_vertices["target"].str.lower().isin([x.lower() for x in current_nodes])
                ][["source","target"]].values.T.ravel()
            )
        )
        current_nodes = augmented_nodes
    return augmented_nodes

def download_html(content, filename, text) :
    buf = io.BytesIO()
    buf.write(content)
    buf.seek(0)
    href = st.download_button(
        label = text,
        data = buf,
        file_name= filename,
        mime="text/html"
    )
    return href

st.set_page_config(layout='wide')

st.markdown("""
      <style>     
            div[data-testid="stMarkdownContainer"] p{
                font-size: 1.5em;
                font-weight: 700;
                color: #021d3a;
            }
            div[role="radiogroup"] div[data-testid="stMarkdownContainer"] p{
                color: #021d3a;
                font-size: 1em;
                font-weight: 400;
            }
      </style>           
""",unsafe_allow_html=True)

st.title("3D Network Graph of League Of Legends Champions")

choice = st.sidebar.radio("Choose your filter method : ", ["Nodes", "Groups"])
selected_nodes = selected_grps = level_direct_sibling = None

if choice == "Nodes" :
    selected_nodes = st.sidebar.multiselect("Select Nodes : ", sorted(
        df_nodes_initial[pd.notna(df_nodes_initial["name"])]["name"].unique()
    ))

    df_vertices = df_vertices_initial[
        df_vertices_initial["source"].str.lower().isin([x.lower() for x in selected_nodes]) |
        df_vertices_initial["target"].str.lower().isin([x.lower() for x in selected_nodes])
    ].drop_duplicates().reset_index(drop=True)

    df_nodes = df_nodes_initial[
        df_nodes_initial["name"].str.lower().isin([x.lower() for x in selected_nodes]) |
        df_nodes_initial["name"].str.lower().isin(df_vertices["source"].str.lower()) |
        df_nodes_initial["name"].str.lower().isin(df_vertices["target"].str.lower()) 
    ]

    if selected_nodes : 
        level_direct_sibling = st.sidebar.radio("Select level of direct sibling : ", [1,2,3,4])
        all_nodes = [selected_nodes]

        if (level_direct_sibling != None) and (level_direct_sibling > 1) :
            selected_nodes_variable = selected_nodes
            
            for level in range(2,level_direct_sibling+2) :

                selected_nodes_per_level = get_nlevel_siblings(df_vertices_initial, level, selected_nodes)

                added_nodes = sorted(list(set(selected_nodes_per_level) - set(selected_nodes_variable) - set(selected_nodes)))

                added_nodes_filtered = [node for node in added_nodes if node in df_nodes_initial["name"].unique()]

                selected_nodes_variable = added_nodes_filtered

                added_nodes_from_input = st.sidebar.multiselect(
                    f'Nodes of level : {level - 1} : ',
                    df_nodes_initial["name"].unique(),
                    default=sorted(added_nodes_filtered)
                )
                all_nodes.append(added_nodes_from_input)
            selected_nodes = [item for sublist in all_nodes for item in sublist]

            df_vertices = df_vertices_initial[
                df_vertices_initial["source"].str.lower().isin([x.lower() for x in selected_nodes]) |
                df_vertices_initial["target"].str.lower().isin([x.lower() for x in selected_nodes])
            ]

            df_nodes = df_nodes_initial[
                df_nodes_initial["name"].str.lower().isin([x.lower() for x in selected_nodes])
            ]


elif choice == "Groups" : 
    selected_grps = st.sidebar.multiselect("Select Groups : ", sorted(
        df_nodes_initial[pd.notna(df_nodes_initial["group"])]["group"].unique()
    ))

    if selected_grps : 
        associated_nodes_initial = df_nodes_initial[df_nodes_initial["group"].isin(selected_grps)]["name"].unique().tolist()

        associated_nodes_initial = [node for node in associated_nodes_initial if node in df_nodes_initial["name"].unique()]

        associated_nodes_initial = sorted(associated_nodes_initial)

        associated_nodes_extended = get_nlevel_siblings(df_vertices_initial, 2 , associated_nodes_initial)

        associated_nodes_extended_filtered = [node for node in associated_nodes_extended if node in df_nodes_initial["name"].unique()]

        associated_nodes_rest = list(set(associated_nodes_extended_filtered) - set(associated_nodes_initial))

        associated_nodes_rest = sorted(associated_nodes_rest)

        selected_nodes_grps = st.sidebar.multiselect(
            f"Nodes selected from : ({', '.join(selected_grps)}) : ",
            df_nodes_initial["name"].unique(), default= associated_nodes_initial
        )

        selected_nodes_rest = st.sidebar.multiselect(
            f"Rest of nodes : ",
            df_nodes_initial["name"].unique(),
            default=associated_nodes_rest
        )

        selected_nodes = selected_nodes_grps + selected_nodes_rest

        df_vertices = df_vertices_initial[
            df_vertices_initial["source"].str.lower().isin([x.lower() for x in selected_nodes]) |
            df_vertices_initial["target"].str.lower().isin([x.lower() for x in selected_nodes])
        ].drop_duplicates().reset_index(drop=True)

        df_nodes = df_nodes_initial[df_nodes_initial["name"].str.lower().isin([x.lower() for x in selected_nodes])]

if (selected_nodes != None) and (len(selected_nodes) > 0 ) : 
    if df_nodes.empty | df_vertices.empty : 
        st.write(f"The selected Data is incomplete")
    else : 
        df_vertices[["source","target"]] = df_vertices[["source", "target"]].apply(lambda x : x.astype('category'))
        df_nodes[["name","group"]] = df_nodes[["name","group"]].apply(lambda x : x.astype("category"))

        names_to_number = df_nodes[df_nodes["name"].notnull()]["name"].cat.codes
        names_mapped = dict(zip(df_nodes[df_nodes["name"].notnull()]["name"].str.lower(),names_to_number))

        df_vertices["source_int"] = df_vertices["source"].str.lower().map(names_mapped)
        df_vertices["target_int"] = df_vertices["target"].str.lower().map(names_mapped)
        df_nodes["name_int"] = df_nodes["name"].str.lower().map(names_mapped)
        df_nodes["group_int"] = df_nodes["group"].cat.codes

        df_vertices = df_vertices[pd.notna(df_vertices["source_int"]) & pd.notna(df_vertices["target_int"])]
        df_vertices[["source_int","target_int"]] = df_vertices[["source_int","target_int"]].astype(int)

        df_nodes["definition"] = df_nodes[
            df_nodes["definition"].notnull()
        ]["definition"].str.wrap(30) if df_nodes["definition"].isnull().values.all() == False else np.nan

        df_nodes["definition"] = df_nodes[df_nodes["definition"].notnull()]["definition"].apply(lambda x : x.replace("\n","<br>"))

        Edges = list(zip(df_vertices["source_int"], df_vertices["target_int"]))
        Edges_names = list(zip(df_vertices["source"],df_vertices["target"]))

        Vertices = df_nodes[(df_nodes["name_int"] != -1) & df_nodes["name_int"].notnull()]["name_int"].unique()

        df_sorted = df_nodes.sort_values(by=["name_int"])

        node_names = df_sorted[df_sorted["name"].notnull()]["name"].tolist()
        node_group = df_sorted[df_sorted["group"].notnull()]["group"].tolist()
        node_definition = df_sorted[df_sorted["name"].notnull()]["definition"].tolist()

        node_group_unique = list(dict.fromkeys(node_group))

        node_color_sequence = [df_nodes[df_nodes["group"] == group]["color"].values[0].lower() for group in node_group_unique]

        vertice_group = [df_nodes[
            df_nodes["name"].str.lower() == source.lower()
        ]["group"].values[0] if not df_nodes[
            df_nodes["name"].str.lower() == source.lower()
        ]["group"].empty else None for source in df_vertices["source"]]

        vertice_group_duplicated = [val for val in vertice_group for _ in (0,1)]

        vertice_group_unique = list(dict.fromkeys(vertice_group))

        vertice_color_sequence = [
                df_nodes[df_nodes["group"] == group]["color"].values[0].lower() if not df_nodes[df_nodes["group"] == group]["color"].empty else None for group in vertice_group_unique
        ]

        vertice_link = df_vertices["link"].tolist()
        vertice_link_duplicated = [val for val in vertice_link for _ in (0,1)]

        G = ig.Graph()

        G.add_vertices(Vertices)

        G.add_edges(Edges)

        layt = G.layout('fr', dim=3)

        Xn = [layt[k][0] for k in range(len(G.vs))]
        Yn = [layt[k][1] for k in range(len(G.vs))]
        Zn = [layt[k][2] for k in range(len(G.vs))]

        Xe = []
        Ye = []
        Ze = []

        for e in Edges :
            Xe+=[layt[e[0]][0], layt[e[1]][0]]
            Ye+=[layt[e[0]][1], layt[e[1]][1]]
            Ze+=[layt[e[0]][2], layt[e[1]][2]]

        df_nodes_finale = pd.DataFrame(list(zip(Xn,Yn,Zn,node_names,node_group,node_definition)),
                columns=["X-coordinates","Y-coordinates","Z-coordinates","Names","Groups","Definition"]
            )
        df_edges_finale = pd.DataFrame(list(zip(Xe,Ye,Ze,vertice_link_duplicated,vertice_group_duplicated)),
                columns=["X-coordinates","Y-coordinates","Z-coordinates","Link","Groups"]
            )
        
        fig_lines = px.line_3d(df_edges_finale,
            x="X-coordinates",
            y="Y-coordinates",
            z="Z-coordinates",
            color="Groups",
            color_discrete_sequence= vertice_color_sequence,
            hover_data = {"X-coordinates":False,"Y-coordinates":False,"Z-coordinates":False, "Groups":False, "Link":True}              
        )

        fig_nodes = px.scatter_3d(df_nodes_finale,
            x="X-coordinates",
            y="Y-coordinates",
            z="Z-coordinates",
            text="Names",
            color="Groups",
            color_discrete_sequence= node_color_sequence,
            hover_data = {"X-coordinates":False,"Y-coordinates":False,"Z-coordinates":False, "Groups":False,"Names":False, "Definition":True}
        )

        fig_lines.update_traces(showlegend = False)
        fig_lines.update(layout_showlegend=False)

        for trace in fig_lines.data : 
            fig_nodes.add_trace(trace)

        fig_nodes.update_scenes(xaxis_visible = False, yaxis_visible=False, zaxis_visible=False)
        fig_nodes.update_traces(marker_size = 9)

        fig_nodes.update_layout(
            legend_title = "Group labels",
            font=dict(
                size = 11,
                color = "#000"
            ),
            height = 450,
            hoverlabel = dict(
                bgcolor="white",
                font_size=10
            )
        )
        fig_nodes.update_layout(margin=dict(l=0,r=0,b=0,t=50))

        arrow_tip_ratio = 0.15
        arrow_starting_ratio = -0.95

        for e in Edges : 
            fig_nodes.add_trace(Cone(
                x= [ Xn[e[0]] + arrow_starting_ratio * ( Xn[e[0]] - Xn[e[1]] ) ],
                y= [ Yn[e[0]] + arrow_starting_ratio * ( Yn[e[0]] - Yn[e[1]] ) ],
                z= [ Zn[e[0]] + arrow_starting_ratio * ( Zn[e[0]] - Zn[e[1]] ) ],
                u= [ arrow_tip_ratio*(Xn[e[1]] - Xn[e[0]] )],
                v= [ arrow_tip_ratio*(Yn[e[1]] - Yn[e[0]] )],
                w= [ arrow_tip_ratio*(Zn[e[1]] - Zn[e[0]] )],
                showlegend=False,
                showscale=False,
                hoverinfo="skip"
            ))
        
        st.plotly_chart(fig_nodes, use_container_width=True)

        html_str = fig_nodes.to_html()
        download_html(html_str.encode(), "plot.html", "Download plot as HTML")
else : 
    st.write("Please select at least one Node :)")



