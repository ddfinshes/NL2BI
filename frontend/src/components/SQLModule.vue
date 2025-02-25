<template>
  <el-container
    id="SQLModuleContainer"
    ref="SQLModuleContainer"
    width="300px"
    @scroll="handleScroll">
    <el-aside
      id="SQLDAGSvgContainer"
      ref="SQLDAGSvgContainer"
      :width="DAGWidth"></el-aside>
    <el-main id="SQLMainContainer" ref="SQLMainContainer">
      <el-divider ref="identifySQLContainerTop" id="identifySQLContainerTop"
        >SQL Module</el-divider
      >
      <el-row>Main question: {{ data.question }}</el-row>
      <el-row> Evidence: {{ data.evidence }}</el-row>
      <el-collapse v-model="activeNames" ref="collapseRef">
        <el-collapse-item
          v-for="subStep in data.COT"
          :key="subStep.index"
          @change="handleChange"
          class="subSteps">
          <template slot="title" class="subStepTitles">
            <el-input
              type="textarea"
              placeholder="SQL Code"
              :autosize="{ minRows: 0, maxRows: 15 }"
              v-model="subStep.subQuestion"
              ref="SQLmod"></el-input>
          </template>
          <subStepTemp
            :data="subStep"
            :ref="'subStepComponent_' + String(subStep.index)">
          </subStepTemp>
        </el-collapse-item>
      </el-collapse>
      <hr />
      <el-switch
        v-model="isShowSQL"
        @change="showSQLMod"
        inactive-text="Show SQL?">
      </el-switch>
      <el-row ref="SQLAssembleContainer" class="hidden">
        <el-input
          v-model="data.SQL"
          ref="SQLCode"
          placeholder="Please input your SQL code"
          type="textarea"
          :rows="5"
          :autosize="{ minRows: 0, maxRows: 15 }"
          @change="formatSQL"></el-input>
      </el-row>
      <el-row>
        <el-button type="primary" @click="generateNewSQL">Generate</el-button>
      </el-row>
      <el-row>
        <el-pagination
          small
          layout="prev, pager, next"
          :total="this.data.history.length"
          :current-page="currentPage"
          :page-size="1"
          @current-change="handleCurrentChange">
        </el-pagination
      ></el-row>
    </el-main>
  </el-container>
</template>
<script>
import VueMarkdown from "vue-markdown"
import subStepTemp from "./subStepTemp"
import * as d3 from "d3"

