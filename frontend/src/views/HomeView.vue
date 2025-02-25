<template>
	<el-container class="home">
		<el-header
			id="headerContainer"
			height="87px">
			<el-row>
				<img
					style="width: 72px; height: 72px"
					src="@/assets/image/icon.png"
					alt="..."
					:fit="`fill`" />
				<span style="font-weight: bold; padding-left: 10px">SQLGenie</span>
			</el-row>
		</el-header>
		<el-container>
			<el-aside
				id="selectPanelContainer"
				width="105px">
				<button
					@click="drawer = true"
					type="button"
					class="btn btn-link"
					style="border-top: 10px; margin-bottom: 15px; border-left: 5px solid white; padding-left: 26px">
					<img
						style="width: 48px; height: 48px"
						src="@/assets/image/database.png"
						alt="..."
						:fit="`fill`" />
				</button>
				<button
					@click="drawer = true"
					type="button"
					class="btn btn-link"
					style="margin-bottom: 15px; border-left: 5px solid none; padding-left: 26px">
					<img
						style="width: 48px; height: 48px"
						src="@/assets/image/chat_history.png"
						alt="..."
						:fit="`fill`" />
				</button>
				<button
					@click="saveLog"
					type="button"
					class="btn btn-link"
					style="margin-bottom: 15px; border-left: 5px solid none; padding-left: 26px">
					<img
						style="width: 48px; height: 48px"
						src="@/assets/image/save.png"
						alt="..."
						:fit="`fill`" />
				</button>
				<el-drawer
					:visible.sync="drawer"
					:direction="direction">
					<SelectBar />
				</el-drawer>
			</el-aside>
			<el-main id="mainContainer">
				<el-container id="DBPanelContainerFather">
					<el-aside
						id="DBPanelContainer"
						width="510px">
						<DBPanel />
					</el-aside>
					<el-main id="mainView">
						<el-row :gutter="20">
							<el-col :span="22"><ShowCommunication /></el-col>
						</el-row>
					</el-main>
				</el-container>
			</el-main>
		</el-container>
	</el-container>
</template>

<script>
// @ is an alias to /src
import ShowCommunication from "../components/ShowCommunication.vue"
import SelectBar from "../components/SelectBar.vue"
import DBPanel from "../components/DBPanel.vue"
export default {
	name: "HomeView",
	components: {
		ShowCommunication,
		SelectBar,
		DBPanel
	},
	data() {
		return {
			drawer: false,
			direction: "ltr",
			ActionRecord: {
				name: "uncreated",
				action: []
			}
		}
	},
	methods: {
		saveLog() {
			this.ActionRecord["endTime"] = new Date().toLocaleString()
			this.axios
				.post("/api/saveLog", { log: this.ActionRecord })
				.then((response) => {
					console.log(response)
					if (response.status == 200) {
						this.$message({
							message: "Save log successfully",
							type: "success"
						})
					} else {
						this.$message({
							message: "Save log failed",
							type: "error"
						})
					}
				})
				.catch((error) => {
					console.log(error)
				})
		}
	},
	mounted() {
		this.$bus.$on("newLog", (name) => {
			this.ActionRecord["name"] = name
			this.ActionRecord["createTime"] = new Date().toLocaleString()
			this.ActionRecord["action"] = []
		})
		this.$bus.$on("addAction", (action) => {
			this.ActionRecord["action"].push(action)
		})
		this.$bus.$on("selectDB", (db) => {
			this.ActionRecord["dbName"] = db
		})
	}
}
</script>
<style>
#mainView {
	height: auto;
	width: auto;
	padding: 0%;
}
#headerContainer {
	height: 87px;
	background-color: #515151;
	font: bold large 94px inter;
	font-size: 64px;
	color: white;
}
#selectPanelContainer {
	height: 1352px;
	background-color: #2c2c2c;
}
#DBPanelContainer {
	height: 1352px;
	background-color: #f3f3f3;
}

#mainContainer {
	height: 1352px;
	width: 2455px;
	padding: 0px;
	overflow: clip;
}
#DBPanelContainerFather {
	background-color: #f3f3f3;
	padding: 0%;
}
</style>
