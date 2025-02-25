import Vue from "vue"
import App from "./App.vue"
import "./registerServiceWorker"
import router from "./router"
import store from "./store"

import axios from "axios"
import VueAxios from "vue-axios"

Vue.use(VueAxios, axios)

Vue.config.productionTip = false

// Bootstrap
import { BootstrapVue, IconsPlugin } from "bootstrap-vue"
import "bootstrap/dist/css/bootstrap.css"
import "jquery/dist/jquery.min.js"
import "popper.js/dist/umd/popper.min.js"
import "bootstrap/dist/js/bootstrap.bundle.js"
import "bootstrap-vue/dist/bootstrap-vue.css"
Vue.use(BootstrapVue)
Vue.use(IconsPlugin)

import ElementUI from "element-ui"
import "element-ui/lib/theme-chalk/index.css"
Vue.use(ElementUI)

Vue.prototype.$bus = new Vue()
new Vue({
  router,
  store,
  render: (h) => h(App)
}).$mount("#app")
