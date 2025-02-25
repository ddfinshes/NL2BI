<template>
	<el-container
		id="IntentionConfirmationModuleContainer"
		v-loading="loading">
		<el-row
			v-if="data.isReady"
			style="position: relative">
			<el-row><h4>Okay. Here's my understanding of you question</h4></el-row>
			<el-row
				ref="questionContainer"
				class="tokensContainer" style="font-size: 20px;"></el-row>
				<button
				ref="tooltipButton"
					class="btn btn-outline-primary btn-sm hidden"
					@click="addTokenLink()"
					style="text-align: left; position:absolute;z-index:888; border-radius: 15.5px; padding-left: 16x; padding-right: 16px">
					Add Connection?
				</button>


			<div
				ref="tooltip"
				class="tooltipIntentionConfirmation hidden"
				style="padding-left: 25px;padding-top: 27px;padding-bottom: 17px;padding-right: 13px;"
				:key="selectedToken.word">
				<div>
					<ul :class="['connectionTokenUl']">
						<li
							v-for="(token_iter, index) in selectedToken.columns"
							:key="`${token_iter[0]}_${token_iter[1]}`"
							:class="[
								'connectionTokenLi',
								`connectionToken_${token_iter[0].replace(/[^a-zA-Z0-9]/g, '')}_${token_iter[1].replace(
									/[^a-zA-Z0-9]/g,
									''
								)}`
							]"
							@click="changeTokenFocus(token_iter[0], token_iter[1])">
							{{ token_iter[0] }}."{{ token_iter[1] }}"
							<el-button
								size="mini"
								circle
								type="info"
								plain
								icon="el-icon-close"
								@click="delToken(token_iter[0], token_iter[1])"></el-button>
						</li>
					</ul>
				</div>
				<hr style="margin-top: 26px; margin-bottom: 31px;margin-left:0px;margin-right:0px;height:1px;opacity: 1; background-color: #515151;"></hr>
				<div
					class="row"
					style="width: 829px; margin-left: 10px">
					<div style="position: relative">
						<span
							style="
								position: absolute;
								color: #dcdfe6;
								z-index: 999;
								top: -13px;
								left: 6px;
								font: 6px #dcdfe6;
								background-color: white;
								
								color:#A1A1A1;
								padding-left:2px;padding-right: 2px;
							">
							Table
						</span>

						<el-select
							style="display: inline-block; min-width: 150px; padding-right: 10px; font: 20px"
							v-model="tooltip_table"
							size="medium"
							placeholder="Plz select table">
							<el-option
								v-for="table_name in dbSchema.table_names"
								:key="table_name"
								:value="table_name"
								:label="table_name"></el-option>
						</el-select>
					</div>
					<div style="position: relative">
						<span
							style="
								position: absolute;
								color: #dcdfe6;
								z-index: 999;
								top: -13px;
								left: 10px;
								font: 6px #dcdfe6;
								background-color: white;		
								color:#A1A1A1;
								padding-left:2px;padding-right: 2px;
							">
							Field
						</span>
						<el-select
							style="display: inline-block; min-width: 150px; padding-right: 10px"
							v-model="tooltip_column"
							size="medium"
							placeholder="Plz select column"
							:key="`tooltip_table_${tooltip_table}`">
							<el-option
								v-for="column_name in dbSchema.columns[tooltip_table]
									? Object.values(dbSchema.columns[tooltip_table]['name'])
									: []"
								:key="column_name"
								:value="column_name"
								:label="column_name"></el-option>
						</el-select>
					</div>
					<button
						class="btn  btn-sm"
						@click="addToken(tooltip_table, tooltip_column)"
						style="border-radius: 15.5px; border: 1px solid #DD9831;padding-left: 16x; padding-right: 16px;color: #DD9831; text-decoration-color:#DD9831">
						+ Add Linking
					</button>
				</div>
				<div
					ref="tooltipTableContainer"
					style="overflow: auto;margin-top: 5px;margin-bottom: 5px;padding:5px;margin-right: 54px ;">
				<table class="table table-hover table-bordered">
  <thead>
    <tr>
      <th scope="col" class="table-secondary">&nbsp;</th>
      <th scope="col"  class="table-secondary">&nbsp;</th>
      <th scope="col"  class="table-secondary">&nbsp;</th>
      <th scope="col"  class="table-secondary">&nbsp;</th>      <th scope="col"  class="table-secondary">&nbsp;</th>
      <th scope="col"  class="table-secondary">&nbsp;</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row"></th>
      <td></td>
      <td></td>
      <td></td>     <td></td>
      <td></td>
    </tr>
    <tr>
      <th scope="row"></th>
      <td></td>
      <td></td>
      <td></td>     <td></td>
      <td></td>
    </tr>
    <tr>
      <th scope="row"></th>
      <td></td>
      <td></td>
      <td></td>     <td></td>
      <td></td>
    </tr>
	    <tr>
      <th scope="row"></th>
      <td></td>
      <td></td>
      <td></td>     <td></td>
      <td></td>
    </tr>
	    <tr>
      <th scope="row"></th>
      <td></td>
      <td></td>
      <td></td>     <td></td>
      <td></td>
    </tr>
  </tbody>
