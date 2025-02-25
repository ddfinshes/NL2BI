<template>
	<div
		:class="['container']"
		id="QueryGenerationModuleContainer"
		:key="`regenerateCNT_${regenerateCNT}`"
		v-loading="loading">
		<div>
			<h4 style="display: inline-block">Let us analyze and construct the SQL query statement step by step</h4>
			<button
				class="btn btn-link btn-sm"
				@click="viewLink">
				<img
					style="width: 36px; height: 36px"
					src="@/assets/image/isNotExpanded.png"
					alt="..."
					ref="isNotExpandedIcon"
					:fit="`fill`" />
				<img
					style="width: 36px; height: 36px"
					src="@/assets/image/isExpanded.png"
					alt="..."
					ref="isExpandedIcon"
					:class="[`hidden`]"
					:fit="`fill`" />
			</button>
		</div>
		<div :ref="`subStepCollectionContainer`">
			<div
				v-for="(step, index) in data.COT"
				style="margin-bottom: 20px">
				<div
					:class="[`subStepHead_${step.stepID}`, `subStepHead`]"
					style="margin-left: 20px">
					<h5 style="display: inline-block; margin-right: 10px">{{ `${index + 1}. ${step.subStep}` }}</h5>
					<button
						type="button"
						class="btn btn-sm btn-outline-primary"
						@click="expandOrHideSubStep($event, { id: step.stepID, index: index })"
						:ref="`ExpandSubStep_${step.stepID}`"
						style="margin-left: 10px; border-radius: 15.5px">
						Expand&nbsp;
						<i class="el-icon-caret-bottom"></i>
					</button>
					<button
						type="button"
						class="btn btn-sm btn-outline-primary"
						@click="regenerate"
						style="margin-left: 10px; border-radius: 15.5px; padding-left: 16x; padding-right: 16px">
						Regenerate
					</button>
				</div>
				<div
					:ref="`subStepContainer_${step.stepID}`"
					:class="['hidden']"
					style="margin-left: 40px">
					<div
						:ref="`stepDescriptionContainer_${step.stepID}`"
						:id="`stepDescriptionContainer_${step.stepID}`"
						:class="['stepDescriptionContainer']"
						@click="handleClickOutsideStepDescription($event, step.stepID)">
						<div
							class=""
							:ref="`stepDescription_${step.stepID}`"
							@click.stop="handleClickInsideStepDescription($event, step.stepID)">
							{{ step.stepDescription }}
						</div>
						<div
							:ref="`stepDescriptionInputContainer_${step.stepID}`"
							:class="['hidden']"
							@click.stop="">
							<el-input
								type="textarea"
								placeholder="Step Description"
								:autosize="{ minRows: 0, maxRows: 15 }"
								v-model="step.stepDescription"
								@change="
									modifyStepDescription({
										value: step.stepDescription,
										isSub: true,
										subID: step.stepID
									})
								"
								:ref="`stepDescriptionInput_${step.stepID}`"></el-input>
						</div>
					</div>
					<div
						:ref="`subSQLContainer_${step.stepID}`"
						:id="`subSQLContainer_${step.stepID}`"
						:class="['subSQLContainer']"
						@click="handleClickOutsideSubSQL($event, step.stepID)">
						<div
							class=""
							style="
								display: flex;
								justify-content: space-between;
								background-color: #2f2f2f;
								border-radius: 5px 5px 0 0;
								padding-top: 5px;
							">
							<div style="text-align: left; margin-left: 10px; color: #969696"><span>sql</span></div>
							<div style="text-align: right">
								<button
									@click.stop="
										gptFix($event, {
											sql: step.subSQLFormatted,
											isSubStep: true,
											subStepID: step.stepID
										})
									"
									class="btn-sm"
									style="
										margin-left: 10px;
										margin-right: 10px;
										background-color: #2f2f2f;
										color: white;
										border: 0px;
									">
									<i class="el-icon-refresh-right"></i>
									&nbsp;Refine
								</button>
								<button
									@click.stop="
										executeSQL($event, {
											id: step.stepID,
											sql: step.subSQLFormatted,
											refNameTable: `executesubStepTableContainer_${step.stepID}`,
											refName: `subSQL_${step.stepID}`,
											isSub: true
										})
									"
									class="btn-sm"
									style="background-color: #2f2f2f; color: white; border: 0px">
									<i class="el-icon-caret-right"></i>
									&nbsp;Execute
								</button>
							</div>
						</div>
						<!--	<div
							:ref="`subSQLContainer_${step.stepID}`"
							:id="`subSQLContainer_${step.stepID}`"
							:class="['subSQLContainer']"
							@click="handleClickOutsideSubSQL($event, step.stepID)">
							<button
								@click.stop="
									executeSQL($event, {
										id: step.stepID,
										sql: step.subSQLFormatted,
										refNameTable: `executesubStepTableContainer_${step.stepID}`,
										refName: `subSQL_${step.stepID}`,
										isSub: true
									})
								"
								class="btn btn-outline-primary btn-sm">
								Execute
							</button>
							<button
								@click.stop="
									gptFix($event, {
										sql: step.subSQLFormatted,
										isSubStep: true,
										subStepID: step.stepID
									})
								"
								class="btn btn-outline-primary btn-sm"
								style="margin-left: 10px"
								v-loading="isRefineLoading">
								Refine
							</button>
						</div>-->
						<div
							:ref="`subSQL_${step.stepID}`"
							:id="`subSQL_${step.stepID}`"
							@click.stop="handleClickInsideSubSQL($event, step.stepID)"
							:class="['SQLCode']"></div>

						<div
							:ref="`subSQLInputContainer_${step.stepID}`"
							:class="['hidden']"
							@click.stop="">
							<el-input
								type="textarea"
								placeholder="Step Description"
								:autosize="{ minRows: 0, maxRows: 15 }"
								v-model="step.subSQLFormatted"
								@change="modifySQL({ value: step.subSQLFormatted, isSub: true, subID: step.stepID })"
								:ref="`subSQLInput_${step.stepID}`"></el-input>
						</div>
						<div
							:ref="`executesubStepTableContainer_${step.stepID}`"
							:class="['hidden']"
							style="margin-top: 10px"></div>
					</div>
				</div>
			</div>
		</div>
		<div
			:ref="`subStepSVGContainer`"
			:id="`subStepSVGContainer_${data.id}`"
			:class="['hidden', 'row']">
			<div
				class="col-3"
				:id="`subStepSVGColContainer_${data.id}`"
				style="height: 300px; border-left: 1px grey">
				<svg
					:id="`subStepSVG_${data.id}`"
					class="subStepSvg"></svg>
			</div>
			<div
				:id="`subStepSvgTooltip_${data.id}`"
				:ref="`subStepSvgTooltip`"
				:class="['subStepSVGToolTip', '', 'col-9']">
				<div>
					{{ `${selectedSubStepID}. ${selectedSubStep.subStep}` }}
					<button
						type="button"
						class="btn btn-sm btn-outline-primary"
						@click="expandOrHideSubStepSVG()"
						:ref="`ExpandSubStepSVGTooltip`"
						style="border-radius: 15.5px; padding-left: 16px; padding-right: 16px">
						Expand&nbsp;
						<i class="el-icon-caret-bottom"></i>
					</button>
					<button
						type="button"
						class="btn btn-sm btn-outline-primary"
						@click="regenerate"
						style="margin-left: 10px; border-radius: 15.5px; padding-left: 16px; padding-right: 16px">
						Regenerate
					</button>
				</div>
				<div
					:ref="`subStepDetailSVGContainer`"
					:class="['hidden']">
					<div
						:ref="`stepDescriptionSVGContainer`"
						:id="`stepDescriptionSVGContainer_${data.id}`"
						:class="['stepDescriptionSVGContainer']"
						@click="handleClickOutsideStepDescriptionSVG()">
						<div
							class=""
							:ref="`stepDescriptionSVG`"
							@click.stop="handleClickInsideStepDescriptionSVG()">
							{{ selectedSubStep.stepDescription }}
						</div>
						<div
							:ref="`stepDescriptionInputSVGContainer`"
							:class="['hidden']"
							@click.stop="">
							<el-input
								type="textarea"
								placeholder="Step Description"
								:autosize="{ minRows: 0, maxRows: 15 }"
								v-model="selectedSubStep.stepDescription"
								@change="
									modifyStepDescription({
										value: selectedSubStep.stepDescription,
										isSub: true,
										subID: selectedSubStep.stepID
									})
								"
								:ref="`stepDescriptionInputSVG`"></el-input>
						</div>
					</div>
					<div
						:ref="`subSQLSVGContainer`"
						:id="`subSQLSVGContainer`"
						:class="['subSQLContainer']"
						@click="handleClickOutsideSubSQLSVG()">
						<div
							class=""
							style="
								display: flex;
								justify-content: space-between;
								background-color: #2f2f2f;
								border-radius: 5px 5px 0 0;
								padding-top: 5px;
							">
							<div style="text-align: left; margin-left: 10px; color: #969696"><span>sql</span></div>
							<div style="text-align: right">
								<button
									@click.stop="
										gptFix($event, {
											sql: selectedSubStep.subSQLFormatted,
											isSubStep: true,
											subStepID: selectedSubStep.stepID
										})
									"
									class="btn-sm"
									style="
										margin-left: 10px;
										margin-right: 10px;
										background-color: #2f2f2f;
										color: white;
										border: 0px;
									">
									<i class="el-icon-refresh-right"></i>
									&nbsp;Refine
								</button>
								<button
									@click.stop="
										executeSQL($event, {
											id: selectedSubStep.stepID,
											sql: selectedSubStep.subSQLFormatted,
											refNameTable: `executesubStepTableContainerSVG`,
											refName: `subSQLSVG`,
											isSub: false,
											isSubSVG: true
										})
									"
									class="btn-sm"
									style="background-color: #2f2f2f; color: white; border: 0px">
									<i class="el-icon-caret-right"></i>
									&nbsp;Execute
								</button>
							</div>
						</div>
						<div
							:ref="`subSQLSVG`"
							:id="`subSQLSVG`"
							@click.stop="handleClickInsideSubSQLSVG()"
							:class="['SQLCode']"></div>

						<div
							:ref="`subSQLInputContainer`"
							:class="['hidden']"
							@click.stop="">
							<el-input
								type="textarea"
								placeholder="Step Description"
								:autosize="{ minRows: 0, maxRows: 15 }"
								v-model="selectedSubStep.subSQLFormatted"
								@change="
									modifySQL({
										value: selectedSubStep.subSQLFormatted,
										isSub: true,
										subID: selectedSubStep.stepID
									})
								"
								:ref="`subSQLSVGInput`"></el-input>
						</div>
						<div
							:ref="`executesubStepTableContainerSVG`"
							:class="['hidden']"></div>
					</div>
					<!--
					<div
						:ref="`subSQLSVGContainer`"
						:id="`subSQLSVGContainer`"
						:class="['subSQLContainer']"
						@click="handleClickOutsideSubSQLSVG()">
						<button
							@click.stop="
								executeSQL($event, {
									id: selectedSubStep.stepID,
									sql: selectedSubStep.subSQLFormatted,
									refNameTable: `executesubStepTableContainerSVG`,
									refName: `subSQLSVG`,
									isSub: false,
									isSubSVG: true
								})
							"
							class="btn btn-outline-primary btn-sm">
							Execute
						</button>
						<button
							@click.stop="
								gptFix($event, {
									sql: selectedSubStep.subSQLFormatted,
									isSubStep: true,
									subStepID: selectedSubStep.stepID
								})
							"
							class="btn btn-outline-primary btn-sm"
							style="margin-left: 10px">
							Refine
						</button>
					</div>
					<div
						:ref="`subSQLSVG`"
						:id="`subSQLSVG`"
						@click.stop="handleClickInsideSubSQLSVG()"
						:class="['SQLCode']"></div>

					<div
						:ref="`subSQLInputContainer`"
						:class="['hidden']"
						@click.stop="">
						<el-input
							type="textarea"
							placeholder="Step Description"
							:autosize="{ minRows: 0, maxRows: 15 }"
							v-model="selectedSubStep.subSQLFormatted"
							@change="
								modifySQL({
									value: selectedSubStep.subSQLFormatted,
									isSub: true,
									subID: selectedSubStep.stepID
								})
							"
							:ref="`subSQLSVGInput`"></el-input>
					</div>
					<div
						:ref="`executesubStepTableContainerSVG`"
						:class="['hidden']"></div>-->
				</div>
			</div>
		</div>
		<div class="dropdown-divider"></div>
		<div @click="handleClickOutsideSQL($event)">
			<h4 style="margin-right: 10px">The final SQL query statement</h4>

			<div>
				<div
					class=""
					style="
						display: flex;
						justify-content: space-between;
						background-color: #2f2f2f;
						border-radius: 5px 5px 0 0;
						padding-top: 5px;
					">
					<div style="text-align: left; margin-left: 10px; color: #969696"><span>sql</span></div>
					<div style="text-align: right">
						<button
							@click.stop="gptFix($event, { sql: data.SQLFormatted, isSubStep: false, subStepID: -1 })"
							class="btn-sm"
							style="
								margin-left: 10px;
								margin-right: 10px;
								background-color: #2f2f2f;
								color: white;
								border: 0px;
							">
							<i class="el-icon-refresh-right"></i>
							&nbsp;Refine
						</button>
						<button
							@click.stop="
								executeSQL($event, {
									id: -1,
									sql: data.SQLFormatted,
									refNameTable: `executeSQLTableContainer`,
									refName: `SQLContainer`,
									isSub: false
								})
							"
							class="btn-sm"
							style="background-color: #2f2f2f; color: white; border: 0px">
							<i class="el-icon-caret-right"></i>
							&nbsp;Execute
						</button>
					</div>
				</div>
				<div
					ref="SQLContainer"
					id="SQLContainer"
					class="SQLCode"
					@click.stop="handleClickInsideSQL($event)"></div>
				<div
					ref="SQLInputContainer"
					:class="['hidden']"
					@click.stop="">
					<el-input
						type="textarea"
						placeholder="Step Description"
						:autosize="{ minRows: 0, maxRows: 15 }"
						v-model="data.SQLFormatted"
						@change="modifySQL({ value: data.SQLFormatted, isSub: false, subID: -1 })"
						:ref="`SQLInput`"></el-input>
				</div>
			</div>

			<div
				:ref="`executeSQLTableContainer`"
				style="margin-top: 10px"></div>
		</div>
		<button
			:ref="'explainModuleTrigger'"
			class="btn btn-outline-primary btn-sm explainTrigger hidden"
			@click="explainButton">
			?
		</button>
		<div
			class="explainModule hidden"
			:ref="'explainModule'">
			<!-- 		<div><el-button @click="explainSelect(false, -1)">Require Explanation(select)</el-button></div>
			<div><el-button @click="explainContext(false, -1)">Require Explanation</el-button></div> -->
			<h5>Selected Context:</h5>
			<p style="margin-left: 10px">{{ selectedContext }}</p>
			<button
				class="btn btn-outline-info btn-sm"
				@click="explainCombine()">
				Send
			</button>
			<div>
				<el-input
					type="textarea"
					placeholder="Please input the question context"
					v-model="questionContext"></el-input>
			</div>
			<div>
				<vue-markdown :key="explanationContext">{{ explanationContext }}</vue-markdown>
			</div>
		</div>
	</div>
