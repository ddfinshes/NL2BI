import sqlite3
from tqdm import tqdm
import copy
import pandas as pd
import json
import openai
import os
import chardet
import pickle
import ast
import pickle
import time
import ast
from func_timeout import func_timeout, FunctionTimedOut
import sqlglot


APIKEY = "sk-awHE6O3rfLOL2QLf43C6CaCc7eB04336933f0dCeC20aE118"
BASEURL = "https://ai-yyds.com/v1"
MAXTOKEN = 1024
TEMPERATURE = 0
ISEVIDENCE = True

EXCNT = 0


class MCS:

    def __init__(
        self,
        configuration={},
        question="Under whose administration does the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 belong to?",
        dbName="california_schools",
        dbFolderPath="./data/dbCollection/",
        evidence="The question is asking for information about the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 in",
    ) -> None:
        self.configuration = configuration
        if "apiKey" not in configuration:
            configuration["apiKey"] = APIKEY
        if "baseURL" not in configuration:
            configuration["baseURL"] = BASEURL
        if "maxtokens" not in configuration:
            configuration["maxtokens"] = MAXTOKEN
        if "temperature" not in configuration:
            configuration["temperature"] = TEMPERATURE
        if "isevidence" not in configuration:
            configuration["isevidence"] = ISEVIDENCE
        self.dbName = dbName
        self.question = question
        self.dbFolderPath = dbFolderPath
        self.dbPath = dbFolderPath + dbName + "/" + dbName + ".sqlite"
        self.evidence = evidence

        ###schemaFilter###
        self.schema_table = None
        self.prompt_table = None
        self.result_table = None
        self.schema_col = None
        self.prompt_link = None
        self.result_col = None
        self.schema_filter = None
        self.sub_question_list = []
        ###SQLGenerator###
        self.reason_list = []
        self.sql_list = []
        ###SQLSelector###
        self.result = None
        self.result_SQL = None
        self.isSchemaFilter = False
        self.schema_table = self.generate_schema(self.dbPath)

    def updatedbName(self, dbName):
        self.dbName = dbName
        self.dbPath = self.dbFolderPath + self.dbName + "/" + self.dbName + ".sqlite"
        self.schema_table = self.generate_schema(self.dbPath)
        return self.schema_table

    def getDBSchema(self):
        return self.schema_table

    def SchemaPreprocess(self, schemaTransfered, schema=None):
        flag = False
        if schema == None:
            schema = self.schema_table
            flag = True
        schema = {
            k: v for k, v in schema.items() if k in schemaTransfered["table_names"]
        }
        if flag:
            self.schema_table = schema
        return schema

    def pipeline(self):
        for i in range(3):
            try:
                self.schemaFilter()
                self.logic()
                for i in range(len(self.sub_question_list)):
                    self.subSQL(i)
                self.result_SQL = self.generate_SQL_new()

                self.assembleCollection()
                break
            except Exception as e:
                print(f"Error Info: {e}")
        return self.result

    def modify_pipeline_subquestion(self, original_data, new_data, differ):
        for i in range(3):
            try:
                if self.isSchemaFilter == False:
                    self.schemaFilter()
                modify = self.modify_prompt(differ, original_data, new_data)
                self.logic(modify=modify)
                len_old = len(original_data["COT"])
                len_new = len(self.sub_question_list)
                len_in = min(len_old, len_new)
                start_ind = 0
                for j in range(len_in):
                    if (
                        original_data["COT"][j]["subQuestion"]
                        != self.sub_question_list[j]["subQuestion"]
                    ):
                        break
                    if (
                        original_data["COT"][j]["stepDescription"]
                        != self.sub_question_list[j]["stepDescription"]
                    ):
                        break
                    if (
                        original_data["COT"][j]["subSQL"]
                        != self.sub_question_list[j]["subSQL"]
                    ):
                        break
                    start_ind += 1
                for j in range(start_ind, len_new):
                    self.subSQL(j)
                self.result_SQL = self.generate_SQL_new()

                self.assembleCollection()
                break
            except Exception as e:
                print("ERROR in modify_pipeline")
                print(f"{e}")
        return self.result

    def assembleCollection(self):
        result = {}
        result["question"] = self.question
        result["dbName"] = self.dbName
        result["dbPath"] = self.dbPath
        result["evidence"] = self.evidence
        result["SQL"] = self.result_SQL["sql"]
        result["COT"] = []
        for i in range(len(self.sub_question_list)):
            result["COT"].append(self.sub_question_list[i])
        result["tableSchema"] = self.getSchema()
        self.result = result
        return result

    def schemaFilter(self):
        self.prompt_table = self.generate_table_prompt(
            self.schema_table, self.question, self.evidence
        )
        self.result_table = self.table_link(self.schema_table, self.prompt_table)
        self.schema_col = {
            k: v
            for k, v in self.schema_table.items()
            if k in self.result_table["tables"]
        }
        self.prompt_link = self.generate_col_prompt(
            self.schema_col, self.question, self.evidence
        )
        self.result_col = self.col_link(self.schema_col, self.prompt_link)
        self.schema_filter = self.schema_after_col_link(
            self.schema_col, self.result_col
        )
        self.isSchemaFilter = True
        return self.schema_filter
        pass

    def SQLGenerator(self):
        for i in range(3):
            self.example_description = ""
            self.schema_description = self.generate_schema_description(
                self.schema_filter, self.dbPath
            )
            self.prompt = self.generate_prompt_generator(
                self.schema_description,
                self.question,
                self.example_description,
                self.evidence,
            )
            self.result = self.generate_sql(self.prompt)
            self.reason_list.append(self.result["reasoning"])
            self.sql_list.append({"sql": self.result["sql"], "db_id": self.dbName})
        pass

    def SQLSelector(self):
        self.sql_refine = self.sql_refine(self.sql_list, self.dbPath)
        self.schema_description = self.generate_schema_description(
            self.schema_filter, self.dbPath
        )
        self.prompt = self.generate_prompt_select(
            self.sql_refine, self.question, self.schema_description, self.evidence
        )
        self.result = self.select_sql(self.prompt)
        pass

    def getSQL(self):
        return self.result["sql"]

    def getReasoning(self):
        return self.result["reasoning"]

    def jsonFKPairs(self, fk_pairs):
        fk_json_list = []
        for fk_pair in fk_pairs:
            fk_json_list.append([])
            for fk in fk_pair:
                fk_json_list[-1].append({"table": fk[0], "column": fk[1]})
        return fk_json_list

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

    def getSchema(self):
        table_names = list(self.schema_filter.keys())
        columns = {
            table_name: self.schema_filter[table_name]["columns"]
            .set_index("cid")
            .to_dict()
            for table_name in table_names
        }
        fk_pairs = copy.deepcopy(self.generateFkpPairsList(self.schema_filter))
        fk_pairs = self.jsonFKPairs(fk_pairs)
        return {"table_names": table_names, "columns": columns, "fk_pairs": fk_pairs}

    ############################################################################################################
    ############################################################################################################
    ########################################schemaFilter########################################################
    ############################################################################################################
    ############################################################################################################
    def generate_fk_pairs_list(self, schema):
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

    def schemaTrans(self, schema):
        result = {}
        result["table_names"] = []
        result["columns"] = {}
        result["fk_pairs"] = []
        for k, v in schema.items():
            result["table_names"].append(k)
            result["columns"][k] = v["columns"].to_dict()
        fk_pairs = self.generateFkpPairsList(schema)
        result["fk_pairs"] = self.jsonFKPairs(fk_pairs)
        return result

    def generate_schema(self, db_path, num_rows=None):
        full_schema_prompt_list = []
        conn = sqlite3.connect(db_path)
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

    def generate_table_prompt(self, schema, question, evidence=""):
        prompt_system = "You are a SQL exert"
        prompt_assistant = "Given a database schema, question, and knowledge evidence, extract a list of tables that should be referenced to convert the question into SQL\n"
        prompt_user = ""
        prompt_assistant += "SQLite SQL tables, with their properties:\n"
        for k, v in schema.items():
            prompt_assistant += f"{k} ("
            prompt_assistant += ", ".join(v["columns"].name.tolist())
            prompt_assistant += ")\n"
        fk_pairs_list = self.generate_fk_pairs_list(schema)

        prompt_assistant += "\n"
        for i in range(len(fk_pairs_list)):
            for pair in list(fk_pairs_list[i]):
                prompt_assistant += f"{pair[0]}.{pair[1]} = "
            prompt_assistant = prompt_assistant[:-2]
            prompt_assistant += "\n"
        pass

        prompt_user += f"Question: {question}\n"
        prompt_user += f"Knowledge evidence: {evidence}\n"
        prompt_user += "You need to not only select the required tables, but also explain in detail why each table is needed.\n"
        prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
        prompt_user += '```json \n {\n "reasoning":"",\n "tables":[],\n}\n ```'
        return {
            "system": prompt_system,
            "assistant": prompt_assistant,
            "user": prompt_user,
        }

    def table_link(self, schema, prompt, model="gpt-4o-mini"):
        result = None
        try:
            client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
            result = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt["system"],
                    },
                    {"role": "assistant", "content": prompt["assistant"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                max_tokens=MAXTOKEN,
                temperature=TEMPERATURE,
            )
            result_ans = result.choices[0].message.content
            if "```" not in result_ans:
                result_ans = "```" + result_ans + "```"

            result_ans = result_ans.split("```")[1]
            result_ans = result_ans.replace("json", "")
            #        result = result.replace(", "")
            result_ans = result_ans.replace("\n", " ")
            if "```" not in result_ans:
                result_ans = result_ans + "```"
            result_ans = result_ans.split("```")[0]

            result_ans = ast.literal_eval(result_ans)
            pass

        except Exception as e:
            print("ERROR!!! in table_link")
            print(f"ERROR INFO: {e}")
            error_info = "ERROR "
            if type(result) == str:
                error_info += result_ans
            result_ans = {
                "reasoning": error_info,
                "tables": [key for key in schema.keys()],
            }
        pass
        return result_ans

    def generate_col_prompt(self, schema, question, evidence=""):
        prompt_system = "You are a SQL exert"
        prompt_assistant = "Given a database schema, question, and knowledge evidence, extract a list of columns that should be referenced to convert the question into SQL\n"
        prompt_user = ""
        prompt_assistant += "SQLite SQL tables, with their properties:\n"
        fk_pairs_list = self.generate_fk_pairs_list(schema)
        for k, v in schema.items():
            prompt_assistant += f"{k} ("
            prompt_assistant += ", ".join(v["columns"].name.tolist())
            prompt_assistant += ")\n"
        prompt_assistant += "\n"
        for i in range(len(fk_pairs_list)):
            for pair in list(fk_pairs_list[i]):
                prompt_assistant += f"{pair[0]}.{pair[1]} = "
            prompt_assistant = prompt_assistant[:-2]
            prompt_assistant += "\n"
        prompt_user += f"Question: {question}\n"
        prompt_user += f"Knowledge evidence: {evidence}\n"
        prompt_user += "You need to not only select the required columns, but also explain in detail why each column is needed.\n"
        prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
        prompt_user += '```json {\n "reasoning":"",\n "columns":[[table_name_i,column_name_j],... ],\n}\n ```'
        return {
            "system": prompt_system,
            "assistant": prompt_assistant,
            "user": prompt_user,
        }

    def col_link(self, schema, prompt, model="gpt-4o-mini"):
        result = None
        try:
            client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
            result = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": prompt["system"],
                    },
                    {"role": "assistant", "content": prompt["assistant"]},
                    {"role": "user", "content": prompt["user"]},
                ],
                max_tokens=MAXTOKEN,
                temperature=TEMPERATURE,
            )
            result_ans = result.choices[0].message.content
            if "```" not in result_ans:
                result_ans = "```" + result_ans + "```"
            result_ans = result_ans.split("```")[1]
            result_ans = result_ans.replace("json", "")
            result_ans = result_ans.replace("\n", " ")
            if "```" not in result_ans:
                result_ans = result_ans + "```"
            result_ans = result_ans.split("```")[0]

            result_ans = ast.literal_eval(result_ans)
            pass
        except Exception as e:
            print("ERROR in col_link!!!")
            print(f"ERROR INFO: {e}")
            error_info = "ERROR "
            cols = []
            for k_table, v_table in schema.items():
                for k_col, v_col in v_table["columns"].iterrows():
                    cols.append([k_table, v_col["name"]])
            if type(result) == str:
                error_info += result_ans
            result_ans = {"reasoning": error_info, "columns": cols}
        pass
        return result_ans

    def schema_after_col_link(self, schema, result):
        schema_after = {}
        fk = pd.DataFrame(columns=["table_1", "column_1", "table_2", "column_2"])
        fk_pairs_list = self.generate_fk_pairs_list(schema)
        fk_pairs_list_1d = []
        for i in range(len(fk_pairs_list)):
            fk_pairs_list_1d += list(fk_pairs_list[i])
        fk_pairs_list_1d_col = [pair[1] for pair in fk_pairs_list_1d]
        for k_table, v_value in schema.items():
            schema_after[k_table] = {}
            selected_cols = [
                pair[1] for pair in result["columns"] if pair[0] == k_table
            ]
            v_col = v_value["columns"]
            v_fk = v_value["foreign_keys"]
            v_col_after = v_col[
                (v_col["name"].isin(selected_cols))
                | (v_col["pk"] > 0)
                | (v_col["name"].isin(fk_pairs_list_1d_col))
            ]
            schema_after[k_table]["columns"] = v_col_after
            """
            v_fk_after = v_fk[
                v_fk["from"].isin(selected_cols) + v_fk["to"].isin(selected_cols)
            ]
            """
            v_fk_after = v_fk
            schema_after[k_table]["foreign_keys"] = v_fk_after
        return schema_after

    ############################################################################################################
    ############################################################################################################
    ########################################SQLGenerator########################################################
    ############################################################################################################
    ############################################################################################################

    def generate_schema_description(self, schema, db_path, num_rows=1):

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        db_path_folder = "/".join(db_path.split("/")[:-1]) + "/"
        schema_description = "SQLite SQL tables, with their properties:\n"
        fk_pairs_list = self.generate_fk_pairs_list(schema)

        for k, v in schema.items():
            schema_description += f"{k} ("
            schema_description += ", ".join(v["columns"].name.tolist())
            schema_description += ")\n"

        schema_description += "\n"
        for i in range(len(fk_pairs_list)):
            for pair in list(fk_pairs_list[i]):
                schema_description += f"{pair[0]}.{pair[1]} = "
            schema_description = schema_description[:-2]
            schema_description += "\n"

        description = "The type and description of each column:\n"
        sample_row = "Sample rows of each table in csv formate:\n"
        for k, v in schema.items():
            description += f"{k}:\n"
            v_col = v["columns"]
            with open(db_path_folder + "database_description/" + k + ".csv", "rb") as f:
                open_file = chardet.detect(f.read())
            description_csv = pd.read_csv(
                db_path_folder + "database_description/" + k + ".csv",
                encoding=open_file["encoding"],
            )
            for i in v_col["name"].tolist():
                str_de = description_csv[
                    ((description_csv["original_column_name"].str.strip()) == (i))
                ]["column_description"].values[0]
                description += f"{i}: {str_de}\n"

            description += "\n"

            sample_row += f"{k}:\n"
            str_col = ", ".join([("'" + str(i) + "'") for i in v_col["name"].tolist()])
            cursor.execute(f"SELECT {str_col} from '{k}' LIMIT {num_rows}")
            rows = cursor.fetchall()
            sample_df = pd.DataFrame(columns=v_col["name"].tolist())
            for i in range(num_rows):
                sample_df.loc[i] = rows[i]
            pass
            sample_row += str(sample_df)
            sample_row += "\n\n"
            pass

        schema_description += description
        schema_description += sample_row
        return schema_description

    def generate_prompt_generator(
        self, schema_description, question, gold_example="", evidence=""
    ):
        prompt_system = "You are a SQL expert"
        prompt_user = ""
        prompt_assistant = "Given a database schema, question, and knowledge evidence, generate the correct sqlite SQL query for the question\n"

        prompt_assistant += gold_example
        prompt_assistant += "\n"
        prompt_assistant += schema_description
        prompt_user += f"Question: {question}\n"
        prompt_user += f"Knowledge evidence: {evidence}\n"
        prompt_user += "You need not to only create the SQL, but also provide the detailed reasoning steps required to create the SQL. Your answer should be strictly follow the following json format and in a json code block. without any comment\n"
        prompt_user += '```json\n {\n "sql": "" \n"reasoning":"",\n }\n```'
        return {
            "system": prompt_system,
            "assistant": prompt_assistant,
            "user": prompt_user,
        }

    def generate_sql(self, prompt, model="gpt-4o-mini"):
        result = None
        i = 0
        while i < 3:
            i += 1
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": prompt["system"],
                        },
                        {"role": "assistant", "content": prompt["assistant"]},
                        {"role": "user", "content": prompt["user"]},
                    ],
                    max_tokens=MAXTOKEN,
                    temperature=TEMPERATURE,
                )
                result_ans = result.choices[0].message.content
                if "```" not in result_ans:
                    result_ans = "```" + result_ans + "```"
                result_ans = result_ans.split("```")[1]
                if "```" not in result_ans:
                    result_ans = result_ans + "```"
                result_ans = result_ans.split("```")[0]
                result_ans = result_ans.replace("json", "")
                result_ans = result_ans.replace("\n", " ")
                result_ans = result_ans.replace(";", " ")
                #  result_ans = result_ans.replace("\\", "")
                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = ast.literal_eval(result_ans)
                if "reasoning" not in result_ans:
                    print(f"ERROR {model}")
                    print(result_ans)
                    result_ans["reasoning"] = "ERROR"
                if "sql" not in result_ans:
                    print(f"ERROR {model}")

                    print(result_ans)
                    result_ans["sql"] = "ERROR"
                result_ans["sql"] = result_ans["sql"].replace(";", " ")
                result_ans["sql"] = result_ans["sql"].replace("\n", " ")
                result_ans["sql"] = result_ans["sql"].replace("\\", " ")
                break
            except:
                print(f"ERROR {model}")
                result_ans = {"reasoning": "ERROR", "sql": "ERROR"}
        return result_ans

    ############################################################################################################
    ############################################################################################################
    ########################################SQLSelector########################################################
    ############################################################################################################
    ############################################################################################################

    def execture_sql(self, sql, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        time_1 = time.time()
        cursor.execute(sql)
        res = cursor.fetchall()
        time_2 = time.time()

        res = set(res)
        return res, time_2 - time_1

    def sql_refine(self, sql_iter, db_path, meta_time_out=30.0, threshold=0):
        pass
        total_length = len(sql_iter)
        sql_result = []
        sql_refine = []
        sql_time = []
        for iter in sql_iter:
            # sql_refine.append(iter["sql"])
            try:
                res, time_exc = func_timeout(
                    meta_time_out, self.execture_sql, args=(iter["sql"], db_path)
                )
            except:
                res = 0
                time_exc = 1e6
            flag = 0
            for j in range(len(sql_result)):
                if res == sql_result[j]:
                    if time_exc < sql_time[j]:
                        sql_refine[j] = iter["sql"]
                        sql_time[j] = time_exc
                    flag = 1
                    break
            if flag == 0:
                sql_result.append(res)
                sql_refine.append(iter["sql"])
                sql_time.append(time_exc)

        return sql_refine

    def generate_prompt_select(
        self, sql_iter, question, schema_description, evidence=""
    ):
        prompt_system = "You are a SQL expert"
        prompt_user = ""
        prompt_assistant = "When a DB schema, a question, and a knowledge evidence are given, and sql queries expressing the question are given, please choose the most accurate SQL\n"

        prompt_assistant += schema_description

        prompt_user += f"Question: {question}\n"
        prompt_user += f"Knowledge evidence: {evidence}\n"
        prompt_user += "SQL queries:\n"
        for sql in sql_iter:
            prompt_user += f"{sql}\n"
        prompt_user += "Your answer should strictly follow the following json format and in a json code block:\n"
        prompt_user += '```json \n {\n "sql": "",\n"reasoning":""\n  }```'
        return {
            "system": prompt_system,
            "assistant": prompt_assistant,
            "user": prompt_user,
        }

    def select_sql(self, prompt, model="gpt-4o-mini"):
        result = None
        i = 0
        while i < 3:
            i += 1
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": prompt["system"],
                        },
                        {"role": "assistant", "content": prompt["assistant"]},
                        {"role": "user", "content": prompt["user"]},
                    ],
                    max_tokens=MAXTOKEN,
                    temperature=TEMPERATURE,
                )
                result_ans = result.choices[0].message.content

                if "```" not in result_ans:
                    result_ans = "```" + result_ans + "```"
                result_ans = result_ans.split("```")[1]
                if "```" not in result_ans:
                    result_ans = result_ans + "```"
                result_ans = result_ans.split("```")[0]
                result_ans = result_ans.replace("json", "")
                # result = result.replace("sql", "")
                result_ans = result_ans.replace("\\", " ")
                result_ans = result_ans.replace("\n", " ")
                result_ans = ast.literal_eval(result_ans)
                result_ans["sql"] = result_ans["sql"].replace(";", " ")
                result_ans["sql"] = result_ans["sql"].replace("\n", " ")
                result_ans["sql"] = result_ans["sql"].replace("\\", " ")
                break
            except:
                print("ERROR SELECT")
                result_ans = {"reasoning": "ERROR", "sql": "ERROR"}
        return result_ans

    ############################################################################################
    ############################################################################################
    ############################################################################################
    ############################################################################################
    def data2description(self, data):
        content = f'question: {data["question"]}\nSQL: {data["SQL"]}\n'
        content += "COT steps"
        content += "```json\n"
        content += f"[\n"
        for j in data["COT"]:
            content += "\{\n"
            content += f'    "subQuestion": {j["subQuestion"]},\n'
            content += f'    "stepDescription": {j["stepDescription"]},\n'
            content += f'    "subSQL": {j["subSQL"]},\n'
            content += f'    "coreSQL": {j["coreSQL"]}\n'
            content += f'    "previousQuestion": {j["previousQuestion"]}\n'
            content += "\},\n"
        content += "]\n"
        content += "```"
        return content

    def modify_prompt(self, modify, old_data, new_data):
        prompt = ""
        old_data_prompt = self.data2description(old_data)
        # new_data_prompt = self.data2description(new_data)

        prompt_old = f"old solution:\n {old_data_prompt}\n"
        prompt_mod = f"The following is the user modifyinh\n"
        for i in range(len(modify)):
            if len(modify[i]["error_type"]) == 0:
                continue
            prompt_mod += f"modify of the {modify[i]['error_index']}th subquestion\n"
            for j in modify[i]["error_type"]:
                if j == "subQuestion":
                    prompt_mod += f"subQuestion is modfied as {new_data['COT'][i]['subQuestion']}\n"
                if j == "stepDescription":
                    prompt_mod += f"stepDescription is modfied as {new_data['COT'][i]['stepDescription']}\n"
                if j == "subSQL":
                    prompt_mod += (
                        f"subSQL is modfied as {new_data['COT'][i]['subSQL']}\n"
                    )
        prompt = {"modify": prompt_mod, "old": prompt_old}
        return prompt
        # prompt += f"user modified data:\n {new_data_prompt}\n"

    def logic(self, modify=None):
        prompt_system = "You are a SQL expert"
        prompt_user = ""
        prompt_assistant = ""
        if modify:
            prompt_assistant += self.generate_schema_description(
                self.schema_filter, self.dbPath
            )
            prompt_assistant += f"Question: {self.question}\n"
            prompt_assistant += f"Knowledge evidence: {self.evidence}\n"
            prompt_assistant += "You made a mistake in the previous output solution, please modify the following solution(the index of subquestions start from 0)\n"
            prompt_assistant += modify["old"]
            prompt_user += "\n Here is the user modification, you should refer them and keep them. Also, before the first modify subquestions, the previous subquestions should be kept and it is the same to their orders unless wrong. Be careful, you may need to reconsider the following step after a wrong step\n"
            prompt_user += modify["modify"]
            prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
            prompt_user += "```json \n"
            prompt_user += "[\n"
            prompt_user += "  {\n"
            prompt_user += '    "id": ,\\\\ int, start from 0 \n'
            prompt_user += '    "subQuestion": "",\n'
            prompt_user += '    "stepDescription": ""\n'
            prompt_user += '    "previousQuestion": [""]\n'
            prompt_user += "  },...\n"
            prompt_user += "]\n"
            prompt_user += "```"
        else:
            prompt_assistant += self.generate_schema_description(
                self.schema_filter, self.dbPath
            )
            prompt_user += f"Question: {self.question}\n"
            prompt_user += f"Knowledge evidence: {self.evidence}\n"
            prompt_user += "You need to analyze the question and split into subquestions, sketching the logic between subquestions, but do not need to generate SQL queries.\n"
            prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
            prompt_user += "```json \n"
            prompt_user += "[\n"
            prompt_user += "  {\n"
            prompt_user += '    "id": ,\\\\ int, start from 0 \n'
            prompt_user += '    "subQuestion": "",\n'
            prompt_user += '    "stepDescription": ""\n'
            prompt_user += '    "previousQuestion": [""]\n'
            prompt_user += "  },...\n"
            prompt_user += "]\n"
            prompt_user += "```"
        i = 0
        while i < 3:
            i += 1
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt_system,
                        },
                        {"role": "assistant", "content": prompt_assistant},
                        {"role": "user", "content": prompt_user},
                    ],
                    max_tokens=MAXTOKEN,
                    temperature=TEMPERATURE,
                )
                result_ans = result.choices[0].message.content

                if "```" not in result_ans:
                    result_ans = "```" + result_ans + "```"
                result_ans = result_ans.split("```")[1]
                if "```" not in result_ans:
                    result_ans = result_ans + "```"
                result_ans = result_ans.split("```")[0]
                result_ans = result_ans.replace("json", "")
                result_ans = result_ans.replace("\n", " ")
                result_ans = result_ans.replace(";", " ")
                #  result_ans = result_ans.replace("\\", "")
                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(result_ans)
                for i in range(len(result_ans)):
                    result_ans[i]["id"] = int(result_ans[i]["id"])
                    for j in range(len(result_ans[i]["previousQuestion"])):
                        result_ans[i]["previousQuestion"][j] = int(
                            result_ans[i]["previousQuestion"][j]
                        )
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    for i in range(len(result_ans)):
                        result_ans[i]["id"] = int(result_ans[i]["id"])
                        for j in range(len(result_ans[i]["previousQuestion"])):
                            result_ans[i]["previousQuestion"][j] = int(
                                result_ans[i]["previousQuestion"][j]
                            )
                except:

                    print("Error in log")
                    print(f"{e}")
                    result_ans = [
                        {
                            "id": 0,
                            "stepDescription": "ERROR",
                            "subQuestion": self.question,
                            "previousQuestion": [],
                            "subSQL": "",
                        }
                    ]
        self.sub_question_list = result_ans
        return result_ans
        pass

    def subSQL(self, i):
        subQuestionNode = self.sub_question_list[i]
        subQuestion = subQuestionNode["subQuestion"]
        requiredQuestions = []

        def bfs(i):
            requiredQuestions = []
            nodes = self.sub_question_list[i]["previousQuestion"]
            for node in nodes:
                requiredQuestions.append(node)

            for node in nodes:
                requiredQuestions += bfs(node)
            return requiredQuestions

        requiredQuestions = bfs(i)
        if len(requiredQuestions) > 0:
            set_req = set(requiredQuestions)
            set_req.discard(i)
            requiredQuestions = list(set_req)
        requiredQuestions.sort()

        prompt_system = "You are a SQL expert"
        prompt_user = ""
        prompt_assistant = ""

        prompt_assistant += self.generate_schema_description(
            self.schema_filter, self.dbPath
        )
        prompt_assistant += "\n"
        prompt_assistant += "Prequestion: \n"
        for j in requiredQuestions:
            prompt_assistant += (
                "subquestion"
                + str(self.sub_question_list[j]["id"])
                + ": "
                + self.sub_question_list[j]["subQuestion"]
                + "\n"
            )
            prompt_assistant += "subSQL: " + self.sub_question_list[j]["subSQL"] + "\n"
            prompt_assistant += (
                "reasoning: " + self.sub_question_list[j]["stepDescription"] + "\n"
            )
            prompt_assistant += (
                "requiredSubquestion: "
                + str(self.sub_question_list[j]["previousQuestion"])
                + "\n"
            )
        prompt_assistant += "\n"
        prompt_user += f'You have to solve the {str(self.sub_question_list[i]["id"])}th subquestion: {subQuestion}\n'
        prompt_user += f"Knowledge evidence: {self.evidence}\n"
        prompt_user += (
            "You need to solve this question and return sql wihch can execute and why\n"
        )
        prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
        prompt_user += "```json \n"
        prompt_user += "  {\n"
        prompt_user += '    "id": "",\n'
        prompt_user += '    "subSQL": "",\n'
        prompt_user += '    "stepDescription": ""\n'
        prompt_user += "  }\n"
        prompt_user += "```"

        cnt = 0
        while cnt < 3:
            cnt += 1
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt_system,
                        },
                        {"role": "assistant", "content": prompt_assistant},
                        {"role": "user", "content": prompt_user},
                    ],
                    max_tokens=MAXTOKEN,
                    temperature=TEMPERATURE,
                )
                result_ans = result.choices[0].message.content

                if "```" not in result_ans:
                    result_ans = "```" + result_ans + "```"
                result_ans = result_ans.split("```")[1]
                if "```" not in result_ans:
                    result_ans = result_ans + "```"
                result_ans = result_ans.split("```")[0]
                result_ans = result_ans.replace("json", "")
                result_ans = result_ans.replace("\n", " ")
                result_ans = result_ans.replace(";", " ")
                #  result_ans = result_ans.replace("\\", "")
                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = ast.literal_eval(result_ans)
                result_ans["subSQL"] = self.formatSQLWithoutPretty(result_ans["subSQL"])
                break
            except:
                result_ans = {
                    "id": self.sub_question_list[i]["id"],
                    "stepDescription": "ERROR",
                    "subSQL": "ERROR",
                }
        self.sub_question_list[i]["subSQL"] = result_ans["subSQL"]
        self.sub_question_list[i]["stepDescription"] = result_ans["stepDescription"]
        pass

    def generate_SQL_new(self):

        prompt_system = "You are a SQL expert"
        prompt_user = ""
        prompt_assistant = ""

        prompt_assistant += self.generate_schema_description(
            self.schema_filter, self.dbPath
        )
        prompt_assistant += "\n"
        prompt_assistant += "Subquestion: \n"
        for i in range(len(self.sub_question_list)):
            prompt_assistant += "subquestion" + str(i) + ": "
            prompt_assistant += self.sub_question_list[i]["subQuestion"] + "\n"
            prompt_assistant += "sql: " + self.sub_question_list[i]["subSQL"] + "\n"
            prompt_assistant += (
                "reasoning: " + self.sub_question_list[i]["stepDescription"] + "\n"
            )
            prompt_assistant += (
                "requiredSubquestion: "
                + str(self.sub_question_list[i]["previousQuestion"])
                + "\n"
            )
        prompt_user += f"Question: {self.question}\n"
        prompt_user += f"Knowledge evidence: {self.evidence}\n"
        prompt_user += "You have to solve the sql quesation and output an SQL. And you have to point the corresponding part matching each subquestion in the output SQL, especially for those operation JOIN, GROUP \n"
        prompt_user += "Your answer should strictly follow the following json format and in a json code block without any comment.\n"
        prompt_user += "```json \n"
        prompt_user += "  {\n"
        prompt_user += '    "sql": "",\n'
        prompt_user += '    "sub":[\n'
        prompt_user += "      {\n"
        prompt_user += (
            '        "id": "",\\\\ int and corresponding to the id of subquestion\n'
        )
        prompt_user += '        "coreSQL": "",\n'
        prompt_user += "      },...\n"
        prompt_user += "    ]\n"
        # prompt_user += '    "reasoning": ""\n'
        prompt_user += "  }\n"
        prompt_user += "```"

        cnt = 0
        while cnt < 3:
            cnt += 1
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": prompt_system,
                        },
                        {"role": "assistant", "content": prompt_assistant},
                        {"role": "user", "content": prompt_user},
                    ],
                    max_tokens=MAXTOKEN,
                    temperature=TEMPERATURE,
                )

                result_ans = result.choices[0].message.content
                if "```" not in result_ans:
                    result_ans = "```" + result_ans + "```"
                result_ans = result_ans.split("```")[1]
                if "```" not in result_ans:
                    result_ans = result_ans + "```"
                result_ans = result_ans.split("```")[0]
                result_ans = result_ans.replace("json", "")
                result_ans = result_ans.replace("\n", " ")
                result_ans = result_ans.replace(";", " ")

                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = ast.literal_eval(result_ans)
                if "sql" not in result_ans:
                    print(f"ERROR SQL")
                    print(result_ans)
                    result_ans["sql"] = "ERROR"
                result_ans["sql"] = result_ans["sql"].replace(";", " ")
                result_ans["sql"] = result_ans["sql"].replace("\n", " ")
                result_ans["sql"] = result_ans["sql"].replace("\\", " ")
                result_ans["sql"] = self.formatSQLWithoutPretty(result_ans["sql"])
                break
            except:
                result_ans = {"reasoning": "ERROR", "sql": "ERROR"}
        self.result_SQL = result_ans
        for i in range(len(self.sub_question_list)):
            self.sub_question_list[i]["coreSQL"] = ""
            if self.sub_question_list[i]["subSQL"] == self.result_SQL["sql"]:
                self.sub_question_list[i]["coreSQL"] = self.result_SQL["sql"]
        for i in range(len(result_ans["sub"])):
            self.sub_question_list[int(result_ans["sub"][i]["id"])]["coreSQL"] = (
                result_ans["sub"][i]["coreSQL"]
            )

        return result_ans

    def formatSQLWithoutPretty(self, sql):
        parse = sqlglot.parse_one(sql)
        return parse.sql(pretty=False)

