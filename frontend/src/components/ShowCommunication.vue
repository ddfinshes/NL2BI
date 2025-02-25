<template>
	<div
		class=""
		id="communication-container"
		ref="communicationContainer">
		<!--    <el-row> <SQLModule :data="testSQL" /> </el-row> -->
		<div style="position: absolute; font-size: 40px; font-weight: 700; left: 40px; top: 28px;color:#4b4848">
			GPT-4o
			<img
				style="width: 36px; height: 36px"
				src="@/assets/image/refresh-page-option 1.png"
				alt="..."
				:fit="`fill`" />
		</div>
		<el-row
			class="chat-container"
			ref="chatContainer"
			:key="`selectCommunicationTurnCnt_${selectedCommunication.id ? selectedCommunication.id : -1}_${
				selectedCommunication.communication ? selectedCommunication.communication.length : -1
			}`">
			<el-row
				:class="{ row: true }"
				style="padding-left: 5%; padding-right: 5%"
				v-for="turn in selectedCommunication.communication">
				<el-container
					:class="{
						message: true,
						chatUser: turn.isUser,
						chatGPT: !turn.isUser
					}">
					<el-aside
						v-if="!turn.isUser"
						width="70px"
						style="overflow: visible">
						<img
							class="mr-3"
							alt="..."
							style="width: 72px; height: 72px"
							src="@/assets/image/robot.png" />
					</el-aside>

					<el-main
						v-if="!turn.isloading"
						style="overflow: visible">
						<div
							v-if="!turn.isSQL"
							class="bubble"
							style="padding-left: 30px; padding-right: 30px">
							<vue-markdown>{{ turn.context }}</vue-markdown>
						</div>
						<div
							v-if="turn.isSQL && !turn.isSQLTG"
							class="bubble">
							<IntentionConfirmationModule :dataInput="turn"></IntentionConfirmationModule>
						</div>
						<div
							v-if="turn.isSQLTG"
							class="bubble">
							<QueryGenerationModule :dataInput="turn"></QueryGenerationModule>
						</div>
					</el-main>
					<el-main v-else>
						<div class="bubble">
							<div
								class="spinner-border text-primary"
								role="status">
								<span class="sr-only">Loading...</span>
							</div>
						</div>
					</el-main>
					<el-aside
						v-if="turn.isUser"
						width="70px"
						style="overflow: visible">
						<img
							class="mr-3"
							style="width: 72px; height: 72px"
							alt="..."
							src="@/assets/image/human.png" />
					</el-aside>
				</el-container>
			</el-row>
		</el-row>

		<el-row
			class="input-container"
			id="chat-GPT-container"
			ref="chatGPTContainer"
			style="background-color: #e7e7e7 !important">
			<textarea
				type="text"
				id="inputField"
				ref="inputField"
				v-model="inputValue"
				placeholder="Send message..."
				@keyup.enter="sendContext()"
				@input="updateValue"></textarea>
			<button
				class="send-button btn btn-light"
				style="background-color: #e7e7e7; border: 0px"
				@click="sendContext()">
				<img
					style="width: 64px; height: 64px"
					src="@/assets/image/send.png"
					alt="..."
					:fit="`fill`" />
			</button>
		</el-row>
	</div>
</template>

<script>
import VueMarkdown from "vue-markdown"
export default {
	name: "ShowCommunication",
	components: {
		VueMarkdown,
		SQLModule: () => import("@/components/SQLModule.vue"),
		IntentionConfirmationModule: () => import("@/components/IntentionConfirmationModule.vue"),
		QueryGenerationModule: () => import("@/components/QueryGenerationModule.vue")
	},
	data() {
		return {
			selectedCommunication: { communication: [] },
			inputValue: ""
		}
	},

	computed: {},
	mounted() {
		this.$bus.$on("selectCommunication", (selectedCommunicationID) => {
			let params = {
				id: selectedCommunicationID
			}
			this.axios
				.get("/api/selectCommunication", { params })
				.then((res) => {
					this.selectedCommunication = res.data
				})
				.catch((error) => {})
		})
		this.$bus.$on("newSolution", (solution) => {
			this.selectedCommunication.communication.push(solution)
		})
		this.$bus.$on("newQuestion", (question) => {
			this.selectedCommunication.communication.push(question)
			/*
			let params = {
				id: this.selectedCommunication.id
			}
			this.axios
				.get("/api/selectCommunication", { params })
				.then((res) => {
					console.log(res)
					this.selectedCommunication = res.data
				})
				.catch((error) => {})*/
		})
	},
	methods: {
		updateValue(event) {
			this.inputValue = event.target.value
			let textarea = this.$refs.inputField
			let communicationContainer = this.$refs.communicationContainer
			textarea.style.height = "auto" // 先将高度重置为auto，以便重新计算

			textarea.style.height =
				textarea.scrollHeight < window.innerHeight * 0.38
					? textarea.scrollHeight + "px"
					: window.innerHeight * 0.38 + "px" // 根据内容设置高度
		},
		sendContext() {
			let params = {
				context: this.inputValue
			}
			this.selectedCommunication.communication.push({
				isUser: true,
				context: this.inputValue
			})
			this.selectedCommunication.communication.push({
				isUser: false,
				context: "",
				isloading: true
			})
			this.inputValue = ""
			this.$nextTick(() => {
				this.scrollToBottom()
			})
			this.$bus.$emit("addAction", {
				action: "sendContext",
				context: params.context,
				time: new Date().toLocaleString()
			})
			this.axios
				.get("/api/sendContext", { params })
				.then((res) => {
					this.selectedCommunication.communication.pop()
					this.selectedCommunication.communication.pop()
					this.selectedCommunication = res.data
					this.scrollToBottom()
					this.$bus.$emit("addAction", {
						action: "receiveContext",
						data: res.data,
						time: new Date().toLocaleString()
					})
				})
				.catch((error) => {
					console.error(error)
				})
		},

		scrollToBottom() {
			/*       let container = this.$refs.communicationContainer
      container.scrollTop = container.scrollHeight */
			console.log(this.$refs.chatContainer.$el.scrollHeight)
			this.$refs.chatContainer.$el.scrollTo(0, this.$refs.chatContainer.$el.scrollHeight)
		}
	}
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style>
#communication-container {
	padding-left: 30px;
	padding-right: 30px;
	width: 1945px;
	height: 1352px;
	background-color: white;

	h3 {
		margin: 40px 0 0;
	}
	ul {
		list-style-type: none;
		padding: 0;
	}
	li {
		display: inline-block;
		margin: 0 10px;
	}
	a {
		color: #42b983;
	}
	hr {
		border: 0;
		clear: both;
		display: block;
		width: 96%;
		background-color: #f3f3f3;
		height: 1px;
	}
	.chatUser {
		text-align: right;
	}

	.chatGPT {
		text-align: left;
	}

	pre {
		display: block;
		padding: 9.5px;
		margin: 0 0 10px;
		font-size: 13px;
		line-height: 1.42857143;
		color: #333;
		word-break: break-all;
		word-wrap: break-word;
		background-color: #f5f5f5;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	#chat-GPT-container {
		position: fixed;
		width: 40%;
		height: auto;
		bottom: 20px;
		max-height: 40%;
		left: 42%;
		display: flex;
	}

	.input-container {
		align-items: center;
		padding: 10px;
		background-color: #f7f7f7;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		textarea {
			flex: 1;
			padding: 10px;
			border: none;
			border-radius: 8px;
			font-size: 16px;
			outline: none;
			box-shadow: none;
			color: #333;
			background-color: #e7e7e7;
			&#inputField {
				overflow-y: auto;
			}
			&::placeholder {
				color: #aaa;
			}

			&:focus {
				border: 1px solid #007bff;
			}
		}
	}

	.message {
		display: flex;
		margin: 10px;
		&.chatUser {
			.bubble {
				font-size: 24px;
				float: right;
				background-color: #f3f3f3;
				align-self: flex-end;
				p {
					text-align: left;
				}
			}
		}

		&.chatGPT {
			justify-content: flex-start;

			.bubble {
				float: left;

				background-color: #f3f3f3;
				align-self: flex-start;
				p {
					align-self: flex-start;
				}
			}
		}

		.bubble {
			max-width: 1155px;
			padding: 10px 15px;
			border-radius: 20px;
			font-size: 16px;
			line-height: 1.4;
			box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		}
	}
	.chat-container {
		margin-bottom: 10%;
		height: 100%;
		padding-bottom: 200px;
		overflow-y: auto;

		overflow-x: clip;
	}
	.chat-container::-webkit-scrollbar {
		display: none;
	}
}
</style>
