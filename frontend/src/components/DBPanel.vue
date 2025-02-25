<template>
	<el-container id="DBPanelContainer">
		<!--     <div id="DBTooltip">
      <el-table :data="DBTableGridData">
        <el-table-column prop="name" label="name" width="180">
        </el-table-column>
      </el-table>
    </div> -->
		<el-header
			id="DBPanelStatusDiv"
			style="font-weight: 700 !important; background-color: #d7d7d7;height: 100px;padding-top: 10px">
					<img
				style="width: 18px; height: 18px"
				src="@/assets/image/cCircle.png"
				alt="..."
				:fit="`fill`" /> &nbsp; &nbsp;DB CONNECTION
		</el-header>
		<el-main id="DBSelectMain">
			<el-row
				class="DBSelectView"
				style="font-size: 20px">
				<el-select
					class="DBSelectBar"
					v-model="selectedDB"
					@change="selectDB(selectedDB)">
					<el-option
						v-for="item in DBList"
						:key="item"
						:label="item"
						:value="item"></el-option>
				</el-select>
			</el-row>
			<el-row class="DBSelectView">
				<el-input
					class="DBSelectBar"
					placeholder="Please input key words">
					<img
						slot="suffix"
						style="width: 32px; height: 32px; margin-top: 1px; margin-right: -2px; vertical-align: middle"
						src="@/assets/image/filter.png"
						alt="..."
						:fit="`fill`" />
				</el-input>
			</el-row>
			<el-row :key="`selectedTable_${selectedDB}`">
				<div class="row dbPanelRowButton">
					<button
						id="selectedTableInfoButton"
						type="button"
						class="DBRowButton btn btn-outline-secondary"
						data-toggle="collapse"
						href="#selectedDBInfo"
						@click="expandOrHiddenIcon(`selectedTableInfoIcon`, `selectedDBInfo`)"
						style="font-size: 24px">
						<i
							id="selectedTableInfoIcon"
							class="el-icon-arrow-right iconTableInfo"
							ref="iconTableInfo"></i>
						SELECTED TABLES&nbsp;({{ DBSelectedTable.length? DBSelectedTable.length: 0 }})
					</button>
				</div>
				<div
					id="selectedDBInfo"
					class="collapse row container">
					<div
						v-for="table_name in DBSelectedTable"
						:key="`selectedTable_${table_name}`"
						class="container"
						data-toggle="collapse"
						:href="`#selectedTable_${table_name}`"
						@click="
							expandOrHiddenIcon(`selectedTable_${table_name}_InfoIcon`, `selectedTable_${table_name}`)
						">
						<div
							class="row table_row"
							style="display: block; text-align: left">
							<i
								:id="`selectedTable_${table_name}_InfoIcon`"
								class="el-icon-arrow-right iconTableInfo"
								ref="iconTableInfo"></i>
							<img
								style="width: 36px; height: 36px"
								src="@/assets/image/table.png"
								alt="..."
								:fit="`fill`" />
							<span>{{ table_name }}</span>
							<button
								class="btn btn-light"
								style="float: right"
								@click.stop="modifySelectTable($event, { table_name: table_name })">
								<i class="el-icon-delete"></i>
							</button>
						</div>
						<div
							class="row collapse column_container"
							:id="`selectedTable_${table_name}`">
							<ul>
								<li
									v-for="column_name in DBInfo['columns'][table_name]
										? DBInfo['columns'][table_name]['name']
										: []"
									class="row">
									{{ column_name }}
								</li>
							</ul>
						</div>
					</div>
				</div>
			</el-row>
			<el-row :key="`Table_${selectedDB}`">
				<div class="row dbPanelRowButton">
					<button
						id="TableInfoButton"
						type="button"
						class="DBRowButton btn btn-outline-secondary"
						data-toggle="collapse"
						href="#DBInfo"
						@click="expandOrHiddenIcon(`TableInfoIcon`, `DBInfo`)">
						<i
							:id="`TableInfoIcon`"
							class="el-icon-arrow-right iconTableInfo"
							ref="iconTableInfo"></i>
						TABLES&nbsp;({{ DBInfo.table_names.length }})
					</button>
				</div>
				<div
					id="DBInfo"
					class="collapse row container">
					<div
						v-for="table_name in DBInfo.table_names"
						class="container"
						data-toggle="collapse"
						:href="`#DBTable_${table_name}`"
						@click="
							expandOrHiddenIcon(`DBTable_${table_name}_InfoIcon`, `DBTable_${table_name}`, {
								selectTable: table_name
							})
						">
						<div
							class="row table_row"
							style="display: block; text-align: left">
							<i
								:id="`DBTable_${table_name}_InfoIcon`"
								class="el-icon-arrow-right iconTableInfo"
								ref="iconTableInfo"></i>
							<img
								style="width: 36px; height: 36px"
								src="@/assets/image/table.png"
								alt="..."
								:fit="`fill`" />
							<span>
								{{ table_name }}
							</span>
							<button
								@click.stop="modifySelectTable($event, { table_name: table_name })"
								class="btn btn-light"
								style="float: right">
								<i class="el-icon-plus"></i>
							</button>
						</div>
						<div
							class="row collapse column_container"
							:id="`DBTable_${table_name}`">
							<ul>
								<li
									v-for="column_name in DBInfo['columns'][table_name]
										? DBInfo['columns'][table_name]['name']
										: []"
									class="row">
									{{ column_name }}
								</li>
							</ul>
						</div>
					</div>
				</div>
			</el-row>
			<el-row class="dbPanelRowButton">
				<button
					@click="expandDBDiv"
					id="DBVisDivButton"
					type="button"
					class="DBRowButton btn btn-outline-secondary">
					<i
						class="el-icon-arrow-right iconTableInfo"
						ref="DBVisDivButton"></i>
					DB STRUCTURE GRAPH
				</button>
				<el-container
					id="DBVisDiv"
					ref="DBVisDiv"
					:class="['hiddenVisibilityComponent']">
					<svg class="DBVisSvg"></svg>
				</el-container>
			</el-row>
		</el-main>
	</el-container>
