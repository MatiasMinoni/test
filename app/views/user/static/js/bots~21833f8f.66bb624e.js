(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["bots~21833f8f"],{"28ed":function(t,e,o){"use strict";o.r(e);var n=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("c-flex",{staticClass:"main__container--chollos",attrs:{align:"center",justify:"start"}},[o("c-box",{staticClass:"main__tabs-container"},[o("c-flex",{staticClass:"chollos__configuration-container"},[t._l(t.bots,(function(t){return o("BotBox",{key:t.bot_id,attrs:{name:t.name,botId:t.bot_id}})})),o("c-box",{staticClass:"create-bot-container"},[o("CreateBotDrawer")],1)],2)],1)],1)},a=[],c=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("c-box",{staticClass:"config__box-container"},[o("div",{staticClass:"config__background"}),o("c-flex",{staticClass:"config__flex-container",attrs:{flexDirection:"column",justifyContent:"space-between"}},[o("c-box",{attrs:{display:"flex",justifyContent:"space-between"}},[o("c-heading",{attrs:{id:"header"}},[t._v(t._s(t.name)+" ")]),o("c-tooltip",{attrs:{label:"Activo",placement:"bottom"}},[o("c-box",{attrs:{h:"15px"}},[o("c-icon",{attrs:{name:"circle",color:"green.400",size:"5"}})],1)],1)],1),o("c-box",{staticClass:"config__button-container",attrs:{textAlign:"end"}},[o("c-button",{attrs:{"variant-color":"blue"},on:{click:function(e){t.$router.push({name:"bot_config",params:{id:t.botId}}),t.$store.state.currentBotName=t.name,t.$store.state.currentBotId=t.botId}}},[t._v(" Configurar ")])],1)],1)],1)},s=[],r={props:{name:String,botId:{type:String,required:!0}},data:function(){return{}}},i=r,l=(o("5043"),o("2877")),u=Object(l["a"])(i,c,s,!1,null,"7aea2a19",null),d=u.exports;const b=o("eb99");b(u,{CHeading:o("89e8").CHeading,CIcon:o("89e8").CIcon,CBox:o("89e8").CBox,CTooltip:o("89e8").CTooltip,CButton:o("89e8").CButton,CFlex:o("89e8").CFlex});var C=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",[o("c-icon-button",{attrs:{"variant-color":"red","aria-label":"Crear un nuevo bot",icon:"plus",size:"lg",isRound:!0,isDisabled:!t.available_button},on:{click:function(e){t.isOpen=!0}}}),o("c-modal",{attrs:{"is-open":t.isOpen,"on-close":t.close}},[o("c-modal-content",{ref:"content"},[o("c-modal-header",[t._v("Crear un nuevo bot 🤖")]),o("c-modal-close-button"),o("c-modal-body",[o("c-form-control",[o("c-form-label",[t._v(" Nombre del bot "),o("c-tooltip",{attrs:{"has-arrow":"",label:"No te preocupes, podrás configurar tu bot más adelante! 🥳",placement:"top",bg:"blue.600"}},[o("c-icon",{attrs:{name:"info-circle",size:"0.9em",focusable:"true"}})],1)],1),o("c-input",{ref:"initialRef",attrs:{placeholder:"Ej. ChollitoWeb"},model:{value:t.name,callback:function(e){t.name=e},expression:"name"}})],1)],1),o("c-modal-footer",[o("c-button",{attrs:{"variant-color":"blue",mr:"3",isLoading:t.isLoading,loadingText:"Creando.. 🤖"},on:{click:t.createBot}},[t._v("Crear bot")]),o("c-button",{on:{click:t.close}},[t._v("Cancelar")])],1)],1),o("c-modal-overlay")],1)],1)},f=[],m=(o("b0c0"),{data:function(){return{isOpen:!1,name:"",available_button:!1,isLoading:!1}},methods:{open:function(){this.isOpen=!0},close:function(){this.isOpen=!1},createBot:function(){this.isLoading=!0,this.$socket.client.emit("create_bot",{name:this.name})}},mounted:function(){var t=this;this.$socket.client.emit("get_available_instances_count"),this.$socket.$subscribe("set_available_instances_count",(function(e){e>=1&&(t.available_button=!0)})),this.$socket.$subscribe("create_bot_status",(function(e){e.status?(t.$toast({title:"Bot creado! 🥳",description:"El bot se ha creado exitosamente.",status:"success",duration:9e3,variant:"subtle"}),t.$router.push({name:"bot_config",params:{id:e.bot_id}}),t.$store.state.currentBotId=e.bot_id,t.$store.state.currentBotName=e.name):t.$toast({title:"Error! 😥 ",description:"Oops, ha ocurrido un error al intentar crear el bot.",status:"error",duration:9e3,variant:"subtle"}),t.isLoading=!1,t.close()}))}}),p=m,_=Object(l["a"])(p,C,f,!1,null,null,null),v=_.exports;const h=o("eb99");h(_,{CIconButton:o("89e8").CIconButton,CModalHeader:o("89e8").CModalHeader,CModalCloseButton:o("89e8").CModalCloseButton,CIcon:o("89e8").CIcon,CTooltip:o("89e8").CTooltip,CFormLabel:o("89e8").CFormLabel,CInput:o("89e8").CInput,CFormControl:o("89e8").CFormControl,CModalBody:o("89e8").CModalBody,CButton:o("89e8").CButton,CModalFooter:o("89e8").CModalFooter,CModalContent:o("89e8").CModalContent,CModalOverlay:o("89e8").CModalOverlay,CModal:o("89e8").CModal});var x={components:{BotBox:d,CreateBotDrawer:v},data:function(){return{bots:[]}},methods:{},activated:function(){this.$root.$emit("add_title","Bots"),this.bots=this.$store.state.bots}},B=x,g=(o("43d5"),Object(l["a"])(B,n,a,!1,null,"f1b43806",null));e["default"]=g.exports;const $=o("eb99");$(g,{CBox:o("89e8").CBox,CFlex:o("89e8").CFlex})},4111:function(t,e,o){},"43d5":function(t,e,o){"use strict";o("4111")},"4e1e":function(t,e,o){},5043:function(t,e,o){"use strict";o("4e1e")}}]);
//# sourceMappingURL=bots~21833f8f.66bb624e.js.map