import json
import pandas as pd
import time
import openai
import sqlglot
import ast
import sqlite3
import copy
import json

from model.parser import SQLParser
from model.mcs import MCS

APIKEY = "sk-awHE6O3rfLOL2QLf43C6CaCc7eB04336933f0dCeC20aE118"
BASEURL = "https://ai-yyds.com/v1"
GPTSETTING = {
    "model": "gpt-4o-mini",
    "temperature": 0,
    "max_tokens": 4096,
}
MODEL_SET = "gpt-4o-mini"
MAX_TOKENS = 4096


class Communication:

    def __init__(
        self,
        communicationListPath="./data/communicationList.json",
        DBListPath="./data/DBList.json",
        communicationFoulderPath="./data/communication/",
        # SQLparserconfig
        SQL="SELECT   name FROM (SELECT * FROM new_table) WHERE   type = 'table'",
        dbName="california_schools",
        dbFolderPath="./data/dbCollection/",
    ):
        self.communicationFoulderPath = communicationFoulderPath
        self.communicationListPath = communicationListPath
        self.communicationListRaw = list(
            json.loads(open(communicationListPath, "r").read())
        )
        for i in self.communicationListRaw:
            i["id"] = str(i["id"])
        self.communicationID = self.communicationListRaw[0]["id"]
        self.communicationList = {i["id"]: i for i in self.communicationListRaw}
        self.DBList = [
            v["name"] for v in list(json.loads(open(DBListPath, "r").read()))
        ]
        self.communicationName = None
        self.communication = None
        print(self.communicationID)
        self.updCommuncation(self.communicationID)
        self.client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
        self.dbName = dbName
        self.SQLParser = SQLParser(SQL, dbName, dbFolderPath)
        self.MCSPipelin = MCS(dbName=self.dbName)
        self.dbSchema = self.MCSPipelin.getDBSchema()
        self.dbSchema = self.MCSPipelin.schemaTrans(self.dbSchema)

        self.isMCSpipeline = False
        self.test = False
        self.testData = json.loads(
            open("./data/communication/step1.json", "r", encoding="utf-8").read()
        )
        self.testData = self.testData["communication"]
    def getDBSchema(self):
        return self.dbSchema

    # V1
    def sendContext_V1(self, context):
        trigger_decision = self.trigger_V1(context)
        self.communication["communication"].append(
            {
                "id": str(int(len(self.communication["communication"]))),
                "isUser": True,
                "context": context,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "isSQL": False,
                "isRequireMOreInfo": False,
            }
        )
        if trigger_decision["isSQLGenProblem"]:
            result = self.step1_V1(context)
            result["modifyCnt"] = 0
            result["previousModify"] = -1
            result["history"] = [copy.deepcopy(result)]
            result["id"] = str(int(len(self.communication["communication"])))
            result["isUser"] = False
            result["isSQL"] = True
            result["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            result["context"] = ""
            result["isSQLTG"] = False
            self.communication["communication"].append(result)
        else:
            returnResponse = self.sendGPT(context)
            self.communication["communication"].append(
                {
                    "id": str(int(len(self.communication["communication"]))),
                    "isUser": False,
                    "context": returnResponse,
                    "isSQL": False,
                    "isRequireMOreInfo": False,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "isSQLTG": False,
                }
            )
        pass
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)

    def trigger_V1(self, context):

        prompt_user = ""
        prompt_user += self.dbSchemaPrompt()
        prompt_user += f"You have to detect whether '{context}' is a question required you to write a SQL query to do something like traverse or not."
        prompt_user += "You should strictly follow the format below."
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "isSQLGenProblem": xxx, \\\\True or False\n'
        prompt_user += '    "reason":xxx\n'
        prompt_user += "\}\n"
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=[{"role": "user", "content": prompt_user}],
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")

                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(str(result_ans))
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    break
                except:
                    i += 1
                    print(e)
                    result_ans = {"isSQLProblem": False}
        print(result_ans)
        return result_ans

    def dbSchemaPrompt(self, dbName=None, dbSchema=None):
        if not dbName:
            dbName = self.dbName
        if not dbSchema:
            dbSchema = self.dbSchema
        prompt = f"The database schema of {dbName} is as follows:\n"
        for i in dbSchema["columns"]:
            prompt += f"    Table {i}: ("
            for j in dbSchema["columns"][i]["name"]:
                prompt += f"'{dbSchema['columns'][i]['name'][j]}', "
            prompt = prompt[:-2] + ")\n"
        prompt += "The foreign key pairs are:\n"
        for i in dbSchema["fk_pairs"]:
            for j in i:
                prompt += f"{j['table']}.'{j['column']}' = "
            prompt = prompt[:-2] + "\n"
        print(dbName)
        print(dbSchema)
        return prompt

    def reStep1_V1(self, configuration):
        self.MCSPipelin = MCS(
            dbName=self.dbName,
            question=configuration["question"],
            evidence=configuration["evidence"],
        )

        self.MCSPipelin.SchemaPreprocess(configuration["dbSchema"])
        schema_filter = self.MCSPipelin.schemaFilter()
        schema_filter = self.MCSPipelin.schemaTrans(schema_filter)
        promptOfDBSchema = self.dbSchemaPrompt(dbSchema=schema_filter)
        prompt_system = "You are an expert on SQL"
        prompt_user = f'You have to consider the following question: {configuration["question"]}\n'
        prompt_user += f'Also, you have evidence: {configuration["evidence"]}\n'
        if "token" in configuration:
            for i in configuration["token"]:
                columnString = ", ".join([f"{j[0]}.{j[1]}" for j in i["columns"]])
                prompt_user += f'    {i["word"]} corresponding to {columnString}\n'
        prompt_user += f"With provided dbinfor, you should splite the question into several parts at noun phrase level and match parts with the provided DB columns.\n"
        prompt_user += (
            f"Be careful, an word may match multiple columns, you should provide all.\n"
        )
        prompt_user += 'For those columns including " ", you should use " " to contain the whole column name.\n'
        prompt_user += "You should strictly follow the format below."
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "question": xxx, \\\\question You understand\n'
        prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think, should be in format of String\n'
        prompt_user += '    "token": [\n'
        prompt_user += "        \{\n"
        prompt_user += '            "word": "xxx", \\\\The part you split\n'
        prompt_user += '            "columns": [\n'
        prompt_user += '                ["table1","word1"],["table2","word2"]...]\n'
        prompt_user += "        \},\n"
        prompt_user += "    ]\n"
        prompt_user += "\}\n"
        prompt = [
            {"role": "system", "content": prompt_system},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "user", "content": prompt_user},
        ]
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")

                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(result_ans)
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans["token"] = []

        configuration["dbSchema"] = schema_filter
        configuration["token"] = result_ans["token"]
        configuration["context"] = ""
        configuration["isReady"] = True
        configuration["needInfo"] = ""
        configuration["question"] = result_ans["question"]
        configuration["evidence"] = result_ans["evidence"]
        if self.test:
            configuration = self.testData[1]
        self.communication["communication"][int(configuration["id"])] = configuration
        pass
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)
        return configuration

    def reStep1_V2(self, configuration):
        self.MCSPipelin = MCS(
            dbName=self.dbName,
            question=configuration["question"],
            evidence=configuration["evidence"],
        )

        self.MCSPipelin.SchemaPreprocess(configuration["dbSchema"])
        promptOfDBSchema = self.dbSchemaPrompt(
            dbSchema=self.MCSPipelin.schemaTrans(self.MCSPipelin.schema_table)
        )
        prompt_system = "You are an expert on SQL"

        promptOfDBSchema = self.dbSchemaPrompt()
        prompt_user = f'You have to consider the following question: {configuration["question"]}\n'
        prompt_user += f'Also, you have evidence: {configuration["evidence"]}\n'
        if "token" in configuration:
            for i in configuration["token"]:
                columnString = ", ".join([f"{j[0]}.{j[1]}" for j in i["columns"]])
                prompt_user += f'    {i["word"]} corresponding to {columnString}\n'
        prompt_user += f"You have to decide whether the provided DBinfo is enough to generate the SQL query."
        prompt_user += "If not, you should set 'isReady' as False, and provide the information you need to generate the SQL query."
        prompt_user += "If yes, you should divide the question into several parts at noun phrase level and match parts with the provided DB columns."
        prompt_user += (
            "Be careful, an word may match multiple columns, you should provide all."
        )
        prompt_user += "You should strictly follow the format below."
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "question": xxx, \\\\question You understand\n'
        prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think. Should be in String format\n'
        prompt_user += '    "isReady": xxx, \\\\True or False\n'
        prompt_user += '    "needInfo": xxx, \\\\The information you need\n'
        prompt_user += '    "token": [\n'
        prompt_user += "        \{\n"
        prompt_user += '            "word": "xxx", \\\\The part you split\n'
        prompt_user += '            "columns": [\n'
        prompt_user += '                ["table1","word1"],["table2","word2"]...]\n'
        prompt_user += "        \},\n"
        prompt_user += "    ]\n"
        prompt_user += "\}\n"

        prompt = [
            {"role": "system", "content": prompt_system},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "user", "content": prompt_user},
        ]
        i = 0
        result_ans = False
        while i < 3 and (not configuration["isReady"]):
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")

                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(result_ans)
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans = {
                        "isReady": False,
                        "needInfo": "",
                        "token": [],
                        "error": "Connecting Error",
                    }

        pass
        if result_ans:
            result_ans["dbSchema"] = self.MCSPipelin.schemaTrans(
                self.MCSPipelin.schema_table
            )
            result_ans_base = result_ans
            for k, v in configuration.items():
                if k not in result_ans:
                    result_ans_base[k] = v
        else:
            result_ans_base = configuration
        print(result_ans_base)
        if result_ans_base["isReady"]:
            self.MCSPipelin = MCS(
                dbName=self.dbName,
                question=configuration["question"],
                evidence=configuration["evidence"],
            )
            self.MCSPipelin.SchemaPreprocess(result_ans_base["dbSchema"])
            schema_filter = self.MCSPipelin.schemaFilter()
            schema_filter = self.MCSPipelin.schemaTrans(schema_filter)

            promptOfDBSchema = self.dbSchemaPrompt(dbSchema=schema_filter)
            prompt_system = "You are an expert on SQL"
            prompt_user = f'You have to consider the following question: {result_ans_base["question"]}\n'
            prompt_user += f'Also, you have evidence: {result_ans_base["evidence"]}\n'
            for i in configuration["token"]:
                columnString = ", ".join([f"{j[0]}.{j[1]}" for j in i["columns"]])
                prompt_user += f'    {i["word"]} corresponding to {columnString}\n'
            prompt_user += f"With provided dbinfor, you should splite the question into several parts at noun phrase level and match parts with the provided DB columns.\n"
            prompt_user += f"Be careful, an word may match multiple columns, you should provide all.\n"
            prompt_user += "You should strictly follow the format below."
            prompt_user += "```json\n"
            prompt_user += "\{\n"
            prompt_user += '    "question": xxx, \\\\question You understand\n'
            prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think. Should be in String format\n'
            prompt_user += '    "token": [\n'
            prompt_user += "        \{\n"
            prompt_user += '            "word": "xxx", \\\\The part you split\n'
            prompt_user += '            "columns": [\n'
            prompt_user += '                ["table1","word1"],["table2","word2"]...]\n'
            prompt_user += "        \},\n"
            prompt_user += "    ]\n"
            prompt_user += "\}\n"
            prompt = [
                {"role": "system", "content": prompt_system},
                {"role": "assistant", "content": promptOfDBSchema},
                {"role": "user", "content": prompt_user},
            ]
            i = 0
            while i < 3:
                try:
                    result = self.client.chat.completions.create(
                        model=MODEL_SET,
                        messages=prompt,
                        temperature=GPTSETTING["temperature"],
                        max_tokens=MAX_TOKENS,
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
                    result_ans = result_ans.replace(": ", ":")

                    if "}" not in result_ans:
                        result_ans += '"}'
                    result_ans = json.loads(result_ans)
                    break
                except Exception as e:
                    try:
                        result_ans = ast.literal_eval(result_ans)
                        break
                    except:
                        i += 1
                        print(result_ans)
                        print(e)
                        result_ans = {
                            "token": [],
                            "error": "Connecting Error",
                            "question": "",
                            "evidence": "",
                        }
            result_ans_base["dbSchema"] = schema_filter
            if result_ans["token"] != []:
                result_ans_base["token"] = result_ans["token"]
            if "error" in result_ans:
                result_ans_base["error"] = result_ans["error"]
            else:
                result_ans_base["question"] = result_ans["question"]
                result_ans_base["evidence"] = result_ans["evidence"]
            result_ans_base["context"] = ""
            result_ans_base["id"] = len(self.communication["communication"])
        if self.test:
            result_ans_base = self.testData[1]
        self.communication["communication"].append(result_ans_base)
        pass
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)

        return result_ans_base

    def step1_V1(self, context):
        prompt_system = "You are an expert on SQL"
        promptOfDBSchema = self.dbSchemaPrompt()
        print("step1")
        print(promptOfDBSchema)
        prompt_user = f"The user has a question: {context}\n"
        prompt_user += f"You have to decide whether the user-providing info is enough to generate the SQL query."
        prompt_user += "If not, you should set 'isReady' as False, and provide the information you need to generate the SQL query."
        prompt_user += "Even current dbinfo may not able solve this problem, as long as it is a sql-generate problem, you should set it as True"
        prompt_user += "If yes, you should divide the question into several parts at noun phrase level and match parts with the provided DB columns."
        prompt_user += (
            "Be careful, an word may match multiple columns, you should provide all."
        )

        prompt_user += 'You should strictly follow the format below(because I will use eval() in py to transfer your answer into dict, avioding using "*" in a String value).'
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "question": xxx, \\\\question You understand\n'
        prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think. Should be in String format\n'
        prompt_user += '    "isReady": xxx, \\\\True or False\n'
        prompt_user += '    "needInfo": xxx, \\\\The information you need\n'
        prompt_user += '    "token": [\n'
        prompt_user += "        \{\n"
        prompt_user += '            "word": "xxx", \\\\The part you split\n'
        prompt_user += '            "columns": [\n'
        prompt_user += '                ["table1","word1"],["table2","word2"]...]\n'
        prompt_user += "        \},\n"
        prompt_user += "    ]\n"
        prompt_user += "\}\n"

        prompt = [
            {"role": "system", "content": prompt_system},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "user", "content": prompt_user},
        ]
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")
                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(result_ans)
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans = {
                        "isReady": False,
                        "needInfo": "",
                        "token": [],
                        "error": "Connecting Error",
                    }
        result_ans["dbSchema"] = self.dbSchema
        pass
        result_ans_base = result_ans

        if result_ans["isReady"]:
            self.MCSPipelin = MCS(
                dbName=self.dbName,
                question=result_ans_base["question"],
                evidence=result_ans_base["evidence"],
            )
            schema_filter = self.MCSPipelin.schemaFilter()
            schema_filter = self.MCSPipelin.schemaTrans(schema_filter)
            promptOfDBSchema = self.dbSchemaPrompt(dbSchema=schema_filter)
            prompt_system = "You are an expert on SQL"
            prompt_user = f'You have to consider the following question: {result_ans_base["question"]}\n'
            prompt_user += f'Also, you have evidence: {result_ans_base["evidence"]}\n'
            prompt_user += f"With provided dbinfor, you should splite the question into several parts at noun phrase level and match parts with the provided DB columns.\n"
            prompt_user += f"Be careful, an word may match multiple columns, you should provide all.\n"
            prompt_user += 'For those columns including " ", you should use " " to contain the whole column name.\n'
            prompt_user += 'For those columns including " ", you should use " " to contain the whole column name.\n'
            prompt_user += "You should strictly follow the format below."
            prompt_user += "```json\n"
            prompt_user += "\{\n"
            prompt_user += '    "token": [\n'
            prompt_user += "        \{\n"
            prompt_user += '            "word": "xxx", \\\\The part you split\n'
            prompt_user += '            "columns": [\n'
            prompt_user += '                ["table1","word1"],["table2","word2"]...]\n'
            prompt_user += "        \},\n"
            prompt_user += "    ]\n"
            prompt_user += "\}\n"
            prompt = [
                {"role": "system", "content": prompt_system},
                {"role": "assistant", "content": promptOfDBSchema},
                {"role": "user", "content": prompt_user},
            ]
            i = 0
            while i < 3:
                try:
                    result = self.client.chat.completions.create(
                        model=MODEL_SET,
                        messages=prompt,
                        temperature=GPTSETTING["temperature"],
                        max_tokens=MAX_TOKENS,
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
                    result_ans = result_ans.replace(": ", ":")
                    #
                    if "}" not in result_ans:
                        result_ans += '"}'
                    result_ans = json.loads(result_ans)
                    break
                except Exception as e:
                    try:
                        result_ans = ast.literal_eval(result_ans)
                        break
                    except:
                        i += 1
                        print(result_ans)
                        print(e)
                        result_ans = {
                            "token": [],
                            "error": "Connecting Error",
                        }
            result_ans_base["dbSchema"] = schema_filter
            if result_ans["token"] != []:
                result_ans_base["token"] = result_ans["token"]
            if "error" in result_ans:
                result_ans_base["error"] = result_ans["error"]
            result_ans["context"] = ""
        print("step1_done")
        if self.test:
            result_ans_base = self.testData[1]
        return result_ans_base

    def step2_v1(self, configuration):
        prompt_system = "You are an expert on SQL"
        prompt_assistant = ""
        promptOfDBSchema = self.dbSchemaPrompt(dbSchema=configuration["dbSchema"])
        prompt_assistant += promptOfDBSchema
        prompt_user = (
            f'You have to solve the following question: {configuration["question"]}\n'
        )
        prompt_user += f'Also, you have evidence: {configuration["evidence"]}\n'
        for i in configuration["token"]:
            columnString = ", ".join([f"{j[0]}.{j[1]}" for j in i["columns"]])
            prompt_user += f'    {i["word"]} corresponding to {columnString}\n'
        prompt_user += f"You have to consider the question step by step and output your thought chain. Becareful, each step may not be directly related to the previous step, you should provide the context of each step."
        prompt_user += 'For those columns including " ", you should use " " to contain the whole column name.\n'
        prompt_user += (
            "You should strictly follow the format below witout non-fill-in space."
        )
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "question": xxx, \\\\question You understand\n'
        prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think. Should be in String format\n'
        prompt_user += '    "SQL": xxx, \\\\ You final SQL query\n'
        prompt_user += '    "COT": [\n'
        prompt_user += "        \{\n"
        prompt_user += (
            '            "stepID": an int number, \\\\The stepID which must be an int\n'
        )
        prompt_user += '            "subStep": xxx, \\\\The substep you are solving\n'
        prompt_user += (
            '            "stepDescription": xxx, \\\\The step you are doing\n'
        )
        prompt_user += '            "subSQL": xxx, \\\\The SQL you are writing\n'
        prompt_user += '            "prerequisiteQuestion": [...], \\\\ the prerequisite subStep to solve this substep\n'
        prompt_user += '            "coreSQL": xxx, \\\\The SQL matching in SQL you output as final solution. Becareful, you should perfectly match with each word\n'
        prompt_user += "        \},\n"
        prompt_user += "    ]\n"
        prompt_user += "\}\n"
        prompt = [
            {"role": "system", "content": prompt_system},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "user", "content": prompt_user},
        ]
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")

                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans = json.loads(result_ans)
                result_ans["SQL"] = result_ans["SQL"].replace("`", '"')
                result_ans["SQL"] = result_ans["SQL"].replace("'", '"')
                result_ans["SQL"] = sqlglot.parse_one(result_ans["SQL"]).sql(
                    pretty=False
                )
                result_ans["SQLFormatted"] = sqlglot.parse_one(result_ans["SQL"]).sql(
                    pretty=True
                )
                for i in range(len(result_ans["COT"])):
                    result_ans["COT"][i]["stepID"] = int(result_ans["COT"][i]["stepID"])
                    result_ans["COT"][i]["prerequisiteQuestion"] = [
                        int(j) for j in result_ans["COT"][i]["prerequisiteQuestion"]
                    ]
                    result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                        "subSQL"
                    ].replace("`", '"')
                    result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                        "subSQL"
                    ].replace("'", '"')
                    result_ans["COT"][i]["subSQL"] = sqlglot.parse_one(
                        result_ans["COT"][i]["subSQL"]
                    ).sql(pretty=False)
                    result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                        "coreSQL"
                    ].replace("`", '"')
                    result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                        "coreSQL"
                    ].replace("'", '"')
                    if result_ans["COT"][i]["coreSQL"] != "":
                        result_ans["COT"][i]["coreSQL"] = sqlglot.parse_one(
                            result_ans["COT"][i]["coreSQL"]
                        ).sql(pretty=False)
                    else:
                        result_ans["COT"][i]["coreSQL"] = result_ans["SQL"]
                    result_ans["COT"][i]["subSQLFormatted"] = sqlglot.parse_one(
                        result_ans["COT"][i]["subSQL"]
                    ).sql(pretty=True)

                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    result_ans["SQL"] = result_ans["SQL"].replace("`", '"')
                    result_ans["SQL"] = result_ans["SQL"].replace("'", '"')
                    result_ans["SQL"] = sqlglot.parse_one(result_ans["SQL"]).sql(
                        pretty=False
                    )
                    result_ans["SQLFormatted"] = sqlglot.parse_one(
                        result_ans["SQL"]
                    ).sql(pretty=True)
                    for i in range(len(result_ans["COT"])):
                        result_ans["COT"][i]["stepID"] = int(
                            result_ans["COT"][i]["stepID"]
                        )
                        result_ans["COT"][i]["prerequisiteQuestion"] = [
                            int(j) for j in result_ans["COT"][i]["prerequisiteQuestion"]
                        ]
                        result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                            "subSQL"
                        ].replace("`", '"')
                        result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                            "subSQL"
                        ].replace("'", '"')
                        result_ans["COT"][i]["subSQL"] = sqlglot.parse_one(
                            result_ans["COT"][i]["subSQL"]
                        ).sql(pretty=False)
                        result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                            "coreSQL"
                        ].replace("`", '"')
                        result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                            "coreSQL"
                        ].replace("'", '"')
                        if result_ans["COT"][i]["coreSQL"] != "":
                            result_ans["COT"][i]["coreSQL"] = sqlglot.parse_one(
                                result_ans["COT"][i]["coreSQL"]
                            ).sql(pretty=False)
                        else:
                            result_ans["COT"][i]["coreSQL"] = result_ans["SQL"]
                        result_ans["COT"][i]["subSQLFormatted"] = sqlglot.parse_one(
                            result_ans["COT"][i]["subSQL"]
                        ).sql(pretty=True)
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans = {
                        "token": [],
                        "error": "Connecting Error",
                    }
        result_ans["isSQLTG"] = True
        result_ans["isSQL"] = True
        result_ans["context"] = ""
        result_ans["id"] = int(len(self.communication["communication"]))
        result_ans["time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        result_ans["isUser"] = False
        result_ans["dbSchema"] = configuration["dbSchema"]
        if self.test:
            result_ans = self.testData[2]
        self.communication["communication"].append(result_ans)
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)
        return result_ans
        pass

    def compare_result_V1(self, new_data, original_data):

        if self.formatSQLWithoutPretty(new_data["SQL"]) != self.formatSQLWithoutPretty(
            original_data["SQL"]
        ):
            # nothing
            pass
        sub_differ = []

        for i in range(len(new_data["COT"])):
            error_index = i
            error_type = []
            if self.formatSQLWithoutPretty(
                new_data["COT"][i]["subSQLFormatted"]
            ) != self.formatSQLWithoutPretty(
                original_data["COT"][i]["subSQLFormatted"]
            ):
                error_type.append("subSQL")
            if new_data["COT"][i]["subStep"] != original_data["COT"][i]["subStep"]:
                error_type.append("subStep")
            if (
                new_data["COT"][i]["stepDescription"]
                != original_data["COT"][i]["stepDescription"]
            ):
                error_type.append("stepDescription")
            sub_differ.append(
                {
                    "error_index": error_index,
                    "error_type": error_type,
                }
            )
        return sub_differ

    def data2Context_V1(self, data):
        prompt = ""
        prompt += f'You have to solve the following question: {data["question"]}\n'
        prompt += f'Also, you have evidence: {data["evidence"]}\n'
        prompt += (
            f'You final SQL is {self.formatSQLWithoutPretty(data["SQLFormatted"])}\n'
        )
        prompt += f"The following is your thought chain:\n"
        for i in data["COT"]:
            prompt += f'    Step {i["stepID"]}: {i["subStep"]}\n'
            prompt += f'        Description: {i["stepDescription"]}\n'
            prompt += f'        SQL: {self.formatSQLWithoutPretty(i["subSQL"])}\n'
            prompt += f'        SQL matched the final solution: {self.formatSQLWithoutPretty(i["coreSQL"])}\n'
            prompt += f'        Prerequisite: {i["prerequisiteQuestion"]}\n'
        return prompt

    def compare2Context_V1(self, compareResult, new_data):
        prompt = ""
        prompt += f'You final SQL is {self.formatSQLWithoutPretty(new_data["SQLFormatted"])}\n'
        for i in compareResult:
            if len(i["error_type"]) == 0:
                continue
            prompt += f'    Step {i["error_index"]} is modified by user \n'
            for j in i["error_type"]:
                modify_part = new_data["COT"][i["error_index"]][j]
                prompt += f"        {j} is modified as {modify_part}\n"
        return prompt

    def modifySQL_V1(self, new_data, original_data, test=False):
        # original_data should be a node of communication
        # new_data could be simplify as (question, dbName,dbPath,evidence, SQL, COT)
        try:
            index = int(original_data["id"])
        except:
            index = 0
        if int(self.communication["communication"][index]["id"]) != int(
            original_data["id"]
        ):
            for i in range(len(self.communication["communication"])):
                if int(self.communication["communication"][i]["id"]) == int(
                    original_data["id"]
                ):
                    index = i
                    break
        result_ans = []
        issubDiff = 0
        subDiff = self.compare_result_V1(new_data, original_data)
        for i in subDiff:
            if len(i["error_type"]) != 0:
                issubDiff = 1
                break

            pass
        if (
            self.formatSQLWithoutPretty(new_data["SQLFormatted"])
            != self.formatSQLWithoutPretty(original_data["SQLFormatted"])
            and False
        ):
            # nothing
            pass
        elif issubDiff or True:
            prompt_system = "You are an expert on SQL"
            prompt_assistant = ["", ""]
            prompt_assistant[0] = ""
            promptOfDBSchema = self.dbSchemaPrompt(dbSchema=original_data["dbSchema"])
            prompt_assistant[0] += promptOfDBSchema
            prompt_assistant[1] += self.data2Context_V1(original_data)
            prompt_assistant[1] += self.compare2Context_V1(subDiff, new_data)
            prompt_user = ""
            prompt_user += f"You have to reconsider the question step by step and output your thought chain. Becareful, you should modify the wrong and following steps, especially for those have been modified by user. Also, before the first modify subquestions, the previous subquestions should be kept and it is the same to their orders unless wrong.\n"
            prompt_user += 'For those columns including " ", you should use " " to contain the whole column name.\n'
            prompt_user += "You should strictly follow the format below."
            prompt_user += "```json\n"
            prompt_user += "\{\n"
            prompt_user += '    "question": xxx, \\\\question You understand\n'
            prompt_user += '    "evidence": xxx, \\\\useful info to solve problems You think. Should be in String format\n'
            prompt_user += '    "SQL": xxx, \\\\ You final SQL query\n'
            prompt_user += '    "COT": [\n'
            prompt_user += "        \{\n"
            prompt_user += '            "stepID": an int number, \\\\The stepID which must be an int\n'
            prompt_user += (
                '            "subStep": xxx, \\\\The substep you are solving\n'
            )
            prompt_user += (
                '            "stepDescription": xxx, \\\\The step you are doing\n'
            )
            prompt_user += '            "subSQL": xxx, \\\\The SQL you are writing\n'
            prompt_user += '            "prerequisiteQuestion": [...], \\\\ the prerequisite subStep to solve this substep\n'
            prompt_user += '            "coreSQL": xxx, \\\\The SQL matching in SQL you output as final solution. Becareful, you should perfectly match with each word\n'
            prompt_user += "        \},\n"
            prompt_user += "    ]\n"
            prompt_user += "\}\n"
            prompt = [
                {"role": "system", "content": prompt_system},
                {"role": "assistant", "content": prompt_assistant[0]},
                {"role": "assistant", "content": prompt_assistant[1]},
                {"role": "user", "content": prompt_user},
            ]
            i = 0

            while i < 3:
                try:
                    result = self.client.chat.completions.create(
                        model=MODEL_SET,
                        messages=prompt,
                        temperature=GPTSETTING["temperature"],
                        max_tokens=MAX_TOKENS,
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
                    result_ans = result_ans.replace(": ", ":")
                    if "}" not in result_ans:
                        result_ans += '"}'
                    result_ans = json.loads(result_ans)

                    break
                except Exception as e:
                    try:
                        result_ans = ast.literal_eval(result_ans)
                        break
                    except:
                        i += 1
                        print(e)
                        result_ans = {
                            "token": [],
                            "error": "Connecting Error",
                        }
            if "error" not in result_ans:
                result_ans["SQL"] = result_ans["SQL"].replace("`", '"')
                result_ans["SQL"] = result_ans["SQL"].replace("'", '"')
                result_ans["SQL"] = sqlglot.parse_one(result_ans["SQL"]).sql(
                    pretty=False
                )
                result_ans["SQLFormatted"] = sqlglot.parse_one(result_ans["SQL"]).sql(
                    pretty=True
                )
                for i in range(len(result_ans["COT"])):
                    result_ans["COT"][i]["stepID"] = int(result_ans["COT"][i]["stepID"])
                    result_ans["COT"][i]["prerequisiteQuestion"] = [
                        int(j) for j in result_ans["COT"][i]["prerequisiteQuestion"]
                    ]
                    result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                        "subSQL"
                    ].replace("`", '"')
                    result_ans["COT"][i]["subSQL"] = result_ans["COT"][i][
                        "subSQL"
                    ].replace("'", '"')
                    result_ans["COT"][i]["subSQL"] = sqlglot.parse_one(
                        result_ans["COT"][i]["subSQL"]
                    ).sql(pretty=False)
                    result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                        "coreSQL"
                    ].replace("`", '"')
                    result_ans["COT"][i]["coreSQL"] = result_ans["COT"][i][
                        "coreSQL"
                    ].replace("'", '"')
                    if result_ans["COT"][i]["coreSQL"] != "":
                        result_ans["COT"][i]["coreSQL"] = sqlglot.parse_one(
                            result_ans["COT"][i]["coreSQL"]
                        ).sql(pretty=False)
                    else:
                        result_ans["COT"][i]["coreSQL"] = result_ans["SQL"]

                    result_ans["COT"][i]["subSQLFormatted"] = sqlglot.parse_one(
                        result_ans["COT"][i]["subSQL"]
                    ).sql(pretty=True)
                    result_ans["COT"][i]["stepDescription"] += "Modified!"

        """
        history_new = {
            "question": result_ans["question"],
            "evidence": result_ans["evidence"],
            "dbName": result_ans["dbName"],
            "dbPath": result_ans["dbPath"],
            "SQL": result_ans["SQL"],
            "COT": copy.deepcopy(result_ans["COT"]),
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "tableSchema": result_ans["tableSchema"],
            "previousModify": original_data["previousModify"],
            "modifyCnt": len(original_data["history"]),
        }
        """
        """
        context = f'question: {result_ans["question"]}\nSQL: {result_ans["SQL"]}\n'
        context += "COT steps"
        context += "```json\n"
        context += f"[\n"
        for i in result_ans["COT"]:
            context += "\{\n"
            context += f'    "subQuestion": {i["subQuestion"]},\n'
            context += f'    "stepDescription": {i["stepDescription"]},\n'
            context += f'    "subSQL": {i["subSQL"]},\n'
            context += f'    "coreSQL": {i["coreSQL"]}\n'
            context += "\},\n"
        context += "]\n"
        context += "```"
        """
        # original_data["history"].append(history_new)

        original_data["question"] = result_ans["question"]
        original_data["evidence"] = result_ans["evidence"]
        # original_data["dbName"] = result_ans["dbName"]
        # original_data["dbPath"] = result_ans["dbPath"]
        original_data["SQL"] = result_ans["SQL"]
        original_data["SQLFormatted"] = sqlglot.parse_one(result_ans["SQL"]).sql(
            pretty=True
        )
        original_data["COT"] = copy.deepcopy(result_ans["COT"])
        # original_data["time"] = result_ans["time"]
        # original_data["previousModify"] = result_ans["previousModify"]
        # original_data["modifyCnt"] = result_ans["modifyCnt"]
        if self.test:
            original_data = self.testData[2]
        self.communication["communication"][index] = copy.deepcopy(original_data)
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)
            pass
        print("modify")
        return original_data

    ##################################################################
    ##################################################################
    ##################################################################

    def getCommunicationList(self):
        print(self.communicationList)
        return [v for k, v in self.communicationList.items()]

    def getDBList(self):
        return self.DBList

    def getCommunication(self):
        return self.communication

    def getOriginalSchemaCollection(self):
        return self.SQLParser.getOriginalSchemaCollection()

    def updCommuncation(self, id=None):
        if id is not None:
            self.communicationID = id
        self.communicationName = self.communicationList[self.communicationID]["name"]
        self.communication = json.loads(
            open(
                f"{self.communicationFoulderPath}{self.communicationName}.json",
                "r",
                encoding="utf-8",
            ).read()
        )

    def sendContext(self, context, test=False):
        flag = 1
        index = -1
        context_list = []
        context_list.append(context)

        """     
        while flag:
            if len(self.communication["communication"]) < -1 * index:
                break
            if self.communication["communication"][index]["isRequireMOreInfo"]:
                if index != -1:
                    context_list.append(
                        self.communication["communication"][index + 1]["context"]
                    )
                context_list.append(
                    self.communication["communication"][index]["context"]
                )
                index -= 2
            else:
                break
        context_list = context_list[::-1] 
        """
        trigger = self.triggerMCS(context_list)
        self.communication["communication"].append(
            {
                "id": str(int(len(self.communication["communication"]))),
                "isUser": True,
                "context": context,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "isSQL": False,
                "isRequireMOreInfo": False,
            }
        )
        if trigger["isSQLProblem"] and not trigger["isRequireMOreInfo"]:
            self.MCSPipelin = MCS(
                question=trigger["question"], evidence=trigger["evidence"]
            )
            self.isMCSpipeline = True
            MCSPipelineResponse = self.MCSPipelin.pipeline()
            MCSPipelineResponse["id"] = str(
                int(len(self.communication["communication"]))
            )
            MCSPipelineResponse["isUser"] = False
            MCSPipelineResponse["isSQL"] = True
            MCSPipelineResponse["time"] = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime()
            )
            MCSPipelineResponse["modifyCnt"] = 0
            MCSPipelineResponse["previousModify"] = -1
            MCSPipelineResponse["context"] = ""
            MCSPipelineResponse["isRequireMOreInfo"] = False
            context = f'question: {MCSPipelineResponse["question"]}\nSQL: {MCSPipelineResponse["SQL"]}\n'
            context += "COT steps"
            context += "```json\n"
            context += f"[\n"
            for i in MCSPipelineResponse["COT"]:
                context += "\{\n"
                context += f'    "subQuestion": {i["subQuestion"]},\n'
                context += f'    "stepDescription": {i["stepDescription"]},\n'
                context += f'    "subSQL": {i["subSQL"]},\n'
                context += f'    "coreSQL": {i["coreSQL"]}\n'
                context += "\},\n"
            context += "]\n"
            context += "```"
            MCSPipelineResponse["context"] = context
            MCSPipelineResponse["modifyCnt"] = 0
            MCSPipelineResponse["previousModify"] = -1
            history_1 = {
                "question": MCSPipelineResponse["question"],
                "evidence": MCSPipelineResponse["evidence"],
                "dbName": MCSPipelineResponse["dbName"],
                "dbPath": MCSPipelineResponse["dbPath"],
                "SQL": MCSPipelineResponse["SQL"],
                "COT": copy.deepcopy(MCSPipelineResponse["COT"]),
                "time": MCSPipelineResponse["time"],
                "tableSchema": MCSPipelineResponse["tableSchema"],
                "modifyCnt": 0,
                "previousModify": -1,
            }
            MCSPipelineResponse["history"] = [history_1]
            self.communication["communication"].append(MCSPipelineResponse)
        elif trigger["isSQLProblem"] and trigger["isRequireMOreInfo"]:
            self.communication["communication"].append(
                {
                    "id": str(int(len(self.communication["communication"]))),
                    "isUser": False,
                    "context": trigger["questionToUser"],
                    "isSQL": False,
                    "isRequireMOreInfo": True,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                }
            )
        else:
            returnResponse = self.sendGPT(context)
            self.communication["communication"].append(
                {
                    "id": str(int(len(self.communication["communication"]))),
                    "isUser": False,
                    "context": returnResponse,
                    "isSQL": False,
                    "isRequireMOreInfo": False,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                }
            )
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)

    def sendGPT(self, context):
        prompt = []
        for i in self.communication["communication"]:
            if i["isSQL"]:
                content = ""
                """
                content = f'question: {i["question"]}\nSQL: {i["SQL"]}\n'
                content += "COT steps"
                content += "```json\n"
                content += f"[\n"
                for j in i["COT"]:
                    content += "\{\n"
                    content += f'    "subQuestion": {j["subQuestion"]},\n'
                    content += f'    "stepDescription": {j["stepDescription"]},\n'
                    content += f'    "subSQL": {j["subSQL"]},\n'
                    content += f'    "coreSQL": {j["coreSQL"]}\n'
                    content += "\},\n"
                content += "]\n"
                content += "```"
                """
                prompt.append({"role": "user", "content": content})
            else:
                prompt.append(
                    {
                        "role": "user" if i["isUser"] else "assistant",
                        "content": i["context"],
                    }
                )
        prompt = [
            {"role": "user" if i["isUser"] else "assistant", "content": i["context"]}
            for i in self.communication["communication"]
        ]
        prompt.append({"role": "user", "content": context})
        response = self.client.chat.completions.create(
            model=GPTSETTING["model"],
            messages=prompt,
            temperature=GPTSETTING["temperature"],
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content

    def addNewChat(self, name=f'{time.strftime("%Y-%m-%d", time.localtime())}'):
        id = str(len(self.communicationListRaw))
        self.communicationListRaw = [
            {
                "id": id,
                "name": name,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            }
        ] + self.communicationListRaw
        self.communicationList = {i["id"]: i for i in self.communicationListRaw}
        communication = {"id": id, "name": name, "communication": []}
        with open(
            f"{self.communicationFoulderPath}{name}.json",
            "w",
        ) as f:
            json.dump(communication, f)
        with open(
            self.communicationListPath,
            "w",
        ) as f:
            json.dump(self.communicationListRaw, f)
        self.updCommuncation(id)

    def getSQLCode(self):
        return self.SQLParser.getFormatSQL()

    def getSQLCodeTree(self):
        return self.SQLParser.getSQLCodeTree()

    def updateSQLCode(self, SQL):
        self.SQLParser.updateSQLCode(SQL)
        return self.SQLParser.getFormatSQL()

    def updateDB(self, selectedDB):
        self.dbName = selectedDB

        self.MCSPipelin = MCS(dbName=self.dbName)
        print(self.dbName)
        self.dbSchema = self.MCSPipelin.getDBSchema()
        self.dbSchema = self.MCSPipelin.schemaTrans(self.dbSchema)
        print(self.dbSchema)
        return self.SQLParser.updateDB(selectedDB)
    def triggerMCS(self, context):
        if type(context) == list:
            context_mod = ""
            for i in context:
                context_mod += i
        else:
            context_mod = context
        prompt_user = context_mod
        prompt_user += "\n"
        prompt_user += f"You have to detect whether it is a question required you to write a SQL query to do something like traverse or  not. Remember it is require you to write not explain or some other actions. An example is to list something and counterexample is to explain select in SQL. If it is, you have to set isSQLProblem as True and extract corresponding information in context and arrange in the following format within an explicitly json code block. If context does not contain required info, mark the correspoding place as None. And you may also ask user to obtain required information. If not, set isSQLProblem as False (Remember, evidence is something helpful to solve problems)(User has chosen {self.dbName} as dataBase):\n"
        prompt_user += "```json \{'isSQLProblem':xxx, \\\\True or False \n "
        prompt_user += "isRequireMOreInfo:xxx, \\\\True or False \n "
        prompt_user += "questionToUser:xxx, \\\\ return '' if no question  \n "
        prompt_user += "'question':xxx, \n  'dbName':xxx,\n 'evidence':xxx \\\\ return '' if no evidence\} ```"
        prompt_user += ""
        prompt = [{"role": "user", "content": prompt_user}]
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = json.loads(str(result_ans))
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans = {"isSQLProblem": False}
        print(result_ans)
        return result_ans

    def compare_result(self, new_data, original_data):
        if (
            new_data["question"] != original_data["question"]
            or new_data["dbName"] != original_data["dbName"]
            or new_data["evidence"] != original_data["evidence"]
        ):
            # rerun MCS
            pass
        if self.formatSQLWithoutPretty(new_data["SQL"]) != self.formatSQLWithoutPretty(
            original_data["SQL"]
        ):
            # nothing
            pass
        sub_differ = []

        for i in range(len(new_data["COT"])):
            error_index = i
            error_type = []
            if self.formatSQLWithoutPretty(
                new_data["COT"][i]["subSQL"]
            ) != self.formatSQLWithoutPretty(original_data["COT"][i]["subSQL"]):
                error_type.append("subSQL")
            if (
                new_data["COT"][i]["subQuestion"]
                != original_data["COT"][i]["subQuestion"]
            ):
                error_type.append("subQuestion")
            if (
                new_data["COT"][i]["stepDescription"]
                != original_data["COT"][i]["stepDescription"]
            ):
                error_type.append("stepDescription")
            sub_differ.append(
                {
                    "error_index": error_index,
                    "error_type": error_type,
                }
            )
        return sub_differ

    def formatSQLWithoutPretty(self, sql):
        try:
            sql = sql.replace("`", '"')
            sql = sql.replace("'", '"')
            parse = sqlglot.parse_one(sql)
            return parse.sql(pretty=False)
        except:
            return sql

    def formatSQLWithPretty(self, sql):
        try:
            sql = sql.replace("`", '"')
            sql = sql.replace("'", '"')
            parse = sqlglot.parse_one(sql)
            return parse.sql(pretty=True)
        except:
            return sql

    def executeSQL(self, sql):
        try:

            sql = self.formatSQLWithoutPretty(sql)
            sql = sql.replace("'", '"')
            dbPath = self.SQLParser.dbPath
            conn = sqlite3.connect(dbPath)
            cursor = conn.cursor()
            cursor.execute(sql)
            column_names = [description[0] for description in cursor.description]
            table = cursor.fetchall()
            return {"column_names": column_names, "table": table}
        except Exception as e:
            return {"error": str(e)}

    def compare_result(self, new_data, original_data):
        if (
            new_data["question"] != original_data["question"]
            or new_data["dbName"] != original_data["dbName"]
            or new_data["evidence"] != original_data["evidence"]
        ):
            # rerun MCS
            pass
        if self.formatSQLWithoutPretty(new_data["SQL"]) != self.formatSQLWithoutPretty(
            original_data["SQL"]
        ):
            # nothing
            pass
        sub_differ = []

        for i in range(len(new_data["COT"])):
            error_index = i
            error_type = []
            if self.formatSQLWithoutPretty(
                new_data["COT"][i]["subSQL"]
            ) != self.formatSQLWithoutPretty(original_data["COT"][i]["subSQL"]):
                error_type.append("subSQL")
            if (
                new_data["COT"][i]["subQuestion"]
                != original_data["COT"][i]["subQuestion"]
            ):
                error_type.append("subQuestion")
            if (
                new_data["COT"][i]["stepDescription"]
                != original_data["COT"][i]["stepDescription"]
            ):
                error_type.append("stepDescription")
            sub_differ.append(
                {
                    "error_index": error_index,
                    "error_type": error_type,
                }
            )
        return sub_differ

    def modifySQL(self, new_data, original_data, test=False):
        # original_data should be a node of communication
        # new_data could be simplify as (question, dbName,dbPath,evidence, SQL, COT)
        try:
            index = int(original_data["id"])
        except:
            index = 0
        if int(self.communication["communication"][index]["id"]) != int(
            original_data["id"]
        ):
            for i in range(len(self.communication["communication"])):
                if int(self.communication["communication"][i]["id"]) == int(
                    original_data["id"]
                ):
                    index = i
                    break
        if test:
            self.MCSPipelin = MCS(
                dbName=self.dbName,
                question=original_data["question"],
                evidence=original_data["evidence"],
            )
            self.MCSPipelin.pipeline()
        issubDiff = 0
        subDiff = self.compare_result(new_data, original_data)
        for i in subDiff:
            if len(i["error_type"]) != 0:
                issubDiff = 1
                break
        if (
            new_data["question"] != original_data["question"]
            or new_data["dbName"] != original_data["dbName"]
            or new_data["evidence"] != original_data["evidence"]
        ):
            self.MCSPipelin = MCS(
                dbName=self.dbName,
                question=new_data["question"],
                evidence=new_data["evidence"],
            )
            MCSPipelineResponse = self.MCSPipelin.pipeline()

            pass
        elif (
            self.formatSQLWithoutPretty(new_data["SQL"])
            != self.formatSQLWithoutPretty(original_data["SQL"])
            and False
        ):
            # nothing
            pass
        elif issubDiff or True:
            if not self.isMCSpipeline:
                self.MCSPipelin = MCS(
                    dbName=self.dbName,
                    question=original_data["question"],
                    evidence=original_data["evidence"],
                )
                self.isMCSpipeline = True
                self.MCSPipelin.schemaFilter()
            MCSPipelineResponse = self.MCSPipelin.modify_pipeline_subquestion(
                original_data, new_data, subDiff
            )
        history_new = {
            "question": MCSPipelineResponse["question"],
            "evidence": MCSPipelineResponse["evidence"],
            "dbName": MCSPipelineResponse["dbName"],
            "dbPath": MCSPipelineResponse["dbPath"],
            "SQL": MCSPipelineResponse["SQL"],
            "COT": copy.deepcopy(MCSPipelineResponse["COT"]),
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "tableSchema": MCSPipelineResponse["tableSchema"],
            "previousModify": original_data["previousModify"],
            "modifyCnt": len(original_data["history"]),
        }
        context = f'question: {MCSPipelineResponse["question"]}\nSQL: {MCSPipelineResponse["SQL"]}\n'
        context += "COT steps"
        context += "```json\n"
        context += f"[\n"
        for i in MCSPipelineResponse["COT"]:
            context += "\{\n"
            context += f'    "subQuestion": {i["subQuestion"]},\n'
            context += f'    "stepDescription": {i["stepDescription"]},\n'
            context += f'    "subSQL": {i["subSQL"]},\n'
            context += f'    "coreSQL": {i["coreSQL"]}\n'
            context += "\},\n"
        context += "]\n"
        context += "```"
        original_data["history"].append(history_new)

        original_data["question"] = history_new["question"]
        original_data["evidence"] = history_new["evidence"]
        original_data["dbName"] = history_new["dbName"]
        original_data["dbPath"] = history_new["dbPath"]
        original_data["SQL"] = history_new["SQL"]
        original_data["COT"] = copy.deepcopy(history_new["COT"])
        original_data["time"] = history_new["time"]
        original_data["previousModify"] = history_new["previousModify"]
        original_data["modifyCnt"] = history_new["modifyCnt"]
        self.communication["communication"][index] = copy.deepcopy(original_data)
        with open(
            f"{self.communicationFoulderPath}{self.communicationName}.json",
            "w",
        ) as f:
            json.dump(self.communication, f)
            pass
        return original_data

    def gptFix(self, sql, data, isSubStep=False, subStepId=-1):
        execute_result = self.executeSQL(sql)
        try:
            sql = self.formatSQLWithoutPretty(sql)
        except:
            pass
        if "error" not in execute_result:
            return {
                "sql": self.formatSQLWithoutPretty(sql),
                "SQLFormatted": self.formatSQLWithPretty(sql),
                "info": "No grammar error",
            }
        promptOfDBSchema = self.dbSchemaPrompt(dbSchema=data["dbSchema"])
        prompt_system = "You are an expert on SQL"
        if isSubStep:
            subStepIndex = int(subStepId) - 1
            step = data["COT"][subStepIndex]["subStep"]
            stepDescription = data["COT"][subStepIndex]["stepDescription"]
        else:
            step = data["question"]
            stepDescription = data["evidence"]

        pass
        prompt_user = f"You have to fix the wrong SQL problem"
        prompt_user += f"SQL: {sql}\n"
        prompt_user += f'Error info from exeute result:{execute_result["error"]}\n'
        prompt_user += f"Object: {step}\n"
        prompt_user += f"Description: {stepDescription}\n"
        prompt_user += promptOfDBSchema
        prompt_user += f"You should strictly follow the format below.\n"
        prompt_user += "```json\n"
        prompt_user += "\{\n"
        prompt_user += '    "SQL": xxx, \n'
        prompt_user += (
            '    "reasoning": xxx(the error you find, how you modify and why)\n'
        )
        prompt_user += "\}\n"
        prompt_user += "```"
        prompt = [
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt_user},
        ]
        i = 0
        result_ans = {"Error": "Connecting Error"}
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
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
                result_ans = result_ans.replace(": ", ":")
                if "}" not in result_ans:
                    result_ans += '"}'
                result_ans["SQL"] = self.formatSQLWithoutPretty(result_ans["SQL"])
                result_ans["SQLFormatted"] = self.formatSQLWithPretty(result_ans["SQL"])
                result_ans = json.loads(str(result_ans))
                break
            except Exception as e:
                try:
                    result_ans = ast.literal_eval(result_ans)
                    result_ans["SQL"] = self.formatSQLWithoutPretty(result_ans["SQL"])
                    result_ans["SQLFormatted"] = self.formatSQLWithPretty(
                        result_ans["SQL"]
                    )
                    break
                except:
                    i += 1
                    print(result_ans)
                    print(e)
                    result_ans = {"Error": "Connecting Error"}
        return result_ans

    def explain(self, content, data, isUserActive=False, isSub=False, subStepID=-1):
        promptSystem = "You are an expert on SQL"
        promptOfDBSchema = self.dbSchemaPrompt(dbSchema=data["dbSchema"])
        promptContext = self.data2Context_V1(data)
        promptUser = ""
        if isUserActive:
            if isSub:
                promptUser += f"{content}"
            else:
                promptUser += f"{content}"

        else:
            if isSub:
                promptUser += f"You have to explain the selected content '{content}' in substep {subStepID}\n"
            else:
                promptUser += f"You have to explain the selected content '{content}'\n"
        prompt = [
            {"role": "system", "content": promptSystem},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "assistant", "content": promptContext},
            {"role": "user", "content": promptUser},
        ]
        result_ans = ""
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
                )
                result_ans = result.choices[0].message.content
                break
            except Exception as e:
                i += 1
                print(e)
                result_ans = "Connecting Error"
        print(result_ans)
        return result_ans

    def explainCombine(self, selContent, context, data):
        promptSystem = "You are an expert on SQL"
        promptOfDBSchema = self.dbSchemaPrompt(dbSchema=data["dbSchema"])
        promptContext = self.data2Context_V1(data)
        promptUser = ""
        promptUser += f"User selected content: {selContent}\n"
        promptUser += f"and has '{context}', which you should respond\n"
        prompt = [
            {"role": "system", "content": promptSystem},
            {"role": "assistant", "content": promptOfDBSchema},
            {"role": "assistant", "content": promptContext},
            {"role": "user", "content": promptUser},
        ]
        result_ans = ""
        i = 0
        while i < 3:
            try:
                result = self.client.chat.completions.create(
                    model=MODEL_SET,
                    messages=prompt,
                    temperature=GPTSETTING["temperature"],
                    max_tokens=MAX_TOKENS,
                )
                result_ans = result.choices[0].message.content
                break
            except Exception as e:
                i += 1
                print(e)
                result_ans = "Connecting Error"
        print(result_ans)
        return result_ans
