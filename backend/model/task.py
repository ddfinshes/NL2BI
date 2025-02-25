import openai
import ast

APIKEY = "sk-awHE6O3rfLOL2QLf43C6CaCc7eB04336933f0dCeC20aE118"
BASEURL = "https://ai-yyds.com/v1"
MAXTOKEN = 1024
TEMPERATURE = 0
ISEVIDENCE = True


class Task:

    def __init__(
        self,
        question="Under whose administration does the school with the highest number of test takers whose total SAT Scores are greater or equal to 1500 belong to?",
        SQL="SELECT schools.AdmFName1, schools.AdmLName1 FROM schools JOIN satscores ON schools.CDSCode = satscores.cds WHERE satscores.NumGE1500 = (SELECT MAX(NumGE1500) FROM satscores)",
    ) -> None:
        self.question = question
        self.SQL = SQL

    def prompt(self):
        prompt = f"Question: {self.question}\n original SQL: {self.SQL}\n"
        prompt += "You should utilize chain of thought to divide question step by step into sub-questions, write sub-SQL for each sub-question and point the corresponding part in original SQL, especially for those operation JOIN, GROUP \n"
        prompt += "You answer should be in an explicitly json code block:\n"
        prompt += "```json\n"
        prompt += "[\n"
        prompt += '    \{"stepDescription": xxx,\n'
        prompt += '    "subquestion": xxx,\n'
        prompt += '    "subSQL": xxx, \\\\ the sub sql for the sub question\n'
        prompt += (
            '    "coreSQL": xxx, \\\\ the corresponding part in the original SQL\n'
        )
        prompt += "\},...]\n"
        prompt += "```"

        return prompt

    def get_response(self, model="gpt-4o-mini"):
        prompt = self.prompt()
        prompt = [{"role": "user", "content": prompt}]
        i = 0
        result_ans = None
        while i < 3:
            try:
                client = openai.OpenAI(api_key=APIKEY, base_url=BASEURL)
                result = client.chat.completions.create(
                    model=model,
                    messages=prompt,
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
                break
            except:
                i += 1
        return result_ans


""" a = Task()
a.get_response()
pass """
