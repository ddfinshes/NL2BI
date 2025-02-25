<template>
  <div class="list-group">
    <div class="row input-container">
      <textarea
        type="text"
        placeholder="new chat"
        @input="updateValue"></textarea>

      <el-button type="primary" @click="startNewChat()">New!</el-button>
    </div>
    <div
      :class="{
        'list-group-item': true,
        row: true,
        active: communicationHead == selectedCommunicationHead
      }"
      v-for="communicationHead in communicationHeadList"
      :key="communicationHead.id"
      @click="selectCommunication(communicationHead)">
      {{ communicationHead.name }}
    </div>
  </div>
</template>
<script>
import axios from "axios"
export default {
  name: "SelectBar",
  data() {
    return {
      communicationHeadList: [],
      selectedCommunicationHead: null,
      inputValue: ""
    }
  },
  methods: {
    updateValue(event) {
      this.inputValue = event.target.value
    },
    fetchCommunicationList() {
      let path = "/api/getCommunicationList"

      axios
        .get(path)
        .then((res) => {
          this.communicationHeadList = res.data

          this.selectCommunication(this.communicationHeadList[0])
        })
        .catch((error) => {
          console.error(error)
        })
    },
    selectCommunication(selectedCommunicationHead) {
      this.selectedCommunicationHead = selectedCommunicationHead
      this.$bus.$emit("selectCommunication", selectedCommunicationHead.id)
    },
    startNewChat() {
      let params = {
        name: this.inputValue
      }
      axios
        .get("/api/startNewChat", { params })
        .then((res) => {
          this.fetchCommunicationList()
          this.$bus.$emit('newLog',this.inputValue)
          this.inputValue = ""

        })
        .catch((error) => {
          console.error(error)
        })
    }
  },

  created() {
    this.fetchCommunicationList()
  }
}
</script>
<style scoped>
.list-group {
  margin: 20px;
}
</style>