</table></div>
			</div>
			<el-row style="background-color: #f3f3f3" background-color='#f3f3f3'
				>
				<el-collapse background-color='#f3f3f3'>
					<el-collapse-item>
						<template slot="title">
							<h4>If you want to modify</h4>
						</template>
						<el-row>
							<h5>Rephrase the question:</h5>
							<el-input
								type="textarea"
								v-model="question"
								@change="modifyQuestion(value)" />
						</el-row>
						<el-row>
							<h5>Reselect the table for query:</h5>
							<el-select
								v-model="selectedSchema.table_names"
								placeholder="Select"
								:multiple="true"
								size="medium"
								style="max-width: 90%;min-width: 50%;width: auto"
								@change="modifySelectedTable(value)">
								<el-option
									v-for="item in dbSchema.table_names"
									:key="item"
									:label="item"
									:value="item"></el-option>
							</el-select>
						</el-row>

						<el-row>
							<h5>Add more knowledge:</h5>
							<el-input
								type="textarea"
								v-model="evidence"
								@change="modifyEvidence(value)"></el-input>
						</el-row>
					</el-collapse-item>
				</el-collapse>
			</el-row>
			<el-row>
				<div style="text-align:right">
					<button
						class="btn btn-outline-primary btn-sm"
						@click="genNewQuestion"
						style="border-radius: 15.5px; padding-left: 16px; padding-right: 16px"
						>
						Regenerate
					</button>
					<button
						class="btn btn-outline-primary btn-sm"
						v-if="data.isReady"
						@click="genSolution"
						style="margin-left: 10px;border-radius: 15.5px; padding-left: 16px; padding-right: 16px">
			
					<span style="text-align: center;">Next Step</span>	
					</button>
				</div>
			</el-row>
		</el-row>
		<el-row v-if="!data.isReady">
			<el-row>
				<h4>Sorry, I can't build a valid query based on your question.</h4>
				{{ data.needInfo }}
			</el-row>
			<el-row><h4 style="color: red">Maybe you can</h4></el-row>

			<el-row>
				<h5>Rephrase the question:</h5>
				<el-input
					type="textarea"
					v-model="question"
					@change="modifyQuestion(question)" />
			</el-row>
			<el-row>
				<h5>Reselect the table for query:</h5>
				<el-select
					v-model="selectedSchema.table_names"
					placeholder="Select"
					:multiple="true"
					style="max-width: 90%"
					@change="modifySelectedTable(selectedSchema.table_names)">
					<el-option
						v-for="item in dbSchema.table_names"
						:key="item"
						:label="item"
						:value="item"></el-option>
				</el-select>
			</el-row>

			<el-row>
				<h5>Add more knowledge:</h5>
				<el-input
					type="textarea"
					v-model="evidence"
					@change="modifyEvidence(evidence)"></el-input>
			</el-row>
			<el-row style="padding-top: 10px"><el-col>
					<button
						class="btn btn-outline-primary btn-sm"
						@click="genNewQuestion" 		style="border-radius: 15.5px; padding-left: 16px; padding-right: 16px">
						Regenerate
					</button>
					<button
						class="btn btn-outline-primary btn-sm"
						v-if="data.isReady"
						@click="genSolution"
					style="margin-left: 10px;border-radius: 15.5px; padding-left: 16px; padding-right: 16px">
			
					<span style="text-align: center;">Next Step</span>	
					</button>
				</el-col>
			</el-row>
		</el-row>
	</el-container>