export default {
  name: "SQLModule",
  props: {
    data_input: {
      type: Object,
      required: true
    }
  },
  components: {
    VueMarkdown,
    subStepTemp
  },
  data() {
    return {
      isShowSQL: false,
      SQLCode: "SELECT \n* FROM table",
      SQLCodeTree: {},
      DAGWidth: "70px",
      activeNames: [],
      original_data: {},
      data: this.data_input,
      currentPage: this.data_input.history.length,
      pageSize: 10
    }
  },
  methods: {
    formatSQL() {
      const args = { sql: this.data.SQL }
      this.axios.post("/api/formatSQL", args).then((response) => {
        this.data.SQL = "\n" + response.data
        this.original_data.SQL = this.data.SQL
      })
    },
    formatSQLExternal(sql) {
      const args = { sql: sql }
      this.axios.post("/api/formatSQL", args).then((response) => {
        return "\n" + response.data
      })
    },
    drawDAG() {
      let DAGContainer = d3.select(this.$refs.SQLDAGSvgContainer.$el)

      let width = this.$refs.SQLDAGSvgContainer.$el.clientWidth
      let height = this.$refs.SQLMainContainer.$el.clientHeight
      DAGContainer.select("svg").remove()
      let DAGSvg = DAGContainer.append("svg")
        .attr("width", width)
        .attr("height", height)

      let mainContainer = d3.select(this.$refs.SQLModuleContainer.$el)

      let coordinatesList = []
      let y_base = this.$refs.SQLMainContainer.$el.getBoundingClientRect().top
      mainContainer.selectAll(".subSteps").each(function () {
        // 使用 this 来获取当前 DOM 元素
        let boundingRect = this.getBoundingClientRect()
        coordinatesList.push({
          x: boundingRect.left, // 元素的 X 坐标
          y: boundingRect.top - y_base + 30 // 元素的 Y 坐标
        })
      })

      let edgeRaw = this.data.COT
      let edges = []

      edgeRaw.forEach((d, i) => {
        let target = +i
        let sourceList = d.previousQuestion
        sourceList.forEach((source) => {
          edges.push({
            source: +source,
            target: target
          })
        })
      })
      let maxCur = d3.max(edges, (d) => d.target - d.source)
      maxCur += 1

      let bezCurverGen = (d) => {
        let x0 = width - 10
        let y0 = coordinatesList[d.source].y
        let x1 = width - 10
        let y1 = coordinatesList[d.target].y
        let path = d3.path()
        path.moveTo(x0, y0)
        path.quadraticCurveTo(
          +(x0 - 10) * (1 - (d.target - d.source) / maxCur),
          y0 * 0.5 + y1 * 0.5,
          x1,
          y1
        )
        return path.toString()
      }
      DAGSvg.append("defs")
        .selectAll("marker")
        .data(edges)
        .enter()
        .append("marker")
        .attr("id", (d) => `arrow_${d.source}_${d.target}`)

        .attr("refX", 20)
        .attr("refY", 5)
        .attr("markerWidth", 20)
        .attr("markerHeight", 20)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M 0 0 L 10 5 L 0 10 z") // 定义箭头的形状
        .attr("fill", "black")
      DAGSvg.append("g")
        .attr("id", "SQLDAGEdges")
        .selectAll("path")
        .data(edges)
        .enter()
        .append("path")
        .attr("d", bezCurverGen)
        .attr("fill", "none")
        .attr("stroke", "black")
        .attr("stroke-width", 1)
        .attr("marker-end", (d) => `url(#arrow_${d.source}_${d.target})`)
      DAGSvg.append("g")
        .attr("id", "SQLDAGNodes")
        .selectAll("circle")
        .data(coordinatesList)
        .enter()
        .append("circle")
        .attr("cx", (d) => width - 10)
        .attr("cy", (d) => d.y)
        .attr("r", 10)
        .attr("fill", "white")
        .attr("stroke", "black")
      DAGSvg.append("g")
        .attr("id", "SQLDAGTexts")
        .selectAll("text")
        .data(coordinatesList)
        .enter()
        .append("text")
        .attr("x", width - 10)
        .attr("y", (d) => d.y)
        .text((d, i) => i + 1)
        .attr("font-size", "10px")
        .attr("text-anchor", "middle")
        .attr("alignment-baseline", "middle")
    },
    handleChange() {

    },
    handleScroll() {
      console.log("gggg")
      this.drawDAG()
    },
    showSQLMod() {
      console.log(this.isShowSQL)
      if (this.isShowSQL) {
        this.$refs.SQLAssembleContainer.$el.classList.remove("hidden")
      } else {
        this.$refs.SQLAssembleContainer.$el.classList.add("hidden")
      }
    },
    generateNewSQL() {
      let data = JSON.parse(JSON.stringify(this.data))
      data.COT.forEach((d) => {
        d = this.$refs["subStepComponent_" + String(d.index)][0].getData()
      })
      console.log(data)
      console.log(this.original_data)
      if (false) {
        pass
      } else {
        const args = { original_data: this.original_data, data: data }
        this.axios.post("/api/modifySQL", args).then((response) => {
          console.log(response.data)
          this.data = JSON.parse(JSON.stringify(response.data))
          this.original_data = JSON.parse(JSON.stringify(response.data))
        })
      }
    },
    handleCurrentChange(page) {
      console.log()
      this.currentPage = page
      this.data.COT = this.data.history[this.currentPage - 1].COT
      this.data.SQL = this.data.history[this.currentPage - 1].SQL
      this.data.dbName = this.data.history[this.currentPage - 1].dbName
      this.data.question = this.data.history[this.currentPage - 1].question
      this.data.evidence = this.data.history[this.currentPage - 1].evidence
      this.data.dbPath = this.data.history[this.currentPage - 1].dbPath
      this.data.previousModify =
        this.data.history[this.currentPage - 1].previousModify
      this.data.modifyCnt = this.data.history[this.currentPage - 1].modifyCnt
      this.data.tableSchema =
        this.data.history[this.currentPage - 1].tableSchema
      this.data.time = this.data.history[this.currentPage - 1].timetime

      this.original_data.COT =
        this.original_data.history[this.currentPage - 1].COT
      this.original_data.SQL =
        this.original_data.history[this.currentPage - 1].SQL
      this.original_data.dbName =
        this.original_data.history[this.currentPage - 1].dbName
      this.original_data.question =
        this.original_data.history[this.currentPage - 1].question
      this.original_data.evidence =
        this.original_data.history[this.currentPage - 1].evidence
      this.original_data.dbPath =
        this.original_data.history[this.currentPage - 1].dbPath
      this.original_data.previousModify =
        this.original_data.history[this.currentPage - 1].previousModify
      this.original_data.modifyCnt =
        this.original_data.history[this.currentPage - 1].modifyCnt
      this.original_data.tableSchema =
        this.original_data.history[this.currentPage - 1].tableSchema
      this.original_data.time =
        this.original_data.history[this.currentPage - 1].timetime
      this.drawDAG()
    }
  },
  mounted() {
    let that =this
    // 创建 ResizeObserver 实例
    console.log(this.data)
    this.original_data = JSON.parse(JSON.stringify(this.data))
    console.log(this.original_data)

    this.formatSQL()
    async function updateSubSQL(i) {
      try {
        const formattedSQL = await that.formatSQLExternal(
          that.data.COT[i].subSQL
        )
        that.data.COT[i].subSQL = formattedSQL
        that.original_data.COT[i].subSQL = formattedSQL
      } catch (error) {
        console.error("Error formatting SQL:", error)
      }
    }
    console.log(('length'))
    console.log((this.data))
    for (let i = 0; i < this.data.COT.length; i++) {
      updateSubSQL(i)
    }

    this.resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        this.drawDAG()
      }
    })

    // 开始观察目标元素
    this.resizeObserver.observe(this.$refs.collapseRef.$el)
    this.$refs.SQLMainContainer.$el.addEventListener("scroll", this.drawDAG)
  },
  beforeDestroy() {
    // 在组件销毁时断开观察
    if (this.resizeObserver) {
      this.resizeObserver.disconnect()
    }
    this.$refs.SQLMainContainer.$el.removeEventListener("scroll", this.drawDAG)
  }
}
</script>
<style scoped>
#SQLModuleContainer {
  height: auto;
  width: 1000px;
  border: 1px solid #000;
  background-color: white;
  max-height: 1000px;
}
#SQLDAGSvgContainer {
  height: 100%;
}
#SQLMainContainer {
  text-align: left;
  width: auto;
  overflow: auto;
}
.hidden {
  display: none;
}
</style>
