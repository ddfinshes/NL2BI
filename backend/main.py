import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from model.communication import Communication
from model.parser import SQLParser
import time
import sqlglot
import networkx as nx
import json

app = Flask(__name__)
CORS(app)

communication = Communication()


@app.route("/")
def test():
    return "Hello World"


@app.route("/getCommunicationList", methods=["GET"])
def getCommunicationList():
    return jsonify(communication.getCommunicationList())


@app.route("/getCommuncation", methods=["GET"])
def getCommunication():
    return jsonify(communication.getCommunication())


@app.route("/selectCommunication", methods=["POST", "GET", "PUT"])
def selectCommunication():
    id = request.args.get("id")

    communication.updCommuncation(id)
    return jsonify(communication.getCommunication())


@app.route("/sendContext", methods=["POST", "GET", "PUT"])
def sendContext():
    context = request.args.get("context")
    communication.sendContext_V1(context)
    return jsonify(communication.getCommunication())


@app.route("/startNewChat", methods=["POST", "GET", "PUT"])
def startNewChat():
    name = request.args.get("name")
    if name is None or name == "":
        name = f'{time.strftime("%Y-%m-%d %H %M %S", time.localtime())}'
    communication.addNewChat(name)
    return jsonify(communication.getCommunicationList())


@app.route("/getSQLCode", methods=["GET"])
def getSQLcode():
    return jsonify({"SQLCode": communication.getSQLCode()})


@app.route("/updateSQLCode", methods=["POST", "GET", "PUT"])
def updateSQLCode():
    SQLCode = request.args.get("SQLCode")
    communication.updateSQLCode(SQLCode)
    return jsonify({"status_code": 200})


@app.route("/getSQLCodeTree", methods=["GET"])
def getSQLCodeTree():
    return jsonify({"SQLCodeTree": communication.getSQLCodeTree()})


@app.route("/getDBInfo", methods=["GET"])
def getDBinfo():
    return jsonify(communication.getOriginalSchemaCollection())


@app.route("/getDBList", methods=["GET"])
def getDBList():
    return jsonify(communication.getDBList())


@app.route("/updateDB", methods=["POST", "PUT"])
def updateDB():
    dbname = request.json.get("selectedDB")
    return jsonify(communication.updateDB(dbname))


@app.route("/formatSQL", methods=["POST"])
def formatSQL():
    sql = request.json.get("sql")
    is_pretty = request.json.get("is_pretty")
    parse = sqlglot.parse_one(sql)
    return parse.sql(pretty=True)


@app.route("/formatSQL_V1", methods=["POST"])
def formatSQL_V1():
    result = {}
    try:
        sql = request.json.get("sql")
        is_pretty = request.json.get("is_pretty")
        parse = sqlglot.parse_one(sql)
        result["sql"] = parse.sql(pretty=True)
        return jsonify(result)
    except Exception as e:
        result["error"] = str(e)
        return jsonify(result)


@app.route("/executeSQL", methods=["POST"])
def executeSQL():
    sql = request.json.get("sql")
    print(sql)
    return jsonify(communication.executeSQL(sql))


@app.route("/modifySQL", methods=["POST"])
def modifySQL():
    new_data = request.json.get("data")
    original_data = request.json.get("original_data")
    result = communication.modifySQL(new_data, original_data)
    return jsonify(result)


@app.route("/getDBSchema", methods=["GET"])
def getDBSchema():
    return jsonify(communication.getDBSchema())


@app.route("/genNewQuestion", methods=["POST"])
def reStep1_V1():
    configuration = request.json.get("configuration")
    return jsonify(communication.reStep1_V2(configuration))


@app.route("/getSolution", methods=["POST"])
def step2():
    configuration = request.json.get("configuration")
    return jsonify(communication.step2_v1(configuration))


@app.route("/getSQLCodeTreeV1", methods=["POST"])
def getSQLCodeTreeV1():
    try:
        sql = request.json.get("sql")
        result = jsonify(SQLParser(SQL=sql).buildTree())
    except:
        result = jsonify({"error": "Invalid SQL"})
    return result


@app.route("/modidyStep2V1", methods=["POST"])
def modidyStep2V1():
    original_data = request.json.get("original_data")
    new_data = request.json.get("new_data")
    return jsonify(communication.modifySQL_V1(new_data, original_data))


@app.route("/gptFix", methods=["POST"])
def gptFix():
    sql = request.json.get("sql")
    data = request.json.get("data")
    isSubStep = request.json.get("isSubStep")
    subStepId = request.json.get("subStepId")
    return jsonify(communication.gptFix(sql, data, isSubStep, subStepId))


@app.route("/explain", methods=["POST"])
def explain():
    content = request.json.get("content")
    data = request.json.get("data")
    isUserActive = request.json.get("isUserActive")
    isSub = request.json.get("isSub")
    subStepID = request.json.get("subStepID")
    return jsonify(communication.explain(content, data, isUserActive, isSub, subStepID))


@app.route("/explainCombine", methods=["POST"])
def explainCombine():
    selContent = request.json.get("selContent")
    context = request.json.get("context")
    data = request.json.get("data")
    return jsonify(communication.explainCombine(selContent, context, data))


####


def assign_layers(G):
    layers = {}
    for node in nx.topological_sort(G):
        layers[node] = (
            max([layers.get(pred, 0) for pred in G.predecessors(node)] + [0]) + 1
        )
    return layers


def position_by_layers(G, layers, grid_size):
    pos = {}
    layer_nodes = {}
    max_nodes_in_layer = 0
    for node, layer in layers.items():
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)
        max_nodes_in_layer = max(max_nodes_in_layer, len(layer_nodes[layer]))
    for layer, nodes in layer_nodes.items():
        step = grid_size / (len(nodes) + 1)
        y_position = grid_size - layer * (grid_size // len(layer_nodes))
        for i, node in enumerate(nodes):
            x_position = (i + 1) * step
            pos[node] = (x_position, y_position)
    return pos


def DAGPositionCal(edgeList: list, grid_size=10):
    G = nx.DiGraph()
    G.add_edges_from(edgeList)
    layers = assign_layers(G)
    grid_size = 10
    grid_pos = position_by_layers(G, layers, grid_size)
    dict_x = {}
    dict_y = {}
    set_x = set()
    set_y = set()
    for key in grid_pos.keys():
        set_x.add(grid_pos[key][0])
        set_y.add(grid_pos[key][1])
    list_x = sorted(list(set_x))
    list_y = sorted(list(set_y), reverse=True)
    for i in range(len(list_x)):
        dict_x[list_x[i]] = i
    for i in range(len(list_y)):
        dict_y[list_y[i]] = i
    for key in grid_pos.keys():
        grid_pos[key] = (dict_x[grid_pos[key][0]], dict_y[grid_pos[key][1]])
    return grid_pos


@app.route("/getDAGPosition", methods=["POST"])
def getDAGPosition():
    edgeList = request.json.get("edgeList")
    return jsonify(DAGPositionCal(edgeList))


@app.route("/saveLog", methods=["POST"])
def saveLog():
    log = request.json.get("log")
    with open(f'./data/log/{log["name"]}.json', "w") as json_file:
        json.dump(log, json_file, indent=4)  #
    return jsonify({"status_code": 200})


###
print(DAGPositionCal([[0, 1], [1, 2], [2, 3], [1, 3]]))
if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=5006)