pass
# For Test
""" 
pass

modify_res = [
{"error_index": 0, "error_type": []},
{"error_index": 1, "error_type": ["subSQL", "subQuestion", "stepDescription"]},
{"error_index": 2, "error_type": []},
]
new_data = {
"question": "Under whose administration does the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 belong to?",
"dbName": "california_schools",
"dbPath": "./data/dbCollection/california_schools/california_schools.sqlite",
"evidence": "The question is asking for information about the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 in",
"SQL": "\nSELECT\n  schools.AdmFName1,\n  schools.AdmLName1\nFROM schools\nJOIN satscores\n  ON schools.CDSCode = satscores.cds\nORDER BY\n  satscores.NumGE1500 DESC\nLIMIT 1",
"COT": [
{
    "id": 0,
    "subQuestion": "Which school has the highest number of test takers whose total SAT scores are greater or equal to 1500?",
    "stepDescription": "To find the school with the highest number of test takers whose total SAT scores are greater or equal to 1500, we can use the SELECT statement to retrieve the 'sname' and 'NumGE1500' columns from the 'satscores' table. We order the results in descending order by 'NumGE1500' and limit the results to only 1 row using the LIMIT clause. This will give us the school with the highest number of test takers with scores greater or equal to 1500.",
    "previousQuestion": [],
    "subSQL": "\nSELECT\n  sname,\n  NumGE1500\nFROM satscores\nORDER BY\n  NumGE1500 DESC\nLIMIT 1",
    "coreSQL": "SELECT schools.AdmFName1, schools.AdmLName1 FROM schools",
},
{
    "id": 1,
    "subQuestion": "Retrieve the CDSCode of the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500.",
    "stepDescription": "I have used a SQL query to select the CDSCode of the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 by selecting the maximum value of NumGE1500 from the satscores table.",
    "previousQuestion": [0],
    "subSQL": "SELECT satscores.cds, MAX(satscores.NumGE1500) AS MaxNumGE1500 FROM satscores",
    "coreSQL": "",
},
{
    "id": 2,
    "subQuestion": "Under whose administration does the school with the highest number of test takers whose total SAT scores are greater or equal to 1500 belong to?",
    "stepDescription": "To find the administrator associated with the school that has the highest number of test takers whose total SAT scores are greater or equal to 1500, we first need to retrieve the CDSCode of that school from the satscores table using a subquery. Then, we use this CDSCode to query the schools table and select the AdmFName1 and AdmLName1 columns for the administrator's first and last names.",
    "previousQuestion": [0, 1],
    "subSQL": "\nSELECT\n  AdmFName1,\n  AdmLName1\nFROM schools\nWHERE\n  CDSCode = (\n    SELECT\n      cds\n    FROM satscores\n    ORDER BY\n      NumGE1500 DESC\n    LIMIT 1\n  )",
    "coreSQL": "ORDER BY satscores.NumGE1500 DESC LIMIT 1",
},
],
"tableSchema": {
"table_names": ["satscores", "schools"],
"columns": {
    "satscores": {
        "name": {"0": "cds", "2": "sname", "10": "NumGE1500"},
        "type": {"0": "TEXT", "2": "TEXT", "10": "INTEGER"},
        "notnull": {"0": 1, "2": 0, "10": 0},
        "dflt_value": {"0": "", "2": "", "10": ""},
        "pk": {"0": 1, "2": 0, "10": 0},
    },
    "schools": {
        "name": {
            "0": "CDSCode",
            "39": "AdmFName1",
            "40": "AdmLName1",
            "42": "AdmFName2",
            "43": "AdmLName2",
            "45": "AdmFName3",
            "46": "AdmLName3",
        },
        "type": {
            "0": "TEXT",
            "39": "TEXT",
            "40": "TEXT",
            "42": "TEXT",
            "43": "TEXT",
            "45": "TEXT",
            "46": "TEXT",
        },
        "notnull": {
            "0": 1,
            "39": 0,
            "40": 0,
            "42": 0,
            "43": 0,
            "45": 0,
            "46": 0,
        },
        "dflt_value": {
            "0": "",
            "39": "",
            "40": "",
            "42": "",
            "43": "",
            "45": "",
            "46": "",
        },
        "pk": {"0": 1, "39": 0, "40": 0, "42": 0, "43": 0, "45": 0, "46": 0},
    },
},
"fk_pairs": [
    [
        {"table": "satscores", "column": "cds"},
        {"table": "schools", "column": "CDSCode"},
    ]
],
},
"id": "49",
"isUser": False,
"isSQL": True,
"time": "2024-08-22 14:55:07",
"modifyCnt": 0,
"previousModify": -1,
"history": [],
"context": "",
}
original_data = {
"question": "Under whose administration does the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 belong to?",
"dbName": "california_schools",
"dbPath": "./data/dbCollection/california_schools/california_schools.sqlite",
"evidence": "The question is asking for information about the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 in",
"SQL": "\nSELECT\n  schools.AdmFName1,\n  schools.AdmLName1\nFROM schools\nJOIN satscores\n  ON schools.CDSCode = satscores.cds\nORDER BY\n  satscores.NumGE1500 DESC\nLIMIT 1",
"COT": [
{
    "id": 0,
    "subQuestion": "Which school has the highest number of test takers whose total SAT scores are greater or equal to 1500?",
    "stepDescription": "To find the school with the highest number of test takers whose total SAT scores are greater or equal to 1500, we can use the SELECT statement to retrieve the 'sname' and 'NumGE1500' columns from the 'satscores' table. We order the results in descending order by 'NumGE1500' and limit the results to only 1 row using the LIMIT clause. This will give us the school with the highest number of test takers with scores greater or equal to 1500.",
    "previousQuestion": [],
    "subSQL": "\nSELECT\n  sname,\n  NumGE1500\nFROM satscores\nORDER BY\n  NumGE1500 DESC\nLIMIT 1",
    "coreSQL": "SELECT schools.AdmFName1, schools.AdmLName1 FROM schools",
},
{
    "id": 1,
    "subQuestion": "Who is the administrator associated with that school?",
    "stepDescription": "To find the administrator associated with the school that has the highest number of test takers whose total SAT scores are greater or equal to 1500, we first need to retrieve the CDSCode of that school from the satscores table using a subquery. Then, we use this CDSCode to query the schools table and select the AdmFName1 and AdmLName1 columns for the administrator's first and last names.",
    "previousQuestion": [0],
    "subSQL": "\nSELECT\n  AdmFName1,\n  AdmLName1\nFROM schools\nWHERE\n  CDSCode = (\n    SELECT\n      cds\n    FROM satscores\n    ORDER BY\n      NumGE1500 DESC\n    LIMIT 1\n  )",
    "coreSQL": "JOIN satscores ON schools.CDSCode = satscores.cds",
},
{
    "id": 2,
    "subQuestion": "Under whose administration does the school with the highest number of test takers whose total SAT scores are greater or equal to 1500 belong to?",
    "stepDescription": "To find the administrator associated with the school that has the highest number of test takers whose total SAT scores are greater or equal to 1500, we first need to retrieve the CDSCode of that school from the satscores table using a subquery. Then, we use this CDSCode to query the schools table and select the AdmFName1 and AdmLName1 columns for the administrator's first and last names.",
    "previousQuestion": [0, 1],
    "subSQL": "\nSELECT\n  AdmFName1,\n  AdmLName1\nFROM schools\nWHERE\n  CDSCode = (\n    SELECT\n      cds\n    FROM satscores\n    ORDER BY\n      NumGE1500 DESC\n    LIMIT 1\n  )",
    "coreSQL": "ORDER BY satscores.NumGE1500 DESC LIMIT 1",
},
],
"tableSchema": {
"table_names": ["satscores", "schools"],
"columns": {
    "satscores": {
        "name": {"0": "cds", "2": "sname", "10": "NumGE1500"},
        "type": {"0": "TEXT", "2": "TEXT", "10": "INTEGER"},
        "notnull": {"0": 1, "2": 0, "10": 0},
        "dflt_value": {"0": "", "2": "", "10": ""},
        "pk": {"0": 1, "2": 0, "10": 0},
    },
    "schools": {
        "name": {
            "0": "CDSCode",
            "39": "AdmFName1",
            "40": "AdmLName1",
            "42": "AdmFName2",
            "43": "AdmLName2",
            "45": "AdmFName3",
            "46": "AdmLName3",
        },
        "type": {
            "0": "TEXT",
            "39": "TEXT",
            "40": "TEXT",
            "42": "TEXT",
            "43": "TEXT",
            "45": "TEXT",
            "46": "TEXT",
        },
        "notnull": {
            "0": 1,
            "39": 0,
            "40": 0,
            "42": 0,
            "43": 0,
            "45": 0,
            "46": 0,
        },
        "dflt_value": {
            "0": "",
            "39": "",
            "40": "",
            "42": "",
            "43": "",
            "45": "",
            "46": "",
        },
        "pk": {"0": 1, "39": 0, "40": 0, "42": 0, "43": 0, "45": 0, "46": 0},
    },
},
"fk_pairs": [
    [
        {"table": "satscores", "column": "cds"},
        {"table": "schools", "column": "CDSCode"},
    ]
],
},
"id": "49",
"isUser": False,
"isSQL": True,
"time": "2024-08-22 14:55:07",
"modifyCnt": 0,
"previousModify": -1,
"history": [],
"context": "",
}
pass
mcs = MCS()
mcs.pipeline()
modif = mcs.modify_pipeline(original_data, new_data, modify_res)
print(modif)
"""
