
const namespace = "/shortener"

const socket = io(location.protocol + '//' + document.domain + ':' + location.port + namespace);

function copyToClipboard() {
    /* Get the text field */
    let copyText = document.querySelector('#cholli-url')
    copyText.setAttribute('type', 'text')    // 不是 hidden 才能複製
    copyText.select()  
    /* Select the text field */
    copyText.setSelectionRange(0, 99999); /* For mobile devices */
  
    /* Copy the text inside the text field */
    document.execCommand("copy");
    copyText.setAttribute('type', 'hidden');
    window.getSelection().removeAllRanges();
}

function fixUrlSection(fixed=false){
    let width = window.innerWidth;
    if (width <= 900 && fixed ){
        return 'fix-url-section';
    }
    return '';
}

function validURL(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
      '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
      '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
      '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
      '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
      '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
    return !!pattern.test(str);
}

function testUrls(){
    app.urls.push({'created':'5 FEB 2021', 'title':'AMAZON BEST PURCHASE', 'url':'cholli.to/asdas', 'original_url':'amazon.com/asdasdasdas', 'clicks':0})
}

app =  new Vue({
    el:"#main-app",
    data:{
        urls:[],
        item:null,
        total_links:0,

        show_created_item:null,
        show_modal:false,
        show_creation:false,
        show_menu:false,
        show_delete_menu:false,
        creation_name:"",
        creation_url:"",
        animation_started:false,
        url_section_style:'',
        uuid:''
    },
    methods:{
        validate(index){
            try{
            if (this.item.index == index){
                return 'chollitos-item--ACTIVE'
            }
            return 'chollitos-item--MAIN'
        }catch{
            return 'chollitos-item--MAIN'
        }
        },
        switchTo(index){
            this.item = this.urls[index];
            this.item.index = index;
            this.fixBrokeUrlSection(fixed=true);
        },
        closeDetailWindow(){
            this.item = null;
            this.fixBrokeUrlSection();
        },
        closeModal(){
            this.show_modal = false;
            this.show_creation = false;
            this.show_menu = false;
            this.show_delete_menu = false;
            this.creation_name = '';
            this.creation_url = '';
            this.show_created_item = false;
        },
        closeModalOnCreatedItem(){
            this.closeModal();
            this.item = null;
        },
        newLinkWindow(){
            this.show_menu = false;
            this.show_modal = true;
            this.show_creation = true;
        },
        showMenu(){
            this.show_creation = false;
            this.show_modal = true;
            this.show_menu = true;
        },
        createLink(){
            if (this.creation_url.length > 1 && validURL(this.creation_url)){
                socket.emit('add_url', {title:this.creation_name, url:this.creation_url})
                this.closeModal();
            }
        },
        onClick(){
            this.animation_started = true;
            copyToClipboard();
            setTimeout(()=>{
                this.activeAnimation()
            }, 400)
        },
        activeAnimation(){
            this.animation_started = !this.animation_started;
        },
        verifyAnimation(){
            if (this.animation_started){
                return 'on-click'
            }
            return ''
        },
        deleteElement(){

            if (this.uuid.length > 1){
                socket.emit("delete_url", this.uuid);
            }
            this.closeModal();
            this.item = null;
        },
        showDeleteMenu(uuid){
            this.show_delete_menu = true;
            this.show_modal = true;
            this.uuid = uuid;
        },
        showItemResponse(data){
            this.closeModal();
            this.show_modal = true;
            this.show_created_item = true;
            this.item = data;
        },
        fixBrokeUrlSection(fixed=false){
            this.url_section_style = fixUrlSection(fixed);
        },
        getUrlSection(){
            return this.url_section_style;
        }
    }
});

socket.on('connect', ()=>{
    socket.emit('connected', app.urls)
    socket.emit('get_total_urls')
});

socket.on('add_urls', (urls)=>{
    app.urls = urls;
    app.urls.reverse();
});

socket.on('add_total_urls', (data)=>{
    app.total_links = data.total;
});

socket.on('created_item_response', (data)=>{
    app.showItemResponse(data);
});