</template>
<script>
import * as d3 from "d3"
import * as d3dag from "d3-dag"
import $ from "jquery"
import VueMarkdown from "vue-markdown"
export default {
	name: "QueryGenerationModule",
	props: {
		dataInput: {
			type: Object,
			required: true
		}
	},
	components: {
		VueMarkdown
	},
	data() {
		return {
			original_data: {},
			data: { SQLFormatted: "" },
			SQLCodeTree: {},
			SQLExpressionList: [],
			subStepStatus: [],
			executeResult: {},
			DAGPosition: {},
			selectedSubStepID: "",
			isselectedSubStepExpanded: false,
			selectedSubStep: { stepDescription: "", subSQLFormatted: "", subStep: "" },
			COTNode: [],
			COTEdge: [],
			isLinkExpanded: false,
			questionContext: "",
			explanationContext: "",
			selectedContext: "",
			COTQueryPair: {},
			loading: false,
			isRefineLoading: false,
			regenerateCNT: 0
		}
	},
	methods: {
		modifyStepDescription(args) {
			this.$bus.$emit("addAction", {
				type: "modifyStepDescription",
				value: args.value,
				isSub: args.isSub,
				subStepID: args.subID,
				time: new Date().toLocaleString()
			})
		},
		modifySQL(args) {
			this.$bus.$emit("addAction", {
				type: "modifySQL",
				value: args.value,
				isSub: args.isSub,
				subStepID: args.subID,
				time: new Date().toLocaleString()
			})
		},
		gptFix(event, args) {
			this.isRefineLoading = true
			this.$bus.$emit("addAction", {
				type: "selfFix",
				sql: args.sql,
				isSubStep: args.isSubStep,
				subStepID: args.subStepID,

				time: new Date().toLocaleString()
			})

			args["data"] = this.data
			this.axios.post("/api/gptFix", args).then((response) => {
				if (args.isSubStep) {
					this.data.COT[+args.subStepID - 1].subSQL = response.data.SQL
					this.data.COT[+args.subStepID - 1].subSQLFormatted = response.data.SQLFormatted
				} else {
					this.data.SQLFormatted = response.data.SQLFormatted
					this.data.SQL = response.data.SQL
				}
				this.$bus.$emit("addAction", {
					type: "receiveSelfFix",
					response: response.data,
					isSub: args.isSub,
					subStepID: args.subStepID,
					time: new Date().toLocaleString()
				})
				// 要补code geng
				/*
				this.SQLCodeBlockGenerate(args.refName, this.SQLCodeTrans(response.data.sql), {
					isSub: args.isSub,
					id: args.id
				})
				*/
				this.isRefineLoading = false
			})
		},
		explainSelect(isSubStep, subStepID) {
			let selObj = window.getSelection()
			let args = {
				context: selObj.toString().replace(/[\n]/g, " "),
				data: this.data,
				isUserActive: false,
				isSubStep: isSubStep,
				subStepID: subStepID
			}
			this.axios.post("/api/explain", args).then((response) => {
				this.explanationContext = response.data
			})
		},
		explainContext(isSubStep, subStepID) {
			let args = {
				context: this.questionContext,
				data: this.data,
				isUserActive: true,
				isSubStep: isSubStep,
				subStepID: subStepID
			}
			this.axios.post("/api/explain", args).then((response) => {
				this.explanationContext = response.data
			})
		},
		explainButton(event) {
			let $explainModule = $(this.$refs.explainModule)
			let $explainModuleTrigger = $(this.$refs.explainModuleTrigger)
			$explainModule.removeClass("hidden")
			$explainModule.css({
				top: $explainModuleTrigger.position().top + 60 + "px",
				left: $explainModuleTrigger.position().left + "px"
			})
			$explainModuleTrigger.addClass("hidden")
			this.selectedContext = window.getSelection().toString()
			this.$bus.$emit("addAction", {
				type: "explain",
				selectedContext: this.selectedContext,
				time: new Date().toLocaleString()
			})
		},
		explainCombine() {
			let selObj = window.getSelection()
			let args = {
				selContent: selObj.toString().replace(/[\n]/g, " "),
				context: this.questionContext,
				data: this.data
			}
			this.$bus.$emit("addAction", {
				type: "explainSend",
				selectedContext: this.selectedContext,
				question: this.questionContext,
				time: new Date().toLocaleString()
			})
			this.axios.post("/api/explainCombine", args).then((response) => {
				this.explanationContext = response.data
				this.$bus.$emit("addAction", {
					type: "receiveExplain",
					response: response.data,
					time: new Date().toLocaleString()
				})
			})
		},
		viewLink() {
			this.isLinkExpanded = !this.isLinkExpanded
			if (this.isLinkExpanded) {
				$(this.$refs.subStepSVGContainer).removeClass("hidden")
				$(this.$refs.subStepCollectionContainer).addClass("hidden")
				$(this.$refs.isNotExpandedIcon).addClass("hidden")
				$(this.$refs.isExpandedIcon).removeClass("hidden")
				this.drawSubStepSVG()
				this.$bus.$emit("addAction", {
					type: "viewLink",
					time: new Date().toLocaleString()
				})
			} else {
				$(this.$refs.subStepSVGContainer).addClass("hidden")
				$(this.$refs.subStepCollectionContainer).removeClass("hidden")
				$(this.$refs.isNotExpandedIcon).removeClass("hidden")
				$(this.$refs.isExpandedIcon).addClass("hidden")
				this.$bus.$emit("addAction", {
					type: "viewSubStep",
					time: new Date().toLocaleString()
				})
			}
		},
		regenerate() {
			this.loading = true
			this.$bus.$emit("addAction", {
				type: "regenerateSubStep",
				new_data: JSON.parse(
					JSON.stringify({
						question: this.data.question,
						evidence: this.data.evidence,
						SQL: this.data.SQLFormatted,
						COT: this.data.COT
					})
				),
				original_data: JSON.parse(
					JSON.stringify({
						question: this.original_data.question,
						evidence: this.original_data.evidence,
						SQL: this.original_data.SQLFormatted,
						COT: this.original_data.COT,
						dbSchema: this.original_data.dbSchema
					})
				),
				time: new Date().toLocaleString()
			})
			this.axios
				.post("/api/modidyStep2V1", {
					original_data: this.original_data,
					new_data: this.data
				})
				.then((response) => {
					this.original_data = JSON.parse(JSON.stringify(response.data))
					this.data = JSON.parse(JSON.stringify(response.data))
					this.$bus.$emit("addAction", {
						type: "receiveRegenerateSubStep",
						time: new Date().toLocaleString()
					})
this.getSQLCodeTree()
					this.loading = false
				})
		},
		executeSQL(event, args) {
			if (!this.$refs[args.refNameTable][0]) {
				$(this.$refs[args.refNameTable]).empty()
			} else {
				$(this.$refs[args.refNameTable][0]).empty()
			}
			let args_sent = { sql: args.sql }
			this.$bus.$emit("addAction", {
				type: "executeSQL",
				sql: args.sql,
				id: args.id, //-1 for SQL, others for subStep
				time: new Date().toLocaleString()
			})
			this.axios.post("/api/executeSQL", args_sent).then((response) => {
				if ("error" in response.data) {
					this.$message.error(response.data.error)
					return
				}
				this.axios.post("api/formatSQL_V1", args_sent).then((response) => {
					if (args.isSub || args.isSubSVG) {
						this.data.COT[+args.id - 1]["subSQLFormatted"] = response.data.sql
					} else {
						this.data.SQLFormatted = response.data.sql
					}
					this.SQLCodeBlockGenerate(args.refName, this.SQLCodeTrans(response.data.sql), {
						isSub: args.isSub,
						isSubSVG: args.isSubSVG ? args.isSubSVG : false,
						id: args.id
					})
				})
				let column_names = response.data["column_names"]
				let data = []
				let data_ver = {}
				for (let i = 0; i < response.data.table.length; i++) {
					let iter = {}
					let flag = false
					for (let j = 0; j < column_names.length; j++) {
						if (i == 0) {
							data_ver[column_names[j]] = []
						}
						data_ver[column_names[j]].push(response.data.table[i][j])
						if (response.data.table[i][j] == null) {
							flag = true
							break
						}
						iter[column_names[j]] = response.data.table[i][j]
					}
					if (flag) {
						continue
					}
					data.push(iter)
				}

				const $table = $("<table></table>")
					.addClass("table-responsive table-bordered")
					.attr("style", `max-height: 700px;'overflow':'auto'`)

				let $thead = $("<thead><tr></tr></thead>")
				column_names.forEach((e) => {
					$thead.append($("<th></th>").text(e).attr("scope", "col").attr("style", "padding: 0.5em;"))
				})
				let tbody = $("<tbody></tbody>")
				data.forEach((d) => {
					let $tr = $("<tr></tr>")
					column_names.forEach((e) => {
						$tr.append($("<td></td>").text(d[e]))
					})
					tbody.append($tr)
				})

				$table.append($thead)
				$table.append(tbody)

				if (!this.$refs[args.refNameTable][0]) {
					$(this.$refs[args.refNameTable]).removeClass("hidden")
					$(this.$refs[args.refNameTable]).append($table)
				} else {
					$(this.$refs[args.refNameTable][0]).removeClass("hidden")
					$(this.$refs[args.refNameTable][0]).append($table)
				}
			})
		},
		expandOrHideSubStep(event, args) {
			let id = args.id
			let index = args.index
			this.data.COT[index].isExpanded = !this.data.COT[index].isExpanded
			if (this.data.COT[index].isExpanded) {
				this.$bus.$emit("addAction", {
					type: "expandSubStep",
					subStepID: id,
					time: new Date().toLocaleString()
				})
				$(this.$refs[`subStepContainer_${id}`][0]).removeClass("hidden")
				$(this.$refs[`ExpandSubStep_${id}`][0]).addClass("btn-primary")
				//$(this.$refs[`ExpandSubStep_${id}`][0]).removeClass("btn-light")
				$(this.$refs[`ExpandSubStep_${id}`][0]).removeClass("btn-outline-primary")
				$(this.$refs[`ExpandSubStep_${id}`][0]).html("Hide&nbsp;<i class='el-icon-caret-top'></i>")
			} else {
				this.$bus.$emit("addAction", {
					type: "hideSubStep",
					subStepID: id,
					time: new Date().toLocaleString()
				})
				$(this.$refs[`subStepContainer_${id}`][0]).addClass("hidden")
				$(this.$refs[`ExpandSubStep_${id}`][0]).removeClass("btn-primary")
				//$(this.$refs[`ExpandSubStep_${id}`][0]).addClass("btn-light")
				$(this.$refs[`ExpandSubStep_${id}`][0]).addClass("btn-outline-primary")

				$(this.$refs[`ExpandSubStep_${id}`][0]).html("Expand&nbsp;<i class='el-icon-caret-bottom'></i>")
			}
		},
		handleClickOutside(event, id) {},
		handleClickInsideStepDescription(event, id) {
			$(this.$refs[`stepDescriptionInputContainer_${id}`][0]).removeClass("hidden")
			$(this.$refs[`stepDescription_${id}`][0]).addClass("hidden")
			//this.handleClickOutsideSubSQL(event, id)
		},
		handleClickOutsideStepDescription(event, id) {
			$(this.$refs[`stepDescriptionInputContainer_${id}`][0]).addClass("hidden")
			$(this.$refs[`stepDescription_${id}`][0]).removeClass("hidden")
		},
		handleClickInsideSubSQL(event, id) {
			$(this.$refs[`subSQLInputContainer_${id}`][0]).removeClass("hidden")
			$(this.$refs[`subSQL_${id}`][0]).addClass("hidden")
			//this.handleClickOutsideStepDescription(event, id)
		},
		handleClickOutsideSubSQL(event, id) {
			$(this.$refs[`subSQLInputContainer_${id}`][0]).addClass("hidden")
			$(this.$refs[`subSQL_${id}`][0]).removeClass("hidden")
		},

		handleClickInsideSQL(event) {
			$(this.$refs.SQLContainer).addClass("hidden")
			$(this.$refs.SQLInputContainer).removeClass("hidden")
		},
		handleClickOutsideSQL(event) {
			$(this.$refs.SQLContainer).removeClass("hidden")
			$(this.$refs.SQLInputContainer).addClass("hidden")
		},
		expandOrHideSubStepSVG() {
			if (this.selectedSubStepID == -1) {
				return
			}
			this.isselectedSubStepExpanded = !this.isselectedSubStepExpanded
			if (this.isselectedSubStepExpanded) {
				this.$bus.$emit("addAction", {
					type: "expandSubStepSVG",
					subStepID: this.selectedSubStepID,
					time: new Date().toLocaleString()
				})
				$(this.$refs[`subStepDetailSVGContainer`]).removeClass("hidden")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).addClass("btn-primary")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).removeClass("btn-light")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).removeClass("btn-outline-primary")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).html("Hide&nbsp;<i class='el-icon-caret-top'></i>")
			} else {
				this.$bus.$emit("addAction", {
					type: "hideSubStepSVG",
					subStepID: this.selectedSubStepID,
					time: new Date().toLocaleString()
				})
				$(this.$refs[`subStepDetailSVGContainer`]).addClass("hidden")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).removeClass("btn-primary")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).addClass("btn-light")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).addClass("btn-outline-primary")
				$(this.$refs[`ExpandSubStepSVGTooltip`]).html("Expand&nbsp;<i class='el-icon-caret-bottom'></i>")
			}
		},
		handleClickOutsideStepDescriptionSVG() {
			$(this.$refs[`stepDescriptionInputSVGContainer`]).addClass("hidden")
			$(this.$refs[`stepDescriptionSVG`]).removeClass("hidden")
		},
		handleClickInsideStepDescriptionSVG() {
			$(this.$refs[`stepDescriptionInputSVGContainer`]).removeClass("hidden")
			$(this.$refs[`stepDescriptionSVG`]).addClass("hidden")
			this.handleClickOutsideSubSQLSVG()
		},
		handleClickOutsideSubSQLSVG() {
			$(this.$refs[`subSQLInputContainer`]).addClass("hidden")
			$(this.$refs[`subSQLSVG`]).removeClass("hidden")
		},
		handleClickInsideSubSQLSVG() {
			$(this.$refs[`subSQLInputContainer`]).removeClass("hidden")
			$(this.$refs[`subSQLSVG`]).addClass("hidden")
			this.handleClickOutsideStepDescriptionSVG()
		},
		generateCOTPair() {
			let visitedList = {}
			for (let i = 0; i < this.data.COT.length; i++) {
				visitedList[i] = false
			}
			let COTQueryPair = {}
			for (let i = 0; i < this.data.COT.length; i++) {
				COTQueryPair[i] = 0
			}
			let dfsQuery = (stepindex, codeTreeindex, sql) => {
				if (this.SQLCodeTree[codeTreeindex].SQL.includes(sql)) {
					COTQueryPair[stepindex] = codeTreeindex
					for (let i = 0; i < this.SQLCodeTree[codeTreeindex].childrenQuerry.length; i++) {
						dfsQuery(stepindex, this.SQLCodeTree[codeTreeindex].childrenQuerry[i], sql)
					}
				} else {
					return
				}
			}
			let bfs = (stepIndex, parentQueryID) => {
				let sql = this.data.COT[stepIndex].coreSQL
				let queryID = parentQueryID
				COTQueryPair[stepIndex] = queryID
				dfsQuery(stepIndex, queryID, sql)
				queryID = COTQueryPair[stepIndex]
				visitedList[stepIndex] = true
				if (this.data.COT[stepIndex].prerequisiteQuestion.length == 0) {
					return
				}
				for (let i = 0; i < this.data.COT[stepIndex].prerequisiteQuestion.length; i++) {
					let prevID = this.data.COT[stepIndex].prerequisiteQuestion[i] - 1
					if (true) {
						bfs(prevID, queryID)
					}
				}
			}
			bfs(this.data.COT.length - 1, 0)

			return COTQueryPair
		},
		executeSQLSVG() {},
		getSQLCodeTree() {
			let args = { sql: this.data.SQL }
			this.axios.post("/api/getSQLCodeTreeV1", args).then((response) => {
				this.SQLCodeTree = response.data.expressionList
				this.SQLExpressionList = this.SQLCodeTrans()
				this.COTQueryPair = this.generateCOTPair()
				this.SQLCodeBlockGenerate("SQLContainer", this.SQLExpressionList, {
					isSub: false
				})
				for (let i = 0; i < this.data.COT.length; i++) {
					let SQLList = this.SQLCodeTrans(this.data.COT[i].subSQLFormatted)
					this.SQLCodeBlockGenerate(`subSQL_${this.data.COT[i].stepID}`, SQLList, {
						id: this.data.COT[i].stepID,
						isSub: true
					})
				}
			})
		},
		SQLCodeTrans(SQL_input = "") {
			if (SQL_input == "" || !SQL_input) {
				SQL_input = this.data.SQLFormatted
			}
			let sqlList = SQL_input.split("\n")
			let sqlDict = []
			let countLeadingSpaces = (str) => {
				const match = str.match(/^ */)
				return match ? match[0].length : 0
			}
			let removeLeadingSpaces = (str) => {
				return str.trimStart()
			}
			let dictToString = (start, end) => {
				let res = []
				for (let i = start; i < end; i++) {
					res.push(sqlDict[i].sql)
				}
				res = res.join("")
				return res
			}

			sqlList.forEach((e) => {
				sqlDict.push({
					leadingSpaces: countLeadingSpaces(e),
					sql: removeLeadingSpaces(e),
					queryBelong: [],
					queryParent: 0
				})
			})
			let bfs = (index) => {
				let SQL = this.SQLCodeTree[index].SQL
				SQL = SQL.replace(/\s+/g, "")
				let start = 0
				let end = 0
				for (let i = 0; i < sqlDict.length; i++) {
					for (let j = i + 1; j <= sqlDict.length; j++) {
						if (dictToString(i, j).replace(/\s+/g, "") == SQL) {
							start = i
							end = j
							break
						}
					}
				}
				for (let k = start; k < end; k++) {
					sqlDict[k].queryBelong.push(index)
					sqlDict[k].queryParent = index
				}
				for (let i = 0; i < this.SQLCodeTree[index].childrenQuerry.length; i++) {
					bfs(this.SQLCodeTree[index].childrenQuerry[i])
				}
			}

			bfs(0)
			for (let i = 0; i < sqlDict.length; i++) {
				sqlDict[i]["indentSpaces"] = d3.min(
					d3.filter(sqlDict, (d) => sqlDict[i].queryParent == d.queryParent),
					(d) => d.leadingSpaces
				)
				sqlDict[i]["paddingRightWidth"] =
					d3.max(
						d3.filter(sqlDict, (d) => d.queryBelong.indexOf(sqlDict[i].queryParent) != -1),
						(d) => d.leadingSpaces + d.sql.length
					) - sqlDict[i].indentSpaces
			}
			return sqlDict
		},

		hoverCodeBlockIn(queryID) {
			this.$bus.$emit("addAction", {
				type: "hoverInCodeBlock",
				queryID: queryID,
				time: new Date().toLocaleString()
			})
			$(`.subStepHead`).find("p").removeClass("hoverHighlight")
			for (let k in this.COTQueryPair) {
				let v = this.COTQueryPair[k]
				if (v == queryID) {
					$(`.subStepHead_${this.data.COT[k].stepID}`).find("h5").addClass("hoverHighlight")
				} else {
				}
			}
		},

		hoverCodeBlockOut(queryID) {
			this.$bus.$emit("addAction", {
				type: "hoverOutCodeBlock",
				queryID: queryID,
				time: new Date().toLocaleString()
			})
			for (let k in this.COTQueryPair) {
				let v = this.COTQueryPair[k]
				if (v == queryID) {
					$(`.subStepHead_${this.data.COT[k].stepID}`).find("h5").removeClass("hoverHighlight")
				} else {
				}
			}
		},
		SQLCodeBlockGenerate(refName, SQLExpressionList, args) {
			let root = $("<div></div>").css({ "margin-left": "1em", display: "block" }).addClass("sqlLineCode")

			let left = []
			let top = []
			let width = []
			let height = []
			let node = []
			node.push(root)
			let index = 0
			let node_stack = []
			node_stack.push(0)
			let queryBelong = SQLExpressionList[0].queryBelong

			let generateCodeBlock = (sqlList) => {
				let i = 0
				let queryBelong = sqlList[0].queryBelong
				let codeBlock = $("<div></div>")
					.css({
						"margin-left": `${sqlList[0].indentSpaces}em`,
						width: `${
							(sqlList[0].paddingRightWidth - sqlList[0].indentSpaces) / 2 +
							7 -
							sqlList[0].queryBelong.length
						}em`
					})
					.addClass("sqlLineCode")
					.addClass(args.isSub || args.isSubSVG ? "" : `Query-level-1 `)
					.addClass(`Query-parent-${sqlList[0].queryParent}`)

				while (i < sqlList.length) {
					let iter = sqlList[i]
					let flag = true
					if (iter.queryBelong.length != queryBelong.length) {
						flag = false
					} else {
						for (let j = 0; j < iter.queryBelong.length; j++) {
							if (iter.queryBelong[j] != queryBelong[j]) {
								flag = false
								break
							}
						}
					}
					if (flag == false) {
						let j = i + 1
						let flag_j = true
						for (; j < sqlList.length; j++) {
							let iter_j = sqlList[j]

							for (let k = 0; k < iter.queryBelong.length; k++) {
								if (iter_j.queryBelong[k] != iter.queryBelong[k]) {
									flag_j = false
									break
								}
							}
							if (flag_j == false) {
								break
							}
						}

						let sqlList_j = sqlList.slice(i, j)
						i = j
						let temp = generateCodeBlock(sqlList_j)
						codeBlock.append(temp)
					} else {
						let temp = $("<div></div>").append(
							$("<code></code>")
								.css({
									"text-indent": iter.leadingSpaces - iter.indentSpaces + "em",
									width:
										iter.paddingRightWidth +
										iter.sql.length +
										iter.leadingSpaces -
										iter.indentSpaces +
										"em",
									color: "white"
								})
								.addClass("sqlLineCode")
								.text(iter.sql)
								.hover(
									() => {
										if (!args.isSub) {
											this.hoverCodeBlockIn(sqlList[0].queryParent)
										}
									},
									() => {
										if (!args.isSub) {
											this.hoverCodeBlockOut(sqlList[0].queryParent)
										}
									}
								)
						)
						codeBlock.append(temp)
						i += 1
					}
				}
				return codeBlock
			}
			if (!this.$refs[refName][0]) {
				$(this.$refs[refName]).empty()
				$(this.$refs[refName]).removeClass("hidden")
				$(this.$refs[refName]).append(generateCodeBlock(SQLExpressionList))
			} else {
				$(this.$refs[refName][0]).empty()
				$(this.$refs[refName][0]).removeClass("hidden")
				$(this.$refs[refName][0]).append(generateCodeBlock(SQLExpressionList))
			}
			if (args.isSub) {
				this.handleClickOutsideSubSQL(null, args.id)
			} else if (args.isSubSVG) {
				this.handleClickOutsideSubSQLSVG()
			} else {
				this.handleClickOutsideSQL(null)
			}
		},
		drawSubStepSVG() {
			let that = this
			let arrowTransform = (points) => {
				const [[x1, y1], [x2, y2]] = points.slice(-2)
				const angle = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI + 90
				return `translate(${x2}, ${y2}) rotate(${angle})`
			}
			let svg = d3.select(`#subStepSVG_${+this.data.id}`)
			svg.selectAll("g").remove()
			let width = $(`#subStepSVGColContainer_${+this.data.id}`).innerWidth()
			let height = $(`#subStepSVGColContainer_${+this.data.id}`).innerHeight()
			/* 		if (height < width) {
				let temp = width
				width = height
				height = temp
			} */
			svg.attr("width", width).attr("height", height)

			let data = []
			let nodeObj = []
			let edgeObj = []
			let points_coll = []
			this.data.COT.forEach((d) => {
				let pIds = []
				d.prerequisiteQuestion.forEach((q) => {
					pIds.push(String(q))
				})
				data.push({ id: String(d.stepID), parentIds: pIds })
			})
			const dag = d3dag.graphStratify()(data)

			const layout = d3dag.sugiyama()
			layout(dag)
			for (const node of dag.nodes()) {
				nodeObj.push({
					id: +node.data.id,
					x: node.x,
					y: node.y,
					parentIds: this.data.COT[+node.data.id - 1].prerequisiteQuestion
				})
				points_coll.push({ x: node.x, y: node.y })
			}
			for (const { points } of dag.links()) {
				points.forEach((p) => {
					points_coll.push({ x: p[0], y: p[1] })
				})
			}
			let x_range = d3.extent(points_coll, (d) => d.x)
			let y_range = d3.extent(points_coll, (d) => d.y)
			x_range[0] = x_range[0] - 1
			x_range[1] = x_range[1] + 1
			y_range[0] = y_range[0] - 1
			y_range[1] = y_range[1] + 1
			let x_scale = d3.scaleLinear().domain(x_range).range([0, width])
			let y_scale = d3.scaleLinear().domain(y_range).range([0, height])
			let edge_g = svg.append("g")
			edge_g
				.selectAll(".edge")
				.data(dag.links())
				.join("path")
				.attr("class", "edge")
				.attr("d", ({ points }) => {
					const [start, ...rest] = points
					return `M${[x_scale(start[0]), y_scale(start[1])]} ${rest
						.map((p) => `L${[x_scale(p[0]), y_scale(p[1])]}`)
						.join("")}`
				})
				.attr("stroke-width", 1)
				.attr("stroke", "black")
				.attr("fill", "none")
				.attr("marker-end", "url(#arrow)")
			let node_g = svg.append("g")
			node_g
				.selectAll(".node")
				.data(nodeObj)
				.join("g")
				.attr("class", "node")
				.attr("transform", (d) => `translate(${x_scale(d.x)}, ${y_scale(d.y)})`)
				.each(function (d) {
					$(this).tooltip({
						title: `Step${d.id}: ${that.data.COT[d.id - 1].subStep}`,
						placement: "top",
						trigger: "hover",
						container: "body"
					})
					d3.select(this)
						.append("circle")
						.attr("class", "nodeCircle")
						.attr("r", 20)
						.attr("fill", "white")
						.attr("stroke-width", 1)
						.attr("stroke", "black")
					d3.select(this)
						.append("text")
						.text(d.id)
						.attr("text-anchor", "middle")
						.attr("alignment-baseline", "middle")
				})
				.on("click", function (event, d) {
					/* $(that.$refs.subStepSvgTooltip).css({
						top:
							$(this).offset().top +
							that.$refs.subStepCollectionContainer.getBoundingClientRect().top -
							that.$refs.subStepSVGContainer.getBoundingClientRect().top +
							"px",
						left:
							$(this).offset().left +
							that.$refs.subStepCollectionContainer.getBoundingClientRect().left -
							that.$refs.subStepSVGContainer.getBoundingClientRect().left +
							"px"
					}) */

					node_g.selectAll("text").attr("fill", "black")
					node_g
						.selectAll(".nodeCircle")
						.attr("stroke-width", 1)
						.attr("fill", "#ffffff")
						.attr("stroke", "black")
					d3.select(this)
						.select("circle")
						.attr("stroke", "#007bff")
						.attr("fill", "#007bff")
						.attr("stroke-width", 2)
					d3.select(this).select("text").attr("fill", "#ffffff")
					that.selectedSubStepID = d.id
					that.selectedSubStep = that.data.COT[d.id - 1]
					that.isselectedSubStepExpanded = false
					let SQLlist = that.SQLCodeTrans(that.selectedSubStep.subSQLFormatted)
					that.SQLCodeBlockGenerate("subSQLSVG", SQLlist, {
						isSub: false,
						isSubSVG: true
					})
					$(that.$refs.subStepSvgTooltip).removeClass("hidden")
				})

			let defs_g = svg.append("defs")
			let markers = defs_g
				.append("marker")
				.attr("class", "arrow")
				.attr("id", "arrow")
				.attr("viewBox", "0 -5 10 10")
				.attr("refX", 30)
				.attr("refY", -0)
				.attr("markerWidth", 10)
				.attr("markerHeight", 20)
				.attr("fill", (d) => "#999")
				.attr("orient", "auto")
				.append("path")
				.attr("d", "M0,-5L10,0L0,5")
		}

		/*     getDAGPosition() {
      let edge = []
      this.data.COT.forEach((s) => {
        s.prerequisiteQuestion.forEach((q) => {
          edge.push([q, s.stepID])
        })
      })
      let args = { edgeList: edge }
      this.axios.post("/api/getDAGPosition", args).then((response) => {
        console.log(response.data)
        this.DAGPosition = response.data

        this.createDAGPosition()
      })
    },
    createDAGPosition() {
      console.log(this.$refs.subStepDag)
      let root = $(this.$refs.subStepDag)
      let domCollection = []
      this.data.COT.forEach((d) => {
        let container = $(`<div></div>`).text(`${d.stepID}. ${d.subStep}`)
        domCollection.push(container)
      })
      console.log(this.DAGPosition)
      let y_max = d3.max(Object.values(this.DAGPosition), (d) => +d[1])
      let x_max = d3.max(Object.values(this.DAGPosition), (d) => +d[0])
      console.log(y_max, x_max)
      for (let i = 0; i < y_max + 1; i++) {
        let row = $(`<div></div>`).css({ display: "flex" })
        for (let j = 0; j < x_max + 1; j++) {
          let container = $(`<div></div>`).css({
            width: "100px",
            height: "100px",
            border: "1px solid black"
          })
          let index = -1

          for (let key in this.DAGPosition) {
            if (this.DAGPosition[key][0] == j && this.DAGPosition[key][1] == i) {
              index = key
              break
            }
          }
          if (index != -1) {
            container.append(domCollection[index])
          }
          row.append(container)
        }
        root.append(row)
      }
    } */
	},

	mounted() {
		this.original_data = JSON.parse(JSON.stringify(this.dataInput))
		this.data = JSON.parse(JSON.stringify(this.dataInput))
		this.subStepStatus = []
		if (this.data.error == "connection error") {
			return
		}
		for (let i = 0; i < this.data.COT ? this.data.COT.length : 0; i++) {
			this.data.COT[i]["isExpanded"] = false
			this.data.COT[i]["buttonText"] = "Expand"
			this.executeResult[this.data.COT[i].stepID] = {
				column_names: [],
				table: []
			}
		}

		let that = this

		this.$nextTick(() => {
			if (this.data.error == "connection error") {
				this.data.SQLFormatted = ""
			}
			this.getSQLCodeTree()
			document.addEventListener("selectionchange", function () {
				//$(that.$refs.explainModule).addClass("hidden")
				if (that.data.error == "connection error") {
					return
				}
				return
				var selection = window.getSelection()
				if (selection.rangeCount > 0) {
					var range = selection.getRangeAt(0)
					var rect = range.getBoundingClientRect()

					var $parent = $(that.$el)
					var anchorNode = selection.anchorNode
					var isWithinParent = $(anchorNode).closest(that.$el).length > 0
					if (!isWithinParent) return
					var parentRect = $parent[0].getBoundingClientRect()

					var relativeX = rect.left - parentRect.left
					var relativeY = rect.top - parentRect.top

					if (selection.toString().length > 0) {
						$(that.$refs.explainModuleTrigger).css({
							top: relativeY - 30 + "px",
							left: relativeX - 15 + "px"
						})
						$(that.$refs.explainModuleTrigger).removeClass("hidden")
						$(that.$refs.explainModule).addClass("hidden")
					} else {
						$(that.$refs.explainModuleTrigger).addClass("hidden")
					}
				}
			})
		})
		//this.getSQLCodeTree()
	}
}
</script>
<style>
#QueryGenerationModuleContainer {
	width: 1100px;
	position: relative;
	display: block;
	.hidden {
		display: none;
	}
	.stepDescriptionContainer {
		padding: 10px;
	}
	.subSQLContainer {
		padding: 10px;
	}
	#SQLContainer {
	}
	.sqlLine {
		margin: 0;
	}
	.sqlLineCode {
		margin: 1px;
		color: black;
		display: block;
		height: auto;
	}
	.Query-level-1 {
		background-color: rgba(75, 150, 237, 0.2);
	}
	.Query-level-2 {
		background-color: rgba(75, 150, 237, 0.2);
	}
	.Query-level-3 {
		background-color: rgba(75, 150, 237, 0.2);
	}
	.Query-level-4 {
		background-color: rgba(75, 150, 237, 0.2);
	}
	.SQLCode {
		width: auto;
		padding-left: 1em;
		padding-top: 1em;
		padding-bottom: 15px;
		background-color: black;
		color: white;
		border-radius: 0 0 5px 5px;
	}
	.selectSubStep {
	}
	.subStepSVGToolTip {
		background-color: #f3f3f3;
		/* 		display: absolute;
		position: fixed; */
	}
	.subStepSvg {
	}
	.explainTrigger {
		position: absolute;
		top: 0%;
		left: 0%;
		border-radius: 50%;
		align-items: center;
		justify-content: center;
	}
	.explainModule {
		position: absolute;
		border: 1px solid #000000;
		box-shadow: 10px 5px 5px grey;
		background-color: white;
		z-index: 999;
		overflow: auto;
		width: 800px;
		height: 400px;
	}
	.hoverHighlight {
		background-color: lightskyblue;
	}
	.subStep {
		width: auto;
	}
	.btn {
		text-align: center;
		padding-left: 16px;
		padding-right: 16px;
	}
}
</style>