</template>

<script>
import * as d3 from "d3"
import * as joint from "jointjs"

class DBVisModule {
	constructor(
		divID = "DBVisDiv",
		DBdata = { columns: {}, fk_pairs: [], table_names: [] },
		width = 510,
		height = 600,
		vueModule = null
	) {
		this.DBdata = DBdata
		this.DBVisDivID = divID
		this.DBVisDiv = d3.select("#" + this.DBVisDivID)
		this.width = width
		this.height = height
		this.DBVisSvg = this.DBVisDiv.select(".DBVisSvg")
			.attr("class", "DBVisSvg")
			.attr("width", width)
			.attr("height", height)
		this.linkG = this.DBVisSvg.append("g").attr("id", "DBlinkG")
		this.nodeG = this.DBVisSvg.append("g").attr("id", "DBnodeG")
		this.textG = this.DBVisSvg.append("g").attr("id", "DBtextG")
		this.DBdataConverted = this.dataConvert()
		this.node = this.DBdataConverted["nodeList"]
		this.link = this.DBdataConverted["linkList"]
		this.force = this.initForce()
		this.width = width
		this.height = height
		this.node_mode = 0 //0:table 1:column
		this.DBTableGridData = []
		this.DBTreeData = []
		this.vueModule = vueModule
	}
	initVis() {
		this.DBVisDiv = d3.select("#" + this.DBVisDivID)
		this.DBVisSvg = this.DBVisDiv.select(".DBVisSvg")
			.attr("class", "DBVisSvg")
			.attr("width", this.width)
			.attr("height", this.height)
		this.linkG = this.DBVisSvg.append("g").attr("id", "DBlinkG")
		this.nodeG = this.DBVisSvg.append("g").attr("id", "DBnodeG")
		this.textG = this.DBVisSvg.append("g").attr("id", "DBtextG")
	}
	initForce() {
		return d3.forceSimulation()
	}
	initVueModule(vueModule) {
		this.vueModule = vueModule
	}
	updateForce() {
		console.log(this.node)
		console.log(this.link)
		this.force
			.nodes(this.node)
			.force("charge", d3.forceManyBody().strength(-1000))
			.force("center", d3.forceCenter(this.width / 2, this.height / 2))
			.force("link", d3.forceLink(this.link).strength(1).distance(300))
	}
	dataConvert() {
		let nodeList = []
		/*
    {
      id: 0,//index
      name:"",//name
      type: "",//table or column
    }
    */
		let linkList = []
		/*
    {
      source: 0,//index
      source_name: "",//name
      target: 1,//index
      target_name: "",//name
      type: "",//"affiliation" "fk"
    }
    */
		let index_node_cnt = 0
		let index_link_cnt = 0
		let node_index = {}

		for (let i = 0; i < this.DBdata.table_names.length; i++) {
			let table_name = this.DBdata.table_names[i]
			nodeList.push({
				id: index_node_cnt,
				name: table_name,
				type: "table",
				columns: Object.values(this.DBdata.columns[table_name]["name"])
			})
			node_index[table_name] = index_node_cnt
			index_node_cnt++
			if (this.node_mode == 1) {
				for (let j in this.DBdata.columns[table_name]["name"]) {
					let column_name = this.DBdata.columns[table_name]["name"][j]
					nodeList.push({
						id: index_node_cnt,
						name: column_name,
						type: "column"
					})
					node_index[`${table_name}_${column_name}`] = index_node_cnt
					index_node_cnt++
					linkList.push({
						id: index_link_cnt,
						source: node_index[table_name],
						source_table: table_name,
						source_name: table_name,
						target: node_index[`${table_name}_${column_name}`],
						target_table: table_name,
						target_name: column_name,
						type: "affiliation"
					})
					index_link_cnt++
				}
			}
		}
		for (let i = 0; i < this.DBdata.fk_pairs.length; i++) {
			let fk_pairs_list = this.DBdata.fk_pairs[i]
			for (let j = 0; j < fk_pairs_list.length; j++) {
				for (let k = j; k < fk_pairs_list.length; k++) {
					if (j != k) {
						linkList.push({
							id: index_link_cnt,
							source: node_index[
								this.node_mode
									? `${fk_pairs_list[j]["table"]}_${fk_pairs_list[j]["column"]}`
									: fk_pairs_list[j]["table"]
							],
							source_table: fk_pairs_list[j]["table"],
							source_column: fk_pairs_list[j]["column"],

							source_name: this.node_mode ? fk_pairs_list[j]["column"] : fk_pairs_list[j]["table"],
							target: this.node_mode
								? node_index[`${fk_pairs_list[k]["table"]}_${fk_pairs_list[k]["column"]}`]
								: node_index[fk_pairs_list[k]["table"]],
							target_table: fk_pairs_list[k]["table"],
							target_column: fk_pairs_list[k]["column"],
							target_name: this.node_mode ? fk_pairs_list[k]["column"] : fk_pairs_list[k]["table"],
							type: "fk"
						})
						index_link_cnt++
					}
				}
			}
		}

		return { nodeList: nodeList, linkList: linkList }
	}
	updateData(DBdata) {
		this.DBdata = DBdata
		this.DBdataConverted = this.dataConvert()
		console.log(this.DBdataConverted)
		this.node = this.DBdataConverted["nodeList"]
		this.link = this.DBdataConverted["linkList"]
		this.DBTreeData = this.getDBTreeData()
		this.vueModule.DBInfoTree = this.DBTreeData
	}
	updateVis() {
		let that = this
		let transform = {
			x: 0,
			y: 0,
			k: 1
		}
		d3.select("#DBlinkG").selectAll(".DBLink").remove()
		d3.select("#DBnodeG").selectAll(".DBNode").remove()
		d3.select("#DBtextG").selectAll(".DBText").remove()
		let link = d3
			.select("#DBlinkG")
			.selectAll(".DBLink")
			.data(this.link)
			.enter()
			.append("line")
			.attr("class", "DBLink")
			.attr("x1", (d) => d.source.x)
			.attr("y1", (d) => d.source.y)
			.attr("x2", (d) => d.target.x)
			.attr("y2", (d) => d.target.y)
			.attr("fill", "none")
			.attr("stroke-width", 2)
			.attr("stroke", "#d7d7d7")
			.on("mouseover", (event, d) => {
				console.log("ggg")
				d3.select(`#DBText_${d.source_table}_${d.source_column}_${d.target_table}_${d.target_column}`).style(
					"opacity",
					1
				)
				console.log(
					d3.select(`#DBText_${d.source_table}_${d.source_column}_${d.target_table}_${d.target_column}`)
				)
			})
			.on("mouseout", (event, d) => {
				console.log("ggggg")
				d3.select(`#DBText_${d.source_table}_${d.source_column}_${d.target_table}_${d.target_column}`).style(
					"opacity",
					0
				)
			})

		let text = d3
			.select("#DBtextG")
			.selectAll(".DBText")
			.data(this.link)
			.enter()
			.append("text")
			.attr("class", (d) => `DBText fk_${d.source_table} fk_${d.target_table}`)
			.attr("x", (d) => (d.source.x + d.target.x) / 2)
			.attr("y", (d) => (d.source.y + d.target.y) / 2)
			.text((d) => `${d.source_table}_${d.source_column} = ${d.target_table}.${d.target_column}`)
			.attr("id", (d) => `DBText_${d.source_table}_${d.source_column}_${d.target_table}_${d.target_column}`)
			.attr("text-anchor", "middle")
			.style("opacity", 0)

		let node = d3
			.select("#DBnodeG")
			.selectAll(".DBNode")
			.data(this.node)
			.enter()
			.append("g")
			.attr("class", "DBNode")
			.attr("id", (d) => `DBNode_${d.name}`)
			.each(function (d) {
				let node_this = d3.select(this)
				node_this
					.append("rect")
					.attr("y", -19)
					.attr("x", -100)
					.attr("width", 200)
					.attr("height", 30)
					.attr("fill", "white")
					.attr("stroke", "black")
				node_this
					.append("text")
					.text(d.name)
					.attr("text-anchor", "middle")
					.attr("fill", "#000")
					.attr("color", "#000")
			})
			.on("click", function (event, data) {
				if (!"isExpand" in data) {
					data.isExpand = false
				}
				if (data.isExpand) {
					d3.select(this).select("foreignObject").remove()
					data.isExpand = false
					that.vueModule.removeSelectedTable(data.name)
					return
				} else {
					that.vueModule.addSelectedTable(data.name)
					let div = d3
						.select(this)
						.append("foreignObject")
						.attr("class", "DBDetailContainer")
						.attr("x", -100)
						.attr("y", 10)
						.attr("width", 200)
						.attr("height", 100)
						.attr("background-color", "white")
						.attr("border", "1px solid black")
						.append("xhtml:div")
						.attr("xmlns", "http://www.w3.org/1999/xhtml")
						.append("ul")
						.attr("class", "list-group  list-group-flush")
					for (let i = 0; i < data.columns.length; i++) {
						div.append("li")
							.text(data.columns[i])
							.attr("class", "list-group-item  ")
							.attr("style", "margin-top:0px;margin-bottom:0px;margin-left:5px; padding:0px;")
					}
					data.isExpand = true
				}
			})
			.on("mouseover", (event, d) => {
				console.log(d)
				console.log("ggg")
				//d3.selectAll(`.fk_${d.name}`).style("opacity", 1)
			})
			.on("mouseout", (event, d) => {
				console.log("ggggg")
				//d3.selectAll(`.fk_${d.name}`).style("opacity", 0)
			})
		this.force.on("tick", () => {
			node.attr("transform", (d) => {
				return `translate(${(d.x - transform.x) * transform.k + transform.x},${
					(d.y - transform.y) * transform.k + transform.y
				})`
			})
			link.attr("x1", (d) => (d.source.x - transform.x) * transform.k + transform.x)
				.attr("y1", (d) => (d.source.y - transform.y) * transform.k + transform.y)
				.attr("x2", (d) => (d.target.x - transform.x) * transform.k + transform.x)
				.attr("y2", (d) => (d.target.y - transform.y) * transform.k + transform.y)
			text.attr("x", (d) => ((d.source.x + d.target.x) / 2 - transform.x) * transform.k + transform.x).attr(
				"y",
				(d) => ((d.source.y + d.target.y) / 2 - transform.y) * transform.k + transform.y
			)
			if (this.force.alpha() < 0.2) {
				this.force.stop()
			}
		})
		let simulation = this.force

		node.call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended))
		function dragstarted(event) {
			if (!event.active) simulation.alphaTarget(0.3).restart()
			event.subject.fx = event.subject.x
			event.subject.fy = event.subject.y
		}
		function dragged(event) {
			event.subject.fx = event.x
			event.subject.fy = event.y
		}
		function dragended(event) {
			if (!event.active) simulation.alphaTarget(0)
			event.subject.fx = null
			event.subject.fy = null
		}
		let zoom = d3.zoom().on("zoom", zoomed)
		function zoomed() {
			transform = d3.zoomTransform(this)
			node.attr("transform", (d) => {
				return `translate(${(d.x - transform.x) * transform.k + transform.x},${
					(d.y - transform.y) * transform.k + transform.y
				})`
			})
			link.attr("x1", (d) => (d.source.x - transform.x) * transform.k + transform.x)
				.attr("y1", (d) => (d.source.y - transform.y) * transform.k + transform.y)
				.attr("x2", (d) => (d.target.x - transform.x) * transform.k + transform.x)
				.attr("y2", (d) => (d.target.y - transform.y) * transform.k + transform.y)
			text.attr("x", (d) => ((d.source.x + d.target.x) / 2 - transform.x) * transform.k + transform.x).attr(
				"y",
				(d) => ((d.source.y + d.target.y) / 2 - transform.y) * transform.k + transform.y
			)
		}
		this.DBVisSvg.call(zoom)
	}

	getDBdataConverted() {
		return this.DBdataConverted
	}
	getNode() {
		return this.node
	}
	getLink() {
		return this.link
	}
	getDBTableGridData(key) {
		this.DBTableGridData = []
		for (let k in this.DBdata.columns[key]["name"]) {
			this.DBTableGridData.push({
				name: this.DBdata.columns[key]["name"][k]
			})
		}
		return this.DBTableGridData
	}
	getDBTreeData() {
		this.DBTreeData = []
		for (let i = 0; i < this.DBdata.table_names.length; i++) {
			let table_name = this.DBdata.table_names[i]
			let tableData = {
				label: table_name,
				depth: 0,
				children: []
			}
			for (let j in this.DBdata.columns[table_name]["name"]) {
				let column_name = this.DBdata.columns[table_name]["name"][j]
				tableData.children.push({
					label: column_name,
					depth: 1,
					children: []
				})
			}
			this.DBTreeData.push(tableData)
		}
		return this.DBTreeData
	}
}
let DBVisModuleInstance = new DBVisModule("DBVisDiv", { columns: {}, fk_pairs: [], table_names: [] }, 510, 600, null)
export default {
	name: "DBPanel",
	data() {
		return {
			props: {
				label: "label",
				children: "children"
			},
			DBList: [],
			DBInfo: {
				table_names: [],
				columns: {}
			},
			selectedDB: "",
			DBVisModule: DBVisModuleInstance,
			configuration: {
				width: 400,
				height: 600
			},
			DBTableGridData: [],
			DBSelectedTable: [],
			DBSelectedTree: [],
			DBInfoTree: [
				{
					label: "SELECTED(0)",
					depth: 0,
					children: []
				},
				{
					depth: 0,
					label: "Level one 1",
					children: [
						{
							label: "Level two 1-1",
							depth: 1,
							children: [
								{
									depth: 2,
									label: "Level three 1-1-1"
								}
							]
						}
					]
				}
			]
		}
	},
	methods: {
		modifySelectTable(event, args) {
			let $icon = null
			if ($(event.target).is("i")) {
				$icon = $(event.target)
			} else {
				$icon = $(event.target).find("i")
			}
			if ($icon.hasClass("el-icon-plus")) {
				this.addSelectedTable(args.table_name)
				$icon.removeClass("el-icon-plus")
				$icon.addClass("el-icon-plus")
				if (d3.select(`#DBNode_${args.table_name}`).select("foreignObject").empty()) {
					d3.select(`#DBNode_${args.table_name}`).dispatch("click")
				}
			} else {
				this.removeSelectedTable(args.table_name)
				$icon.removeClass("el-icon-plus")
				$icon.addClass("el-icon-plus")
				if (!d3.select(`#DBNode_${args.table_name}`).select("foreignObject").empty()) {
					d3.select(`#DBNode_${args.table_name}`).dispatch("click")
				}
			}
			/* 			let $icon = null
			if ($(event.target).is("img")) {
				$icon = $(event.target)
			} else {
				$icon = $(event.target).find("img")
			}
			let $button = $icon.parent()

			if ($button.hasClass("unChosenTable")) {
				this.addSelectedTable(args.table_name)
				$button.find(".addIcon").addClass("hiddenComponent")
				$button.find(".removeIcon").removeClass("hiddenComponent")

				if (d3.select(`#DBNode_${args.table_name}`).select("foreignObject").empty()) {
					d3.select(`#DBNode_${args.table_name}`).dispatch("click")
				}
			} else {
				this.removeSelectedTable(args.table_name)
				$button.find(".addIcon").removeClass("hiddenComponent")
				$button.find(".removeIcon").addClass("hiddenComponent")
				console.log(d3.select(`#DBNode_${args.table_name}`).select("foreignObject")["_groups"][0])
				if (!d3.select(`#DBNode_${args.table_name}`).select("foreignObject").empty()) {
					d3.select(`#DBNode_${args.table_name}`).dispatch("click")
				}
			} */
		},
		expandOrHiddenIcon(id, toggle_id, args = {}) {
			if (toggle_id && $(`#${toggle_id}`).hasClass("collapsing")) {
				return
			}
			if ($(`#${id}`).hasClass("el-icon-arrow-right") && !(toggle_id && $(`#${toggle_id}`).hasClass("show"))) {
				$(`#${id}`).removeClass("el-icon-arrow-right")
				$(`#${id}`).addClass("el-icon-arrow-down")
				/* 			if ("selectTable" in args) {
					this.addSelectedTable(args.selectTable)
				} */
			} else if (toggle_id && $(`#${toggle_id}`).hasClass("show")) {
				$(`#${id}`).addClass("el-icon-arrow-right")
				$(`#${id}`).removeClass("el-icon-arrow-down")
				/* 			if ("selectTable" in args) {
					this.removeSelectedTable(args.selectTable)
				} */
			}
		},
		expandIcon(id) {
			$(`#${id}`).removeClass("el-icon-arrow-right")
			$(`#${id}`).addClass("el-icon-arrow-down")
		},
		hideIcon(id) {
			$(`#${id}`).addClass("el-icon-arrow-right")
			$(`#${id}`).removeClass("el-icon-arrow-down")
		},
		expandTableInfo() {
			if (this.$refs.iconTableInfo.classList.contains("el-icon-arrow-down")) {
				this.$refs.iconTableInfo.classList.remove("el-icon-arrow-down")
				this.$refs.iconTableInfo.classList.add("el-icon-arrow-right")
				this.$refs.tableInfoTree.$el.classList.add("hiddenComponent")
			} else {
				this.$refs.iconTableInfo.classList.add("el-icon-arrow-down")
				this.$refs.iconTableInfo.classList.remove("el-icon-arrow-right")
				this.$refs.tableInfoTree.$el.classList.remove("hiddenComponent")
			}
		},
		expandDBDiv() {
			if (this.$refs.DBVisDivButton.classList.contains("el-icon-arrow-down")) {
				this.$refs.DBVisDivButton.classList.remove("el-icon-arrow-down")
				this.$refs.DBVisDivButton.classList.add("el-icon-arrow-right")
				this.$refs.DBVisDiv.$el.classList.add("hiddenVisibilityComponent")
			} else {
				this.$refs.DBVisDivButton.classList.add("el-icon-arrow-down")
				this.$refs.DBVisDivButton.classList.remove("el-icon-arrow-right")
				this.$refs.DBVisDiv.$el.classList.remove("hiddenVisibilityComponent")
			}
		},
		handleClick() {
			alert("button click")
		},
		getDBList() {
			this.axios.get("/api/getDBList").then((res) => {
				this.DBList = res.data
				this.selectedDB = this.DBList[0]
				this.selectDB(this.selectedDB)
			})
		},
		getDBInfo() {
			this.axios.get("/api/getDBInfo").then((res) => {
				this.DBInfo = res.data
				this.DBVisModule.updateData(this.DBInfo)
				this.DBVisModule.updateForce()
				this.DBVisModule.updateVis()
			})
		},
		selectDB(selectedDB) {
			const args = { selectedDB: this.selectedDB }
			console.log(this.selectedDB)
			console.log(this.DBSelectedTable)
			this.DBSelectedTable = []
			this.axios.post("/api/updateDB", args).then((res) => {
				this.$bus.$emit("selectDB", this.selectedDB)
				this.DBInfo = res.data
				this.DBVisModule.updateData(this.DBInfo)
				this.DBVisModule.updateForce()
				this.DBVisModule.updateVis()
			})
		},
		updDBTableTooltip(DBTableGridData, x, y) {
			this.DBTableGridData = DBTableGridData
			d3.select("#DBTooltip")
				.style("left", x + "px")
				.style("top", y + "px")
				.style("display", "block")
		},
		addSelectedTable(table_name) {
			this.DBSelectedTable.push(table_name)
			this.DBSelectedTable = Array.from(new Set(this.DBSelectedTable))
			this.DBSelectedTable.sort()
		},
		removeSelectedTable(table_name) {
			this.DBSelectedTable = this.DBSelectedTable.filter((item) => item !== table_name)
			this.DBSelectedTable = Array.from(new Set(this.DBSelectedTable))
			this.DBSelectedTable.sort()
		}
	},
	mounted() {
		this.getDBList()
		this.getDBInfo()
		this.DBVisModule.initVis()
		this.DBVisModule.initVueModule(this)
		this.$bus.$on("updateSelectedSchema", (schema) => {
			for (let table_name of schema.table_names) {
				this.addSelectedTable(table_name)
			}
		})
	},
	watch: {
		selectDB(selectedDB) {
			console.log("this.DBSelectedTable")
			console.log(this.DBSelectedTable)
		}
	}
}
</script>
<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");