</template>
<script>
export default {
	name: "IntentionConfirmationModule",
	props: {
		dataInput: {
			type: Object,
			required: true
		}
	},
	data() {
		return {
			data: {},
			question: "",
			questionToken: [],
			evidence: "",
			knowledge: "",
			table: [],
			selectedSchema: { table_names: [] },
			dbSchema: {
				columns: {}
			},
			selectedToken: { word: "", token: [], isToken: false },
			tooltip_table: "",
			tooltip_column: "",
			loading: false
		}
	},
	methods: {
		modifyQuestion(value) {
			this.$bus.$emit("addAction", {
				type: "modifyQuestion",
				question: value,
				time: new Date().toLocaleString()
			})
		},
		modifySelectedTable(value) {
			this.$bus.$emit("addAction", {
				type: "modifySelectedTable",
				table: value,
				time: new Date().toLocaleString()
			})
		},
		modifyEvidence(value) {
			this.$bus.$emit("addAction", {
				type: "modifyEvidence",
				evidence: value,
				time: new Date().toLocaleString()
			})
		},
		addTokenLink() {
			let selObj = window.getSelection()
			let questionOnlyWord = this.question.replace(/[^\w\s]/g, "")
			questionOnlyWord = questionOnlyWord.replace(/[\n]/g, " ")
			questionOnlyWord = questionOnlyWord.replace(/\s+/g, "")
			let selectString = selObj.toString()
			let cleanStr = selectString.replace(/[^\w\s]/g, "")
			console.log(cleanStr)
			cleanStr = cleanStr.replace(/[\n]/g, " ")
			let selectStringOnlyWord = cleanStr.replace(/\s+/g, "")
			if (selectStringOnlyWord.length == 0) {
				this.$message.error("Plz select qualified word")
				return
			}
			if (questionOnlyWord.indexOf(selectStringOnlyWord) == -1) {
				this.$message.error("Plz select qualified word")
				return
			}
			let questionOnlyWithBackSpace = this.question.replace(/[^\w\s]/g, "")
			questionOnlyWithBackSpace = questionOnlyWithBackSpace.replace(/[\n]/g, " ")
			let questionWithComma = this.question.replace(/[\n]/g, " ")
			let questionTokenList = questionOnlyWithBackSpace.split(" ")
			let cleanStrTokenList = cleanStr.split(" ")
			cleanStrTokenList = cleanStrTokenList.filter((x) => x != "")

			let start = -1
			let end = -1
			if (!questionTokenList.includes(cleanStrTokenList[0])) {
				cleanStrTokenList.shift()
			}
			for (let j = 0; j < questionTokenList.length; j++) {
				if (questionTokenList[j] == cleanStrTokenList[0]) {
					let flag = true
					let i = 0
					for (i = 0; i < cleanStrTokenList.length; i++) {
						if (questionTokenList[j + i] != cleanStrTokenList[i]) {
							if (i == cleanStrTokenList.length - 1) {
								flag = true
								cleanStrTokenList.pop()
								break
							}
							flag = false
							break
						}
					}
					if (flag) {
						start = j
						end = j + i
						break
					}
				}
			}
			if (start == -1 || end == -1 || start == end) {
				this.$message.error("Plz select whole word")
				return
			}
			let word = questionWithComma.split(" ").slice(start, end).join(" ")
			let token_list = JSON.parse(JSON.stringify(this.data.token))
			let token = {
				word: word,
				columns: []
			}
			token_list.push(token)
			token_list = token_list.sort(this.sortTokenFun)
			let index = -1
			for (let i = 0; i < token_list.length; i++) {
				if (token_list[i].word == word) {
					index = i
					break
				}
			}
			// remove index_equal
			let index_containe = -1
			let len = token_list.length
			for (index_containe = 0; index_containe < len; index_containe++) {
				if (index == index_containe) {
					continue
				}
				if (token_list[index_containe].word.includes(word)) {
					let word_list = token_list[index_containe].word
					let column = token_list[index_containe].columns
					token_list = token_list.filter((_, i) => i != index_containe)
					let word_list_split = word_list.split(word)
					token_list.push({
						word: word_list_split[0],
						columns: column
					})
					token_list.push({
						word: word_list_split[1],
						columns: []
					})
					token_list = token_list.sort(this.sortTokenFun)
					break
				}
			}
			if (index_containe == len) {
				let index_prev = index - 1
				let index_next = index + 1
				let questionWithCommaList = questionWithComma.split(" ")
				if (index_prev >= 0) {
					let word_prev_list = token_list[index_prev].word.split(" ")
					let start_prev = -1
					let end_prev = -1
					for (let i = 0; i < questionWithCommaList.length; i++) {
						if (questionWithCommaList[i] == word_prev_list[0]) {
							let flag = true
							let j = 0
							for (j = 0; j < word_prev_list.length; j++) {
								if (questionWithCommaList[i + j] != word_prev_list[j]) {
									flag = false
									break
								}
							}
							if (flag) {
								start_prev = i
								end_prev = i + j
								break
							}
						}
					}
					if (end_prev > start && start_prev != -1) {
						end_prev = start
						if (start_prev >= start) {
							token_list = token_list.filter((_, i) => i != index_prev)
						} else {
							token_list[index_prev].word = questionWithCommaList.slice(start_prev, end_prev).join(" ")
						}
					}
				}
				if (index_next < token_list.length) {
					let word_next_list = token_list[index_next].word.split(" ")
					let start_next = -1
					let end_next = -1
					for (let i = 0; i < questionWithCommaList.length; i++) {
						if (questionWithCommaList[i] == word_next_list[0]) {
							let flag = true
							let j = 0
							for (j = 0; j < word_next_list.length; j++) {
								if (questionWithCommaList[i + j] != word_next_list[j]) {
									flag = false
									break
								}
							}
							if (flag) {
								start_next = i
								end_next = i + j
								break
							}
						}
					}
					if (start_next < end && start_next != -1) {
						start_next = end
						if (end_next <= end) {
							token_list = token_list.filter((_, i) => i != index_next)
						} else {
							token_list[index_next].word = questionWithCommaList.slice(start_next, end_next).join(" ")
						}
					}
				}
			}
			console.log(token_list)
			this.$bus.$emit("addAction", {
				type: "addTokenLink",
				token: token,
				time: new Date().toLocaleString()
			})
			this.data.token = token_list
			this.interactiveQuestion()
			$(this.$refs.tooltipButton).removeClass("hidden")
		},
		obtainTableInfo(table) {
			if (table == "") {
				return
			}
			let sql = `SELECT * FROM ${table} LIMIT 5`
			this.axios.post("/api/executeSQL", { sql: sql }).then((response) => {
				let root = $(this.$refs.tooltipTableContainer)
				root.empty()
				let tableContainer = $("<table class='table table-hover table-bordered'></table>")
				let thead = $("<thead></thead>")
				let tbody = $("<tbody></tbody>")
				let tr = $("<tr></tr>")
				for (let i = 0; i < response.data.column_names.length; i++) {
					let th = $(`<th scope="col"></th>`)
					th.text(response.data.column_names[i])
						.addClass(`tooltip_${response.data.column_names[i].replace(/[^a-zA-Z0-9]/g, "")}`)
						.addClass("table-secondary")
						.on("click", () => {
							this.changeTokenFocus(table, response.data.column_names[i])
						})
					tr.append(th)
				}
				thead.append(tr)

				for (let i = 0; i < response.data.table.length; i++) {
					let tr = $("<tr></tr>")
					for (let j = 0; j < response.data.table[i].length; j++) {
						let td = $("<td></td>")
						td.text(response.data.table[i][j]).addClass(
							`tooltip_${response.data.column_names[j].replace(/[^a-zA-Z0-9]/g, "")}`
						)
						tr.append(td)
					}
					tbody.append(tr)
				}

				tableContainer.append(thead)
				tableContainer.append(tbody)
				root.append(tableContainer)
				for (let i = 0; i < this.selectedToken.columns.length; i++) {
					$(this.$refs.tooltipTableContainer)
						.find(`.tooltip_${this.selectedToken.columns[i][1].replace(/[^a-zA-Z0-9]/g, "")}`)
						.addClass("")
				}
			})
		},
		changeTokenFocus(table, column) {
			this.tooltip_table = table
			this.tooltip_column = column
			$(this.$el).find(".connectionTokenLi").removeClass("selectedConnectionTokenLi")
			$(this.$el)
				.find(`.connectionToken_${table.replace(/[^a-zA-Z0-9]/g, "")}_${column.replace(/[^a-zA-Z0-9]/g, "")}`)
				.addClass("selectedConnectionTokenLi")
		},
		delToken(table, column) {
			this.selectedToken.columns = this.selectedToken.columns.filter((x) => x[0] != table || x[1] != column)
			this.selectedToken.table = Array.from(new Set(this.selectedToken.columns.map((x) => x[0])))
			this.$bus.$emit("addAction", {
				type: "delTokenLink",
				word: this.selectedToken.word,
				table: table,
				column: column,
				time: new Date().toLocaleString()
			})
		},
		addToken(table, column) {
			if (table == "" || column == "") {
				return
			}
			//this.selectedToken.token.push([table, column])
			//this.selectedToken.token=this.selectedToken.token.sort()
			let isExist = false
			for (let i = 0; i < this.selectedToken.columns.length; i++) {
				if (this.selectedToken.columns[i][0] == table && this.selectedToken.columns[i][1] == column) {
					isExist = true
					break
				}
			}
			if (!isExist) {
				this.selectedToken.columns.push([table, column])
				this.$bus.$emit("addAction", {
					type: "addTokenLink",
					word: this.selectedToken.word,
					table: table,
					column: column,
					time: new Date().toLocaleString()
				})
			}
			this.selectedToken.columns = this.selectedToken.columns.sort(this.token_sort)
			this.selectedToken.table = Array.from(new Set(this.selectedToken.columns.map((x) => x[0])))
		},
		sortTokenFun(a, b) {
			if (this.data.question.indexOf(a.word) - this.data.question.indexOf(b.word) != 0) {
				return this.data.question.indexOf(a.word) - this.data.question.indexOf(b.word)
			} else {
				return a.word.length - b.word.length
			}
		},
		token_sort(a, b) {
			if (a[0] < b[0]) {
				return -1
			} else {
				if (a[0] == b[0]) {
					return a[1] < b[1] ? -1 : 1
				} else {
					return 1
				}
			}
		},
		/* 		confirmIntention() {}, */
		interactiveQuestion(token = null) {
			let that = this
			if (!this.data.isReady) {
				return
			}
			if (this.$refs.questionContainer) {
				this.$refs.questionContainer.$el.innerHTML = ""
			}

			let position = []

			if (token == null) {
				token = this.data.token.sort(this.sortTokenFun)
			}
			let word_set = new Set()
			let originalQuestion = this.data.question
			let token_List = []
			let id = 0
			for (let i = 0; i < token.length; i++) {
				if (word_set.has(token[i].word)) {
					continue
				}
				word_set.add(token[i].word)
				if (originalQuestion.indexOf(token[i].word) === -1) {
					continue
				}
				let split_iter = originalQuestion.split(token[i].word)
				if (split_iter[0] != " ") {
					token_List.push({
						word: split_iter[0].replace(/(^\s*)|(\s*$)/g, ""),
						isToken: false,
						id: id
					})
				}

				id++
				let tokenTable = Array.from(new Set(token[i].columns.map((x) => x[0])))
				token_List.push({
					word: token[i].word.replace(/(^\s*)|(\s*$)/g, ""),
					isToken: true,
					columns: token[i].columns.sort(this.token_sort),
					table: tokenTable,
					id: id
				})
				id++
				split_iter.shift()
				originalQuestion = split_iter.join(token[i].word)
				console.log(token[i].word)
				console.log(split_iter)
				console.log(originalQuestion)
			}

			if (originalQuestion != " ") {
				token_List.push({
					word: originalQuestion.replace(/(^\s*)|(\s*$)/g, ""),
					isToken: false,
					id: id
				})
			}
			this.questionToken = token_List
			let charToken = []
			token_List.forEach((wToken) => {
				let charList = wToken.word.split(" ")
			})
			/*
			for (let i = 0; i < token_List.length; i++) {
				if (token_List[i].isToken) {
					let token = token_List[i]
					let tokenContainer = document.createElement("ul")
					for (let j = 0; j < token_List[i].token.length; j++) {
						let content = `${token_List[i].token[j][0]}.${token_List[i].token[j][1]}`
						let columnContainer = document.createElement("li")
						columnContainer.setAttribute("id", `question_token_${token.id}_column_${j}`)
						columnContainer.setAttribute("style", "display: inline-item")
						columnContainer.style.color = "#DD9831"
						columnContainer.innerHTML = content
						columnContainer.addEventListener("click", (event) => {
							if (columnContainer.style.backgroundColor === "rgb(255, 255, 255)") {
							} else {
							}
						})
						tokenContainer.appendChild(columnContainer)
					}
					tokenContainer.setAttribute("id", `question_token_tooltip_${token.id}`)
					tokenContainer.style.position = "fixed"
					tokenContainer.style.border = "1px solid #DD9831"
					tokenContainer.style["z-index"] = "1000"
					tokenContainer.classList.add("hidden")
					tokenContainer.classList.add("token-tooltip")

					this.$refs.tooltipCollections.appendChild(tokenContainer)
				}
			}
			*/
			for (let i = 0; i < token_List.length; i++) {
				if (token_List[i].isToken) {
					let token = token_List[i]
					/*
					let word_list = token.word.split(" ")
					for (let j = 0; j < word_list.length; j++) {
						let tokenContainer = document.createElement("span")
						tokenContainer.setAttribute("class", `question_token_${token.id}`)
						tokenContainer.setAttribute("class", "token token-match")
						tokenContainer.setAttribute("style", "display: inline-block;text-decoration:underline;")
						tokenContainer.style.color = "#DD9831"
						tokenContainer.innerHTML = word_list[j]
						tokenContainer.addEventListener("click", (event) => {
							console.log(token)
							this.selectedToken = token
						})
						this.$refs.questionContainer.$el.appendChild(tokenContainer)
					}
					*/

					let tokenContainer = document.createElement("span")
					tokenContainer.setAttribute("class", `question_token_${token.id}`)
					tokenContainer.setAttribute("class", "token token-match")
					tokenContainer.setAttribute("style", "display: inline-block;text-decoration:underline;")
					tokenContainer.style.color = "#DD9831"
					tokenContainer.innerHTML = token.word
					tokenContainer.addEventListener("click", function (event) {
						that.tooltip_table = ""
						that.tooltip_column = ""
						that.selectedToken = token
						$(that.$refs.tooltip).removeClass("hidden")
						let position = $(this).position()
						$(that.$refs.tooltip).css({
							top: `${position.top + 60}px`,
							left: `${position.left}px`
						})
						that.$bus.$emit("addAction", {
							type: "clickTokenLink",
							token: token,
							time: new Date().toLocaleString()
						})
					})
					this.$refs.questionContainer.$el.appendChild(tokenContainer)
				} else {
					let token = token_List[i]
					let word_list = token.word.split(" ")
					for (let j = 0; j < word_list.length; j++) {
						let tokenContainer = document.createElement("span")
						tokenContainer.setAttribute("class", `question_token_tooltip_${token.id}`)
						tokenContainer.setAttribute("class", "token")
						tokenContainer.setAttribute("style", "display: inline-block")
						tokenContainer.innerHTML = word_list[j]
						tokenContainer.addEventListener("click", (event) => {
							this.tooltip_table = ""
							this.tooltip_column = ""
							this.selectedToken = token
							$(that.$refs.tooltip).addClass("hidden")
						})
						this.$refs.questionContainer.$el.appendChild(tokenContainer)
					}

					/*
					let tokenContainer = document.createElement("span")
					tokenContainer.setAttribute("class", `question_token_tooltip_${token.id}`)
					tokenContainer.setAttribute("class", "token")
					tokenContainer.setAttribute("style", "display: inline-block")
					tokenContainer.innerHTML = token.word
					this.$refs.questionContainer.$el.appendChild(tokenContainer)
					*/
				}
			}
		},
		getDBSchema() {
			this.axios.get("/api/getDBSchema").then((response) => {
				this.dbSchema = response.data
			})
		},
		genNewQuestion() {
			this.loading = true
			this.selectedSchema["columns"] = {}
			for (let i = 0; i < this.selectedSchema.table_names.length; i++) {
				let table = this.selectedSchema.table_names[i]
				this.selectedSchema.columns[table] = this.dbSchema.columns[table]
			}
			this.selectedSchema["fk_pairs"] = this.dbSchema.fk_pairs
			let configuration = JSON.parse(JSON.stringify(this.data))
			configuration["dbSchema"] = this.selectedSchema
			configuration["question"] = this.question
			if (this.question != this.data.question) {
				this.evidence = ""
			}
			configuration["evidence"] = this.evidence
			configuration["token"] = this.questionToken.filter((x) => x.isToken)
			let args = { configuration: configuration }
			this.$bus.$emit("addAction", {
				type: "regenerateIntentionConfirmation",
				question: configuration.question,
				evidence: configuration.evidence,
				selectedTable: configuration.dbSchema.table_names,
				isReady: this.data.isReady,
				token: configuration.token,
				time: new Date().toLocaleString()
			})
			this.axios.post("/api/genNewQuestion", args).then((response) => {
				/*
				this.data = response.data
				this.question = this.data.question
				this.evidence = this.data.evidence
				this.selectedSchema = JSON.parse(JSON.stringify(this.data.dbSchema))
				this.interactiveQuestion() */
				this.$bus.$emit("addAction", {
					type: "receiveNewQuestion",
					response: response.data,
					time: new Date().toLocaleString()
				})
				this.$bus.$emit("newQuestion", response.data)
				this.loading = false
			})
		},
		genSolution() {
			this.loading = true
			this.selectedSchema["columns"] = {}
			for (let i = 0; i < this.selectedSchema.table_names.length; i++) {
				let table = this.selectedSchema.table_names[i]
				this.selectedSchema.columns[table] = this.dbSchema.columns[table]
			}
			this.selectedSchema["fk_pairs"] = this.dbSchema.fk_pairs
			let configuration = JSON.parse(JSON.stringify(this.data))
			configuration["dbSchema"] = this.selectedSchema
			configuration["question"] = this.question
			if (this.question != this.data.question) {
				this.evidence = ""
			}

			configuration["token"] = this.questionToken.filter((x) => x.isToken)

			configuration["evidence"] = this.evidence
			this.$bus.$emit("addAction", {
				type: "nextStep",
				question: configuration.question,
				evidence: configuration.evidence,
				selectedTable: configuration.dbSchema.table_names,
				isReady: this.data.isReady,
				token: configuration.token,
				time: new Date().toLocaleString()
			})
			let args = { configuration: configuration }
			this.axios.post("/api/getSolution", args).then((response) => {
				this.$bus.$emit("addAction", {
					type: "receiveNextStep",
					response: response.data,
					time: new Date().toLocaleString()
				})
				this.$bus.$emit("newSolution", response.data)
				this.loading = false
			})
		}
	},
	mounted() {
		this.data = JSON.parse(JSON.stringify(this.dataInput))
		this.data.token = this.data.token.filter((x) => x.columns.length != 0)
		console.log(this.data)
		this.question = this.data.question
		this.evidence = this.data.evidence

		this.selectedSchema = JSON.parse(JSON.stringify(this.data.dbSchema))
		this.$nextTick(() => {
			this.interactiveQuestion()
			this.getDBSchema()
			let that = this
			document.addEventListener("selectionchange", function () {
				//$(that.$refs.explainModule).addClass("hidden")
				if(!that.$refs.questionContainer){
					return
				}
				if(!that.$refs.questionContainer.$el){
					return
				}
				var selection = window.getSelection()
				if (selection.rangeCount > 0) {
			var range = selection.getRangeAt(0)
					var rect = range.getBoundingClientRect()
					console.log((that))
					console.log(that.$refs.questionContainer)
					var $parent = $(that.$refs.questionContainer.$el)
					var anchorNode = selection.anchorNode
					var isWithinParent = $(anchorNode).closest(that.$refs.questionContainer.$el).length > 0
					if (!isWithinParent) return
					var parentRect = $parent[0].getBoundingClientRect()

					var relativeX = rect.left - parentRect.left
					var relativeY = rect.top - parentRect.top

					if (selection.toString().length > 0) {
						$(that.$refs.tooltipButton).css({
							top: relativeY + 60 + "px",
							left: relativeX +15 + "px"
						})
						$(that.$refs.tooltipButton).removeClass("hidden")
					} else {
						$(that.$refs.tooltipButton).addClass("hidden")
					}
				}
			})
		})
	},
	watch: {
		tooltip_table() {
			this.tooltip_column = ""
			this.obtainTableInfo(this.tooltip_table)
			this.$bus.$emit("addAction", {
				type: "changeTooltipTable",
				table: this.tooltip_table,
				time: new Date().toLocaleString()
			})
		},
		tooltip_column(new_column, old_column) {
			console.log((`tooltip_${new_column.replace(/[^a-zA-Z0-9]/g, "")}`))
			$(this.$refs.tooltipTableContainer)
				.find("th")
				.each(function () {
					if ($(this).hasClass(`tooltip_${new_column.replace(/[^a-zA-Z0-9]/g, "")}`)) {
						$(this).addClass("table-warning")
					} else {
						$(this).removeClass("table-warning")
					}
				})
			$(this.$refs.tooltipTableContainer)
				.find("td")
				.each(function () {
					if ($(this).hasClass(`tooltip_${new_column.replace(/[^a-zA-Z0-9]/g, "")}`)) {
						$(this).addClass("table-warning")
					} else {
						$(this).removeClass("table-warning")
					}
				})
			this.$bus.$emit("addAction", {
				type: "changeTooltipColumn",
				table: this.tooltip_table,
				column: new_column,
				time: new Date().toLocaleString()
			})
		},
		"selectedSchema.table_names"() {
			this.$bus.$emit("updateSelectedSchema", this.selectedSchema)
		}
	}
}
</script>
<style>
#IntentionConfirmationModuleContainer {
	padding-left: 15px;
	padding-right: 15px;
	overflow: visible;
	.hidden {
		display: none;
	}
	.token-tooltip {
		background-color: white;
	}
	.tooltiphighlight {
		color: #dd9831;
	}
	.tooltipConnection {
		color: #1dc5c5;
	}
	.token {
		white-space: normal;
		margin-left: 0.5em;
	}
	.tokensContainer {
		display: flex;
		flex-wrap: wrap;
	}
	.hightLightToken {
		background-color: #aaa69f;
	}
	.tooltipIntentionConfirmation {
		position: absolute;
		border: 2px solid #616161;
		padding: 5px;
		box-shadow: 4px 4px 4px #616161;
		border-radius: 5px;

		background-color: white;
		z-index: 999;
		overflow: visible;
width:931px;
		height: 900px;
		overflow: auto;
	}
	.connectionTokenUl {
		margin: 0px;
	}
	.connectionTokenLi {
		border-radius: 10px;
		border: 1px solid #dd9831;
		color: #dd9831;
		padding: 5px;
		margin: 5px;
		background-color: white;
		cursor: pointer;
		&:hover {
			background-color: #e0e0e0;
		}
	}
	.selectedConnectionTokenLi {
		background-color: #dd9831;
		color: white;
	}
	.el-collapse{
		background-color: #f3f3f3;
	}
	.el-collapse,.el-collapse-item__header{
		background-color: #f3f3f3;
	}
	.el-collapse-item__content{
		background-color: #f3f3f3;
	}
	.el-collapse-item__content{
		background-color: #f3f3f3;
	}
	.el-input__inner{
		border-color: #616161;
	}
	.el-collapse-item__arrow{
		text-align: left
		;margin-left: 10px;
	}
	.table-warning{

	}

}
</style>
