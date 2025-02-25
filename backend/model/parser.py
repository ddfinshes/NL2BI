import sqlparse
import sqlglot
import sqlite3
import copy
import pandas as pd


class SQLParser:

    def __init__(
        self,
        SQL="SELECT * FROM schools WHERE CDSCode IN (SELECT CDSCode FROM frpm)",
        dbName="california_schools",
        dbFolderPath="./data/dbCollection/",
    ):
        self.dbName = dbName
        self.dbFolderPath = dbFolderPath
        self.dbPath = dbFolderPath + dbName + "/" + dbName + ".sqlite"
        self.originalSQL = SQL
        self.parse = sqlglot.parse_one(SQL)
        self.formatSQL = self.parse.sql(pretty=True)
        self.queryTree = self.buildTree()
        self.conn = sqlite3.connect(self.dbPath)
        self.cursor = self.conn.cursor()
        self.originalSchema = self.generateSchema()
        self.originalSchemaFKPairs = self.generateFkpPairsList(self.originalSchema)

    def buildTree(self):
        queryCollection = list(self.parse.find_all(sqlglot.exp.Select))
        """
        node structure
        {
            'originalSQL':'xxx',
            'node':xxx,
            # 'replacedSQL':'xxx',
            'children':[]
        }
        """
        # Proble
        """
        query_list = [
            {
                "SQL": copy.deepcopy(queryCollection[i].sql()),
                # "node": copy.deepcopy(queryCollection[i]),
                "children": [],
                "parent": None,
            }
            for i in range(len(queryCollection))
        ]
        for j in range(len(queryCollection), 0, -1):
            for i in range(len(queryCollection), 0, -1):
                if i == j:
                    continue
                if queryCollection[i].sql() is queryCollection[j].sql():
                    query_list[i]["SQL"] = query_list[i]["SQL"].replace(
                        queryCollection[j].sql(), f"query_{j}"
                    )
                    query_list[i]["children"].append(j)
                    query_list[j]["parent"] = i
                    break
        for i in range(len(query_list)):
            query_list[i]["SQL"] = sqlglot.parse(query_list[i]["SQL"]).sql(pretty=True) 
        """
        expressionCollection = list(self.parse.find_all(sqlglot.exp.Expression))
        expressionList = [
            {
                "index": i,
                "SQL": copy.deepcopy(expressionCollection[i].sql()),
                # "node": copy.deepcopy(queryCollection[i]),
                "children": [],
                "childrenQuerry": [],
                "parent": None,
                "parentQuerry": None,
                "isQuerry": False,
            }
            for i in range(len(expressionCollection))
        ]
        for i in range(len(expressionCollection)):
            if type(expressionCollection[i]) == sqlglot.exp.Select:
                expressionList[i]["isQuerry"] = True
            for j in range(len(expressionCollection)):
                if i == j:
                    continue
                if expressionCollection[i] == expressionCollection[j].parent:
                    expressionList[i]["children"].append(j)
                    expressionList[j]["parent"] = i
        visited = [0 for i in range(len(expressionList))]
        querryList = []
        # depth = 0

        def dfs(i, depth=0):
            expressionList[i]["depth"] = depth
            visited[i] = 1
            if expressionList[i]["isQuerry"]:
                querryList.append(i)

            for j in expressionList[i]["children"]:
                if visited[j] == 0:
                    expressionList[j]["depth"] = depth
                    if expressionList[j]["isQuerry"]:
                        expressionList[querryList[-1]]["childrenQuerry"].append(j)
                        expressionList[j]["parentQuerry"] = querryList[-1]
                        expressionList[j]["depth"] += 1
                    expressionList[j]["querryBelong"] = querryList[-1]
                    dfs(j, expressionList[j]["depth"])
            if expressionList[i]["isQuerry"]:
                querryList.pop()

        dfs(0, 0)
        return {"expressionList": expressionList}

    def getFormatSQL(self):
        return self.formatSQL

    def getSQLCodeTree(self):
        return self.queryTree

    def executeSQL(self):
        self.cursor.execute(self.parse.sql())
        return self.cursor.fetchall()

    def updateSQLCode(self, SQLCode):
        self.originalSQL = SQLCode
        self.parse = sqlglot.parse_one(SQLCode)
        self.formatSQL = self.parse.sql(pretty=True)
        self.queryTree = self.buildTree()

    def generateSchema(self):
        full_schema_prompt_list = []
        conn = sqlite3.connect(self.dbPath)
        # Create a cursor object
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        schemas = {}
        for table in tables:
            if table == "sqlite_sequence":
                continue
            cursor.execute(f"PRAGMA table_info('{table[0]}')")
            columns_info = cursor.fetchall()
            column_df = pd.DataFrame(
                columns_info,
                columns=["cid", "name", "type", "notnull", "dflt_value", "pk"],
            )
            cursor.execute(f"PRAGMA foreign_key_list('{table[0]}')")
            fk_info = cursor.fetchall()
            fk_df = pd.DataFrame(
                fk_info,
                columns=[
                    "id",
                    "seq",
                    "table",
                    "from",
                    "to",
                    "on_update",
                    "on_delete",
                    "match",
                ],
            )
            schemas[table[0]] = {"columns": column_df, "foreign_keys": fk_df}
        return schemas

    def generateFkpPairsList(self, schema):
        fk_pairs_list = []
        for k, v in schema.items():
            for iter, row in v["foreign_keys"].iterrows():
                pair_1 = (k, row["from"])
                pair_2 = (row["table"], row["to"])
                flag = 0
                for j in range(len(fk_pairs_list)):
                    if pair_1 in fk_pairs_list[j] or pair_2 in fk_pairs_list[j]:
                        fk_pairs_list[j].add(pair_1)
                        fk_pairs_list[j].add(pair_2)
                        flag = 1
                        break
                if flag == 0:
                    fk_pairs_list.append(set([pair_1, pair_2]))
        return fk_pairs_list

    def getOriginalSchema(self):
        return self.originalSchema

    def getOriginalSchemaFKPairs(self):
        return self.originalSchemaFKPairs

    def jsonFKPairs(self, fk_pairs):
        fk_json_list = []
        for fk_pair in fk_pairs:
            fk_json_list.append([])
            for fk in fk_pair:
                fk_json_list[-1].append({"table": fk[0], "column": fk[1]})
        return fk_json_list

    def getOriginalSchemaCollection(self):

        table_names = list(self.originalSchema.keys())
        columns = {
            table_name: self.originalSchema[table_name]["columns"]
            .set_index("cid")
            .to_dict()
            for table_name in table_names
        }
        fk_pairs = copy.deepcopy(self.originalSchemaFKPairs)
        fk_pairs = self.jsonFKPairs(fk_pairs)
        return {"table_names": table_names, "columns": columns, "fk_pairs": fk_pairs}

    def updateDB(self, dbName):
        self.dbName = dbName
        self.dbPath = self.dbFolderPath + dbName + "/" + dbName + ".sqlite"
        self.originalSchema = self.generateSchema()
        self.originalSchemaFKPairs = self.generateFkpPairsList(self.originalSchema)
        self.conn = sqlite3.connect(self.dbPath)
        self.cursor = self.conn.cursor()
        return self.getOriginalSchemaCollection()

    def getdbPath(self):
        return self.dbPath

    def getCursor(self):
        return self.cursor