#DBPanelContainer {
	#DBTooltip {
		position: fixed;
		height: 100px;
		overflow: auto;
		border: 1px solid #515151;
		z-index: 999;
		display: none;
	}
	#DBPanelStatusDiv {
		background-color: #f3f3f3;
		font-size: 36px;
		text-align: center;
		display: flex;
		color: #50b498;
		align-items: center;
		justify-content: center;
	}
	#DBSelectMain {
		padding: 0px;
		height: auto;
		background-color: None;
	}
	#DBSelectMain::-webkit-scrollbar {
		display: none;
	}
	.DBSelectView {
		width: 492px;
		height: 60px;
		padding: 9px;
	}
	.DBSelectBar {
		padding-left: 0px;
		padding-right: 0px;
		width: 492px;
	}

	.hiddenComponent {
		display: none;
	}
	.hiddenVisibilityComponent {
		visibility: hidden;
	}
	.DBRowButton {
		width: 100%;
		text-align: left;
		background-color: #d7d7d7;
		border: 0px;
		padding-left: 0px;
		padding-right: 0px;
		font-size: 24px;
		font: inter;
	}
	.table_row {
		font-size: 24px;
		font: inter;
		margin-left: 5px;
	}
	.column_container {
		margin-left: 20px;
	}
	#DBVisDivButton {
		border: 0px;
		text-align: left;
		background-color: #d7d7d7;
		border: 0px;
		padding-left: 0px;
		padding-right: 0px;
	}
	#tableInfoButton {
		border: 0px;
		text-align: left;
		background-color: #d7d7d7;
		border: 0px;
		padding-left: 0px;
		padding-right: 0px;
	}
	.DBVisSvg {
	}
	#tableInfoTree {
		padding: 0px;
	}
	#tableInfoTreeInner {
		left: 10px;
		background-color: #d7d7d7;
	}
	#DBVisDiv {
		background-color: #f7f7f7;
	}
	span {
		color: black;
	}
	.el-scrollbar {
		span {
			color: black;
		}
	}

	#DBUMLDiv {
		width: 510px;
		height: 600px;
	}
	.DBDetailContainer {
		background-color: white;
		border: 1px solid black;
		overflow: auto;
		z-index: 999;
		div {
			text-align: left;
		}
	}
	.dbPanelRowButton {
		margin-left: 0px;
		margin-bottom: 10px;
	}
}
#DBPanelContainer::-webkit-scrollbar {
	display: none;
}
</style>
