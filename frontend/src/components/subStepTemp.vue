<template>
  <div v-on:click="handleClickOutside" ref="container">
    <el-input
      type="textarea"
      placeholder="Step Description"
      :autosize="{ minRows: 7, maxRows: 15 }"
      v-model="data.stepDescription"></el-input>

    <pre v-on:click.stop="handleClickInside" ref="SQLcode">
      {{ data.subSQL }}
    </pre>
    <div ref="SQLmoddiv" class="hidden">
      <el-input
        type="textarea"
        placeholder="SQL Code"
        :autosize="{ minRows: 0, maxRows: 15 }"
        v-model="data.subSQL"
        ref="SQLmod"></el-input>
    </div>
    <el-button type="primary" @click="formatSQL">Format</el-button>
    <el-button type="primary" @click="executeSQL">Execute</el-button>
    <el-row ref="executeTableContainer" :class="['hidden']">    <el-table ref="executeTable" :data="excuteResult" height="250" >
      <el-table-column
        v-for="item in column_names"
        :prop="item"
        :label="item"></el-table-column>
    </el-table></el-row>

  </div>
</template>

<script>
import VueMarkdown from "vue-markdown"
export default {
  name: "subStepTemp",
  components: {
    VueMarkdown
  },
  props: {
    data: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      excuteResult: [],
      column_names: []
    }
  },
  mounted() {
    this.$emit("template-loaded")
    this.formatSQL()

  },
  methods: {
    formatSQL() {
      const args = { sql: this.data.subSQL }
      this.axios.post("/api/formatSQL", args).then((response) => {
        this.data.subSQL = "\n" + response.data
      })
    },

    runSQL() {},
    handleClickInside(event) {
      this.$refs.SQLcode.classList.add("hidden")
      this.$refs.SQLmoddiv.classList.remove("hidden")
    },
    handleClickOutside(event) {
      // 获取点击的目标元素
      const target = event.target

      // 判断点击是否在指定的区域外
      if (
        !this.$refs.SQLcode.contains(target) &&
        !this.$refs.SQLmod.$el.contains(target)
      ) {
        // 执行你想要的操作
        this.$refs.SQLcode.classList.remove("hidden")
        this.$refs.SQLmoddiv.classList.add("hidden")
      }
    },
    getData() {
      return this.data
    },
    executeSQL() {
      const args = { sql: this.data.subSQL }
      this.axios.post("/api/executeSQL", args).then((response) => {

        if ("error" in response.data) {
          this.$message.error(response.data.error)
          return
        }
        this.column_names = response.data.column_names
        

        let data = []
        for (let i = 0; i < response.data.table.length; i++) {
          let iter = {}
          for (let j = 0; j < this.column_names.length; j++) {
            iter[this.column_names[j]] = response.data.table[i][j]
          }
          data.push(iter)
        }
        this.excuteResult = data
        this.$refs.executeTableContainer.$el.classList.remove("hidden")
      })
    }
  }
}
</script>
<style scoped>
.hidden {
  display: none;
}
</style>
