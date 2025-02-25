const { defineConfig } = require("@vue/cli-service")
var webpack = require("webpack")
/* module.exports = defineConfig({
  transpileDependencies: true
})
 */
module.exports = {
  configureWebpack: {
    devServer: {
      proxy: {
        // 如果请求地址以/api打头,就出触发代理机制
        "/api": {
          target: "http://localhost:5006",
          pathRewrite: {
            "^/api": ""
          }
        }
      }
    },
    plugins: [
      new webpack.ProvidePlugin({
        $: "jquery",
        jQuery: "jquery",
        jquery: "jquery",
        "windows.jQuery": "jquery"
      })
    ]
  }
}
